import json
from collections import defaultdict

# Load the GeoJSON data
with open("relevant_topologies.geojson", "r") as f:
    geojson_data = json.load(f)

# Dictionary to hold sum and count for averages
fc_speed_data = defaultdict(lambda: {"sum": 0, "count": 0})

# Iterate through features
for feature in geojson_data["features"]:
    props = feature.get("properties", {})

    # Get functional class list and speed limit list
    fc_list = props.get("functionalClass", [])
    speed_list = props.get("speedLimit") or []

    for fc in fc_list:
        fc_value = fc.get("value")
        if fc_value in [1, 2, 3, 4, 5]:
            for speed in speed_list:
                speed_kph = speed.get("valueKph")
                if speed_kph is not None:
                    fc_speed_data[fc_value]["sum"] += speed_kph
                    fc_speed_data[fc_value]["count"] += 1

# Write results to a TXT file
with open("functional_class_speed_averages.txt", "w") as f:
    for fc_value in sorted(fc_speed_data.keys()):
        total = fc_speed_data[fc_value]["sum"]
        count = fc_speed_data[fc_value]["count"]
        avg = total / count if count > 0 else 0
        f.write(f"Functional Class {fc_value}: Average Speed = {avg:.2f} kph\n")

print("Output written to functional_class_speed_averages.txt")