import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import os

tile_id = "23608592"  # ⬅️ Change this to any tile you'd like to check
tile_path = f"/Users/kush/Chicago_Hackathon_Expanded_Datasets/{tile_id}"

# Load combined.geojson and filter violations
combined = gpd.read_file(os.path.join(tile_path, f"{tile_id}_combined.geojson"))
violations = combined[
    (combined['Rule Code'] == 'WSIGN406') & 
    (combined['signType'] == 'MOTORWAY')
].copy()

if violations.empty:
    print("No WSIGN406 violations in this tile.")
else:
    violations = violations.to_crs(epsg=4326)

# Load probe data and convert to GeoDataFrame
probe_df = pd.read_csv(os.path.join(tile_path, f"{tile_id}_probe_data.csv"))
probe_gdf = gpd.GeoDataFrame(
    probe_df, 
    geometry=gpd.points_from_xy(probe_df.longitude, probe_df.latitude),
    crs="EPSG:4326"
)

# Plot
fig, ax = plt.subplots(figsize=(8, 8))
probe_gdf.plot(ax=ax, markersize=1, alpha=0.3, color='blue', label='Probe Points')
if not violations.empty:
    violations.plot(ax=ax, markersize=30, color='red', label='WSIGN406 Violations')

plt.title(f"Tile {tile_id} — Probe Points vs Violations")
plt.legend()
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)
plt.show()
