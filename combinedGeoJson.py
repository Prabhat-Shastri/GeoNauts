import os
import json
import glob

def merge_geojson_files():
    # Path to the folder containing the numbered directories
    root_folder = '.'  # Current directory (Chicago_Hackathon)
    
    # Create an empty FeatureCollection to store all features
    all_validations = {
        "type": "FeatureCollection",
        "name": "all_validations",
        "features": []
    }
    
    # Get a list of all validation files
    validation_files = []
    
    # Look through each numbered directory for validation files
    for directory in os.listdir(root_folder):
        dir_path = os.path.join(root_folder, directory)
        if os.path.isdir(dir_path):
            # Search for files ending with _validations.geojson
            pattern = os.path.join(dir_path, "*_validations.geojson")
            files = glob.glob(pattern)
            validation_files.extend(files)
    
    print(f"Found {len(validation_files)} validation files")
    
    # Process each validation file
    for file_path in validation_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Extract features from the file and add to our collection
                if "features" in data and isinstance(data["features"], list):
                    all_validations["features"].extend(data["features"])
                    print(f"Added {len(data['features'])} features from {os.path.basename(file_path)}")
                else:
                    print(f"Warning: No features found in {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Save the combined data to a new file
    output_file = os.path.join(root_folder, "all_validations.geojson")
    with open(output_file, 'w') as f:
        json.dump(all_validations, f, indent=2)
    
    print(f"Successfully created {output_file} with {len(all_validations['features'])} total features")

if __name__ == "__main__":
    merge_geojson_files()