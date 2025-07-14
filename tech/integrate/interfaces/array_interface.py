"""
Array Characterization Interface

This interface provides real connection to ArrayCharacterization/NVSim
executable with tentpole mode and dynamic configuration generation.
"""

from typing import Dict, Any, Optional
import logging
import subprocess
import tempfile
import os
import time
import sys
from pathlib import Path
import shutil

# Add module paths for imports
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

# Import modules
# from tentpoles import form_tentpoles  # Temporarily disabled due to pandas dependency
from input_defs.nvsim_interface import NVSimInputConfig

# Import fault injection controller
try:
    from .msxfi_controller import MSXFIController
except ImportError:
    MSXFIController = None

class ArrayCharacterizationInterface:
    """
    Real interface to ArrayCharacterization/NVSim executable
    
    This interface generates proper configuration files and calls the actual
    ArrayCharacterization (NVSim) executable to get real results.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup paths
        current_dir = Path(__file__).parent.parent.parent
        self.array_char_dir = current_dir / "ArrayCharacterization"
        self.executable_path = self.array_char_dir / "nvsim"
        
        # Setup data and configuration paths  
        self.integrate_dir = current_dir / "integrate"
        self.data_dir = self.integrate_dir / "data"
        self.mem_cfgs_dir = self.data_dir / "mem_cfgs"
        self.cell_cfgs_dir = self.data_dir / "cell_cfgs"
        
        # Ensure directories exist
        self.mem_cfgs_dir.mkdir(parents=True, exist_ok=True)
        self.cell_cfgs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize fault injection controller if available and configured
        self.fault_controller = None
        if config and MSXFIController:
            fault_config = config.get('fault_injection', {})
            if fault_config.get('enabled', False):
                try:
                    self.fault_controller = MSXFIController(config)
                    self.logger.info("Fault injection controller initialized")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize fault injection: {e}")
        
        # Validate executable exists
        if not self.executable_path.exists():
            self.logger.error(f"NVSim executable not found at {self.executable_path}")
            raise FileNotFoundError(f"NVSim executable not found at {self.executable_path}")
    
    def run_characterization(self, memory_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run array characterization using real NVSim executable
        
        Args:
            memory_config: Memory configuration parameters
            
        Returns:
            Dictionary containing array characteristics
        """
        memory_type = memory_config.get('memory_type', 'SRAM')
        process_node = memory_config.get('process_node', 22)
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        opt_target = memory_config.get('optimization_target', 'ReadLatency')
        
        # Ensure case is set following NVMExplorer logic
        if 'case' not in memory_config:
            memory_config = memory_config.copy()
            # Default to best_case for tentpole mode unless custom_cells are specified
            if memory_config.get('custom_cells') is None:
                memory_config['case'] = 'best_case'
            else:
                memory_config['case'] = 'custom'
        
        case = memory_config.get('case', 'best_case')
        self.logger.info(f"Characterizing {memory_type} {capacity_mb}MB {opt_target} ({case})")
        
        try:
            # Generate configuration files using simplified logic
            cell_file = self._find_cell_file(memory_config)
            config_file = self._get_or_generate_config_file(memory_config)
            
            # Run NVSim executable
            results = self._run_nvsim(config_file, cell_file)
            
            # Parse results
            parsed_results = self._parse_nvsim_output(results, memory_type)
            
            # Add cell parameters
            cell_params = self._extract_cell_parameters(cell_file)
            parsed_results.update(cell_params)
            
            self.logger.info(f"✓ Read={parsed_results['read_latency_ns']:.1f}ns, Write={parsed_results['write_latency_ns']:.1f}ns")
            
            return parsed_results
            
        except Exception as e:
            self.logger.error(f"NVSim characterization failed for {memory_type}: {e}")
            # Fallback to default values
            return self._get_default_characteristics(memory_type, process_node, capacity_mb)
    
    def run_tentpole_characterization(self, memory_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run tentpole-style characterization generating both best_case and worst_case results
        
        This follows the NVMExplorer approach of generating best and worst case scenarios
        for each memory technology configuration.
        
        Args:
            memory_config: Memory configuration parameters
            
        Returns:
            Dictionary containing both best_case and worst_case results
        """
        memory_type = memory_config.get('memory_type', 'SRAM')
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        opt_target = memory_config.get('optimization_target', 'ReadLatency')
        bits_per_cell = memory_config.get('bits_per_cell', 1)
        
        self.logger.info(f"Running tentpole characterization for {memory_type}")
        
        results = {}
        
        for case in ['best_case', 'worst_case']:
            try:
                # Create case-specific config
                case_config = memory_config.copy()
                case_config['case'] = case
                
                # Run characterization for this case
                case_results = self.run_characterization(case_config)
                results[case] = case_results
                
                self.logger.info(f"{case} characterization complete for {memory_type}")
                
            except Exception as e:
                self.logger.error(f"{case} characterization failed for {memory_type}: {e}")
                # Use default values for failed case
                results[case] = self._get_default_characteristics(memory_type, 
                                                                memory_config.get('process_node', 22), 
                                                                capacity_mb)
        
        return results
    
    def run_fault_aware_characterization(self, memory_config: Dict[str, Any], seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Run fault-aware array characterization with optional fault injection.
        
        Args:
            memory_config: Memory configuration parameters
            seed: Random seed for reproducible fault injection
            
        Returns:
            Dictionary containing both baseline and faulty characteristics
        """
        # Get baseline characteristics
        baseline_results = self.run_characterization(memory_config)
        
        # If fault injection is not enabled, return baseline only
        if not self.fault_controller or not self.fault_controller.is_enabled():
            return {
                'baseline': baseline_results,
                'fault_injection_enabled': False
            }
        
        # Apply fault injection to memory characteristics
        try:
            # Create a synthetic memory array for fault injection testing
            import numpy as np
            memory_size = int(memory_config.get('capacity_mb', 1.0) * 1024 * 1024 / 8)  # in bytes
            test_array = np.random.randn(min(memory_size // 4, 1000), 4).astype(np.float32)  # Limit size for testing
            
            # Inject faults
            faulty_array = self.fault_controller.inject_memory_faults(test_array, seed)
            
            # Calculate fault statistics
            fault_stats = self.fault_controller.get_fault_statistics(test_array, faulty_array)
            
            # Estimate impact on memory characteristics
            fault_impact = self._estimate_fault_impact(baseline_results, fault_stats)
            
            # Create faulty characteristics
            faulty_results = baseline_results.copy()
            for metric, impact in fault_impact.items():
                if metric in faulty_results:
                    faulty_results[metric] *= impact
            
            self.logger.info(f"Fault injection applied: {fault_stats['fault_rate']:.4f} fault rate")
            
            return {
                'baseline': baseline_results,
                'faulty': faulty_results,
                'fault_statistics': fault_stats,
                'fault_impact': fault_impact,
                'fault_injection_enabled': True,
                'memory_model': self.fault_controller.get_memory_model_info()
            }
            
        except Exception as e:
            self.logger.error(f"Fault-aware characterization failed: {e}")
            return {
                'baseline': baseline_results,
                'fault_injection_enabled': False,
                'error': str(e)
            }
    
    def _estimate_fault_impact(self, baseline_results: Dict[str, Any], fault_stats: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate the impact of faults on memory characteristics.
        
        Args:
            baseline_results: Baseline memory characteristics
            fault_stats: Fault injection statistics
            
        Returns:
            Dictionary of impact factors (multipliers) for each characteristic
        """
        fault_rate = fault_stats.get('fault_rate', 0.0)
        
        if fault_rate == 0.0:
            return {key: 1.0 for key in baseline_results.keys()}
        
        # Empirical model for fault impact (can be refined with real data)
        latency_degradation = 1.0 + (fault_rate * 2.0)  # Faults can cause retries
        energy_increase = 1.0 + (fault_rate * 1.5)      # Additional energy for error handling
        bandwidth_reduction = 1.0 / (1.0 + fault_rate * 0.5)  # Reduced effective bandwidth
        
        impact_factors = {}
        for key in baseline_results.keys():
            if 'latency' in key.lower():
                impact_factors[key] = latency_degradation
            elif 'energy' in key.lower() or 'power' in key.lower():
                impact_factors[key] = energy_increase
            elif 'bandwidth' in key.lower():
                impact_factors[key] = bandwidth_reduction
            else:
                impact_factors[key] = 1.0  # No impact on other metrics
        
        return impact_factors
    
    def _get_default_characteristics(self, memory_type: str, process_node: int, 
                                   capacity_mb: float) -> Dict[str, Any]:
        """
        Get default characteristics for memory type
        
        Args:
            memory_type: Type of memory (SRAM, RRAM, etc.)
            process_node: Process node in nanometers
            capacity_mb: Capacity in megabytes
            
        Returns:
            Dictionary with memory characteristics
        """
        # Base characteristics by memory type
        base_characteristics = {
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
            },
            "eDRAM1T": {
                "read_latency_ns": 2.5,
                "write_latency_ns": 2.5,
                "read_energy_pj": 15.0,
                "write_energy_pj": 20.0,
                "leakage_power_mw": 5.0,
                "area_mm2": 0.02,
                "read_bandwidth_gbps": 80.0,
                "write_bandwidth_gbps": 80.0
            },
            "eDRAM3T": {
                "read_latency_ns": 1.8,
                "write_latency_ns": 2.0,
                "read_energy_pj": 12.0,
                "write_energy_pj": 18.0,
                "leakage_power_mw": 8.0,
                "area_mm2": 0.03,
                "read_bandwidth_gbps": 90.0,
                "write_bandwidth_gbps": 85.0
            },
            "eDRAM3T_333": {
                "read_latency_ns": 1.5,
                "write_latency_ns": 1.8,
                "read_energy_pj": 10.0,
                "write_energy_pj": 15.0,
                "leakage_power_mw": 10.0,
                "area_mm2": 0.025,
                "read_bandwidth_gbps": 100.0,
                "write_bandwidth_gbps": 90.0
            }
        }
        
        # Get base characteristics
        if memory_type not in base_characteristics:
            self.logger.warning(f"Unknown memory type {memory_type}, using SRAM defaults")
            memory_type = "SRAM"
        
        characteristics = base_characteristics[memory_type].copy()
        
        process_scaling = (22.0 / process_node) ** 2
        
        characteristics["read_energy_pj"] *= process_scaling
        characteristics["write_energy_pj"] *= process_scaling
        characteristics["area_mm2"] *= process_scaling
        characteristics["leakage_power_mw"] *= process_scaling
        
        capacity_scaling = capacity_mb / 1.0
        
        characteristics["area_mm2"] *= capacity_scaling
        characteristics["leakage_power_mw"] *= capacity_scaling
        
        return characteristics
    
    def _generate_config_files(self, memory_config: Dict[str, Any]) -> tuple[str, str]:
        """
        Generate NVSim configuration files based on memory configuration
        
        Args:
            memory_config: Memory configuration parameters
            
        Returns:
            Tuple of (cell_file_path, config_file_path)
        """
        memory_type = memory_config.get('memory_type', 'SRAM')
        process_node = memory_config.get('process_node', 22)
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        opt_target = memory_config.get('optimization_target', 'ReadLatency')
        bits_per_cell = memory_config.get('bits_per_cell', 1)
        case = memory_config.get('case', 'best_case')
        
        # Check if we have a unified memory config file
        unified_config = self._find_memory_config_file(memory_type, process_node, 
                                                      capacity_mb, opt_target, 
                                                      bits_per_cell, case)
        
        if unified_config:
            # Read the unified config to get the cell file path
            with open(unified_config, 'r') as f:
                for line in f:
                    if line.strip().startswith('-MemoryCellInputFile:'):
                        cell_file_ref = line.split(':', 1)[1].strip()
                        # Convert relative path to absolute
                        if cell_file_ref.startswith('../integrate/data/cell_cfgs/'):
                            # Remove the ../ prefix and construct absolute path
                            cell_file_name = cell_file_ref.split('/')[-1]
                            cell_file = str(self.integrate_dir / 'cell_cfgs' / cell_file_name)
                        elif cell_file_ref.startswith('integrate/data/cell_cfgs/'):
                            cell_file = str(self.integrate_dir.parent / cell_file_ref)
                        else:
                            cell_file = cell_file_ref
                        break
                else:
                    # Fallback if no cell file found in config
                    cell_file = self._find_cell_file(memory_type, process_node)
            
            # Update capacity and optimization target in the unified config
            config_file = self._update_unified_config(unified_config, memory_config)
        else:
            # Find appropriate cell file
            cell_file = self._find_cell_file(memory_type, process_node)
            
            # Generate configuration file using full configuration
            config_file = self._generate_memory_config(memory_config, cell_file)
        
        return cell_file, config_file
    
    def _find_cell_file(self, memory_config: Dict[str, Any]) -> str:
        """
        Find appropriate cell file for memory type following NVMExplorer tentpole logic
        
        Args:
            memory_config: Memory configuration parameters
            
        Returns:
            Path to cell file
        """
        memory_type = memory_config.get('memory_type', 'SRAM')
        case = memory_config.get('case', 'best_case')
        
        self.logger.debug(f"Looking for cell file: {memory_type}, case: {case}")
        
        cell_filename = f"{memory_type}_{case}.cell"
        cell_path = self.cell_cfgs_dir / cell_filename
        
        if cell_path.exists():
            self.logger.debug(f"Using tentpole cell file: {cell_path}")
            return str(cell_path)
            
        cell_filename = f"{memory_type}.cell"
        cell_path = self.cell_cfgs_dir / cell_filename
        
        if cell_path.exists():
            self.logger.debug(f"Using generic cell file: {cell_path}")
            return str(cell_path)
        
        # Handle memory type mappings
        memory_type_mappings = {
            "STTRAM": "MRAM",
            "eDRAM1T": "eDRAM", 
            "EDRAM1T": "eDRAM",
            "eDRAM3T": "eDRAM3T",
            "EDRAM3T": "eDRAM3T",
            "eDRAM3T_333": "eDRAM3T333",
            "EDRAM3T_333": "eDRAM3T333"
        }
        
        if memory_type in memory_type_mappings:
            mapped_type = memory_type_mappings[memory_type]
            
            # Try mapped type with case
            cell_filename = f"{mapped_type}_{case}.cell"
            cell_path = self.cell_cfgs_dir / cell_filename
            
            if cell_path.exists():
                self.logger.debug(f"Using mapped tentpole cell file: {cell_path}")
                return str(cell_path)
                
            # Try mapped type without case
            cell_filename = f"{mapped_type}.cell"
            cell_path = self.cell_cfgs_dir / cell_filename
            
            if cell_path.exists():
                self.logger.debug(f"Using mapped generic cell file: {cell_path}")
                return str(cell_path)
        
        # If no tentpole files found, this is an error since tentpoles should auto-generate
        raise FileNotFoundError(
            f"No tentpole cell file found for {memory_type}_{case}. "
            f"Expected file: {self.cell_cfgs_dir / cell_filename}. "
            f"Tentpole files should be auto-generated."
        )
    
    def _get_or_generate_config_file(self, memory_config: Dict[str, Any]) -> str:
        """
        Get existing config file or generate a new one following NVMExplorer logic
        
        Args:
            memory_config: Memory configuration parameters
            
        Returns:
            Path to memory config file
        """
        memory_type = memory_config.get('memory_type', 'SRAM')
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        opt_target = memory_config.get('optimization_target', 'ReadLatency')
        bits_per_cell = memory_config.get('bits_per_cell', 1)
        case = memory_config.get('case', 'best_case')
        
        if isinstance(bits_per_cell, list):
            bits_per_cell = bits_per_cell[0] if bits_per_cell else 1
        
        config_filename = f"{memory_type}_{capacity_mb:.0f}MB_{opt_target}_{bits_per_cell}BPC-{case}.cfg"
        config_path = self.mem_cfgs_dir / config_filename
        
        if config_path.exists():
            self.logger.debug(f"Found existing config: {config_path}")
            return str(config_path)
        
        self.logger.debug(f"Generating new config: {config_path}")
        
        # Find cell file first
        cell_path = self._find_cell_file(memory_config)
        
        # Generate config content using NVSimInputConfig
        config_content = self._generate_config_content(memory_config, cell_path)
        
        # Write config file
        with open(config_path, 'w') as f:
            f.write(config_content)
            
        return str(config_path)
    
    def _generate_config_content(self, memory_config: Dict[str, Any], cell_path: str) -> str:
        """
        Generate memory configuration content using NVMExplorer logic
        """
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        capacity_kb = int(capacity_mb * 1024)
        memory_type = memory_config.get('memory_type', 'SRAM')
        
        # Helper function to extract scalar values from lists
        def get_scalar_value(config, key, default):
            value = config.get(key, default)
            if isinstance(value, list):
                return value[0] if value else default
            return value
        
        # Convert absolute cell path to relative path for config file
        if cell_path.startswith(str(self.cell_cfgs_dir)):
            # Convert absolute path to relative path from ArrayCharacterization directory
            # The path should be relative to ArrayCharacterization directory
            cell_relative_path = f"../integrate/data/cell_cfgs/{Path(cell_path).name}"
        else:
            # Already a relative path or fallback path
            cell_relative_path = cell_path
        
        # Get scalar values for configuration parameters
        process_node = get_scalar_value(memory_config, 'process_node', 22)
        word_width = get_scalar_value(memory_config, 'word_width', 64)
        opt_target = get_scalar_value(memory_config, 'optimization_target', 'ReadLatency')
        
        # Build config content following NVMExplorer format
        config_lines = [
            f"-MemoryCellInputFile: {cell_relative_path}",
            "",
            f"-ProcessNode: {process_node}",
            f"-DeviceRoadmap: LOP"
        ]
        
        # Add special process node configurations for eDRAM3T variants
        if memory_type == "eDRAM3T":
            # For standard eDRAM3T, use same process node for all transistors unless explicitly specified
            process_node_r = get_scalar_value(memory_config, 'process_node_r', process_node)
            process_node_w = get_scalar_value(memory_config, 'process_node_w', process_node)
            device_roadmap_r = get_scalar_value(memory_config, 'device_roadmap_r', 'LOP')
            device_roadmap_w = get_scalar_value(memory_config, 'device_roadmap_w', 'LOP')
            
            config_lines.extend([
                "",
                f"-ProcessNodeR: {process_node_r}",
                f"-DeviceRoadmapR: {device_roadmap_r}",
                "",
                f"-ProcessNodeW: {process_node_w}",
                f"-DeviceRoadmapW: {device_roadmap_w}"
            ])
        elif memory_type == "eDRAM3T_333":
            # For eDRAM3T_333, use specific default values for different transistors
            process_node_r = get_scalar_value(memory_config, 'process_node_r', 22)
            process_node_w = get_scalar_value(memory_config, 'process_node_w', 45)
            device_roadmap_r = get_scalar_value(memory_config, 'device_roadmap_r', 'CNT')
            device_roadmap_w = get_scalar_value(memory_config, 'device_roadmap_w', 'IGZO')
            
            config_lines.extend([
                "",
                f"-ProcessNodeR: {process_node_r}",
                f"-DeviceRoadmapR: {device_roadmap_r}", 
                "",
                f"-ProcessNodeW: {process_node_w}",
                f"-DeviceRoadmapW: {device_roadmap_w}"
            ])
        
        # Add common configuration parameters
        config_lines.extend([
            "",
            f"-DesignTarget: cache",
            "",
            f"-CacheAccessMode: Normal",
            f"-Associativity (for cache only): 8",
            "",
            f"-OptimizationTarget: {opt_target}",
            "",
            f"-OutputFilePrefix: nvsim",
            f"-EnablePruning: Yes",
            "",
            f"-Capacity (KB): {capacity_kb}",
            f"-WordWidth (bit): {word_width}",
            "",
            f"-LocalWireType: LocalAggressive",
            f"-LocalWireRepeaterType: RepeatedNone",
            "",
            f"-LocalWireUseLowSwing: No",
            "",
            f"-GlobalWireType: GlobalAggressive",
            f"-GlobalWireRepeaterType: RepeatedNone",
            f"-GlobalWireUseLowSwing: No",
            "",
            f"-Routing: H-tree",
            "",
            f"-InternalSensing: true",
            "",
            f"-Temperature (K): 370",
            "",
            f"-BufferDesignOptimization: latency",
            ""
        ])
        
        return "\n".join(config_lines) + "\n"
    
    def _update_unified_config(self, unified_config_path: str, memory_config: Dict[str, Any]) -> str:
        """
        Update unified config with specific parameters from memory_config
        
        Args:
            unified_config_path: Path to unified config file
            memory_config: Memory configuration parameters
            
        Returns:
            Path to updated config file
        """
        # Read the unified config
        with open(unified_config_path, 'r') as f:
            lines = f.readlines()
        
        # Update specific parameters
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        # Handle case where capacity_mb might be a list
        if isinstance(capacity_mb, list):
            capacity_mb = capacity_mb[0] if capacity_mb else 1.0
        capacity_kb = int(capacity_mb * 1024)
        opt_target = memory_config.get('optimization_target', 'ReadLatency')
        word_width = memory_config.get('word_width', 64)
        
        updated_lines = []
        for line in lines:
            if line.strip().startswith('-Capacity (KB):'):
                updated_lines.append(f'-Capacity (KB): {capacity_kb}\n')
            elif line.strip().startswith('-OptimizationTarget:'):
                updated_lines.append(f'-OptimizationTarget: {opt_target}\n')
            elif line.strip().startswith('-WordWidth (bit):'):
                updated_lines.append(f'-WordWidth (bit): {word_width}\n')
            elif line.strip().startswith('-ProcessNode:'):
                # Update process node if specified
                if 'process_node' in memory_config:
                    updated_lines.append(f'-ProcessNode: {memory_config["process_node"]}\n')
                else:
                    updated_lines.append(line)
            elif line.strip().startswith('-MemoryCellInputFile:'):
                # Fix cell file path to be absolute
                cell_file_ref = line.split(':', 1)[1].strip()
                if cell_file_ref.startswith('../integrate/data/cell_cfgs/'):
                    # Convert to absolute path
                    cell_file_absolute = str(self.integrate_dir / 'cell_cfgs' / cell_file_ref.split('/')[-1])
                    updated_lines.append(f'-MemoryCellInputFile: {cell_file_absolute}\n')
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as tmp_file:
            tmp_file.writelines(updated_lines)
            temp_config_path = tmp_file.name
        
        return temp_config_path
    
    def _generate_memory_config(self, memory_config: Dict[str, Any], cell_file: str) -> str:
        """
        Generate memory configuration file from JSON configuration
        
        Args:
            memory_config: Complete memory configuration from JSON
            cell_file: Path to cell file
            
        Returns:
            Path to generated config file
        """
        # Extract configuration parameters with defaults
        process_node = memory_config.get('process_node', 22)
        opt_target = memory_config.get('optimization_target', 'ReadLatency')
        word_width = memory_config.get('word_width', 64)
        capacity_mb = memory_config.get('capacity_mb', 1.0)
        
        # Extract all possible NVSim configuration parameters from JSON
        design_target = memory_config.get('design_target', 'RAM')
        device_roadmap = memory_config.get('device_roadmap', 'LOP')
        local_wire_type = memory_config.get('local_wire_type', 'LocalAggressive')
        local_wire_repeater_type = memory_config.get('local_wire_repeater_type', 'RepeatedNone')
        local_wire_use_low_swing = memory_config.get('local_wire_use_low_swing', 'No')
        global_wire_type = memory_config.get('global_wire_type', 'GlobalAggressive')
        global_wire_repeater_type = memory_config.get('global_wire_repeater_type', 'RepeatedNone')
        global_wire_use_low_swing = memory_config.get('global_wire_use_low_swing', 'No')
        routing = memory_config.get('routing', 'H-tree')
        internal_sensing = memory_config.get('internal_sensing', 'true')
        temperature = memory_config.get('temperature', 350)
        buffer_design_optimization = memory_config.get('buffer_design_optimization', 'balanced')
        
        # Convert MB to KB for NVSim
        # Handle case where capacity_mb might be a list
        if isinstance(capacity_mb, list):
            capacity_mb = capacity_mb[0] if capacity_mb else 1.0
        capacity_kb = int(capacity_mb * 1024)
        
        # Check if this is eDRAM3T_333 which requires special ProcessNodeR/W format
        memory_type = memory_config.get('memory_type', 'SRAM')
        
        # Create temporary config file with proper NVSim format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            config_content = f"-MemoryCellInputFile: {cell_file}\n\n"
            
            # Handle eDRAM3T_333 special format
            if memory_type == "eDRAM3T_333":
                # Use separate read/write process nodes and roadmaps
                process_node_r = memory_config.get('process_node_r', 22)
                device_roadmap_r = memory_config.get('device_roadmap_r', 'CNT')
                process_node_w = memory_config.get('process_node_w', 45)
                device_roadmap_w = memory_config.get('device_roadmap_w', 'IGZO')
                
                config_content += f"""-ProcessNode: {process_node}
-DeviceRoadmap: {device_roadmap}

-ProcessNodeR: {process_node_r}
-DeviceRoadmapR: {device_roadmap_r}

-ProcessNodeW: {process_node_w}
-DeviceRoadmapW: {device_roadmap_w}

"""
            else:
                # Standard format for all other memory types
                config_content += f"""-ProcessNode: {process_node}
-DeviceRoadmap: {device_roadmap}

"""
            
            # Add common configuration parameters
            config_content += f"""-DesignTarget: cache

-CacheAccessMode: Normal
-Associativity (for cache only): 8

-OptimizationTarget: {opt_target}

-OutputFilePrefix: test
-EnablePruning: Yes

-Capacity (KB): {capacity_kb}
-WordWidth (bit): {word_width}

-LocalWireType: {local_wire_type}
-LocalWireRepeaterType: {local_wire_repeater_type}

-LocalWireUseLowSwing: {local_wire_use_low_swing}

-GlobalWireType: {global_wire_type}
-GlobalWireRepeaterType: {global_wire_repeater_type}
-GlobalWireUseLowSwing: {global_wire_use_low_swing}

-Routing: {routing}

-InternalSensing: {internal_sensing}

-Temperature (K): {temperature}
"""
            
            # Add retention time for DRAM types
            if "eDRAM" in memory_type or "DRAM" in memory_type:
                retention_time = memory_config.get('retention_time_us', 40)
                config_content += f"-RetentionTime (us): {retention_time}\n"
            
            config_content += f"""
-BufferDesignOptimization: {buffer_design_optimization}

"""
            f.write(config_content)
            config_path = f.name
        
        return config_path
    
    def _run_nvsim(self, config_file: str, cell_file: str) -> str:
        """
        Run NVSim executable with configuration
        
        Args:
            config_file: Path to configuration file
            cell_file: Path to cell file
            
        Returns:
            NVSim output string
        """
        try:
            # Change to ArrayCharacterization directory
            original_cwd = os.getcwd()
            os.chdir(self.array_char_dir)
            
            # Run NVSim executable
            cmd = [str(self.executable_path), config_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Restore original directory
            os.chdir(original_cwd)
            
            if result.returncode != 0:
                # NVSim often puts error messages in stdout, not stderr
                error_output = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
                # Extract key error information from the output
                error_lines = []
                if error_output:
                    for line in error_output.split('\n'):
                        if 'Error:' in line or 'error:' in line or 'ERROR:' in line:
                            error_lines.append(line.strip())
                
                if error_lines:
                    error_msg = '; '.join(error_lines)
                else:
                    error_msg = error_output[-500:] if len(error_output) > 500 else error_output
                
                raise RuntimeError(f"NVSim execution failed: {error_msg}")
            
            # Save NVSim output to logs directory
            self._save_nvsim_output(result.stdout, result.stderr, config_file, cell_file)
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            raise RuntimeError("NVSim execution timed out")
        except Exception as e:
            os.chdir(original_cwd)
            raise RuntimeError(f"NVSim execution error: {e}")
    
    def _save_nvsim_output(self, stdout: str, stderr: str, config_file: str, cell_file: str):
        """
        Save NVSim output and error logs to files
        
        Args:
            stdout: NVSim standard output
            stderr: NVSim standard error 
            config_file: Path to configuration file used
            cell_file: Path to cell file used
        """
        try:
            # Create output directories (only use array_output, not logs)
            array_output_dir = Path("output/array_output")
            array_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract clean cell name from file path
            cell_name = Path(cell_file).stem if cell_file else "unknown_cell"
            # Remove 'sample_' prefix if present to clean up filename
            if cell_name.startswith('sample_'):
                cell_name = cell_name[7:]  # Remove 'sample_' prefix
            
            # Use simpler timestamp (just hour and minute)
            timestamp = time.strftime("%H%M")
            
            # Save NVSim output to array_output directory only (no duplication)
            array_output_file = array_output_dir / f"nvsim_{cell_name}_{timestamp}.out"
            with open(array_output_file, 'w') as f:
                f.write(f"NVSim Array Characterization Results\n")
                f.write(f"===================================\n")
                f.write(f"Cell: {cell_name}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Cell file: {cell_file}\n")
                f.write(f"Config file: {config_file}\n")
                f.write(f"\nArray Characteristics:\n")
                f.write("=" * 30 + "\n")
                f.write(stdout)
            
            # Save stderr only if there's content (in logs directory for debugging)
            if stderr.strip():
                logs_dir = Path("output/logs")
                logs_dir.mkdir(parents=True, exist_ok=True)
                stderr_file = logs_dir / f"nvsim_{cell_name}_{timestamp}_error.log"
                with open(stderr_file, 'w') as f:
                    f.write(f"NVSim Error Log\n")
                    f.write(f"===============\n")
                    f.write(f"Cell file: {cell_file}\n")
                    f.write(f"Config file: {config_file}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Command: {self.executable_path} {config_file}\n")
                    f.write(f"\nSTDERR:\n")
                    f.write("=" * 50 + "\n")
                    f.write(stderr)
                self.logger.debug(f"NVSim output saved to {array_output_file}, error log saved to {stderr_file}")
            else:
                self.logger.debug(f"NVSim output saved to {array_output_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save NVSim output: {e}")
    
    def _parse_nvsim_output(self, output: str, memory_type: str) -> Dict[str, Any]:
        """
        Parse NVSim output to extract key metrics with proper unit conversions
        
        Parse NVSim output to extract key metrics with proper unit conversions
        
        Args:
            output: NVSim output string
            memory_type: Type of memory
            
        Returns:
            Dictionary with parsed results
        """
        results = {
            'read_latency_ns': -1.0,
            'write_latency_ns': -1.0,
            'read_energy_pj': -1.0,
            'write_energy_pj': -1.0,
            'leakage_power_mw': -1.0,
            'area_mm2': -1.0,
            'read_bandwidth_gbps': -1.0,
            'write_bandwidth_gbps': -1.0,
            'area_efficiency': -1.0
        }
        
        lines = output.split('\n')
        in_data_array_section = False
        
        for line in lines:
            line = line.strip()
            
            if 'CACHE DATA ARRAY' in line:
                in_data_array_section = True
            elif 'CACHE TAG ARRAY' in line:
                in_data_array_section = False
            
            # Area parsing
            if '- Total Area =' in line and results['area_mm2'] == -1.0:
                try:
                    if 'mm^2' in line:
                        area_str = line.split('=')[1].strip().replace('mm^2', '')
                        results['area_mm2'] = float(area_str)
                    elif 'um^2' in line and '=' in line:
                        parts = line.split('=')
                        if len(parts) >= 3:
                            area_part = parts[-1].strip()
                            if 'um^2' in area_part:
                                area_str = area_part.replace('um^2', '').strip()
                                results['area_mm2'] = float(area_str) / (1000.**2)
                except (ValueError, IndexError):
                    pass
            
            elif '-  Read Latency' in line and in_data_array_section and results['read_latency_ns'] == -1.0:
                try:
                    if '=' in line:
                        latency_part = line.split('=')[1].strip()
                        if 'ns' in latency_part:
                            results['read_latency_ns'] = float(latency_part.replace('ns', ''))
                        elif 'us' in latency_part:
                            results['read_latency_ns'] = float(latency_part.replace('us', '')) * 1000.
                        elif 'ps' in latency_part:
                            results['read_latency_ns'] = float(latency_part.replace('ps', '')) / 1000.
                        elif 'ms' in latency_part:
                            results['read_latency_ns'] = float(latency_part.replace('ms', '')) * 1000000.
                except (ValueError, IndexError):
                    pass
            
            elif '- Write Latency' in line and in_data_array_section and results['write_latency_ns'] == -1.0:
                try:
                    if '=' in line:
                        latency_part = line.split('=')[1].strip()
                        if 'ns' in latency_part:
                            results['write_latency_ns'] = float(latency_part.replace('ns', ''))
                        elif 'us' in latency_part:
                            results['write_latency_ns'] = float(latency_part.replace('us', '')) * 1000.
                        elif 'ps' in latency_part:
                            results['write_latency_ns'] = float(latency_part.replace('ps', '')) / 1000.
                        elif 'ms' in latency_part:
                            results['write_latency_ns'] = float(latency_part.replace('ms', '')) * 1000000.
                except (ValueError, IndexError):
                    pass
            
            elif '- Area Efficiency =' in line and in_data_array_section:
                try:
                    if '=' in line:
                        efficiency_part = line.split('=')[1].strip()
                        results['area_efficiency'] = float(efficiency_part.replace('%', ''))
                except (ValueError, IndexError):
                    pass
            
            elif '- Read Bandwidth' in line and in_data_array_section:
                try:
                    if '=' in line:
                        bw_part = line.split('=')[1].strip()
                        if 'GB/s' in bw_part:
                            results['read_bandwidth_gbps'] = float(bw_part.replace('GB/s', ''))
                        elif 'MB/s' in bw_part:
                            results['read_bandwidth_gbps'] = float(bw_part.replace('MB/s', '')) / 1024.
                        elif 'KB/s' in bw_part:
                            results['read_bandwidth_gbps'] = float(bw_part.replace('KB/s', '')) / 1024. / 1024.
                except (ValueError, IndexError):
                    pass
            
            elif '- Write Bandwidth' in line and in_data_array_section:
                try:
                    if '=' in line:
                        bw_part = line.split('=')[1].strip()
                        if 'GB/s' in bw_part:
                            results['write_bandwidth_gbps'] = float(bw_part.replace('GB/s', ''))
                        elif 'MB/s' in bw_part:
                            results['write_bandwidth_gbps'] = float(bw_part.replace('MB/s', '')) / 1024.
                        elif 'KB/s' in bw_part:
                            results['write_bandwidth_gbps'] = float(bw_part.replace('KB/s', '')) / 1024. / 1024.
                except (ValueError, IndexError):
                    pass
            
            elif '-  Read Dynamic Energy' in line and in_data_array_section and results['read_energy_pj'] == -1.0:
                try:
                    if '=' in line:
                        energy_part = line.split('=')[1].strip()
                        if 'pJ' in energy_part:
                            results['read_energy_pj'] = float(energy_part.replace('pJ', ''))
                        elif 'nJ' in energy_part:
                            results['read_energy_pj'] = float(energy_part.replace('nJ', '')) * 1000.
                        elif 'uJ' in energy_part:
                            results['read_energy_pj'] = float(energy_part.replace('uJ', '')) * 1000. * 1000.
                except (ValueError, IndexError):
                    pass
            
            elif '- Write Dynamic Energy' in line and in_data_array_section and results['write_energy_pj'] == -1.0:
                try:
                    if '=' in line:
                        energy_part = line.split('=')[1].strip()
                        if 'pJ' in energy_part:
                            results['write_energy_pj'] = float(energy_part.replace('pJ', ''))
                        elif 'nJ' in energy_part:
                            results['write_energy_pj'] = float(energy_part.replace('nJ', '')) * 1000.
                        elif 'uJ' in energy_part:
                            results['write_energy_pj'] = float(energy_part.replace('uJ', '')) * 1000. * 1000.
                except (ValueError, IndexError):
                    pass
            
            elif '- Leakage Power' in line and in_data_array_section:
                try:
                    if '=' in line:
                        power_part = line.split('=')[1].strip()
                        if 'mW' in power_part:
                            results['leakage_power_mw'] = float(power_part.replace('mW', ''))
                        elif 'uW' in power_part:
                            results['leakage_power_mw'] = float(power_part.replace('uW', '')) / 1000.
                        elif 'W' in power_part and 'mW' not in power_part:
                            results['leakage_power_mw'] = float(power_part.replace('W', '')) * 1000.
                except (ValueError, IndexError):
                    pass
            
            if memory_type != "SRAM":
                if ' - SET Latency' in line:
                    try:
                        results['write_latency_ns'] = float(line[line.index("=")+1:][:-2])
                        if line[-2:] == "us":
                            results['write_latency_ns'] = results['write_latency_ns'] * 1000.
                        elif line[-2:] == "ps":
                            results['write_latency_ns'] = results['write_latency_ns'] / 1000.
                        elif line[-2:] == "ms":
                            results['write_latency_ns'] = results['write_latency_ns'] * 1000000.
                    except (ValueError, IndexError):
                        pass
                
                elif ' - SET Dynamic Energy ' in line:
                    try:
                        results['write_energy_pj'] = float(line[line.index("=")+1:][:-2])
                        if line[-2:] == "nJ":
                            results['write_energy_pj'] = results['write_energy_pj'] * 1000.
                        elif line[-2:] == "uJ":
                            results['write_energy_pj'] = results['write_energy_pj'] * 1000. * 1000.
                    except (ValueError, IndexError):
                        pass
        
        defaults = self._get_default_characteristics(memory_type, 22, 1.0)
        for key in results:
            if results[key] == -1.0:
                if key in defaults:
                    results[key] = defaults[key]
        
        return results
    
    def _extract_cell_parameters(self, cell_file: str) -> Dict[str, Any]:
        """
        Extract cell parameters from cell file for CSV output
        
        Args:
            cell_file: Path to cell file
            
        Returns:
            Dictionary with cell parameters
        """
        cell_params = {}
        
        try:
            with open(cell_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines or comment lines
                    if not line or line.startswith('//') or line.startswith('#'):
                        continue
                    
                    # Cell files use either ':' or space as separators
                    if ':' in line:
                        # Format: -MemCellType: SRAM
                        key, value = line.split(':', 1)
                        key = key.strip().lstrip('-')
                        value = value.strip()
                        cell_params[key] = value
                    else:
                        # Format: -MemCellType SRAM (space separated)
                        parts = line.split(maxsplit=1)
                        if len(parts) == 2:
                            key, value = parts
                            key = key.strip().lstrip('-')
                            value = value.strip()
                            cell_params[key] = value
        
        except (FileNotFoundError, IOError) as e:
            self.logger.warning(f"Could not read cell file {cell_file}: {e}")
        
        return cell_params