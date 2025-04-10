# 🛰️ GeoNauts

**GeoNauts** is a spatial data validation pipeline that detects and corrects mismatches in topology access characteristics — such as pedestrian access incorrectly allowed on highways. This project won **1st place at the HERE Technologies Student Hackathon – April 2025** 🏆

---

## 🌍 Project Scope

The core issue revolves around HERE's Validation Rule `WSIGN406`, which triggers when a regulatory sign (typically a pedestrian restriction) is incorrectly associated with a road segment that permits pedestrian access. These mismatches often result from automated processes that associate signs to topologies without accounting for their intended context — for example, linking a motorway sign to an adjacent pedestrian path.

These validation triggers can arise from several root causes:

We defined 4 core cases of validation outcomes based on HERE's internal rules:

- **Case 1 – No sign in reality**: The violation is invalid because the sign no longer exists in the real world.  
  _Fix: Remove the sign from the dataset._

- **Case 2 – Wrong sign-to-road association**: The sign exists, but it is incorrectly associated with the wrong road segment.  
  _Fix: Replace the associated topology with the correct nearby one._

- **Case 3 – Incorrect road attribution**: The sign is correctly placed on the right topology, but that topology incorrectly allows pedestrian access.  
  _Fix: Update the topology’s `accessCharacteristics` to set pedestrian access to false._

- **Case 4 – Legitimate exception**: The pedestrian access is valid, even though it triggers the validation rule.  
  _Fix: Mark the violation as a legitimate exception and take no further action._

Our project automates the correction of these mismatches using spatial heuristics, connected topology analysis, and rule-based validation.

We processed 60+ violations across European tiles and proposed corrections using:
- **Nearby topology matching**
- **Pedestrian access overflow checks**
- **Node chain analysis**
- **Topology flag updates**
- **Structured logging (CSV + GeoJSON)**

Our approach ensures this pipeline can scale globally by modularizing region-specific heuristics.

> During the hackathon, our pipeline correctly and accurately classified **25 validations** with fixes applied in just **3.5 minutes**.  
> With more time and data, our approach is scalable and can handle significantly more cases beyond the initial scope.

---

## 🚀 What It Does

The pipeline:
1. Collects and combines all validation data from partitions.
2. Enriches each validation with its corresponding topology.
3. Identifies and corrects mismatches in pedestrian/car access (e.g., sidewalks vs motorways).
4. Replaces inappropriate topologies with more appropriate nearby ones.
5. Analyzes connected topologies via node chains to detect inconsistencies.
6. Logs everything to a `results.csv` file and generates human-readable `.txt` reports.

---

## 🗂️ File Structure

```
GeoNauts/
├── combineData.py                 # Step 1: Collect + enrich validations
├── processNoTopology.py          # Step 2: Suggest topologies for unlinked validations
├── access_mismatch.py            # Step 3: Resolve access mismatches (e.g. pedestrian on motorways)
├── searchCase3.py                # Step 4: Pedestrian access overflow fix
├── nodes.py                      # Step 5: Analyze node connectivity for access consistency
├── run_pipeline.py               # Run all steps in order using subprocess
├── results.csv                   # Final output log (updated per step)
├── *.geojson                     # Input/output validation and topology files
└── *.txt                         # Step-specific debug reports
```

---

## ⚙️ How to Run

### 1. Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline:

```bash
python run_pipeline.py
```

> Or run each step individually as needed:
```bash
python combineData.py
python processNoTopology.py
python access_mismatch.py
python searchCase3.py
python nodes.py
```

---

## 📊 Outputs

- `validation_with_topology_suggestions.geojson`: evolving dataset with corrected and enriched topologies
- `results.csv`: structured log of classifications (Cases 1–6), match details, and processing status
- `*.txt`: human-readable debug/review reports

---

## 🏆 Award

**Winner of the HERE Technologies Student Hackathon – April 2025**  
Our team was awarded **1st place** for designing the most innovative and scalable solution. As a result, we earned internship offers at HERE Technologies for Summer 2025!

The challenge: **Automatically correcting spatial validations**.  
We focused on violations triggered by **motorway signs incorrectly associated with pedestrian-accessible roads** (Validation Rule `WSIGN406`), and built a fully automated pipeline to clean and correct the map data.

---

## 🖥️ Final Presentation

We presented our project live at the HERE Technologies Hackathon in Chicago, April 2025.

📽️ [View the presentation slides](https://drive.google.com/file/d/1qCW_RZEWx4DY3TqRdrdd2UEjs-QNI7dV/view?usp=drive_link)

Our demo walked through:
- The real-world motivation behind `WSIGN406` validations
- How our pipeline identifies and classifies access violations
- Case-by-case walkthroughs of logic, code, and fixes

---

## ✍️ Editors

- Aryaman Bhardwaj ([aryamanB0506](https://github.com/aryamanB0506))
- Prabhat Shastri Vemparala ([Prabhat-Shastri](https://github.com/Prabhat-Shastri))
- Kush Mehta ([Kush-Meta](https://github.com/Kush-Meta))
