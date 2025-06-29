# Profiling with Sniper Architectural Simulator

The **SniperProfiler** integrates the Sniper architectural simulator into MemSysExplorer to evaluate memory system behavior at cycle-level precision. It enables users to run real workloads in a simulated environment and analyze cache/memory interactions, latency, and access statistics.

## Workflow Overview

The Sniper integration supports the following two actions:

1. **Profiling (`profiling`)** – Runs Sniper with the specified application and configuration.
2. **Metric Extraction (`extract_metrics`)** – Parses Sniper outputs and summarizes memory access statistics.

> When using the `both` action, profiling and extraction are executed sequentially.

---

## Required Arguments

The following arguments are required depending on the selected action:

```python
@classmethod
def required_profiling_args(cls):
    return ["config", "executable"]

@classmethod
def required_extract_args(cls, action):
    if action == "extract_metrics":
        return ["results_dir", "level"]
    else:
        return []
```

### CLI Flags
* `--config` – Path to Sniper configuration file
* `--executable` – Application to simulate
* `--results_dir` – Directory containing Sniper simulation output
* `--level` – Memory level to analyze (`l1`, `l2`, `l3`, `dram`)

---

## Example Usage

### Run simulation and extract metrics:

```bash
python3 main.py --profiler sniper --action both \
    --config config/skylake.cfg \
    --level l3 \
    --results_dir ./output_path
    --executable ./your_app
```

### Extract metrics from previous simulation:

```bash
python3 main.py --profiler sniper --action extract_metrics \
    --results_dir ./output_path \
    --level dram
```

---

## Customizing Memory Modeling

Sniper supports memory hierarchy modeling by allowing users to define latency values in the config file. This enables simulation of custom memory technologies like DRAM, HBM, or NVM.

Modify your config file (e.g., `config/skylake.cfg`) by setting the appropriate latency parameters:

```ini
[perf_model/l3_cache]
rw_enabled = true
read_access_time = 100
write_access_time = 50000
```

You may apply the same format to:

* `[perf_model/l1_cache]`
* `[perf_model/l2_cache]`
* `[perf_model/dram]`

This feature lets you evaluate the impact of memory latency changes on workload performance.

### Example Config File

MemSysExplorer provides an example config at:

```
config/skylake.cfg
```

Use this as a starting point and adjust it for your target system or memory design.

---

## Output and Metrics

Once simulation is complete, the memory stats are processed and stored in:

```
memsys_stats.out
```

This file contains:

* Read/write event counts
* Access latencies
* Statistics grouped by memory level

The `snipermem.py` script is used internally to parse and filter these metrics.

---

## Troubleshooting

* **Missing Sniper binary:**
  Ensure `run-sniper` exists in `profilers/snipersim/`. Otherwise, update the path in the script.

* **Missing stats script:**
  Confirm that `snipermem.py` is present in `snipersim/tools/`.

* **Invalid config block:**
  Check that `[perf_model/*]` sections in the config file are properly defined. Refer to the [official Sniper docs](https://snipersim.org) for more examples.

## License

This profiler integrates the [Sniper Multicore Simulator](https://snipersim.org), a high-speed, cycle-level architectural simulator developed by the HPC Group at Ghent University and contributors.

> Citation:
> 
> Trevor E. Carlson, Wim Heirman, and Lieven Eeckhout.  
> *Sniper: Exploring the Level of Abstraction for Scalable and Accurate Parallel Multi-Core Simulation.*  
> In *Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis (SC’11)*.  
> DOI: [10.1145/2063384.2063454](https://doi.org/10.1145/2063384.2063454)

> License: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)

