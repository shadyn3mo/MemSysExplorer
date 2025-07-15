"""
Traffic Evaluation

This module contains the core traffic evaluation functions for
memory system traffic pattern analysis and evaluation.
"""

from ..data.workload_data import *
from .eval_utils import ExperimentResult

# Import fault injection controller for fault-aware evaluation
try:
    from ..interfaces.msxfi_controller import MSXFIController
except ImportError:
    MSXFIController = None


def generic_traffic(access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths):
    """
    Evaluates and writes results for scenarios from a pre-set, generic traffic sweep
    
    Args:
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects which were used for array simulation
        nvsim_outputs: paths to NVSim output files
        results_csv: path to CSV file containing results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
    """
    write_accesses = [0, 1, 2, 1e1, 2e1, 1e2, 2e2, 1e3, 2e3, 1e4, 2e4, 1e5, 2e5, 1e6, 2e6, 1e7]
    read_accesses = [0, 1, 2, 1e1, 2e1, 1e2, 2e2, 1e3, 2e3, 1e4, 2e4, 1e5, 2e5, 1e6, 2e6, 1e7, 2e7, 1e8, 2e8, 1e9, 2e9, 1e10]
    
    for wr in write_accesses:
        for rd in read_accesses:
            access_pattern.write_freq = wr
            access_pattern.read_freq = rd
            access_pattern.benchmark_name = "test"  # Generic uses "test" as benchmark name
            
            for i in range(len(cell_paths)):
                this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[i], nvsim_outputs[i])
                this_result.evaluate()
                this_result.report_result_benchmark(1, results_csv, cell_paths[i], cfg_paths[i], access_pattern)


def graph_traffic(graph8MB, access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths):
    """
    Evaluates and writes results for scenarios from a graph application traffic sweep
    
    Args:
        graph8MB: Graph workload data
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects which were used for array simulation
        nvsim_outputs: paths to NVSim output files
        results_csv: path to CSV file containing results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
    """
    for (i, name) in enumerate(graph8MB["names"]):
        access_pattern.benchmark_name = name
        if (graph8MB["read_freq"][i] > 0):
            access_pattern.name = name
            access_pattern.write_freq = graph8MB["write_freq"][i] 
            access_pattern.read_freq = graph8MB["read_freq"][i]
            
            for j in range(len(cell_paths)):
                this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[j], nvsim_outputs[j])
                this_result.evaluate()
                this_result.report_result_benchmark(1, results_csv, cell_paths[j], cfg_paths[j], access_pattern)


def dnn_traffic(DNN_weights, DNN_weights_acts, access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths):
    """
    Evaluates and writes results for scenarios from a DNN application traffic sweep
    
    Args:
        DNN_weights: DNN weights workload data
        DNN_weights_acts: DNN weights+activations workload data
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects which were used for array simulation
        nvsim_outputs: paths to NVSim output files
        results_csv: path to CSV file containing results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
    """
    dnns = [DNN_weights, DNN_weights_acts]
    
    for dnn in dnns:
        for (i, name) in enumerate(dnn["names"]):
            access_pattern.benchmark_name = name
            if (dnn["reads"][i] > 0):
                access_pattern.name = name
                access_pattern.read_freq = dnn["reads"][i] * dnn["ips"][i]
                access_pattern.write_freq = dnn["writes"][i] * dnn["ips"][i]
                
                for j in range(len(cell_paths)):
                    this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[j], nvsim_outputs[j])
                    this_result.evaluate()
                    this_result.report_result_benchmark(1, results_csv, cell_paths[j], cfg_paths[j], access_pattern)


def spec_traffic_single(spec8MBLLC, access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths):
    """
    Evaluates and writes results for scenarios from SPEC2017 Cache Profiling traffic sweep (single dataset)
    
    Args:
        spec8MBLLC: SPEC workload data
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects which were used for array simulation
        nvsim_outputs: paths to NVSim output files
        results_csv: path to CSV file containing results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
    """
    for (i, name) in enumerate(spec8MBLLC["names"]):  
        access_pattern.benchmark_name = name
        if (spec8MBLLC["reads"][i] > 0):
            access_pattern.name = name
            access_pattern.write_freq = spec8MBLLC["writes"][i] / spec8MBLLC["ex_time"][i]
            access_pattern.read_freq = spec8MBLLC["reads"][i] / spec8MBLLC["ex_time"][i]
            
            for j in range(len(cell_paths)):
                this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[j], nvsim_outputs[j])
                this_result.evaluate()
                this_result.report_result_benchmark(1, results_csv, cell_paths[j], cfg_paths[j], access_pattern)


def spec_traffic(spec8MBLLC, spec16MBLLC, spec16MBDRAM, spec16MBL2, spec32MBLLC, spec64MBLLC, 
                access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths):
    """
    Evaluates and writes results for scenarios from SPEC2017 Cache Profiling traffic sweep
    
    Args:
        spec8MBLLC: SPEC 8MB LLC workload data
        spec16MBLLC: SPEC 16MB LLC workload data
        spec16MBDRAM: SPEC 16MB DRAM workload data
        spec16MBL2: SPEC 16MB L2 workload data
        spec32MBLLC: SPEC 32MB LLC workload data
        spec64MBLLC: SPEC 64MB LLC workload data
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects which were used for array simulation
        nvsim_outputs: paths to NVSim output files
        results_csv: path to CSV file containing results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
    """
    for benchmark in [spec8MBLLC, spec16MBLLC, spec16MBDRAM, spec16MBL2, spec32MBLLC, spec64MBLLC]:
        for (i, name) in enumerate(benchmark["names"]):  
            access_pattern.benchmark_name = name
            if (benchmark["reads"][i] > 0):
                access_pattern.name = name
                access_pattern.write_freq = benchmark["writes"][i] / benchmark["ex_time"][i]
                access_pattern.read_freq = benchmark["reads"][i] / benchmark["ex_time"][i]
                
                for j in range(len(cell_paths)):
                    this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[j], nvsim_outputs[j])
                    this_result.evaluate()
                    this_result.report_result_benchmark(1, results_csv, cell_paths[j], cfg_paths[j], access_pattern)


def generic_traffic_with_write_buff(access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths):
    """
    Evaluates and writes results for pre-defined case study scenarios from a generic application 
    traffic sweep with write buffering that is evaluated
    
    Args:
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects which were used for array simulation
        nvsim_outputs: paths to NVSim output files
        results_csv: path to CSV file containing results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
    """
    rd_base_spec = 3.7e6   # geomean of SPEC CPU2017 16MB cache accesses
    wr_base_spec = 2.3e6   # geomean of SPEC CPU2017
    rd_base_graph = 4.2e7  # FB BFS
    wr_base_graph = 1.9e5  # FB BFS

    percent_write_traffic_reduction = [0.001, 0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 0.999, 1.0]
    percent_write_latency_mask = [0.001, 0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 0.999, 1.0]

    for pct_traffic in percent_write_traffic_reduction:
        for pct_mask in percent_write_latency_mask:
            for i in range(len(cell_paths)):
                # Create temp write latency, scale just for eval, reset
                temp_write_latency = nvsim_outputs[i].write_latency
                # Set updated write latency
                nvsim_outputs[i].write_latency = temp_write_latency * pct_mask
                
                # Repeat for spec geomean, graph example      
                access_pattern.write_freq = wr_base_spec * pct_traffic
                access_pattern.read_freq = rd_base_spec
                access_pattern.benchmark_name = f"spec_{pct_traffic}_{pct_mask}"
                
                this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[i], nvsim_outputs[i])
                this_result.evaluate()
                this_result.report_result_benchmark(1, results_csv, cell_paths[i], cfg_paths[i], access_pattern)
                
                # Graph example start
                access_pattern.write_freq = wr_base_graph * pct_traffic
                access_pattern.read_freq = rd_base_graph
                access_pattern.benchmark_name = f"fbbfs_{pct_traffic}_{pct_mask}"
                
                this_result = ExperimentResult(access_pattern, nvsim_input_cfgs[i], nvsim_outputs[i])
                this_result.evaluate()
                this_result.report_result_benchmark(1, results_csv, cell_paths[i], cfg_paths[i], access_pattern)
                
                # Reset write latency
                nvsim_outputs[i].write_latency = temp_write_latency