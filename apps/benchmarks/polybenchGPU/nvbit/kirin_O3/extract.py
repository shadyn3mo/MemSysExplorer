import os
import json
import csv

# Output CSV path
output_csv = "nvbit_metrics.csv"

# Metrics to collect from JSON
metrics_keys = ["total_reads", "total_writes", "read_freq", "write_freq", "workingset_size"]

# Prepare CSV
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["opt_flags", "workload"] + metrics_keys)

    # Loop through all directories
    for dirname in sorted(os.listdir(".")):
        if os.path.isdir(dirname):
            patternconfig_path = None

            # Try to find memsyspatternconfig_*.json inside the directory
            for filename in os.listdir(dirname):
                if filename.startswith("memsyspatternconfig_") and filename.endswith(".json"):
                    patternconfig_path = os.path.join(dirname, filename)
                    break

            if not patternconfig_path:
                print(f"⚠️ No patternconfig file found in {dirname}")
                continue

            # Load and parse the JSON
            try:
                with open(patternconfig_path, "r") as f:
                    data = json.load(f)

                # Create a row with default values
                row = ["O3", dirname]
                for key in metrics_keys:
                    row.append(data.get(key, ""))  # fallback to blank if key missing

                writer.writerow(row)
                print(f"✅ Processed {dirname}")
            except Exception as e:
                print(f"❌ Failed to read {patternconfig_path}: {e}")

