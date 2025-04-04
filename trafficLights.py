import json
import os

def filter_traffic_signal_pedestrian_features():
    print("[DEBUG] Starting filtering for TRAFFIC_SIGNAL with pedestrian constraint...")
    
    # File paths
    input_file = "./relevant_topologies.geojson"
    output_file = "./case_4.geojson"
    
    # Check if the input file exists
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file {input_file} does not exist.")
        return
    
    print(f"[DEBUG] Reading from {input_file}...")
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {input_file}: {str(e)}")
        return
    
    features = data.get("features", [])
    print(f"[DEBUG] Loaded {len(features)} features.")
    
    filtered_features = []
    
    # Iterate over each feature and inspect its conditionalAttributes
    for feature in features:
        properties = feature.get("properties", {})
        cond_attrs = properties.get("conditionalAttributes") or []
        
        # Iterate over the list of conditional attributes
        for cond_attr in cond_attrs:
            attributes = cond_attr.get("attributes", [])
            if not isinstance(attributes, list):
                continue
            
            # Check each attribute for TRAFFIC_SIGNAL with pedestrian true
            for attr in attributes:
                if attr.get("attributeType") == "TRAFFIC_SIGNAL":
                    constraints = attr.get("constraints", [])
                    if not isinstance(constraints, list):
                        continue
                    for constraint in constraints:
                        vehicle_types = constraint.get("vehicleTypes", {})
                        if isinstance(vehicle_types, dict) and vehicle_types.get("pedestrian") is True:
                            filtered_features.append(feature)
                            # Found a matching attribute; break out of loops for this feature
                            break
                    else:
                        continue
                    break
            else:
                continue
            break  # Stop processing further conditional attributes for this feature
    
    print(f"[DEBUG] Found {len(filtered_features)} features with TRAFFIC_SIGNAL conditional attribute having pedestrian == true.")
    
    output_data = {
        "type": "FeatureCollection",
        "features": filtered_features
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[DEBUG] Saved filtered results to {output_file}.")

if __name__ == "__main__":
    filter_traffic_signal_pedestrian_features()