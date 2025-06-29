# Profiling with NVBit

The **NVBitProfiler** integrates NVIDIA's NVBit (NVIDIA Binary Instrumentation Tool) with MemSysExplorer to provide dynamic instrumentation of memory accesses at the GPU level. It collects memory access frequency and working set statistics during runtime by intercepting and analyzing memory instructions on CUDA binaries.

This lightweight profiler is suitable for evaluating the memory access behavior of GPU kernels without modifying source code.

## Overview

NVBit leverages a custom shared object (`nvbit.so`) injected at runtime using the `LD_PRELOAD` mechanism. During execution, the instrumentation layer collects various memory-related statistics and writes them to a summary file.

The profiling workflow includes:

1. **Profiling (`profiling`)** – Runs the target GPU application with NVBit instrumentation enabled.
2. **Metric Extraction (`extract_metrics`)** – Parses the generated `global_summary.txt` file to extract relevant memory access statistics.

## Required Arguments

The profiler defines required arguments for each stage as follows:

```python
@classmethod
def required_profiling_args(cls):
    return ["executable"]

@classmethod
def required_extract_args(cls, action):
    if action == "extract_metrics":
        return ["report_file"]
    else:
        return []
```

## Usage Example

* **Run NVBit profiling on a GPU application:**

```bash
python3 main.py --profiler nvbit --action profiling --executable ./your_gpu_app
```

* **Extract metrics from NVBit output:**

```bash
python3 main.py --profiler nvbit --action extract_metrics --report_file global_summary.txt
```

* **Do both profiling and extraction sequentially:**

```bash
python3 main.py --profiler nvbit --action both --executable ./your_gpu_app
```

## Instrumentation Behavior

The NVBit profiler dynamically injects instrumentation code using `LD_PRELOAD` to load:

```text
profilers/nvbit/lib/nvbit.so
```

During execution, this shared object captures memory access events and records statistics into a text file (default: `global_summary.txt`).

This behavior is managed by a preload wrapper script:

```text
profilers/nvbit/preload_run.py
```

> This script ensures that the target application runs with the required environment and instrumentation hooks set via `LD_PRELOAD`. It is automatically invoked when using NVBit with `main.py`.

The instrumentation core is implemented in:

```text
profilers/nvbit/src/memcount.cu
profilers/nvbit/src/inject_funcs.cu
```

> These files are adapted from the original NVBit example source but modified to suit MemSysExplorer's profiling needs.

## Environment Notes

* Ensure that the file `nvbit.so` is located in `profilers/nvbit/lib/` and is executable.
* The `LD_PRELOAD` environment variable is automatically set by the profiler before execution.
* Only CUDA-enabled applications with GPU kernels are supported. CPU binaries will fail silently.

## Troubleshooting

1. **Missing `nvbit.so`:**
   Ensure that `lib/nvbit.so` exists relative to the `NVBitProfilers` script after building the tools.

2. **Permission Denied or Silent Exit:**
   Confirm that your application is CUDA-based and built for a supported GPU architecture.

3. **No Output Generated:**
   Make sure your application launches actual CUDA kernels. NVBit will not instrument empty or stub kernels.

## License

This profiler integrates [NVBit](https://nvbit.github.io/), a dynamic binary instrumentation framework developed by NVIDIA.

NVBit is used in accordance with the licensing and distribution terms provided by NVIDIA.

Academic reference:

> Oreste Villa, Mark Stephenson, David Nellans, and Stephen W. Keckler. 2019.
> *NVBit: A Dynamic Binary Instrumentation Framework for NVIDIA GPUs*.
> In *Proceedings of the 52nd Annual IEEE/ACM International Symposium on Microarchitecture (MICRO '52)*, 372–383.
> [https://doi.org/10.1145/3352460.3358307](https://doi.org/10.1145/3352460.3358307)

