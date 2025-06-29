import os
import json
from collections import defaultdict

# Root directory containing inrate folders
ROOT_DIR = "inrate"

# Metrics to accumulate
METRICS = ["read_freq", "write_freq", "total_reads", "total_writes", "workingset_size"]

# Traverse each inrate_<tech> directory
for tech_dir in sorted(os.listdir(ROOT_DIR)):
    tech_path = os.path.join(ROOT_DIR, tech_dir)
    if not os.path.isdir(tech_path):
        continue

    print(f"\n=== Technology: {tech_dir} ===")
    tech_totals = defaultdict(int)
    print(f"{'Benchmark':<35} {'Reads':>10} {'Writes':>10} {'R.Freq':>10} {'W.Freq':>10} {'WSS':>12}")
    print("=" * 95)

    # Traverse each benchmark directory inside
    for bench_dir in os.listdir(tech_path):
        bench_path = os.path.join(tech_path, bench_dir)
        if not os.path.isdir(bench_path):
            continue

        # Look for the patternconfig JSON file
        for filename in os.listdir(bench_path):
            if filename.startswith("memsyspatternconfig_") and filename.endswith(".json"):
                file_path = os.path.join(bench_path, filename)
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Warning: Failed to parse JSON in {file_path}")
                        continue

                # If the file is a list of cores (multi-core stats)
                if isinstance(data, list):
                    totals = defaultdict(int)
                    for entry in data:
                        for key in METRICS:
                            totals[key] += entry.get(key, 0)
                            tech_totals[key] += entry.get(key, 0)

                    print(f"{bench_dir:<35} {totals['total_reads']:>10} {totals['total_writes']:>10} "
                          f"{totals['read_freq']:>10} {totals['write_freq']:>10} {totals['workingset_size']:>12}")
                break  # Done with this benchmark

    # Print totals per technology
    print("=" * 95)
    print(f"{'TOTAL for ' + tech_dir:<35} {tech_totals['total_reads']:>10} {tech_totals['total_writes']:>10} "
          f"{tech_totals['read_freq']:>10} {tech_totals['write_freq']:>10} {tech_totals['workingset_size']:>12}")

