import os
import json
from geopy.distance import geodesic

def is_within_25m(val_coord, geometry):
    if geometry["type"] == "LineString":
        for coord in geometry["coordinates"]:
            if geodesic((val_coord[1], val_coord[0]), (coord[1], coord[0])).meters <= 25:
                return True
    elif geometry["type"] == "MultiLineString":
        for linestring in geometry["coordinates"]:
            for coord in linestring:
                if geodesic((val_coord[1], val_coord[0]), (coord[1], coord[0])).meters <= 25:
                    return True
    return False

def find_nearby_topologies():
    root_folder = "."
    validation_file = os.path.join(root_folder, "all_validations.geojson")
    output_file = os.path.join(root_folder, "nearby_topologies_per_validation.json")

    if not os.path.exists(validation_file):
        print("[ERROR] all_validations.geojson not found.")
        return

    with open(validation_file, "r") as f:
        validations = json.load(f)["features"]

    results = []

    for i, validation in enumerate(validations):
        val_coord = validation.get("geometry", {}).get("coordinates", [])
        partition_id = str(validation.get("properties", {}).get("Partition ID"))
        validation_id = validation.get("properties", {}).get("Feature ID", f"validation_{i}")

        if not partition_id:
            continue

        topo_path = os.path.join(root_folder, partition_id, f"{partition_id}_full_topology_data.geojson")
        if not os.path.exists(topo_path):
            continue

        try:
            with open(topo_path, "r") as tf:
                topo_data = json.load(tf)
        except Exception as e:
            print(f"[ERROR] Failed to read topology file for {partition_id}: {e}")
            continue

        nearby = []
        for feature in topo_data.get("features", []):
            if is_within_25m(val_coord, feature.get("geometry", {})):
                nearby.append(feature)

        results.append({
            "validation_id": validation_id,
            "validation_coords": val_coord,
            "partition_id": partition_id,
            "nearby_topologies": nearby
        })

    with open(output_file, "w") as out_f:
        json.dump(results, out_f, indent=2)

    print(f"[DEBUG] Nearby topologies saved to {output_file}")

if __name__ == "__main__":
    find_nearby_topologies()