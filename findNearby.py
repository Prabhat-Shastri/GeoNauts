import os
import json
import math

def generate_motorway_validation_report():
    # Path to the specific directory and file
    root_folder = '.'  # Current directory (chicago_hackathon)
    target_directory = "23599610"  # Directory to process
    sign_file_path = os.path.join(root_folder, target_directory, f"{target_directory}_signs.geojson")  # The specific signs file

    # Coordinates to check proximity against
    target_coords = [8.163311696952888, 49.139013978719746]
    # Set margin of error for determining if a sign is "nearby"
    NEARBY_THRESHOLD = 0.0001  # Adjust as needed

    # Function to calculate distance between two coordinates
    def calculate_distance(coord1, coord2):
        dx = coord1[0] - coord2[0]
        dy = coord1[1] - coord2[1]
        return math.sqrt(dx*dx + dy*dy)

    # Check if the sign file exists
    if not os.path.exists(sign_file_path):
        print(f"Sign file {sign_file_path} does not exist.")
        return

    # Load sign data from the specified file
    try:
        with open(sign_file_path, 'r') as f:
            sign_data = json.load(f)
    except Exception as e:
        print(f"Error loading sign data: {str(e)}")
        return

    # Process each feature in the sign file
    nearby_signs = []  # Will hold all signs near the target coordinates
    for feature in sign_data.get('features', []):
        sign_coords = feature.get('geometry', {}).get('coordinates', [0, 0])

        # Calculate distance from the target coordinates
        distance = calculate_distance(target_coords, sign_coords)

        # Corrected: Accessing signType from properties
        sign_type = feature.get('properties', {}).get('signType', 'Unknown')

        # If the sign is within the nearby threshold, add to the list
        if distance < NEARBY_THRESHOLD:
            nearby_signs.append({
                "id": feature.get('properties', {}).get('signType', 'Unknown ID'),
                "coordinates": sign_coords,
                "distance": distance
            })

    # Create a report for the nearby signs
    report_entries = []
    for sign in nearby_signs:
        entry = {
            "sign_id": sign["id"],
            "sign_coordinates": sign["coordinates"],
            "distance": sign["distance"]
        }
        report_entries.append(entry)

    # Save the report to a JSON file
    report_file = os.path.join(root_folder, "nearby_signs_report.json")
    with open(report_file, 'w') as f:
        json.dump(report_entries, f, indent=2)

    print(f"Created report at {report_file} with {len(nearby_signs)} nearby signs")

    # Also generate a text report for easier reading
    text_report = []
    text_report.append("NEARBY SIGNS REPORT")
    text_report.append("=" * 50)

    for entry in report_entries:
        text_report.append(f"Sign ID: {entry['sign_id']}")
        text_report.append(f"  Coordinates: {entry['sign_coordinates']}")
        text_report.append(f"  Distance: {entry['distance']:.6f}")
        text_report.append("-" * 50)

    text_report_file = os.path.join(root_folder, "nearby_signs_report.txt")
    with open(text_report_file, 'w') as f:
        f.write("\n".join(text_report))

    print(f"Created text report at {text_report_file}")

if __name__ == "__main__":
    generate_motorway_validation_report()