import os
import json
import math

def generate_motorway_validation_report():
    # Path to the specific files
    root_folder = '.'  # Current directory
    validation_file_path = os.path.join(root_folder, "all_validations.geojson")  # The validation file

    # Set margin of error for determining if a sign is "nearby"
    NEARBY_THRESHOLD = 0.001  # Adjust as needed

    # Function to calculate distance between two coordinates
    def calculate_distance(coord1, coord2):
        dx = coord1[0] - coord2[0]
        dy = coord1[1] - coord2[1]
        return math.sqrt(dx * dx + dy * dy)

    # Check if the validation file exists
    if not os.path.exists(validation_file_path):
        print(f"Validation file {validation_file_path} does not exist.")
        return

    # Load validation data from the specified file
    try:
        with open(validation_file_path, 'r') as f:
            validation_data = json.load(f)
    except Exception as e:
        print(f"Error loading validation data: {str(e)}")
        return

    # Create a report for the validations
    text_report = []
    text_report.append("VALIDATION AND NEARBY SIGNS REPORT")
    text_report.append("=" * 50)

    # Iterate through the validations in the geojson file
    for validation in validation_data.get('features', []):
        validation_coords = validation.get('geometry', {}).get('coordinates', [0, 0])
        validation_id = validation.get('properties', {}).get('Partition ID', 'Unknown ID')

        # Access the target directory from the validation file, assuming it's specified in the properties
        target_directory = str(validation.get('properties', {}).get('Partition ID', 'Unknown Directory'))

        # Path to the signs file in the validation's directory
        sign_file_path = os.path.join(root_folder, target_directory, f"{target_directory}_signs.geojson")

        # Check if the sign file exists
        if not os.path.exists(sign_file_path):
            text_report.append(f"  Sign file {sign_file_path} does not exist. Skipping validation.")
            continue

        # Load sign data from the specific sign file for this validation
        try:
            with open(sign_file_path, 'r') as f:
                sign_data = json.load(f)
        except Exception as e:
            text_report.append(f"  Error loading sign data: {str(e)}")
            continue

        # Process each feature in the sign file
        nearby_signs = []  # Will hold all signs near the target coordinates
        for feature in sign_data.get('features', []):
            sign_coords = feature.get('geometry', {}).get('coordinates', [0, 0])

            # Calculate distance from the validation coordinates
            distance = calculate_distance(validation_coords, sign_coords)

            # Access signType from properties
            sign_type = feature.get('properties', {}).get('signType', 'Unknown')

            # If the sign is within the nearby threshold, add to the list
            if distance < NEARBY_THRESHOLD:
                nearby_signs.append({
                    "id": feature.get('properties', {}).get('signType', 'Unknown ID'),
                    "coordinates": sign_coords,
                    "distance": distance
                })

        # Add validation info to the report
        text_report.append(f"Validation ID: {validation_id}")
        text_report.append(f"  Validation Coordinates: {validation_coords}")

        # Check nearby signs and classify as Case 2 if a highway or exit is nearby
        case_2_found = False
        for sign in nearby_signs:
            text_report.append(f"  Nearby Sign ID: {sign['id']}")
            text_report.append(f"  Sign Coordinates: {sign['coordinates']}")
            text_report.append(f"  Distance: {sign['distance']:.6f}")

            # Check if the nearby sign is a highway or highway exit
            if 'highway' in sign['id'].lower() or 'exit' in sign['id'].lower():
                case_2_found = True

        # Print Case 2 if found
        if case_2_found:
            text_report.append("  Case 2: Highway or Highway Exit nearby.")
        text_report.append("-" * 50)

    # Save the text report to a file
    text_report_file = os.path.join(root_folder, "validation_nearby_signs_report.txt")
    with open(text_report_file, 'w') as f:
        f.write("\n".join(text_report))

    print(f"Created text report at {text_report_file}")

if __name__ == "__main__":
    generate_motorway_validation_report()