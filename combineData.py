import os
import json
import glob
import re

def collect_all_validations(root_folder):
    all_validations = {
        "type": "FeatureCollection",
        "name": "all_validations",
        "features": []
    }

    validation_files = []
    for directory in os.listdir(root_folder):
        dir_path = os.path.join(root_folder, directory)
        if os.path.isdir(dir_path):
            pattern = os.path.join(dir_path, "*_validations.geojson")
            files = glob.glob(pattern)
            validation_files.extend(files)

    print(f"[DEBUG] Found {len(validation_files)} validation files")

    for file_path in validation_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if "features" in data and isinstance(data["features"], list):
                    all_validations["features"].extend(data["features"])
                    print(f"[DEBUG] Added {len(data['features'])} from {os.path.basename(file_path)}")
                else:
                    print(f"[WARN] No features found in {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {e}")

    output_file = os.path.join(root_folder, "all_validations.geojson")
    with open(output_file, 'w') as f:
        json.dump(all_validations, f, indent=2)

    print(f"[DEBUG] Saved merged validations to {output_file}")
    return output_file

def enrich_with_topologies(validation_file_path, root_folder):
    with open(validation_file_path, 'r') as f:
        validation_data = json.load(f)

    enriched_output = {"type": "FeatureCollection", "features": []}
    validations = validation_data.get("features", [])

    print(f"[DEBUG] Enriching {len(validations)} validations with topology data...")

    for val in validations:
        partition_id = str(val.get("properties", {}).get("Partition ID", "Unknown"))
        error_msg = val.get("properties", {}).get("Error Message", "")
        validation_id = val.get("properties", {}).get("Feature ID", "Unknown")
        validation_copy = val.copy()
        validation_copy.setdefault("properties", {})

        match = re.search(r'(urn:here::here:Topology:\d+)', error_msg)
        if not match:
            print(f"[DEBUG] No topology ID found in error message for {validation_id}")
            validation_copy["properties"]["noTopologyFound"] = True
            enriched_output["features"].append(validation_copy)
            continue

        topo_id = match.group(1)
        topo_file = os.path.join(root_folder, partition_id, f"{partition_id}_full_topology_data.geojson")

        if not os.path.exists(topo_file):
            print(f"[DEBUG] Topology file missing: {topo_file}")
            validation_copy["properties"]["noTopologyFound"] = True
            enriched_output["features"].append(validation_copy)
            continue

        try:
            with open(topo_file, 'r') as tf:
                topo_data = json.load(tf)
        except Exception as e:
            print(f"[ERROR] Failed to read {topo_file}: {e}")
            validation_copy["properties"]["noTopologyFound"] = True
            enriched_output["features"].append(validation_copy)
            continue

        found = False
        for feature in topo_data.get("features", []):
            feature_id = feature.get("properties", {}).get("id", "")
            if feature_id == topo_id or str(feature_id) == str(topo_id):
                print(f"[DEBUG] Found match for validation {validation_id}: {feature_id}")
                validation_copy["properties"]["relevantTopology"] = feature
                found = True
                break

        if not found:
            print(f"[DEBUG] Topology {topo_id} not found for validation {validation_id}")
            validation_copy["properties"]["noTopologyFound"] = True

        enriched_output["features"].append(validation_copy)

    enriched_path = os.path.join(root_folder, "validation_with_topologies.geojson")
    with open(enriched_path, 'w') as out:
        json.dump(enriched_output, out, indent=2)

    print(f"[DEBUG] Wrote enriched validation data to {enriched_path}")

if __name__ == "__main__":
    print("[DEBUG] Starting unified validation + topology merge process")
    base_path = "."  # or update if different
    all_val_file = collect_all_validations(base_path)
    enrich_with_topologies(all_val_file, base_path)
    print("[DEBUG] Done.")