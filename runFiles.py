import subprocess

# List of your step scripts in order
scripts = [
    "combineData.py",         # Step 1: Collect validations & enrich with topologies
    "processNoTopology.py",   # Step 2: Handle missing topology suggestions
    "pedestriansNoCars.py",     # Step 3: Access mismatch correction
    "searchCase3.py",         # Step 4: Motorway pedestrian overflow fix
    "nodes.py"                # Step 5: Node chain access analysis
]

for script in scripts:
    print(f"\n[🔁 Running {script}]")
    result = subprocess.run(["python", script])
    if result.returncode != 0:
        print(f"[❌ ERROR] Script {script} exited with code {result.returncode}")
        break
    else:
        print(f"[✅ DONE] {script} completed successfully.")