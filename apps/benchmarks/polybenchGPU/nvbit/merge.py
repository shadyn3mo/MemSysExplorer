import os
import pandas as pd

# Root directory containing the flag_O* folders
root_dir = "."
output_file = "nvbit_flags.csv"

# List to hold all DataFrames
all_data = []

# Loop through subdirectories like flag_O1, flag_O2, ...
for dirname in sorted(os.listdir(root_dir)):
    dirpath = os.path.join(root_dir, dirname)
    if os.path.isdir(dirpath) and dirname.startswith("flag_"):
        filepath = os.path.join(dirpath, "nvbit_metrics.csv")
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df["opt_flags"] = dirname  # Add source directory as opt_flags
            all_data.append(df)
        else:
            print(f"⚠️ No nvbit_metrics.csv in {dirname}")

# Concatenate and write out
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv(output_file, index=False)
    print(f"✅ Combined CSV written to: {output_file}")
else:
    print("❌ No data found to merge.")

