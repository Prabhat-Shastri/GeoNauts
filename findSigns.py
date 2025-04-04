import os
import json
import glob
import math

def generate_nearby_signs_report():
    root_folder = '.'
    NEARBY_THRESHOLD = 0.001  # Approximate threshold for 20m

    validation_file = os.path.join(root_folder, "all_validations.geojson")
    with open(validation_file, 'r') as f:
        validation_data = json.load(f)
    validation_features = validation_data.get('features', [])
    print(f"Loaded {len(validation_features)} validation points")

    sign_files = []
    for directory in os.listdir(root_folder):
        dir_path = os.path.join(root_folder, directory)
        if os.path.isdir(dir_path):
            pattern = os.path.join(dir_path, f"{directory}_signs.geojson")
            matching_files = glob.glob(pattern)
            sign_files.extend(matching_files)
    print(f"Found {len(sign_files)} sign files")

    relevant_signs = []
    for sign_file in sign_files:
        try:
            with open(sign_file, 'r') as f:
                sign_data = json.load(f)
            for feature in sign_data.get('features', []):
                sign_type = feature.get('properties', {}).get('signType')
                if sign_type in ["MOTORWAY", "HWYEXIT"]:
                    relevant_signs.append(feature)
        except Exception as e:
            print(f"Error processing {sign_file}: {str(e)}")
    print(f"Collected {len(relevant_signs)} relevant signs from sign files")

    def calculate_distance(coord1, coord2):
        dx = coord1[0] - coord2[0]
        dy = coord1[1] - coord2[1]
        return math.sqrt(dx * dx + dy * dy)

    grouped_signs_report = []

    for validation in validation_features:
        validation_id = validation.get('properties', {}).get('Feature ID', 'Unknown')
        validation_coords = validation.get('geometry', {}).get('coordinates', [0, 0])
        nearby_signs = []

        for sign in relevant_signs:
            sign_coords = sign.get('geometry', {}).get('coordinates', [0, 0])
            distance = calculate_distance(validation_coords, sign_coords)
            if distance < NEARBY_THRESHOLD:
                nearby_signs.append({
                    "sign_id": sign.get('properties', {}).get('id', 'Unknown'),
                    "sign_type": sign.get('properties', {}).get('signType', 'Unknown'),
                    "sign_coordinates": sign_coords,
                    "distance": distance,
                    "observationCounts": sign.get('properties', {}).get('observationCounts', {})
                })

        grouped_signs_report.append({
            "validation_id": validation_id,
            "validation_coordinates": validation_coords,
            "nearby_signs": nearby_signs
        })

    report_file = os.path.join(root_folder, "nearby_motorway_hwyexit_signs.json")
    with open(report_file, 'w') as f:
        json.dump(grouped_signs_report, f, indent=2)
    print(f"Grouped signs report created at {report_file}")

if __name__ == "__main__":
    generate_nearby_signs_report()