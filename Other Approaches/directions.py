import json
import os
from geopy.distance import geodesic

# Utility: get heading from ADAS topology if available
def get_topology_heading(relevant_topology):
    try:
        return relevant_topology["properties"]["adasTopology"]["startNodeTraversals"][0]["heading"]
    except (KeyError, IndexError, TypeError):
        return None

# Utility: calculate angular difference

def angular_difference(h1, h2):
    diff = abs(h1 - h2) % 360
    return min(diff, 360 - diff)

def find_directional_mismatches():
    validations_file = "validation_with_topology_case3_applied.geojson"
    output_txt = "directional_mismatches.txt"

    if not os.path.exists(validations_file):
        print(f"[ERROR] File not found: {validations_file}")
        return

    with open(validations_file, "r") as f:
        data = json.load(f)

    print(f"[DEBUG] Loaded {len(data.get('features', []))} validations")

    mismatches = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        processed = props.get("processed", None)

        if processed is not None:
            continue  # Only run for unprocessed validations

        validation_id = props.get("Feature ID", "Unknown")
        partition_id = str(props.get("Partition ID", "Unknown"))
        coordinates = feature.get("geometry", {}).get("coordinates", [])

        # Load sign file
        sign_path = os.path.join(".", partition_id, f"{partition_id}_signs.geojson")
        if not os.path.exists(sign_path):
            print(f"[DEBUG] Sign file not found: {sign_path}")
            continue

        try:
            with open(sign_path, "r") as sf:
                signs = json.load(sf).get("features", [])
        except Exception as e:
            print(f"[ERROR] Reading signs file {sign_path}: {e}")
            continue

        # Get sign data
        sign_heading = None
        for sign in signs:
            print(f"[DEBUG] Checking sign ID: {sign.get('properties', {}).get('id')}")
            if sign.get("properties", {}).get("id") == validation_id:
                sign_heading = sign.get("properties", {}).get("vehicleHeading")
                break

        if sign_heading is None:
            print(f"[DEBUG] No matching sign found for validation ID: {validation_id}")
            continue  # Skip if we can't find a heading

        # Try ADAS fallback for sign heading
        if sign_heading is None:
            sign_heading = get_topology_heading(props.get("relevantTopology", {}))

        if sign_heading is None:
            print(f"[DEBUG] Skipping {validation_id} — no vehicleHeading found in sign.")
            continue

        # Get topology heading
        topo_heading = get_topology_heading(props.get("relevantTopology", {}))
        if topo_heading is not None:
            topo_heading = topo_heading / 1000  # Convert from millidegrees to degrees

        if topo_heading is None:
            print(f"[DEBUG] Skipping {validation_id} — no topology heading found.")
            continue

        diff = angular_difference(sign_heading, topo_heading)

        print(f"[DEBUG] Validation {validation_id} | Sign: {sign_heading} | Topo: {topo_heading} | Diff: {round(diff, 2)}°")

        mismatches.append(f"Validation ID: {validation_id}")
        mismatches.append(f"Partition ID: {partition_id}")
        mismatches.append(f"Sign Heading: {sign_heading}")
        mismatches.append(f"Topology Heading: {topo_heading}")
        mismatches.append(f"Angular Difference: {round(diff, 2)} degrees")
        mismatches.append(f"Coordinates: {coordinates}")
        if diff > 90:
            mismatches.append("=> Directional mismatch detected (Case 5)")
        else:
            mismatches.append("=> Direction consistent")
        mismatches.append("-" * 60)

    # Write output
    with open(output_txt, "w") as f:
        f.write("DIRECTIONAL MISMATCH REPORT\n")
        f.write("=" * 60 + "\n")
        if mismatches:
            f.write("\n".join(mismatches))
        else:
            f.write("No directional mismatches found.\n")

    print(f"[DEBUG] Report saved to {output_txt}")

if __name__ == "__main__":
    find_directional_mismatches()
