import os
import json
import math
import re

def generate_topology_validation_report():
    # print("[DEBUG] Starting topology validation report generation...")
    
    # Path to the specific files
    root_folder = '.'  # Current directory
    validation_file_path = os.path.join(root_folder, "all_validations.geojson")  # The validation file
    
    # print(f"[DEBUG] Validation file path: {validation_file_path}")

    # Check if the validation file exists
    if not os.path.exists(validation_file_path):
        print(f"[ERROR] Validation file {validation_file_path} does not exist.")
        return

    # Load validation data from the specified file
    try:
        # print("[DEBUG] Attempting to load validation data...")
        with open(validation_file_path, 'r') as f:
            validation_data = json.load(f)
        print(f"[DEBUG] Successfully loaded validation data. Found {len(validation_data.get('features', []))} features.")
    except Exception as e:
        print(f"[ERROR] Error loading validation data: {str(e)}")
        return

    # Create a report for the validations
    text_report = []
    text_report.append("TOPOLOGY VALIDATION REPORT")
    text_report.append("=" * 50)
    
    print("[DEBUG] Beginning to process validation features...")

    relevant_topologies = {"type": "FeatureCollection", "features": []}  # Initialize relevant topologies

    # Iterate through the validations in the geojson file
    for i, validation in enumerate(validation_data.get('features', [])):
        # print(f"[DEBUG] Processing validation {i+1}/{len(validation_data.get('features', []))}...")
        
        validation_coords = validation.get('geometry', {}).get('coordinates', [0, 0])
        validation_id = validation.get('properties', {}).get('Partition ID', 'Unknown ID')
        error_message = validation.get('properties', {}).get('Error Message', '')
        
        # print(f"[DEBUG] Validation ID: {validation_id}, Coordinates: {validation_coords}")
        # print(f"[DEBUG] Error message: {error_message}")

        # Extract directory using partition ID
        target_directory = str(validation.get('properties', {}).get('Partition ID', 'Unknown Directory'))
        print(f"[DEBUG] Target directory: {target_directory}")
        
        # Extract topology number from error message using regex
        # print("[DEBUG] Attempting to extract topology number from error message...")
        topology_match = re.search(r'(urn:here::here:Topology:\d+)', error_message)
        if not topology_match:
            print("[DEBUG] Could not extract topology number from error message.")
            text_report.append(f"Validation ID: {validation_id}")
            text_report.append(f"  Validation Coordinates: {validation_coords}")
            text_report.append(f"  Could not extract topology number from error message.")
            text_report.append("-" * 50)
            continue
        
        topology_number = topology_match.group(1)
        # print(f"[DEBUG] Extracted topology number: {topology_number}")
        
        # Path to the topology file in the validation's directory
        topology_file_path = os.path.join(root_folder, target_directory, f"{target_directory}_full_topology_data.geojson")
        # print(f"[DEBUG] Topology file path: {topology_file_path}")
        
        # Check if the topology file exists
        if not os.path.exists(topology_file_path):
            # print(f"[DEBUG] Topology file {topology_file_path} does not exist.")
            text_report.append(f"Validation ID: {validation_id}")
            text_report.append(f"  Validation Coordinates: {validation_coords}")
            text_report.append(f"  Topology Number: {topology_number}")
            text_report.append(f"  Topology file {topology_file_path} does not exist. Skipping validation.")
            text_report.append("-" * 50)
            continue

        # Load topology data from the specific topology file for this validation
        try:
            # print(f"[DEBUG] Attempting to load topology data from {topology_file_path}...")
            with open(topology_file_path, 'r') as f:
                topology_data = json.load(f)
            # print(f"[DEBUG] Successfully loaded topology data. Found {len(topology_data.get('features', []))} features.")
        except Exception as e:
            print(f"[ERROR] Error loading topology data: {str(e)}")
            text_report.append(f"Validation ID: {validation_id}")
            text_report.append(f"  Error loading topology data: {str(e)}")
            text_report.append("-" * 50)
            continue

        # Find the specific topology in the file
        found_topology = False
        topology_info = {}
        
        # print(f"[DEBUG] Searching for topology ID {topology_number} in topology data...")
        feature_count = len(topology_data.get('features', []))
        
        for j, feature in enumerate(topology_data.get('features', [])):
            # if j % 1000 == 0:  # Print progress every 1000 features
            #     print(f"[DEBUG] Checking feature {j+1}/{feature_count}...")
                
            topo_id = feature.get('properties', {}).get('id', '')
            
            # Check if this is the topology we're looking for
            if topo_id == topology_number or str(topo_id) == str(topology_number):
                print(f"[DEBUG] Found matching topology ID: {topo_id}")
                found_topology = True
                # Extract relevant topology data
                topology_info = {
                    "isRamp": feature.get('properties', {}).get('isRamp', 'N/A'),
                    "isMotorway": feature.get('properties', {}).get('isMotorway', 'N/A'),
                    "isPedestrian": feature.get('properties', {}).get('isPedestrian', 'N/A'),
                    "formOfWay": feature.get('properties', {}).get('formOfWay', 'N/A'),
                    "functionalClass": feature.get('properties', {}).get('functionalClass', 'N/A')
                }
                feature["properties"]["Partition ID"] = validation_id  # Include Partition ID
                relevant_topologies["features"].append(feature)  # Store relevant topology feature
                # print(f"[DEBUG] Extracted topology info: {topology_info}")
                break
        
        if not found_topology:
            print(f"[DEBUG] Topology ID {topology_number} not found in file after checking {feature_count} features.")

        # # Add validation and topology info to the report
        # print("[DEBUG] Adding validation and topology info to report...")
        # text_report.append(f"Validation ID: {validation_id}")
        # text_report.append(f"  Validation Coordinates: {validation_coords}")
        # text_report.append(f"  Topology Number: {topology_number}")
        
        # if found_topology:
        #     text_report.append(f"  Topology Found: Yes")
        #     text_report.append(f"  isRamp: {topology_info.get('isRamp')}")
        #     text_report.append(f"  isMotorway: {topology_info.get('isMotorway')}")
        #     text_report.append(f"  isPedestrian: {topology_info.get('isPedestrian')}")
        #     text_report.append(f"  formOfWay: {topology_info.get('formOfWay')}")
        #     text_report.append(f"  functionalClass: {topology_info.get('functionalClass')}")
        # else:
        #     text_report.append(f"  Topology Found: No (Topology {topology_number} not found in file)")
        
        # text_report.append("-" * 50)
        print(f"[DEBUG] Completed processing for validation ID: {validation_id}")

    # # Save the text report to a file
    # text_report_file = os.path.join(root_folder, "topology_validation_report.txt")
    # print(f"[DEBUG] Saving report to {text_report_file}...")
    # with open(text_report_file, 'w') as f:
    #     f.write("\n".join(text_report))

    # Save the relevant topologies to a new file
    relevant_topologies_file = os.path.join(root_folder, "relevant_topologies.geojson")
    print(f"[DEBUG] Saving relevant topologies to {relevant_topologies_file}...")
    with open(relevant_topologies_file, 'w') as f:
        json.dump(relevant_topologies, f, indent=4)

    print(f"[DEBUG] Successfully created relevant topologies file at {relevant_topologies_file}")
    # print(f"[DEBUG] Successfully created topology validation report at {text_report_file}")

if __name__ == "__main__":
    print("[DEBUG] Script execution started")
    generate_topology_validation_report()
    print("[DEBUG] Script execution completed")