# Step 5
# Analyzes node chains between topologies to detect pedestrian access mismatches.
# If the original topology allows pedestrian access but a connected one doesn't, it's likely a misclassification.
# Replaces the original relevantTopology with the better matched one and logs to results.csv and a text report.

import json
import os
import pandas as pd

# Main function to analyze validation topologies for node-based access mismatches
def extract_node_id_connections():
    # Load the validation data with previously enriched topologies
    validations_file = "validation_with_topology_suggestions.geojson"
    output_file = "node_chain_analysis.txt"

    if not os.path.exists(validations_file):
        print(f"[ERROR] File not found: {validations_file}")
        return

    with open(validations_file, "r") as f:
        data = json.load(f)
    print(f"[DEBUG] Loaded {len(data.get('features', []))} validations")

    results = []

    # Iterate through each validation feature
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        relevant_topology = props.get("relevantTopology", {})
        rel_props = relevant_topology.get("properties", {})

        validation_id = props.get("Feature ID", "Unknown")
        partition_id = str(props.get("Partition ID", "Unknown"))
        coords = feature.get("geometry", {}).get("coordinates", [])

        # Determine if the original topology allows pedestrian access
        access_chars = rel_props.get("accessCharacteristics", [])
        original_allows_ped = False
        if isinstance(access_chars, list) and len(access_chars) > 0:
            original_allows_ped = access_chars[0].get("pedestrian", False)

        # Use ADAS topology references to find connected topology IDs
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

        # Open the corresponding partition topology file to look for referenced topologies
        part_path = os.path.join(partition_id, f"{partition_id}_full_topology_data.geojson")
        if not os.path.isfile(part_path):
            print(f"[DEBUG] Topology file not found for partition {partition_id}")
            result.append(f"[DEBUG] Topology file not found for partition {partition_id}")
            results.append("\n".join(result))
            continue

        try:
            with open(part_path, "r") as tf:
                topo_data = json.load(tf)
            for topo in topo_data.get("features", []):
                tprops = topo.get("properties", {})
                topo_id = tprops.get("id", "Unknown")
                if topo_id not in reference_topo_ids:
                    continue

                access = tprops.get("accessCharacteristics", [])
                allows_ped = False
                if isinstance(access, list) and len(access) > 0:
                    allows_ped = access[0].get("pedestrian", False)

                # Compare access flags to find connected topologies that disallow pedestrian access
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

        # If a connected topology with mismatched access is found, log to results.csv
        csv_path = "results.csv"
        if os.path.exists(csv_path):
            results_df = pd.read_csv(csv_path)
        else:
            results_df = pd.DataFrame(columns=[
                "Feature ID", "Violation ID", "Partition ID",
                "Case", "Processed", "Topology Found",
                "Suggested Topology ID", "Notes"
            ])

        if found_matches:
            first_match = found_matches[0]
            suggested_topo_id = first_match[0]
            new_row = {
                "Feature ID": validation_id,
                "Violation ID": props.get("Violation ID", ""),
                "Partition ID": partition_id,
                "Case": 2,
                "Processed": "Yes",
                "Topology Found": "Yes",
                "Suggested Topology ID": suggested_topo_id,
                "Notes": f"Pedestrian access allowed on original, but not on connected topology ({suggested_topo_id})"
            }

            match = (
                (results_df["Feature ID"] == new_row["Feature ID"]) &
                (results_df["Violation ID"] == new_row["Violation ID"]) &
                (results_df["Partition ID"] == new_row["Partition ID"])
            )

            if match.any():
                results_df.loc[match, list(new_row.keys())] = list(new_row.values())
            else:
                results_df = results_df.append(new_row, ignore_index=True)

            results_df.to_csv(csv_path, index=False)

            # Replace the original relevantTopology with the connected one that better reflects access characteristics
            for topo_feature in topo_data.get("features", []):
                if topo_feature.get("properties", {}).get("id") == suggested_topo_id:
                    feature["properties"]["relevantTopology"] = topo_feature
                    break

    # Write updated validation data with modified topologies back to disk
    with open(validations_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[DEBUG] Updated relevantTopology for applicable validations in {validations_file}")

    # Write a human-readable report with analysis of all checked validations
    with open(output_file, "w") as f:
        f.write("NODE CONNECTION CHAIN ANALYSIS\n")
        f.write("=" * 60 + "\n")
        f.write("\n".join(results))
    print(f"[DEBUG] Finished writing results to {output_file}")

if __name__ == "__main__":
    extract_node_id_connections()