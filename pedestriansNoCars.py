import json
import os
from geopy.distance import geodesic

def extract_access_flags(access_list):
    if not isinstance(access_list, list) or len(access_list) == 0:
        return {}
    access = access_list[0]  # Assuming single entry
    return {
        "auto": access.get("auto"),
        "bicycle": access.get("bicycle"),
        "pedestrian": access.get("pedestrian")
    }

def check_access_mismatch(flags):
    return (
        flags.get("auto") is False and 
        (flags.get("bicycle") is True or flags.get("pedestrian") is True)
    )

def find_unprocessed_access_mismatches():
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

                    first_coord = None
                    if geom_type == "LineString" and coords:
                        first_coord = coords[0]
                    elif geom_type == "MultiLineString" and coords and coords[0]:
                        first_coord = coords[0][0]

                    if not first_coord:
                        continue

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
                    props["correctTopology"] = {
                        "type": "Feature",
                        "geometry": full_geom,
                        "properties": best_props  # store full original properties
                    }
                    props["Case"] = 2
                else:
                    result.append("  No suitable best match found from nearby topologies.")
                    props["Case"] = 5
            else:
                result.append("  No nearby topologies found.")
                props["Case"] = 5

            props["processed"] = True  # Ensure processed is set either way

        # Add Case and best match info (even if already processed)
        case_type = props.get("Case", "Unknown")
        result.append(f"Case: {case_type}")
        if "correctTopology" in props:
            ct = props["correctTopology"]
            result.append("Best Match:")
            result.append(f"  - ID: {ct['properties'].get('id')}, Access: {ct['properties'].get('accessCharacteristics')}")
            result.append(f"    isRamp: {ct['properties'].get('isRamp')}, isMotorway: {ct['properties'].get('isMotorway')}")

        result.append("-" * 60)
        results.append("\n".join(result))

    # Write full report
    with open(output_file, "w") as f:
        f.write("ACCESS MISMATCH REPORT (All Processed Mismatches)\n")
        f.write("=" * 60 + "\n")
        if results:
            f.write("\n".join(results))
        else:
            f.write("No mismatches found.\n")

    # Save updated JSON
    with open(input_file, "w") as out_json:
        json.dump(data, out_json, indent=2)

    print(f"[DEBUG] Report saved to {output_file}")

if __name__ == "__main__":
    find_unprocessed_access_mismatches()