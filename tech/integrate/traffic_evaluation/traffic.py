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


def fault_aware_traffic_evaluation(access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, 
                                  cell_paths, cfg_paths, fault_config, traffic_type="generic"):
    """
    Enhanced traffic evaluation with fault injection capabilities.
    
    Compares baseline performance with fault-injected memory characteristics
    to assess system reliability and performance degradation.
    
    Args:
        access_pattern: AccessPattern object
        nvsim_input_cfgs: NVSimInputConfig objects used for array simulation
        nvsim_outputs: paths to NVSim output files (baseline)
        results_csv: path to CSV file for results
        cell_paths: paths to NVSim input cell files
        cfg_paths: paths to NVSim input config files
        fault_config: Fault injection configuration dictionary
        traffic_type: Type of traffic pattern ("generic", "spec", "dnn", "graph")
    """
    if not MSXFIController:
        # Fall back to baseline evaluation if msxFI is not available
        if traffic_type == "generic":
            generic_traffic(access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths)
        return
    
    # Initialize fault injection controller
    try:
        fault_controller = MSXFIController(fault_config)
        if not fault_controller.is_enabled():
            # Fall back to baseline evaluation
            if traffic_type == "generic":
                generic_traffic(access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths)
            return
    except Exception as e:
        print(f"Warning: Failed to initialize fault injection: {e}")
        if traffic_type == "generic":
            generic_traffic(access_pattern, nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths)
        return
    
    # Define traffic patterns based on type
    traffic_patterns = []
    if traffic_type == "generic":
        write_accesses = [0, 1, 2, 1e1, 2e1, 1e2, 2e2, 1e3, 2e3, 1e4, 2e4, 1e5, 2e5, 1e6, 2e6, 1e7]
        read_accesses = [0, 1, 2, 1e1, 2e1, 1e2, 2e2, 1e3, 2e3, 1e4, 2e4, 1e5, 2e5, 1e6, 2e6, 1e7, 2e7, 1e8, 2e8, 1e9, 2e9, 1e10]
        for wr in write_accesses:
            for rd in read_accesses:
                traffic_patterns.append({"write_freq": wr, "read_freq": rd, "benchmark": "test"})
    elif traffic_type == "dnn":
        dnns = [DNN_weights, DNN_weights_acts]
        for dnn in dnns:
            for (i, name) in enumerate(dnn["names"]):
                if dnn["reads"][i] > 0:
                    traffic_patterns.append({
                        "write_freq": dnn["writes"][i] * dnn["ips"][i],
                        "read_freq": dnn["reads"][i] * dnn["ips"][i],
                        "benchmark": name
                    })
    
    # Generate fault-injected versions of memory outputs
    faulty_outputs = []
    for i, nvsim_output in enumerate(nvsim_outputs):
        try:
            # Create synthetic memory data for fault injection
            import numpy as np
            # Use memory characteristics as basis for fault injection
            memory_data = np.array([
                nvsim_output.read_latency,
                nvsim_output.write_latency,
                nvsim_output.read_energy,
                nvsim_output.write_energy
            ]).reshape(2, 2)
            
            # Apply fault injection
            faulty_data = fault_controller.inject_memory_faults(memory_data, seed=i)
            
            # Calculate fault statistics
            fault_stats = fault_controller.get_fault_statistics(memory_data, faulty_data)
            
            # Create modified output with fault-affected characteristics
            faulty_output = type(nvsim_output)()  # Create new instance of same type
            faulty_output.__dict__.update(nvsim_output.__dict__.copy())
            
            # Apply fault impact to timing and energy characteristics
            fault_rate = fault_stats.get('fault_rate', 0.0)
            if fault_rate > 0:
                # Empirical model for fault impact
                latency_degradation = 1.0 + (fault_rate * 2.0)
                energy_increase = 1.0 + (fault_rate * 1.5)
                
                faulty_output.read_latency *= latency_degradation
                faulty_output.write_latency *= latency_degradation
                faulty_output.read_energy *= energy_increase
                faulty_output.write_energy *= energy_increase
            
            faulty_outputs.append(faulty_output)
            
        except Exception as e:
            print(f"Warning: Fault injection failed for output {i}: {e}")
            faulty_outputs.append(nvsim_output)  # Use baseline if fault injection fails
    
    # Evaluate both baseline and faulty scenarios
    for pattern in traffic_patterns:
        access_pattern.write_freq = pattern["write_freq"]
        access_pattern.read_freq = pattern["read_freq"]
        access_pattern.benchmark_name = pattern["benchmark"]
        
        # Evaluate baseline performance
        for i in range(len(cell_paths)):
            baseline_result = ExperimentResult(access_pattern, nvsim_input_cfgs[i], nvsim_outputs[i])
            baseline_result.evaluate()
            
            # Mark as baseline result
            baseline_access_pattern = type(access_pattern)()
            baseline_access_pattern.__dict__.update(access_pattern.__dict__.copy())
            baseline_access_pattern.benchmark_name = f"{pattern['benchmark']}_baseline"
            
            baseline_result.report_result_benchmark(1, results_csv, cell_paths[i], cfg_paths[i], baseline_access_pattern)
            
            # Evaluate fault-injected performance
            faulty_result = ExperimentResult(access_pattern, nvsim_input_cfgs[i], faulty_outputs[i])
            faulty_result.evaluate()
            
            # Mark as faulty result
            faulty_access_pattern = type(access_pattern)()
            faulty_access_pattern.__dict__.update(access_pattern.__dict__.copy())
            faulty_access_pattern.benchmark_name = f"{pattern['benchmark']}_faulty"
            
            faulty_result.report_result_benchmark(1, results_csv, cell_paths[i], cfg_paths[i], faulty_access_pattern)
            
            # Calculate and report performance degradation
            try:
                performance_degradation = {
                    'latency_degradation': (faulty_result.avg_latency / baseline_result.avg_latency) if baseline_result.avg_latency > 0 else 1.0,
                    'energy_degradation': (faulty_result.avg_energy / baseline_result.avg_energy) if baseline_result.avg_energy > 0 else 1.0,
                    'bandwidth_degradation': (baseline_result.bandwidth / faulty_result.bandwidth) if faulty_result.bandwidth > 0 else 1.0
                }
                
                # Create degradation result entry
                degradation_access_pattern = type(access_pattern)()
                degradation_access_pattern.__dict__.update(access_pattern.__dict__.copy())
                degradation_access_pattern.benchmark_name = f"{pattern['benchmark']}_degradation"
                
                # Store degradation metrics in a custom result object
                degradation_result = ExperimentResult(degradation_access_pattern, nvsim_input_cfgs[i], nvsim_outputs[i])
                degradation_result.avg_latency = performance_degradation['latency_degradation']
                degradation_result.avg_energy = performance_degradation['energy_degradation']
                degradation_result.bandwidth = performance_degradation['bandwidth_degradation']
                
                degradation_result.report_result_benchmark(1, results_csv, cell_paths[i], cfg_paths[i], degradation_access_pattern)
                
            except Exception as e:
                print(f"Warning: Failed to calculate performance degradation: {e}")


def get_fault_injection_summary(fault_config, nvsim_outputs):
    """
    Generate a summary of fault injection effects on memory characteristics.
    
    Args:
        fault_config: Fault injection configuration
        nvsim_outputs: Baseline NVSim output objects
        
    Returns:
        Dictionary containing fault injection summary
    """
    if not MSXFIController:
        return {"fault_injection_available": False}
    
    try:
        fault_controller = MSXFIController(fault_config)
        if not fault_controller.is_enabled():
            return {"fault_injection_enabled": False}
        
        summary = {
            "fault_injection_enabled": True,
            "memory_model": fault_controller.get_memory_model_info(),
            "per_memory_impact": []
        }
        
        # Analyze impact on each memory configuration
        for i, output in enumerate(nvsim_outputs):
            import numpy as np
            
            # Create test data
            test_data = np.array([
                output.read_latency,
                output.write_latency,
                output.read_energy,
                output.write_energy
            ]).reshape(2, 2)
            
            # Apply fault injection
            faulty_data = fault_controller.inject_memory_faults(test_data, seed=i)
            fault_stats = fault_controller.get_fault_statistics(test_data, faulty_data)
            
            summary["per_memory_impact"].append({
                "memory_index": i,
                "fault_statistics": fault_stats,
                "estimated_impact": {
                    "latency_increase": 1.0 + (fault_stats.get('fault_rate', 0.0) * 2.0),
                    "energy_increase": 1.0 + (fault_stats.get('fault_rate', 0.0) * 1.5),
                    "bandwidth_reduction": 1.0 / (1.0 + fault_stats.get('fault_rate', 0.0) * 0.5)
                }
            })
        
        return summary
        
    except Exception as e:
        return {
            "fault_injection_enabled": False,
            "error": str(e)
        }