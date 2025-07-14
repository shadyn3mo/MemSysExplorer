# MemSysExplorer: An Integrated Framework for Advanced Memory System Analysis

This repository provides an integrated framework for comprehensive memory system analysis, combining detailed array characterization, robust fault injection, and flexible traffic evaluation.

## Overview

This framework offers a suite of tools for in-depth memory exploration:

- **Array Characterization**: Detailed memory array characterization for performance and energy, powered by NVSim.
- **Fault Injection**: Robust fault injection and reliability analysis using the integrated msxFI engine.
- **Traffic Evaluation**: Flexible, workload-driven performance evaluation using various traffic patterns.

## Quick Start

### Prerequisites

- The ArrayCharacterization executable (`tech/ArrayCharacterization/nvsim`) must be built.

### Basic Usage

1.  **Define your experiment** in a JSON configuration file:
    ```json
    {
      "experiment": {
        "exp_name": "my_experiment",
        "cell_type": ["SRAM", "RRAM"],
        "opt_target": ["ReadLatency"],
        "capacity": [1, 4],
        "bits_per_cell": [1],
        "case": "best_case",
        "process_node": [22],
        "traffic": ["generic"],
        "output_path": "./output"
      }
    }
    ```

2.  **Run the analysis** from the `tech` directory:
    ```bash
    cd tech
    python main.py --config configs/your_config.json
    ```

3.  **Inspect the results** in the specified output directory.

## Supported Memory Technologies

### Standard Technologies
- **SRAM**: Static Random Access Memory
- **RRAM**: Resistive Random Access Memory  
- **PCM**: Phase Change Memory
- **STT**: Spin-Transfer Torque MRAM
- **FeFET**: Ferroelectric Field-Effect Transistor
- **eDRAM1T**: Single-transistor embedded DRAM
- **eDRAM3T**: Three-transistor embedded DRAM
- **eDRAM3T333**: An advanced 3T eDRAM variant utilizing a multi-process technology:

## Configuration System

### Basic Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `cell_type` | list | Memory technologies to evaluate. | `["SRAM", "RRAM"]` |
| `opt_target` | list | Optimization targets for NVSim. | `["ReadLatency", "Area"]` |
| `capacity` | list | Memory capacity in megabytes (MB). | `[1, 4, 16]` |
| `bits_per_cell` | list | Bits stored per memory cell. | `[1, 2]` |
| `process_node` | int/list | Process technology node in nanometers (nm). | `[22]` |
| `case` | string | Specifies whether to use `"best_case"` or `"worst_case"` cell parameters. | `"best_case"` |


### Traffic Configuration
Please check the examples in `tech/configs`


## License

This framework combines components from multiple projects. Please refer to the licenses of individual components for specific terms.