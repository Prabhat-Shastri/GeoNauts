import os
import json

root_dir = "."
validation_file = os.path.join(root_dir, "all_validations.geojson")
output_file = os.path.join(root_dir, "topologies_below_60_kph.txt")

with open(validation_file, "r") as f:
    validations = json.load(f)["features"]

print(f"[DEBUG] Loaded {len(validations)} validations")

report_lines = []

for val in validations:
    partition_id = str(val["properties"].get("Partition ID"))
    validation_id = val["properties"].get("Feature ID")
    relevant_topos_path = os.path.join(root_dir, "relevant_topologies.geojson")

    print(f"[DEBUG] Processing Validation ID: {validation_id}, Partition ID: {partition_id}")

    if not os.path.exists(relevant_topos_path):
        continue

    print(f"[DEBUG] Found topology file: {relevant_topos_path}")

    with open(relevant_topos_path, "r") as f:
        topo_data = json.load(f)

    for feature in topo_data.get("features", []):
        props = feature.get("properties", {})
        speed_limits = props.get("speedLimit")

        if speed_limits is None:
            print(f"[DEBUG] Topology ID {props.get('id', 'Unknown')} has no speedLimit property.")
            continue

        if not isinstance(speed_limits, list):
            print(f"[DEBUG] Topology ID {props.get('id', 'Unknown')} has speedLimit in unexpected format: {speed_limits}")
            continue

        for speed in speed_limits:
            speed_kph = speed.get("valueKph")
            if speed_kph is not None:
                print(f"[DEBUG] Topology ID {props.get('id', 'Unknown')} speedLimit = {speed_kph} kph")
                if speed_kph < 60:
                    report_lines.append(f"Validation ID: {validation_id}")
                    report_lines.append(f"  Topology ID: {props.get('id', 'Unknown')}")
                    report_lines.append(f"  Speed: {speed_kph} kph")
                    report_lines.append("-" * 40)
                    break  # Only report each feature once

with open(output_file, "w") as f:
    f.write("\n".join(report_lines))

print(f"Topologies with speedLimit < 60 kph saved to {output_file}")