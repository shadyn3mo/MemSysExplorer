# Profiling with Nsight Compute 

Nsight Compute (NCU) is used in **MemSysExplorer** to collect detailed **Hardware Performance Counter (HPC)** metrics on NVIDIA GPUs. This integration enables fine-grained insight into GPU memory hierarchy behavior, such as cache hit/miss rates, DRAM utilization, and kernel-level efficiency.

## Workflow Overview

MemSysExplorer supports two actions when using the Nsight Compute profiler:

1. **Profiling (`profiling`)** – Runs the target application under `ncu`, collecting metrics as defined in the config file.
2. **Metric Extraction (`extract_metrics`)** – Parses the `.ncu-rep` report to extract relevant metrics.

You can also combine both using the `--action both` flag.

## Required Arguments

Depending on the selected action, different arguments are required:

```python
@classmethod
def required_profiling_args(cls):
    return ["executable", "level"]

@classmethod
def required_extract_args(cls, action):
    if action == "extract_metrics":
        return ["report_file"]
    else:
        return []
```

## Supported Memory Levels

Use the `--level` flag to select the memory hierarchy region for profiling:

| **Level** | **Description**                                   |
| --------- | ------------------------------------------------- |
| `l2`      | L2 unified cache statistics (hit rate, miss rate) |
| `dram`    | DRAM-level traffic (read/write bytes, cycles)     |
| `custom`  | User-defined metrics for advanced analysis        |

> **Note:** `l1` and `l3` levels are not currently supported and default to `custom`.

## Example Usage

### Run profiling

```bash
python main.py --profiler ncu --action profiling --level l2 --executable ./your_gpu_binary
```

### Extract metrics from an existing report

```bash
python main.py --profiler ncu --action extract_metrics --report_file ./example.ncu-rep
```

### Run both profiling and extraction

```bash
python main.py --profiler ncu --action both --level dram --executable ./your_gpu_binary
```

## Configuration System

Nsight Compute uses a **two-part configuration system** in MemSysExplorer:

1. **Metric Configuration (`settings.conf`)**
2. **Section File (`.section`)** used by Nsight Compute

These are auto-generated in the following directories:

* `profilers/ncu/configs/` – Contains `[Metrics]` blocks with desired performance counters.
* `profilers/ncu/sections/` – Contains generated `.section` files.

If no config is found for a selected level, MemSysExplorer generates a default one.

### Example Config Files

**`l2_settings.conf`**

```ini
[Metrics]
L2 Cache Hit Rate = lts__t_sectors_hit_rate.pct
L2 Cache Miss Rate = lts__t_sectors_miss_rate.pct
```

**`dram_settings.conf`**

```ini
[Metrics]
DRAM Reads = dram__bytes_read.sum
DRAM Writes = dram__bytes_write.sum
```

### Custom Configuration

You may create your own metrics set using:

```bash
--level custom
```

Edit `profilers/ncu/configs/custom_settings.conf` to define your own metrics.

## Checking Supported Metrics

To list all valid counters supported by your GPU:

```bash
ncu --query-metrics
```

Use these metric names in the relevant `settings.conf` file.

## Additional Notes

* Ensure `ncu` is available in your system `PATH`.
* `.ncu-rep` files are generated using the target executable's name.
* `.section` files are dynamically created and stored in `sections/`.

## Troubleshooting

1. **ncu not found:**

   * Make sure Nsight Compute CLI is installed and `ncu` is in `PATH`.
   * You can export `NCU_HOME` and adjust `PATH` accordingly.

2. **Permission denied:**

   * Ensure that GPU counters are enabled for your user. See: [NVIDIA Perf Counter Guide](https://developer.nvidia.com/nvidia-development-tools-solutions-err_nvgpuctrperm-permission-issue-performance-counters)

3. **Missing config/section files:**

   * MemSysExplorer will auto-generate them as needed if not present.

---

## License

This profiler integrates [Nsight Compute](https://developer.nvidia.com/nsight-compute), a proprietary performance analysis tool provided by NVIDIA Corporation.

Nsight Compute is used under the terms of the [NVIDIA Nsight Compute EULA](https://developer.nvidia.com/nsight-compute-eula). All rights reserved by NVIDIA.

