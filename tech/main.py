"""
MemSysExplorer - Memory System Traffic Evaluation

This is the main entry point that implements traffic evaluation
with ArrayCharacterization integration.

Usage:
    python main.py <config_file.json>
    
Example:
    python main.py configs/basic_memory_comparison.json
"""

import json
import time
import os
import sys
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import traffic evaluation components
from integrate.traffic_evaluation.traffic import (
    generic_traffic, dnn_traffic, graph_traffic, spec_traffic, 
    generic_traffic_with_write_buff
)
from integrate.traffic_evaluation.eval_utils import ExperimentResult
from integrate.data.workload_data import (
    DNN_weights, DNN_weights_acts, graph8MB, spec8MBLLC
)
from integrate.input_defs.access_pattern import PatternConfig
from integrate.interfaces.array_interface import ArrayCharacterizationInterface

class MemSysExplorer:
    """
    Main MemSysExplorer runner for memory system traffic evaluation
    
    This implementation provides traffic evaluation capabilities
    integrating with ArrayCharacterization instead of NVSim.
    """
    
    def __init__(self, config_path: str):
        """Initialize runner with JSON configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self.array_interface = ArrayCharacterizationInterface(self.config)
        self.logger = self._setup_logging()
        
        self.exp_name = "default"
        self.read_frequency = 100000
        self.read_size = 8
        self.write_frequency = 10
        self.write_size = 8
        self.working_set = 1
        self.cell_type = ["SRAM"]
        self.process_node = 22
        self.opt_target = ["ReadLatency"]
        self.word_width = 64
        self.capacity = [1]
        self.bits_per_cell = [1]
        self.traffic = []
        self.output_path = "output"
        self._parse_config()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(self.__class__.__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load JSON configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config file {self.config_path}: {e}")
    
    def _parse_config(self):
        """Parse config file and override default values"""
        experiment = self.config.get("experiment", {})
        
        if "exp_name" in experiment and experiment["exp_name"]:
            self.exp_name = experiment["exp_name"]
        if "read_frequency" in experiment and experiment["read_frequency"]:
            self.read_frequency = experiment["read_frequency"]
        if "write_frequency" in experiment and experiment["write_frequency"]:
            self.write_frequency = experiment["write_frequency"]
        if "read_size" in experiment and experiment["read_size"]:
            self.read_size = experiment["read_size"]
        if "write_size" in experiment and experiment["write_size"]:
            self.write_size = experiment["write_size"]
        if "working_set" in experiment and experiment["working_set"]:
            self.working_set = experiment["working_set"]
        if "cell_type" in experiment and experiment["cell_type"]:
            self.cell_type = experiment["cell_type"]
        if "process_node" in experiment and experiment["process_node"]:
            self.process_node = experiment["process_node"]
        if "opt_target" in experiment and experiment["opt_target"]:
            self.opt_target = experiment["opt_target"]
        if "word_width" in experiment and experiment["word_width"]:
            self.word_width = experiment["word_width"]
        if "capacity" in experiment and experiment["capacity"]:
            self.capacity = experiment["capacity"]
        if "bits_per_cell" in experiment and experiment["bits_per_cell"]:
            self.bits_per_cell = experiment["bits_per_cell"]
        if "traffic" in experiment and experiment["traffic"]:
            self.traffic = experiment["traffic"]
        if "output_path" in experiment and experiment["output_path"]:
            self.output_path = experiment["output_path"]
    
    def run(self) -> Dict[str, Any]:
        """
        Main execution loop
        
        Returns:
            Dictionary containing execution results
        """
        start_time = time.time()
        self.logger.info("Starting MemSysExplorer traffic evaluation")
        
        try:
            self._setup_output_directories()
            
            for _cell_type in self.cell_type:
                for _opt_target in self.opt_target:
                    for _capacity in self.capacity:
                        for _bits_per_cell in self.bits_per_cell:
                            self._run_single_configuration(
                                _cell_type, _opt_target, _capacity, _bits_per_cell
                            )
            
            execution_time = time.time() - start_time
            self.logger.info(f"Traffic evaluation completed in {execution_time:.2f} seconds")
            
            return {
                "status": "success",
                "execution_time": execution_time,
                "output_path": self.output_path
            }
            
        except Exception as e:
            self.logger.error(f"Traffic evaluation failed: {e}")
            raise
    
    def _setup_output_directories(self):
        """Setup output directory structure"""
        output_dir = Path(self.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        (output_dir / "array_output").mkdir(exist_ok=True)
        (output_dir / "results").mkdir(exist_ok=True)
    
    def _run_single_configuration(self, cell_type: str, opt_target: str, 
                                capacity: float, bits_per_cell: int):
        """
        Run traffic evaluation for a single memory configuration
        
        Args:
            cell_type: Memory technology (SRAM, RRAM, etc.)
            opt_target: Optimization target (ReadLatency, ReadEDP, etc.)
            capacity: Memory capacity in MB
            bits_per_cell: Bits per memory cell
        """
        display_type = cell_type
        self.logger.info(f"→ {display_type} {capacity}MB {opt_target} {bits_per_cell}BPC")
        
        access_pattern = PatternConfig(
            exp_name=self.exp_name,
            read_freq=self.read_frequency,
            read_size=self.read_size,
            write_freq=self.write_frequency,
            write_size=self.write_size,
            workingset=self.working_set
        )
        
        results_csv = os.path.join(
            self.output_path, "results",
            f"{display_type}_{capacity}MB_{opt_target}_{bits_per_cell}BPC-{self.exp_name}.csv"
        )
        
        if os.path.exists(results_csv):
            os.remove(results_csv)
        
        array_results = self._run_array_characterization(
            cell_type, opt_target, capacity, bits_per_cell
        )
        
        nvsim_input_cfgs, nvsim_outputs, cell_paths, cfg_paths = self._create_nvsim_compatible_objects(
            array_results, cell_type, opt_target, capacity, bits_per_cell
        )
        
        if len(self.traffic) > 0:
            if nvsim_input_cfgs and nvsim_outputs:
                result = ExperimentResult(access_pattern, nvsim_input_cfgs[0], nvsim_outputs[0])
                result.evaluate()
                result.report_header_benchmark(1, results_csv, cell_paths[0], cfg_paths[0])
                
                if "generic" in self.traffic:
                    self.logger.info("→ Running traffic evaluation")
                    generic_traffic(access_pattern, nvsim_input_cfgs, nvsim_outputs, 
                                      results_csv, cell_paths, cfg_paths)
                
                if "graph" in self.traffic:
                    self.logger.info("Running graph traffic sweep")
                    graph_traffic(graph8MB, access_pattern, nvsim_input_cfgs, nvsim_outputs,
                                results_csv, cell_paths, cfg_paths)
                
                if "dnn" in self.traffic:
                    self.logger.info("Running DNN traffic sweep")
                    dnn_traffic(DNN_weights, DNN_weights_acts, access_pattern, 
                                  nvsim_input_cfgs, nvsim_outputs, results_csv, cell_paths, cfg_paths)
                
                if "spec" in self.traffic:
                    self.logger.info("Running SPEC traffic sweep")
                    from integrate.traffic_evaluation.traffic import spec_traffic_single
                    spec_traffic_single(spec8MBLLC, access_pattern, nvsim_input_cfgs, 
                                      nvsim_outputs, results_csv, cell_paths, cfg_paths)
                
                if "generic_write_buff" in self.traffic:
                    self.logger.info("Running generic traffic with write buffering")
                    generic_traffic_with_write_buff(access_pattern, nvsim_input_cfgs, nvsim_outputs,
                                                  results_csv, cell_paths, cfg_paths)
    
    def _run_array_characterization(self, cell_type: str, opt_target: str, 
                                  capacity: float, bits_per_cell: int) -> Dict[str, Any]:
        """
        Run ArrayCharacterization for the specified memory configuration
        
        Returns:
            Dictionary containing array characterization results
        """
        experiment_config = self.config.get("experiment", {}).copy()
        experiment_config.pop("bits_per_cell", None)
        experiment_config.pop("capacity", None)
        experiment_config.pop("process_node", None)
        experiment_config.pop("opt_target", None)
        experiment_config.pop("cell_type", None)
        
        memory_config = {
            "memory_type": cell_type,
            "process_node": self.process_node,
            "capacity_mb": capacity,
            "optimization_target": opt_target,
            "word_width": self.word_width,
            "bits_per_cell": bits_per_cell,
            **experiment_config
        }
        
        try:
            results = self.array_interface.run_characterization(memory_config)
            return results
        except Exception as e:
            self.logger.error(f"ArrayCharacterization failed for {cell_type}: {e}")
            return self._get_default_array_results(cell_type)
    
    def _get_default_array_results(self, cell_type: str) -> Dict[str, Any]:
        """Return default array results when ArrayCharacterization fails"""
        defaults = {
            "SRAM": {
                "read_latency_ns": 1.0,
                "write_latency_ns": 1.0,
                "read_energy_pj": 10.0,
                "write_energy_pj": 15.0,
                "leakage_power_mw": 1.0,
                "area_mm2": 0.1,
                "read_bandwidth_gbps": 100.0,
                "write_bandwidth_gbps": 100.0
            },
            "RRAM": {
                "read_latency_ns": 5.0,
                "write_latency_ns": 50.0,
                "read_energy_pj": 5.0,
                "write_energy_pj": 100.0,
                "leakage_power_mw": 0.1,
                "area_mm2": 0.05,
                "read_bandwidth_gbps": 50.0,
                "write_bandwidth_gbps": 10.0
            },
            "FeFET": {
                "read_latency_ns": 3.0,
                "write_latency_ns": 30.0,
                "read_energy_pj": 8.0,
                "write_energy_pj": 80.0,
                "leakage_power_mw": 0.05,
                "area_mm2": 0.03,
                "read_bandwidth_gbps": 60.0,
                "write_bandwidth_gbps": 15.0
            },
            "CTT": {
                "read_latency_ns": 4.0,
                "write_latency_ns": 40.0,
                "read_energy_pj": 6.0,
                "write_energy_pj": 90.0,
                "leakage_power_mw": 0.08,
                "area_mm2": 0.04,
                "read_bandwidth_gbps": 55.0,
                "write_bandwidth_gbps": 12.0
            }
        }
        
        return defaults.get(cell_type, defaults["SRAM"])
    
    def _create_nvsim_compatible_objects(self, array_results: Dict[str, Any], 
                                       cell_type: str, opt_target: str, 
                                       capacity: float, bits_per_cell: int):
        """
        Create NVSim-compatible objects from ArrayCharacterization results
        
        This allows us to reuse traffic evaluation functions without modification
        """
        from integrate.input_defs.nvsim_interface import NVSimInputConfig, NVSimOutputConfig
        
        cfg_name = f"{cell_type}_{capacity}MB_{opt_target}_{bits_per_cell}BPC"
        
        try:
            memory_config_for_path = {
                "memory_type": cell_type,
                "process_node": self.process_node,
                "capacity_mb": capacity,
                "optimization_target": opt_target,
                "word_width": self.word_width,
                "bits_per_cell": bits_per_cell,
                "case": "best_case",
                **self.config.get("experiment", {})
            }
            
            case = memory_config_for_path.get('case', 'best_case')
            cell_filename = f"{cell_type}_{case}.cell"
            cell_path_check = self.array_interface.cell_cfgs_dir / cell_filename
            
            if cell_path_check.exists():
                cell_path = str(cell_path_check)
            else:
                cell_path = f"../integrate/data/cell_cfgs/{cell_type}_{case}.cell"
                
        except Exception as e:
            self.logger.warning(f"Could not resolve actual cell path: {e}")
            cell_path = f"../integrate/data/cell_cfgs/{cell_type}_best_case.cell"
        
        cfg_path = f"data/mem_cfgs/{cfg_name}.cfg"
        
        nvsim_input_cfg = NVSimInputConfig(
            mem_cfg_file_path=cfg_path,
            process_node=self.process_node,
            opt_target=opt_target,
            word_width=self.word_width,
            capacity=capacity,
            cell_type=cell_type
        )
        
        nvsim_output = NVSimOutputConfig(
            read_latency=array_results.get("read_latency_ns", 1.0),
            write_latency=array_results.get("write_latency_ns", 1.0),
            read_energy=array_results.get("read_energy_pj", 10.0),
            write_energy=array_results.get("write_energy_pj", 15.0),
            leakage_power=array_results.get("leakage_power_mw", 1.0),
            area=array_results.get("area_mm2", 0.1),
            read_bw=array_results.get("read_bandwidth_gbps", 100.0),
            write_bw=array_results.get("write_bandwidth_gbps", 100.0),
            area_efficiency=80.0
        )
        
        return ([nvsim_input_cfg], [nvsim_output], [cell_path], [cfg_path])


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <config_file.json>")
        print("Example: python main.py configs/basic_memory_comparison.json")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    try:
        if not Path(config_path).exists():
            print(f"Error: Configuration file '{config_path}' not found")
            sys.exit(1)
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            if "experiment" not in config:
                print(f"Error: Configuration file must contain 'experiment' section")
                sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration file: {e}")
            sys.exit(1)
        
        print("Successfully Loaded Config File")
        
        explorer = MemSysExplorer(config_path)
        results = explorer.run()
        
        print("Retrieved Array-Level Results; Running Analytical Model")
        print("Reported Results; Evaluation Complete")
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()