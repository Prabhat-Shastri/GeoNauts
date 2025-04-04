import os
import json
import re

def match_exit_signs_with_ramps():
    root = '.'
    validations_path = os.path.join(root, "all_validations.geojson")
    signs_path = os.path.join(root, "nearby_motorway_hwyexit_signs.json")
    topo_path = os.path.join(root, "nearby_topologies_per_validation.json")
    output_txt = os.path.join(root, "ramp_candidate_matches.txt")

    with open(validations_path) as f:
        validations = json.load(f)["features"]

    with open(signs_path) as f:
        nearby_signs = json.load(f)

    with open(topo_path) as f:
        nearby_topos = json.load(f)

    report_lines = []
    matches_found = 0
    for val in validations:
        val_id = val["properties"].get("Feature ID")
        partition_id = val["properties"].get("Partition ID")
        coords = val.get("geometry", {}).get("coordinates", [])
        error_msg = val["properties"].get("Error Message", "")

        print(f"\n[DEBUG] --- Validation: {val_id} ---")

        # Get original topology ID
        topo_match = re.search(r"(urn:here::here:Topology:\d+)", error_msg)
        original_topo_id = topo_match.group(1) if topo_match else "Unknown"

        # Match validation to nearby HWYEXIT sign
        signs_entry = next((s for s in nearby_signs if s["validation_id"] == val_id), None)
        if not signs_entry:
            print(f"[DEBUG] No nearby sign entry found for validation {val_id}")
            continue

        print(f"[DEBUG] Total nearby signs: {len(signs_entry.get('nearby_signs', []))}")
        hwyexit_signs = [s for s in signs_entry.get("nearby_signs", []) if s.get("sign_type") == "HWYEXIT"]
        print(f"[DEBUG] Found {len(hwyexit_signs)} HWYEXIT signs")
        if not hwyexit_signs:
            continue

        # Match to nearby topology features
        topo_entry = next((t for t in nearby_topos if t["validation_id"] == val_id), None)
        if not topo_entry:
            print(f"[DEBUG] No nearby topologies found for validation {val_id}")
            continue

        print(f"[DEBUG] Total nearby topologies: {len(topo_entry.get('nearby_topologies', []))}")

        ramp_topos = []
        for feature in topo_entry.get("nearby_topologies", []):
            props = feature.get("properties", {})
            is_ramp = False

            # Case 1: Check directly under props
            if "isRamp" in props and isinstance(props["isRamp"], list):
                is_ramp = props["isRamp"][0].get("value", False)

            # Case 2: Check under topologyCharacteristics
            elif "topologyCharacteristics" in props:
                tc = props["topologyCharacteristics"]
                if "isRamp" in tc and isinstance(tc["isRamp"], list):
                    is_ramp = tc["isRamp"][0].get("value", False)

            print(f"[DEBUG] Topology {props.get('id')} isRamp = {is_ramp}")

            if is_ramp == True:
                ramp_topos.append({
                    "id": props.get("id", "Unknown"),
                    "coordinates": feature.get("geometry", {}).get("coordinates", [])
                })

        print(f"[DEBUG] Validation {val_id}: {'Found' if ramp_topos else 'No'} nearby topologies with isRamp=True")
        if not ramp_topos:
            continue

        matches_found += 1
        report_lines.append(f"Validation ID: {val_id}")
        report_lines.append(f"  Partition ID: {partition_id}")
        report_lines.append(f"  Validation Coordinates: {coords}")
        report_lines.append(f"  Original Topology: {original_topo_id}")

        # Try to find and include coordinates of the original topology
        original_coords = "Not found"
        for feature in topo_entry.get("nearby_topologies", []):
            if feature.get("properties", {}).get("id") == original_topo_id:
                original_coords = feature.get("geometry", {}).get("coordinates", [])
                break
        report_lines.append(f"    Coordinates: {original_coords}")

        report_lines.append(f"  HWYEXIT Sign:")
        for s in hwyexit_signs:
            report_lines.append(f"    Sign ID: {s.get('sign_id')}")
            report_lines.append(f"    Coordinates: {s.get('sign_coordinates')}")
            report_lines.append(f"    Distance: {s.get('distance'):.6f}")

        report_lines.append(f"  Nearby Ramp Topologies:")
        for ramp in ramp_topos:
            report_lines.append(f"    ID: {ramp['id']}")
            report_lines.append(f"    Coordinates: {ramp['coordinates']}")

        report_lines.append("-" * 60)

    with open(output_txt, 'w') as f:
        f.write("\n".join(report_lines))

    print(f"[DEBUG] Output written to {output_txt}")
    print(f"[DEBUG] Total matches found: {matches_found}")

if __name__ == "__main__":
    match_exit_signs_with_ramps()