import os
import json
import csv
import statistics

# Config
root_dir = "."
output_csv = "ncu_metrics.csv"
metrics_keys = ["total_reads", "total_writes", "read_freq", "write_freq", "workingset_size"]

with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["opt_flags", "workload"] + metrics_keys)

    for workload in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, workload)
        if not os.path.isdir(path):
            continue

        # Track lists for each metric
        totals = {"total_reads": 0, "total_writes": 0}
        avgables = {"read_freq": [], "write_freq": [], "workingset_size": []}
        found = 0

        # Collect patternconfig files
        for file in os.listdir(path):
            if file.startswith("memsyspatternconfig_") and file.endswith(".json"):
                filepath = os.path.join(path, file)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    
                    totals["total_reads"] += data.get("total_reads", 0)
                    totals["total_writes"] += data.get("total_writes", 0)
                    for key in avgables:
                        val = data.get(key)
                        if val is not None:
                            avgables[key].append(val)
                    found += 1
                except Exception as e:
                    print(f"❌ Error reading {filepath}: {e}")

        if found == 0:
            print(f"⚠️ No patternconfig files found for workload: {workload}")
            continue

        # Prepare final values
        row = ["O3", workload]
        row.append(totals["total_reads"])
        row.append(totals["total_writes"])
        for key in ["read_freq", "write_freq", "workingset_size"]:
            values = avgables[key]
            avg = statistics.mean(values) if values else 0
            row.append(avg)

        writer.writerow(row)
        print(f"✅ Processed {workload} with {found} kernels")

