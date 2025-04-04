import json
import os

def filter_ramp_topologies():
    print("[DEBUG] Starting filtering process...")
    
    # File paths
    input_file = "./relevant_topologies.geojson"
    output_file = "./case_2.geojson"
    
    # Check if the input file exists
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file {input_file} does not exist.")
        return
    
    # Load the relevant topologies file
    print(f"[DEBUG] Reading from {input_file}...")
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {input_file}: {str(e)}")
        return

    features = data.get("features", [])
    print(f"[DEBUG] Loaded {len(features)} features.")
    
    # Filter features where isRamp.value == true
    ramp_features = []

    for feature in features:
        properties = feature.get("properties", {})
        topology_characteristics = properties.get("topologyCharacteristics")

        # Handle both list and dict cases
        if isinstance(topology_characteristics, list):
            topology_characteristics = topology_characteristics[0] if topology_characteristics else None

        if not isinstance(topology_characteristics, dict):
            continue  # skip if it's not a dict now

        is_ramp_data = topology_characteristics.get("isRamp")

        if isinstance(is_ramp_data, list):
            is_ramp_data = is_ramp_data[0] if is_ramp_data else None

        is_ramp = None
        if isinstance(is_ramp_data, dict):
            is_ramp = is_ramp_data.get("value")

        if is_ramp is True:
            ramp_features.append(feature)

    print(f"[DEBUG] Found {len(ramp_features)} features where isRamp.value == true.")

    # Save filtered features to case_2.geojson
    output_data = {
        "type": "FeatureCollection",
        "features": ramp_features
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"[DEBUG] Saved filtered results to {output_file}.")

if __name__ == "__main__":
    filter_ramp_topologies()