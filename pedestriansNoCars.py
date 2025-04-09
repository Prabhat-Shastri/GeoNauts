#Step 3
#Checks for mismatches where auto access is False but pedestrian or bicycle is True.
#These are often motorways signs incorrectly linked to nearby sidewalk topologies.
#If unprocessed, it searches nearby topologies to resolve the mismatch.
#Classifies as Case 2 (match found) or Case 4 (no suitable match).

import json
import os
import pandas as pd

from geopy.distance import geodesic

# Extracts access flags from a topology's accessCharacteristics list
def extract_access_flags(access_list):
    if not isinstance(access_list, list) or len(access_list) == 0:
        return {}
    access = access_list[0]  # Assuming single entry
    return {
        "auto": access.get("auto"),
        "bicycle": access.get("bicycle"),
        "pedestrian": access.get("pedestrian")
    }

# Returns True if topology blocks auto but allows pedestrian or bicycle (potential sidewalk mismatch)
def check_access_mismatch(flags):
    return (
        flags.get("auto") is False and 
        (flags.get("bicycle") is True or flags.get("pedestrian") is True)
    )

def find_unprocessed_access_mismatches():
    # Load the validation file containing possibly mismatched topologies
    input_file = "validation_with_topology_suggestions.geojson"
    output_file = "access_mismatch_unprocessed.txt"

    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return

    with open(input_file, "r") as f:
        data = json.load(f)

    results = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        validation_id = props.get("Feature ID", "Unknown")
        partition_id = str(props.get("Partition ID", "Unknown"))
        coordinates = feature.get("geometry", {}).get("coordinates", [])

        relevant_topo = props.get("relevantTopology", {})
        topo_props = relevant_topo.get("properties", {})
        access_flags = extract_access_flags(topo_props.get("accessCharacteristics", []))

        # Skip validations that don't meet mismatch criteria
        is_mismatch = check_access_mismatch(access_flags)
        was_processed = props.get("processed", None)

        if not is_mismatch:
            continue  # Skip non-mismatches

        result = [
            f"Validation ID: {validation_id}",
            f"Partition ID: {partition_id}",
            f"Coordinates: {coordinates}",
            f"  -> Original Topology ID: {topo_props.get('id', 'Unknown')}",
            f"     Access - Auto: {access_flags.get('auto')}, Bicycle: {access_flags.get('bicycle')}, Pedestrian: {access_flags.get('pedestrian')}"
        ]

        # If mismatch is unprocessed, search for nearby topologies in same tile
        if not was_processed:
            # Load partition tile
            topo_path = os.path.join(".", partition_id, f"{partition_id}_full_topology_data.geojson")
            nearby_topos = []
            if os.path.exists(topo_path):
                with open(topo_path, "r") as tf:
                    tile_data = json.load(tf)

                for candidate in tile_data.get("features", []):
                    geom = candidate.get("geometry", {})
                    coords = geom.get("coordinates", [])
                    geom_type = geom.get("type", "")

                    # Extract the first coordinate of the topology for distance calculation
                    first_coord = None
                    if geom_type == "LineString" and coords:
                        first_coord = coords[0]
                    elif geom_type == "MultiLineString" and coords and coords[0]:
                        first_coord = coords[0][0]

                    if not first_coord:
                        continue

                    # Compute distance between validation and topology (must be within 50 meters)
                    dist = geodesic((coordinates[1], coordinates[0]), (first_coord[1], first_coord[0])).meters
                    if dist <= 50:
                        c_props = candidate.get("properties", {})
                        access = extract_access_flags(c_props.get("accessCharacteristics", []))

                        topo_chars = c_props.get("topologyCharacteristics")
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

                        # Store topologies within 50m with relevant access info and characteristics
                        nearby_topos.append((
                            c_props.get("id", "Unknown"),
                            geom_type,
                            access,
                            round(dist, 2),
                            coords,
                            is_ramp,
                            is_motorway,
                            candidate.get("geometry", {}),
                            c_props  # full original properties
                        ))

            if nearby_topos:
                result.append("Nearby Topologies:")
                for nid, ntype, naccess, distance, all_coords, is_ramp, is_motorway, _, _ in nearby_topos:
                    result.append(f"  - ID: {nid}, Type: {ntype}, Distance: {distance} meters, Coordinates: {all_coords}")
                    result.append(f"    Access: {naccess}, isRamp: {is_ramp}, isMotorway: {is_motorway}")
                
                # Select best candidate based on distance and preference (auto=True, not pedestrian/bike, ramp/motorway)
                best_match = None

                if len(nearby_topos) == 1:
                    best_match = nearby_topos[0]
                elif len(nearby_topos) > 1:
                    filtered = [t for t in nearby_topos if t[2].get("auto") is True]
                    if filtered:
                        preferred = [t for t in filtered if not t[2].get("pedestrian", False) and not t[2].get("bicycle", False)]
                        candidates = preferred if preferred else filtered
                        candidates.sort(key=lambda x: x[3])
                        if candidates:
                            closest_dist = candidates[0][3]
                            closest_group = [t for t in candidates if t[3] <= closest_dist + 15]
                            best_match = max(closest_group, key=lambda x: int(x[5] is True) + int(x[6] is True))

                if best_match:
                    best_id, best_type, best_access, best_dist, best_coords, best_ramp, best_motorway, full_geom, best_props = best_match
                    result.append("Best Match:")
                    result.append(f"  - ID: {best_id}, Type: {best_type}, Distance: {best_dist} meters")
                    result.append(f"    Access: {best_access}, isRamp: {best_ramp}, isMotorway: {best_motorway}")
                    # Case 2: match found and relevant topology assigned
                    props["relevantTopology"] = {
                        "type": "Feature",
                        "geometry": full_geom,
                        "properties": best_props  # store full original properties
                    }
                    props["Case"] = 2
                else:
                    result.append("  No suitable best match found from nearby topologies.")
                    # Case 4: no suitable match found
                    props["Case"] = 4
            else:
                result.append("  No nearby topologies found.")
                # Case 4: no suitable match found
                props["Case"] = 4

            # Mark this validation as processed regardless of match result
            props["processed"] = True  # Ensure processed is set either way

        # Add Case and best match info (even if already processed)
        case_type = props.get("Case", "Unknown")
        result.append(f"Case: {case_type}")
        if "relevantTopology" in props:
            ct = props["relevantTopology"]
            result.append("Best Match:")
            result.append(f"  - ID: {ct['properties'].get('id')}, Access: {ct['properties'].get('accessCharacteristics')}")
            result.append(f"    isRamp: {ct['properties'].get('isRamp')}, isMotorway: {ct['properties'].get('isMotorway')}")

        result.append("-" * 60)
        results.append("\n".join(result))

    # Write mismatch analysis report to text file
    with open(output_file, "w") as f:
        f.write("ACCESS MISMATCH REPORT (All Processed Mismatches)\n")
        f.write("=" * 60 + "\n")
        if results:
            f.write("\n".join(results))
        else:
            f.write("No mismatches found.\n")

    # Save updated validations back to the same input file
    with open(input_file, "w") as out_json:
        json.dump(data, out_json, indent=2)

    # Append Case 2 and Case 4 entries to results.csv
    csv_path = os.path.join(".", "results.csv")

    # Load or create results DataFrame
    if os.path.exists(csv_path):
        results_df = pd.read_csv(csv_path)
    else:
        results_df = pd.DataFrame(columns=[
            "Feature ID", "Violation ID", "Partition ID",
            "Case", "Processed", "Topology Found",
            "Suggested Topology ID", "Notes"
        ])

    # For each processed mismatch, add a row to results.csv
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        feature_id = props.get("Feature ID", "")
        violation_id = props.get("Violation ID", "")
        partition_id = props.get("Partition ID", "")
        case = props.get("Case", "")
        processed = props.get("processed", False)
        correct_topology = props.get("relevantTopology", {})
        suggested_topo_id = correct_topology.get("properties", {}).get("id", "") if correct_topology else ""

        # Only log mismatches processed by this step
        if case not in [2, 4] or not processed:
            continue

        topology_found = "Yes" if case == 2 else "No"
        note = (
            f"Access mismatch, resolved with nearby topology ({suggested_topo_id})"
            if case == 2 else
            "Access mismatch, no suitable nearby topology found"
        )

        new_row = {
            "Feature ID": feature_id,
            "Violation ID": violation_id,
            "Partition ID": partition_id,
            "Case": case,
            "Processed": "Yes",
            "Topology Found": topology_found,
            "Suggested Topology ID": suggested_topo_id,
            "Notes": note
        }
        
        results_df = results_df.append(new_row, ignore_index=True)

    results_df.to_csv(csv_path, index=False)
    print(f"[DEBUG] results.csv updated with access mismatch entries")

if __name__ == "__main__":
    find_unprocessed_access_mismatches()