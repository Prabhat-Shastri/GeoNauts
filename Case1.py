import os
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
from tqdm import tqdm

# --- Configuration ---
BASE_DIR = "/Users/kush/Chicago_Hackathon_Expanded_Datasets"  # CHANGE THIS TO YOUR PATH
TILE_IDS = ['23608577', '23608578', '23608580', '23608592', '23612004', '23612006', '23612035']
BUFFER_RADIUS = 300  # meters
DECEL_THRESHOLD = -1.5  # km/h

# --- Detect deceleration events for points within a violation buffer ---
def analyze_violation(violation_buffer, probe_gdf, threshold=DECEL_THRESHOLD):
    probe_subset = probe_gdf[probe_gdf.within(violation_buffer)]
    print(f"\nViolation buffer — {len(probe_subset)} probe points found.")
    if not probe_subset.empty:
        print(probe_subset[['traceid', 'speed', 'latitude', 'longitude']].head())
    if probe_subset.empty:
        return {"avg_decel": 0, "count_decel": 0}

    decel_events = []
    for traceid, group in probe_subset.groupby('traceid'):
        group = group.sort_values('sampledate')
        speeds = group['speed'].values
        if len(speeds) < 2:
            continue
        speed_diffs = np.diff(speeds)
        decel_indices = np.where(speed_diffs < threshold)[0]
        if decel_indices.size > 0:
            decel_events.extend(speed_diffs[decel_indices])

    if decel_events:
        return {
            "avg_decel": np.mean(decel_events),
            "count_decel": len(decel_events)
        }
    else:
        return {"avg_decel": 0, "count_decel": 0}

# --- Main Processing Loop ---
all_results = []

for tile_id in tqdm(TILE_IDS, desc="Processing Tiles"):
    try:
        tile_path = os.path.join(BASE_DIR, tile_id)
        combined_path = os.path.join(tile_path, f"{tile_id}_combined.geojson")
        probe_path = os.path.join(tile_path, f"{tile_id}_probe_data.csv")

        # Load and filter violations
        combined_gdf = gpd.read_file(combined_path)
        violations_gdf = combined_gdf[
            (combined_gdf['Rule Code'] == 'WSIGN406') &
            (combined_gdf['signType'] == 'MOTORWAY')
        ].copy()

        if violations_gdf.empty:
            print(f"[{tile_id}] No violations.")
            continue

        # Reproject to metric system
        violations_gdf = violations_gdf.to_crs(epsg=3857)
        violations_gdf['buffer'] = violations_gdf.geometry.buffer(BUFFER_RADIUS)

        # Load probe data
        probe_df = pd.read_csv(probe_path)
        probe_df['sampledate'] = pd.to_datetime(probe_df['sampledate'])
        probe_gdf = gpd.GeoDataFrame(
            probe_df,
            geometry=gpd.points_from_xy(probe_df.longitude, probe_df.latitude),
            crs="EPSG:4326"
        ).to_crs(epsg=3857)

        # 🚨 Diagnostic Check: Sample probe + sign coords
        print(f"\n📍 TILE: {tile_id}")
        print(f"📌 CRS Check — Violations: {violations_gdf.crs}, Probes: {probe_gdf.crs}")
        print(f"📌 Total Violations: {len(violations_gdf)}, Total Probes: {len(probe_gdf)}")

        # Preview coordinates (in WGS84 for sanity)
        probes_preview = probe_gdf.to_crs(epsg=4326).sample(min(len(probe_gdf), 5))
        violations_preview = violations_gdf.to_crs(epsg=4326).head(5)

        print("\n🧭 Sample probe coordinates:")
        print(probes_preview['geometry'])

        print("\n🚧 Sample violation coordinates:")
        print(violations_preview['geometry'])

        # Analyze each violation
        for idx, row in violations_gdf.iterrows():
            metrics = analyze_violation(row['buffer'], probe_gdf, DECEL_THRESHOLD)
            result = {
                "tile_id": tile_id,
                "Feature ID": row.get("Feature ID", "Unknown"),
                "avg_decel": metrics["avg_decel"],
                "count_decel": metrics["count_decel"],
                "geometry": row.geometry
            }
            all_results.append(result)

    except Exception as e:
        print(f"[{tile_id}] Error: {e}")

# --- Export Results ---
if all_results:
    result_gdf = gpd.GeoDataFrame(all_results, geometry="geometry", crs="EPSG:3857")
    result_gdf.to_file(os.path.join(BASE_DIR, "violation_probe_all.geojson"), driver="GeoJSON")
    result_gdf.to_csv(os.path.join(BASE_DIR, "violation_probe_all.csv"), index=False)
    print("\n✅ Saved results for all tiles!")
else:
    print("\n❌ No results found across all tiles. Try visual or CRS check.")
