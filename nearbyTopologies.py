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

def suggest_topologies():
    root_folder = "."
    input_path = os.path.join(root_folder, "validation_with_topologies.geojson")
    enriched_output_path = os.path.join(root_folder, "validation_with_topology_suggestions.geojson")
    text_output_path = os.path.join(root_folder, "suggested_topologies_report.txt")

    with open(input_path, "r") as f:
        validations = json.load(f)

    updated_validations = {"type": "FeatureCollection", "features": []}
    text_lines = []

    for val in validations["features"]:
        updated_val = val.copy()
        props = updated_val.get("properties", {})
        if not props.get("noTopologyFound"):
            updated_validations["features"].append(updated_val)
            continue

        validation_id = props.get("Feature ID", "Unknown")
        partition_id = str(props.get("Partition ID", "Unknown"))
        val_coords = val.get("geometry", {}).get("coordinates", [])

        topo_path = os.path.join(root_folder, partition_id, f"{partition_id}_full_topology_data.geojson")
        if not os.path.exists(topo_path):
            print(f"[WARN] Missing topology file for Partition {partition_id}")
            updated_validations["features"].append(updated_val)
            continue

        try:
            with open(topo_path, "r") as tf:
                topo_data = json.load(tf)
        except Exception as e:
            print(f"[ERROR] Failed to read {topo_path}: {e}")
            updated_validations["features"].append(updated_val)
            continue

        suggested = []
        for feature in topo_data.get("features", []):
            if is_within_25m(val_coords, feature.get("geometry", {})):
                suggested.append(feature)

        if suggested:
            updated_val["properties"]["suggestedTopologies"] = suggested
            text_lines.append(f"Validation ID: {validation_id}")
            text_lines.append(f"Partition ID: {partition_id}")
            text_lines.append(f"Coordinates: {val_coords}")
            for topo in suggested:
                props = topo.get("properties", {})
                tid = props.get("id", "Unknown")
                geom_type = topo.get("geometry", {}).get("type", "Unknown")
                coords = topo.get("geometry", {}).get("coordinates", [])
                is_ramp = props.get("isRamp", "N/A")
                is_motorway = props.get("isMotorway", "N/A")
                access_char = props.get("accessCharacteristics", "N/A")

                text_lines.append(f"  Suggested Topology ID: {tid}")
                text_lines.append(f"    Geometry Type: {geom_type}")
                text_lines.append(f"    Coordinates: {coords}")
                text_lines.append(f"    Partition ID: {partition_id}")
                text_lines.append(f"    isRamp: {is_ramp}")
                text_lines.append(f"    isMotorway: {is_motorway}")
                text_lines.append(f"    accessCharacteristics: {access_char}")
            text_lines.append("-" * 60)

        updated_validations["features"].append(updated_val)

    with open(enriched_output_path, "w") as outf:
        json.dump(updated_validations, outf, indent=2)

    with open(text_output_path, "w") as txtf:
        txtf.write("\n".join(text_lines))

    print(f"[DEBUG] Saved enriched validations to {enriched_output_path}")
    print(f"[DEBUG] Suggested topologies report written to {text_output_path}")

if __name__ == "__main__":
    suggest_topologies()