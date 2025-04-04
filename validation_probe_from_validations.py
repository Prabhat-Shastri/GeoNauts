import os
import json
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import shape
from shapely import wkt

# --- CONFIGURATION ---
BASE_DIR = "/Users/kush/Chicago_Hackathon_Expanded_Datasets"  # CHANGE THIS to your actual path
BUFFER_RADIUS_SIGNS = 100  # meters for nearby sign analysis
decel_results_path = os.path.join(BASE_DIR, "violation_probe_all.geojson")

# --- Step 1: Load Deceleration Results ---
decel_gdf = gpd.read_file(decel_results_path)

# Convert geometry strings to shapely geometries if needed
if isinstance(decel_gdf.geometry.iloc[0], str):
    print("🔁 Converting geometry strings to Shapely geometries...")
    decel_gdf['geometry'] = decel_gdf['geometry'].apply(wkt.loads)
    decel_gdf = gpd.GeoDataFrame(decel_gdf, geometry='geometry', crs="EPSG:3857")

# --- Helper Function: Extract Sign Info ---
def extract_sign_info(properties):
    """
    Extract the functional class and pedestrian access from sign properties.
    Handles cases where these fields might be lists or dictionaries.
    """
    fc = None
    pedestrian = None
    try:
        if "functionalClass" in properties:
            if isinstance(properties["functionalClass"], list):
                if len(properties["functionalClass"]) > 0:
                    fc = properties["functionalClass"][0].get("value", None)
            else:
                fc = properties["functionalClass"]
        if "accessCharacteristics" in properties:
            if isinstance(properties["accessCharacteristics"], list):
                if len(properties["accessCharacteristics"]) > 0:
                    pedestrian = properties["accessCharacteristics"][0].get("pedestrian", None)
            else:
                pedestrian = properties["accessCharacteristics"].get("pedestrian", None)
    except Exception as e:
        print("Error extracting sign info:", e)
    return fc, pedestrian

# --- Step 2: Process Each Violation to Gather Additional Metrics ---
env_counts = []       # Count of nearby signs (Sign Environment Score)
fc_scores = []        # Functional class for the violation sign
pedestrian_flags = [] # Pedestrian access flag

for idx, row in decel_gdf.iterrows():
    tile_id = row['tile_id']
    feature_id = row['Feature ID']
    # Create a buffer around the violation sign
    buffer_geom = row.geometry.buffer(BUFFER_RADIUS_SIGNS)
    
    # Build the path to the tile's combined.geojson
    combined_path = os.path.join(BASE_DIR, tile_id, f"{tile_id}_combined.geojson")
    try:
        with open(combined_path, 'r') as f:
            combined_data = json.load(f)
    except Exception as e:
        print(f"Error loading combined.geojson for tile {tile_id}: {e}")
        env_counts.append(0)
        fc_scores.append(None)
        pedestrian_flags.append(None)
        continue

    signs_in_tile = []
    fc_score = None
    ped_flag = None

    # Loop over each feature (sign) in the combined file
    for feat in combined_data.get("features", []):
        properties = feat.get("properties", {})
        fid = properties.get("Feature ID", "")
        geom = shape(feat.get("geometry"))
        signs_in_tile.append(geom)
        
        # When we find the matching violation sign, extract its info
        if fid == feature_id:
            fc, pedestrian = extract_sign_info(properties)
            try:
                fc_score = int(fc) if fc is not None else None
            except:
                fc_score = None
            ped_flag = pedestrian

    # Count how many sign geometries intersect with the buffer
    count_nearby = sum(1 for geom in signs_in_tile if buffer_geom.intersects(geom))
    
    env_counts.append(count_nearby)
    fc_scores.append(fc_score)
    pedestrian_flags.append(ped_flag)

# Append these new metrics to the deceleration GeoDataFrame
decel_gdf['sign_cluster_count'] = env_counts
decel_gdf['functional_class'] = fc_scores
decel_gdf['pedestrian_access'] = pedestrian_flags

# --- Step 3: Classification Logic ---
def classify_violation(row):
    """
    Classify each violation based on:
      - Deceleration events (count_decel)
      - Sign cluster (sign_cluster_count)
      - Functional class (fc): expected to be 1 or 2 for proper motorway
      - Pedestrian access (ped): should be False for a valid motorway
    Categories:
      1. NO SIGN IN REALITY
      2. SIGN EXISTS, WRONG ROAD
      3. CORRECT SIGN, WRONG ATTRIBUTES
      4. LEGITIMATE EXCEPTION
    """
    decel = row.get('count_decel', 0)
    cluster = row.get('sign_cluster_count', 0)
    fc = row.get('functional_class', None)
    ped = row.get('pedestrian_access', None)
    
    # Category 1: Likely phantom sign
    if (cluster <= 1) and (decel == 0) and (fc is None or fc > 2) and (ped in [True, 'true', 'True']):
        return "1. NO SIGN IN REALITY"
    # Category 2: Sign exists but is associated with the wrong road
    if (cluster >= 2) and (decel > 0) and (fc is None or (fc > 2) or (ped in [True, 'true', 'True'])):
        return "2. SIGN EXISTS, WRONG ROAD"
    # Category 3: Correct association but wrong road attributes (e.g., pedestrian access issue)
    if (cluster >= 2) and (decel > 0) and (fc in [1, 2]) and (ped in [True, 'true', 'True']):
        return "3. CORRECT SIGN, WRONG ATTRIBUTES"
    # Category 4: Legitimate exception (correct sign, correct road attributes, deceleration present)
    if (cluster >= 2) and (decel > 0) and (fc in [1, 2]) and (ped in [False, 'false', 'False']):
        return "4. LEGITIMATE EXCEPTION"
    
    return "Uncertain"

# Apply the classification logic to each row
decel_gdf['classification_category'] = decel_gdf.apply(classify_violation, axis=1)

# --- Step 4: Save the Final Enhanced & Classified Output ---
final_path = os.path.join(BASE_DIR, "violation_probe_classified.csv")
decel_gdf.to_csv(final_path, index=False)
print(f"✅ Classification categories added and saved to {final_path}")
