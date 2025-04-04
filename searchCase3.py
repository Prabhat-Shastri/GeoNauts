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

def is_valid_case3_candidate(flags):
    return flags.get("auto") is True and flags.get("pedestrian") is True

def is_case3_target(flags):
    return flags.get("auto") is False and flags.get("pedestrian") is True

def find_case3_candidates():
    input_file = "validation_with_topology_suggestions.geojson"
    output_file = "case_3_possible_matches.txt"

    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return

    with open(input_file, "r") as f:
        data = json.load(f)

    results = []
    match_count = 0

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        validation_id = props.get("Feature ID", "Unknown")
        partition_id = str(props.get("Partition ID", "Unknown"))
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        processed = props.get("processed", None)

        if processed:
            continue

        relevant_topo = props.get("relevantTopology", {})
        topo_props = relevant_topo.get("properties", {})
        access_flags = extract_access_flags(topo_props.get("accessCharacteristics", []))

        if not is_valid_case3_candidate(access_flags):
            continue

        result = [
            f"Validation ID: {validation_id}",
            f"Partition ID: {partition_id}",
            f"Validation Coordinates: {coordinates}",
            f"  -> Original Topology ID: {topo_props.get('id', 'Unknown')}",
            f"     Access - Auto: {access_flags.get('auto')}, Pedestrian: {access_flags.get('pedestrian')}"
        ]

        topo_path = os.path.join(".", partition_id, f"{partition_id}_full_topology_data.geojson")
        nearby_topos = []

        if not os.path.exists(topo_path):
            result.append("  [WARN] Missing partition topology file.")
            result.append("-" * 60)
            results.append("\n".join(result))
            continue

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

                if is_case3_target(access):
                    is_ramp = is_motorway = "N/A"

                    topo_chars = c_props.get("topologyCharacteristics")
                    if isinstance(topo_chars, list):
                        topo_chars = topo_chars[0] if topo_chars else {}
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
                        is_motorway
                    ))

        if not nearby_topos:
            continue  # Skip this one if no matching topologies found

        result.append("Nearby Topologies (Auto=False, Pedestrian=True):")
        for nid, ntype, naccess, distance, all_coords, is_ramp, is_motorway in nearby_topos:
            result.append(f"  - ID: {nid}, Type: {ntype}, Distance: {distance} meters")
            result.append(f"    Access: {naccess}, isRamp: {is_ramp}, isMotorway: {is_motorway}")
            result.append(f"    Coordinates: {all_coords}")

        # Pick best match
        best_match = nearby_topos[0]
        if len(nearby_topos) > 1:
            nearby_topos.sort(key=lambda x: x[3])
            closest = nearby_topos[0][3]
            close_group = [t for t in nearby_topos if t[3] <= closest + 15]
            best_match = max(close_group, key=lambda x: int(x[5] is True) + int(x[6] is True))

        best_id, best_type, best_access, best_dist, best_coords, best_ramp, best_motorway = best_match
        result.append("Best Match (Case = 3):")
        result.append(f"  - ID: {best_id}, Type: {best_type}, Distance: {best_dist} meters")
        result.append(f"    Access: {best_access}, isRamp: {best_ramp}, isMotorway: {best_motorway}")
        result.append(f"    Coordinates: {best_coords}")
        result.append("Case: 3")
        result.append("-" * 60)

        # Modify relevantTopology accessCharacteristics in memory
        access_list = topo_props.get("accessCharacteristics", [])
        if isinstance(access_list, list) and access_list:
            first_entry = access_list[0]
            if isinstance(first_entry, dict) and first_entry.get("pedestrian") is True:
                first_entry["pedestrian"] = False
                match_count += 1

        results.append("\n".join(result))

    with open(output_file, "w") as f:
        f.write("CASE 3 REPORT: Auto+Pedestrian ➝ Pedestrian-only Nearby Topologies\n")
        f.write("=" * 60 + "\n\n")
        if results:
            f.write("\n\n".join(results))
        else:
            f.write("No case 3 matches found.\n")

    print(f"[DEBUG] Case 3 report saved to {output_file}")
    print(f"[DEBUG] Updated pedestrian access to False for {match_count} relevant topologies (in-memory only).")

def extract_case3_ids(txt_path):
    case3_ids = set()
    current_id = None
    with open(txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Validation ID:"):
                current_id = line.split("Validation ID:")[1].strip()
            elif line.startswith("Case: 3") and current_id:
                case3_ids.add(current_id)
                current_id = None
    return case3_ids

def apply_case3_flag_to_geojson():
    input_geojson = "validation_with_topology_suggestions.geojson"
    txt_report = "case_3_possible_matches.txt"
    output_geojson = "validation_with_topology_case3_applied.geojson"

    if not os.path.exists(input_geojson):
        print(f"[ERROR] Missing GeoJSON: {input_geojson}")
        return

    if not os.path.exists(txt_report):
        print(f"[ERROR] Missing TXT report: {txt_report}")
        return

    case3_ids = extract_case3_ids(txt_report)

    with open(input_geojson, "r") as f:
        data = json.load(f)

    modified_count = 0

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        validation_id = props.get("Feature ID", "Unknown")

        if validation_id in case3_ids:
            props["Case"] = 3

            relevant_topo = props.get("relevantTopology", {})
            topo_props = relevant_topo.get("properties", {})
            access_chars = topo_props.get("accessCharacteristics", [])

            if isinstance(access_chars, list) and access_chars:
                first_entry = access_chars[0]
                if isinstance(first_entry, dict):
                    if first_entry.get("pedestrian", True):
                        first_entry["pedestrian"] = False
                        modified_count += 1

    with open(output_geojson, "w") as outf:
        json.dump(data, outf, indent=2)

    print(f"[DEBUG] Applied Case 3 to {modified_count} features in new GeoJSON.")
    print(f"[DEBUG] Output saved to {output_geojson}")

if __name__ == "__main__":
    find_case3_candidates()
    apply_case3_flag_to_geojson()