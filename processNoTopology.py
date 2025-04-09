#Step 2
#For validations where no topology was linked, this script attempts to find nearby topologies (within 25 meters) that match certain characteristics (ramp/motorway and no pedestrian access).

import os
import json
import pandas as pd
import csv
from geopy.distance import geodesic

#Checks if any point in a topology geometry is within 25 meters of the validation
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
    matched_summary = []

    #Loop through each validation with no matched topology, and attempt to find candidates nearby
    for val in validations["features"]:
        updated_val = val.copy()
        props = updated_val.get("properties", {})
        if props.get("processed"):
            updated_validations["features"].append(updated_val)
            continue

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

        #Log all potential matches for manual review
        if suggested:
            text_lines.append(f"Validation ID: {validation_id}")
            text_lines.append(f"Partition ID: {partition_id}")
            text_lines.append(f"Coordinates: {val_coords}")
            for topo in suggested:
                props = topo.get("properties", {})
                tid = props.get("id", "Unknown")
                geom = topo.get("geometry", {})
                coords = geom.get("coordinates", [])
                geom_type = geom.get("type", "Unknown")
                first_coord = coords[0] if geom_type == "LineString" and coords else coords[0][0] if geom_type == "MultiLineString" and coords else None
                distance = round(geodesic((val_coords[1], val_coords[0]), (first_coord[1], first_coord[0])).meters, 2) if first_coord else "N/A"

                topo_chars = props.get("topologyCharacteristics")
                if isinstance(topo_chars, list):
                    topo_chars = topo_chars[0] if topo_chars else {}

                is_ramp = is_motorway = "N/A"
                if isinstance(topo_chars, dict):
                    ramp_data = topo_chars.get("isRamp")
                    if isinstance(ramp_data, list) and ramp_data:
                        ramp_data = ramp_data[0]
                    if isinstance(ramp_data, dict):
                        is_ramp = ramp_data.get("value", "N/A")

                    motorway_data = topo_chars.get("isMotorway")
                    if isinstance(motorway_data, list) and motorway_data:
                        motorway_data = motorway_data[0]
                    if isinstance(motorway_data, dict):
                        is_motorway = motorway_data.get("value", "N/A")

                access_data = props.get("accessCharacteristics", [])
                access_flags = "N/A"
                if isinstance(access_data, list) and access_data:
                    first_entry = access_data[0]
                    if isinstance(first_entry, dict):
                        access_flags = {k: v for k, v in first_entry.items() if isinstance(v, bool)}

                text_lines.append(f"  Suggested Topology ID: {tid}")
                text_lines.append(f"    Geometry Type: {geom_type}")
                text_lines.append(f"    Coordinates: {coords}")
                text_lines.append(f"    Distance to Validation: {distance} meters")
                text_lines.append(f"    isRamp: {is_ramp}")
                text_lines.append(f"    isMotorway: {is_motorway}")
                text_lines.append(f"    accessCharacteristics (boolean flags): {access_flags}")
            text_lines.append("-" * 60)

        #Apply stricter filtering for matches: must be ramp or motorway and must not allow pedestrian access
        candidates = []
        for topo in suggested:
            props = topo.get("properties", {})
            topo_chars = props.get("topologyCharacteristics")
            if isinstance(topo_chars, list):
                topo_chars = topo_chars[0] if topo_chars else {}

            is_ramp = is_motorway = False
            if isinstance(topo_chars, dict):
                ramp_data = topo_chars.get("isRamp")
                if isinstance(ramp_data, list) and ramp_data:
                    ramp_data = ramp_data[0]
                if isinstance(ramp_data, dict):
                    is_ramp = ramp_data.get("value") is True

                motorway_data = topo_chars.get("isMotorway")
                if isinstance(motorway_data, list) and motorway_data:
                    motorway_data = motorway_data[0]
                if isinstance(motorway_data, dict):
                    is_motorway = motorway_data.get("value") is True

            access_list = props.get("accessCharacteristics", [])
            ped_access = True
            if isinstance(access_list, list) and access_list:
                first_entry = access_list[0]
                if isinstance(first_entry, dict):
                    ped_access = first_entry.get("pedestrian", True)

            if (is_ramp or is_motorway) and not ped_access:
                geom = topo.get("geometry", {})
                coords = geom.get("coordinates", [])
                geom_type = geom.get("type", "")
                first_coord = coords[0] if geom_type == "LineString" and coords else coords[0][0] if geom_type == "MultiLineString" and coords else None
                if first_coord:
                    distance = round(geodesic((val_coords[1], val_coords[0]), (first_coord[1], first_coord[0])).meters, 2)
                    candidates.append((topo, distance))

        #If we found any candidates, pick the closest one as the best match and attach to validation
        if candidates:
            candidates.sort(key=lambda x: x[1])
            best_topo = candidates[0][0]
            updated_val["properties"]["relevantTopology"] = best_topo
            updated_val["properties"]["processed"] = True
            updated_val["properties"]["noTopologyFound"] = False
            updated_val["properties"]["Case"] = 2

            matched_summary.append({
                "validation_id": validation_id,
                "partition_id": partition_id,
                "new_topo_id": best_topo.get("properties", {}).get("id", "Unknown")
            })
        else:
            updated_val["properties"]["noSuggestedMatch"] = True
            updated_val["properties"]["processed"] = False
            updated_val["properties"]["Case"] = 4

        updated_validations["features"].append(updated_val)

    if matched_summary:
        text_lines.append("")
        text_lines.append("FINAL MATCHED SUMMARY")
        text_lines.append("=" * 60)
        for item in matched_summary:
            text_lines.append(f"Validation ID: {item['validation_id']}")
            text_lines.append(f"Partition ID: {item['partition_id']}")
            text_lines.append(f"New Topology ID: {item['new_topo_id']}")
            text_lines.append("-" * 60)

    #Write enriched results and text-based match report
    with open(enriched_output_path, "w") as outf:
        json.dump(updated_validations, outf, indent=2)

    with open(text_output_path, "w") as txtf:
        txtf.write("\n".join(text_lines))

    # Update results.csv with processed validations
    csv_path = os.path.join(root_folder, "results.csv")

    # Load existing results or create new dataframe
    if os.path.exists(csv_path):
        results_df = pd.read_csv(csv_path)
    else:
        results_df = pd.DataFrame(columns=[
            "Feature ID", "Violation ID", "Partition ID",
            "Case", "Processed", "Topology Found",
            "Suggested Topology ID", "Notes"
        ])

    # Process and update results
    for val in updated_validations["features"]:
        props = val.get("properties", {})
        feature_id = props.get("Feature ID", "")
        violation_id = props.get("Violation ID", "")
        partition_id = props.get("Partition ID", "")
        case_id = props.get("Case", "")
        suggested_topology = props.get("relevantTopology", {}).get("properties", {}).get("id", "")

        if case_id not in [2, 4]:
            continue

        topology_found = "Yes" if case_id == 2 else "No"
        
        if case_id == 2:
            note = f"No original topology found, replaced with {suggested_topology}"
        elif case_id == 4:
            note = "No topology found in tile (tile overflow)"
            suggested_topology = ""
        else:
            note = ""

        new_row = {
            "Feature ID": feature_id,
            "Violation ID": violation_id,
            "Partition ID": partition_id,
            "Case": case_id,
            "Processed": "Yes",
            "Topology Found": topology_found,
            "Suggested Topology ID": suggested_topology,
            "Notes": note
        }

        # Check if already in results
        match = (results_df["Feature ID"] == feature_id) & \
                (results_df["Violation ID"] == violation_id) & \
                (results_df["Partition ID"] == partition_id)

        if match.any():
            results_df.loc[match, list(new_row.keys())] = list(new_row.values())
        else:
            results_df = results_df.append(new_row, ignore_index=True)

    # Save back to CSV
    results_df.to_csv(csv_path, index=False)
    print(f"[DEBUG] results.csv updated with {len(updated_validations['features'])} entries")
    
    print(f"[DEBUG] Saved enriched validations to {enriched_output_path}")
    print(f"[DEBUG] Suggested topologies report written to {text_output_path}")

if __name__ == "__main__":
    suggest_topologies()