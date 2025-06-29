# Profiling with Dynamorio

### Features

* Tracks memory access frequency and working set size.
* Separates read/write statistics.
* Lightweight and configurable through runtime arguments.
* Supports integration with MemSysExplorer for streamlined workflows.

## Setup Instructions

### 1. Environment Variables

```bash
export DYNAMORIO_HOME=/path/to/dynamorio
export APPS_HOME=/path/to/MemSys-Playground/apps
```

### 2. Build the DynamoRIO Client

```bash
cd $APPS_HOME/profilers/dynamorio/build
./build.sh
```

## Usage

### A. Standalone Mode

Run a target executable with `memcount` instrumentation:

```bash
$DYNAMORIO_HOME/bin64/drrun -c $APPS_HOME/profilers/dynamorio/build/libmemcount.so -- <executable>
```

### B. Integrated with MemSysExplorer

```bash
cd $APPS_HOME
python3 main.py --profiler dynamorio --action both --executable /path/to/executable
```

## Output

The profiler will generate a summary report with metrics such as:

* Total memory reads and writes
* Unique accessed addresses (Working Set Size)
* Frequency of repeated accesses

These can be further analyzed using MemSysExplorer tools.

## License

This tool includes components built using [DynamoRIO](https://dynamorio.org/), which is licensed under the [DynamoRIO License](https://dynamorio.org/page_license.html).

