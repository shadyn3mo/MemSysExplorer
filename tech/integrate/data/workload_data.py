"""
Workload Data

This file contains workload data definitions for
various application domains including DNN inference,
graph processing, and SPEC benchmarks.
"""

# =============================================================================
# DNN Workloads
# =============================================================================

DNN_weights = {
  "names": ["ResNet50w",
            "ResNet50w_int",
            "ResNet26w_single",
            "ResNet26w_single_int",
            "ResNet26w_multi",
            "ResNet26w_multi_int",
            "ALBERTw_emb",
            "ALBERTw_all",
            "ALBERTw_multi"
  ],
  "reads": [4.7e6, #per input
            4.7e6,
            1.95e6,
            1.95e6,
            5.9e6,
            5.9e6,
            3.84e6,
            1.17e7,
            2.92e7,
  ],
  "writes": [0, #per input
             0,
             0,
             0,
             0,
             0,
             0,
             0,
             0,
  ],
  "ips": [45, #inferences per second
          1,
          45,
          1,
          45,
          1,
          1,
          1,
          1,
  ]
}

DNN_weights_acts = {
  "names": ["ResNet50",
            "ResNet50_int",
            "ResNet26_single",
            "ResNet26_single_int",
            "ResNet26_multi",
            "ResNet26_multi_int",
  ],
  "reads": [7.2e6, #per input
            7.2e6,
            2.2e6,
            2.2e6,
            6.6e6,
            6.6e6,
  ],
  "writes": [2.4e6, #per input
             2.4e6,
             0.22e6,
             0.22e6,
             0.9e6,
             0.9e6,
  ],
  "ips": [45, #inferences per second
          1,
          45,
          1,
          45,
          1,
  ]
}

# =============================================================================
# Graph Workloads
# =============================================================================

graph8MB = {
  "names": ["Facebook--BFS8MB",
            "Facebook--SSSP8MB",
            "Wikipedia--BFS8MB",
  ],
  "raw_thruput": [1.6e9, #edges/s
                  1.4e9,
                  1e8
  ],
  "read_freq": [4.2e7,
                2.8e8,
                1.3e6
  ],
  "write_freq": [8.8e5,
                 1.9e5,
                 7.2e4
  ],
}

# =============================================================================
# SPEC Workloads
# =============================================================================

spec8MBLLC = {
  "names": ["544.nab_r",
    "502.gcc_r",
    "520.omnetpp_r",
    "527.cam4_r",
    "525.x264_r",
    "523.xalancbmk_r",
    "505.mcf_r",
    "503.bwaves_r",
    "511.povray_r",
    "510.parest_r",
    "521.wrf_r",
    "500.perlbench_r",
    "508.namd_r",
    "519.lbm_r",
    "526.blender_r",
    "531.deepsjeng_r",
    "538.imagick_r",
    "541.leela_r",
    "549.fotonik3d_r",
    "557.xz_r",
    "548.exchange2_r",
    "554.roms_r",
  ],
  "reads": [718221,
    315974,
    3247385,
    0,
    1694407,
    14189676,
    21663715,
    0,
    367,
    0,
    0,
    537236,
    88373,
    15594920,
    7088,
    216957,
    131702,
    43089,
    0,
    348859,
    0,
    0,
  ],
  "writes": [316842,
    492005,
    461957,
    0,
    988554,
    177170,
    16453043,
    0,
    948,
    0,
    0,
    432168,
    769990,
    15602139,
    133884,
    238895,
    800795,
    57942,
    0,
    879848,
    0,
    0,
  ],
  "ex_time": [0.13499321,
    0.119132203,
    0.128960125,
    0,
    0.076020581,
    0.127457892,
    0.299732027,
    0,
    0.098303235,
    0,
    0,
    0.123662168,
    0.087542673,
    0.338967826,
    0.101472204,
    0.104507865,
    0.069970796,
    0.105329386,
    0,
    0.118264606,
    0,
    0,
  ]
}

# Add the MB suffix to names for consistency
spec8MBLLC["names"] = [ name+"8MB" for name in spec8MBLLC["names"] ]

# =============================================================================
# Utility Functions
# =============================================================================

def get_workload_by_name(workload_name: str):
    """
    Get workload data by name
    
    Args:
        workload_name: Name of the workload dataset
        
    Returns:
        Dictionary containing workload data
        
    Raises:
        ValueError: If workload name not found
    """
    workloads = {
        # DNN workloads (only include the ones that actually exist)
        'DNN_weights': DNN_weights,
        'DNN_weights_acts': DNN_weights_acts,
        
        # Graph workloads (only include the ones that actually exist)
        'graph8MB': graph8MB,
        
        # SPEC workloads (only include the ones that actually exist)
        'spec8MBLLC': spec8MBLLC
    }
    
    if workload_name not in workloads:
        available = list(workloads.keys())
        raise ValueError(f"Workload '{workload_name}' not found. Available: {available}")
    
    return workloads[workload_name]

def get_all_workloads():
    """Get all available workload datasets"""
    return {
        'DNN_weights': DNN_weights,
        'DNN_weights_acts': DNN_weights_acts,
        'graph8MB': graph8MB,
        'spec8MBLLC': spec8MBLLC
    }

def list_available_workloads():
    """List names of all available workload datasets"""
    return list(get_all_workloads().keys())

def get_benchmark_count(workload_name: str) -> int:
    """Get number of benchmarks in a workload dataset"""
    workload = get_workload_by_name(workload_name)
    return len(workload.get('names', []))

def get_benchmark_data(workload_name: str, benchmark_index: int) -> dict:
    """
    Get data for a specific benchmark by index
    
    Args:
        workload_name: Name of the workload dataset
        benchmark_index: Index of the benchmark (0-based)
        
    Returns:
        Dictionary with benchmark data
    """
    workload = get_workload_by_name(workload_name)
    
    if benchmark_index >= len(workload['names']):
        raise IndexError(f"Benchmark index {benchmark_index} out of range for {workload_name}")
    
    benchmark_data = {'name': workload['names'][benchmark_index]}
    
    # Extract all data for this benchmark index
    for key, values in workload.items():
        if key != 'names' and isinstance(values, list):
            benchmark_data[key] = values[benchmark_index]
    
    return benchmark_data

def iterate_benchmarks(workload_name: str):
    """
    Iterator over all benchmarks in a workload dataset
    
    Args:
        workload_name: Name of the workload dataset
        
    Yields:
        Dictionary with benchmark data for each benchmark
    """
    workload = get_workload_by_name(workload_name)
    
    for i in range(len(workload['names'])):
        yield get_benchmark_data(workload_name, i)