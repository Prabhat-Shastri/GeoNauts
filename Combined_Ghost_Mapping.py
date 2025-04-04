import os
import json
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import shape
from shapely import wkt

# --- CONFIGURATION ---
BASE_DIR = "/Users/kush/Chicago_Hackathon_Expanded_Datasets" 
BUFFER_RADIUS_SIGNS = 100  # meters for nearby signs analysis
decel_results_path = os.path.join(BASE_DIR, "violation_probe_all.geojson")

# --- Step 1: Load the Deceleration Results ---
decel_gdf = gpd.read_file(decel_results_path)

# Fix geometry column if it is stored as a string
if isinstance(decel_gdf.geometry.iloc[0], str):
    print("🔁 Converting geometry strings to Shapely geometries...")
    decel_gdf['geometry'] = decel_gdf['geometry'].apply(wkt.loads)
    decel_gdf = gpd.GeoDataFrame(decel_gdf, geometry='geometry', crs="EPSG:3857")

# --- Helper Function: Extract Sign Info ---
def extract_sign_info(properties):
    """
    Extracts the functional class and pedestrian access from a sign's properties.
    Expects functionalClass and accessCharacteristics to be lists of dicts or dicts.
    """
    fc = None
    pedestrian = None
    try:
        # Try to get functionalClass; it might be a list of dictionaries.
        if "functionalClass" in properties:
            if isinstance(properties["functionalClass"], list):
                if len(properties["functionalClass"]) > 0:
                    fc = properties["functionalClass"][0].get("value", None)
            else:
                fc = properties["functionalClass"]
        # Try to get pedestrian access; again, it might be a list.
        if "accessCharacteristics" in properties:
            if isinstance(properties["accessCharacteristics"], list):
                if len(properties["accessCharacteristics"]) > 0:
                    pedestrian = properties["accessCharacteristics"][0].get("pedestrian", None)
            else:
                pedestrian = properties["accessCharacteristics"].get("pedestrian", None)
    except Exception as e:
        print("Error extracting sign info:", e)
    return fc, pedestrian

# --- Prepare Lists to Store New Metrics ---
env_counts = []         # Number of nearby signs (Sign Environment Score)
fc_scores = []          # Functional class (ideally 1 or 2 for motorway segments)
pedestrian_flags = []   # Pedestrian access flag (should be False for a valid motorway)

# --- Step 2: Process Each Violation in the Deceleration Results ---
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

    # Initialize values for this violation
    signs_in_tile = []
    fc_score = None
    ped_flag = None

    # Iterate through all signs in this tile
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

    # Count how many signs (their geometries) intersect with the buffer zone
    count_nearby = sum(1 for geom in signs_in_tile if buffer_geom.intersects(geom))
    
    env_counts.append(count_nearby)
    fc_scores.append(fc_score)
    pedestrian_flags.append(ped_flag)

# --- Step 3: Append New Metrics to the Deceleration GeoDataFrame ---
decel_gdf['sign_cluster_count'] = env_counts
decel_gdf['functional_class'] = fc_scores
decel_gdf['pedestrian_access'] = pedestrian_flags

# --- Step 4: Save the Enhanced Results ---
output_csv = os.path.join(BASE_DIR, "violation_probe_enhanced.csv")
decel_gdf.to_csv(output_csv, index=False)
print(f"✅ Enhanced validation saved to {output_csv}")
