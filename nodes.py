import json
import os

def extract_node_id_connections():
    validations_file = "validation_with_topology_case3_applied.geojson"
    output_file = "node_chain_analysis.txt"

    if not os.path.exists(validations_file):
        print(f"[ERROR] File not found: {validations_file}")
        return

    with open(validations_file, "r") as f:
        data = json.load(f)
    print(f"[DEBUG] Loaded {len(data.get('features', []))} validations")

    results = []

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        relevant_topology = props.get("relevantTopology", {})
        rel_props = relevant_topology.get("properties", {})

        validation_id = props.get("Feature ID", "Unknown")
        partition_id = str(props.get("Partition ID", "Unknown"))
        coords = feature.get("geometry", {}).get("coordinates", [])

        access_chars = rel_props.get("accessCharacteristics", [])
        original_allows_ped = False
        if isinstance(access_chars, list) and len(access_chars) > 0:
            original_allows_ped = access_chars[0].get("pedestrian", False)

        print(f"[DEBUG] Processing Validation ID: {validation_id}, Partition: {partition_id}")

        # Extract connected topology IDs from adasTopology
        reference_topo_ids = set()
        adas = rel_props.get("adasTopology", {})
        traversals = adas.get("startNodeTraversals", [])
        for traversal in traversals:
            for ref in traversal.get("references", []):
                ref_id = ref.get("id")
                if ref_id:
                    reference_topo_ids.add(ref_id)

        result = [
            f"Validation ID: {validation_id}",
            f"Partition ID: {partition_id}",
            f"Original Topology ID: {rel_props.get('id', 'Unknown')}",
            f"Coordinates: {coords}",
        ]
        original_coords = relevant_topology.get("geometry", {}).get("coordinates", [])
        result.append(f"Original Topology Coordinates: {original_coords}")

        result.append(f"Original Allows Pedestrian: {original_allows_ped}")
        result.append(f"Connected Topology IDs: {', '.join(reference_topo_ids) if reference_topo_ids else 'None'}")

        found_matches = []

        part_path = os.path.join(partition_id, f"{partition_id}_full_topology_data.geojson")
        if not os.path.isfile(part_path):
            print(f"[DEBUG] Topology file not found for partition {partition_id}")
            result.append(f"[DEBUG] Topology file not found for partition {partition_id}")
            results.append("\n".join(result))
            continue

        print(f"[DEBUG] Loading topology file: {part_path}")
        try:
            with open(part_path, "r") as tf:
                topo_data = json.load(tf)
            for topo in topo_data.get("features", []):
                tprops = topo.get("properties", {})
                topo_id = tprops.get("id", "Unknown")
                print(f"[DEBUG] Checking Topology ID: {topo_id}")
                if topo_id not in reference_topo_ids:
                    continue

                access = tprops.get("accessCharacteristics", [])
                allows_ped = False
                if isinstance(access, list) and len(access) > 0:
                    allows_ped = access[0].get("pedestrian", False)

                if original_allows_ped and not allows_ped:
                    match_coords = topo.get("geometry", {}).get("coordinates", [])
                    found_matches.append((topo_id, partition_id, allows_ped, match_coords))

        except Exception as e:
            print(f"[ERROR] Reading {part_path}: {e}")
            result.append(f"[ERROR] Reading {part_path}: {e}")

        if found_matches:
            result.append("Possible better matches (pedestrian access = False):")
            for match_id, match_partition, _, match_coords in found_matches:
                result.append(f"  -> Topology ID: {match_id} in Partition {match_partition}")
                result.append(f"     Coordinates: {match_coords}")
        else:
            result.append("No alternative matches found.")

        result.append("-" * 60)
        results.append("\n".join(result))

    with open(output_file, "w") as f:
        f.write("NODE CONNECTION CHAIN ANALYSIS\n")
        f.write("=" * 60 + "\n")
        f.write("\n".join(results))
    print(f"[DEBUG] Finished writing results to {output_file}")

if __name__ == "__main__":
    extract_node_id_connections()