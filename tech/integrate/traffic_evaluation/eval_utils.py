"""
Evaluation Utils

This module contains the core evaluation logic for memory system
traffic evaluation and performance analysis.
"""

import os
import math
import fileinput
import csv
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..input_defs.access_pattern import PatternConfig
    from ..input_defs.nvsim_interface import NVSimInputConfig, NVSimOutputConfig

def parse_nvsim_input_file(file_path: str) -> Tuple[List[str], List[str]]:
    """
    Helper function to parse cell cfgs and mem cfgs
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Tuple of (headers, values) lists
    """
    headers = []
    vals = []
    
    try:
        with open(file_path) as fp:
            for line in fp:
                line = line.strip()
                if ':' in line and line.startswith('-'):
                    # Split on first colon only
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        header = parts[0].strip()
                        if header.startswith('-'):
                            header = header[1:]
                        val = parts[1].strip()
                        headers.append(header)
                        vals.append(val)
    except (FileNotFoundError, IOError):
        pass
    
    return headers, vals


class ExperimentResult:
    """
    Experiment result evaluation and reporting
    
    This class handles the calculation of power, energy, latency, and bandwidth
    metrics based on access patterns and memory array characteristics.
    """
    
    def __init__(self, access_pattern: Optional["PatternConfig"] = None, 
                 nvsim_input_cfg: Optional["NVSimInputConfig"] = None, 
                 nvsim_output: Optional["NVSimOutputConfig"] = None):
        """
        Initialize experiment result
        
        Args:
            access_pattern: Access pattern configuration
            nvsim_input_cfg: NVSim input configuration
            nvsim_output: NVSim output configuration
        """
        self.access_pattern: Optional["PatternConfig"] = access_pattern
        self.input_cfg: Optional["NVSimInputConfig"] = nvsim_input_cfg
        self.output: Optional["NVSimOutputConfig"] = nvsim_output
        
        self.total_dynamic_read_power: float = 0.0
        self.total_dynamic_write_power: float = 0.0
        self.total_power: float = 0.0
        self.total_write_energy: float = 0.0
        self.total_read_energy: float = 0.0
        self.total_read_latency: float = 0.0
        self.total_write_latency: float = 0.0
        self.read_bw_utilization: float = 0.0
        self.write_bw_utilization: float = 0.0
        self.time_until_degraded: float = 0.0
        self.read_per_s: float = 0.0
        self.write_per_s: float = 0.0
    
    def evaluate(self):
        """
        Calculate total # reads/writes per second and derive all metrics
        """
        if self.access_pattern is None:
            raise ValueError("access_pattern is required for evaluation")
        if self.input_cfg is None:
            raise ValueError("nvsim_input_cfg is required for evaluation")
        if self.output is None:
            raise ValueError("nvsim_output is required for evaluation")
        
        if (self.access_pattern.read_freq == -1 or self.access_pattern.write_freq == -1):
            self.access_pattern.read_freq = (self.access_pattern.total_reads / self.access_pattern.total_ins) / 1.e8  # FIXME yikes I'm having to assume an IPC to approximate this?
            self.access_pattern.write_freq = (self.access_pattern.total_writes / self.access_pattern.total_ins) / 1.e8  # FIXME yikes I'm having to assume an IPC to approximate this?
        
        self.read_per_s = math.ceil((8 * self.access_pattern.read_size * self.access_pattern.read_freq) / self.input_cfg.word_width)
        self.total_dynamic_read_power = self.read_per_s * self.output.read_energy / 1000. / 1000. / 1000.
        
        self.write_per_s = math.ceil((8 * self.access_pattern.write_size * self.access_pattern.write_freq) / self.input_cfg.word_width)
        self.total_dynamic_write_power = self.write_per_s * self.output.write_energy / 1000. / 1000. /1000.

        self.total_power = self.output.leakage_power + self.total_dynamic_read_power + self.total_dynamic_write_power

        if (self.access_pattern.total_reads == -1):
            self.total_read_energy = self.total_dynamic_read_power
            self.total_write_energy = self.total_dynamic_write_power
            self.total_read_latency = self.read_per_s * self.output.read_latency / 1000. / 1000.
            self.total_write_latency = self.write_per_s * self.output.write_latency / 1000. / 1000.
        else:
            total_read_access = math.ceil((8 * self.access_pattern.total_reads * self.access_pattern.read_size) / self.input_cfg.word_width) 
            self.total_read_energy = total_read_access * self.output.read_energy / 1000. / 1000. / 1000.
            total_write_access = math.ceil((8 * self.access_pattern.total_writes * self.access_pattern.write_size) / self.input_cfg.word_width) 
            self.total_write_energy = total_write_access * self.output.write_energy / 1000. / 1000. /1000.
            self.total_read_latency = total_read_access * self.output.read_latency / 1000. / 1000. 
            self.total_write_latency = total_write_access * self.output.write_latency / 1000. / 1000.

        self.read_bw_utilization = ((self.read_per_s * self.input_cfg.word_width) / (self.output.read_bw * 8e9)) * 100
        self.write_bw_utilization = ((self.write_per_s * self.input_cfg.word_width) / (self.output.write_bw * 8e9)) * 100
    
    def report_header(self):
        """
        Report all results header
        
        Configuration for memory access patterns
        """
        print("Total Dynamic Read Power (mW)\tTotal Dynamic Write Power (mW)\tTotal Power", end="\t")
        print("Total Dynamic Read Energy (mJ)\tTotal Dynamic Write Energy (mJ)", end="\t")
        print("Total Read Latency (ms)\tTotal Write Latency (ms)\tRead BW Util\tWrite BW Util")

    def report_result(self):
        """
        Report all results
        
        Configuration for memory access patterns
        """
        print(self.total_dynamic_read_power, end="\t")  
        print(self.total_dynamic_write_power, end="\t")  
        print(self.total_power, end="\t")
        print(self.total_read_energy, end="\t")  
        print(self.total_write_energy, end="\t")  
        print(self.total_read_latency, end="\t")
        print(self.total_write_latency, end="\t")
        print(self.read_bw_utilization, end="\t")
        print(self.write_bw_utilization, end="\t")
        print()

    def report_header_benchmark(self, to_csv: int, csv_file_path: str, cell_cfg_path: str, mem_cfg_path: str):
        """
        Report all results header for benchmark studies
        
        Configuration for memory access patterns
        
        Args:
            to_csv: Flag for CSV output (1 for CSV, 0 for other)
            csv_file_path: Path to CSV output file
            cell_cfg_path: Path to cell configuration file
            mem_cfg_path: Path to memory configuration file
        """
        # Remove empty lines from cfg file to make processing easier
        if os.path.exists(mem_cfg_path):
            for line in fileinput.FileInput(mem_cfg_path, inplace=True):
                if line.rstrip():
                    print(line, end="")

        cell_headers, cell_vals = parse_nvsim_input_file(cell_cfg_path)
        mem_headers, mem_vals = parse_nvsim_input_file(mem_cfg_path)

        # Get memory type to determine which parameters to include
        cell_param_map = dict(zip(cell_headers, cell_vals)) if len(cell_headers) == len(cell_vals) else {}
        memory_type = cell_param_map.get("MemCellType", "")
        
        # Generate dynamic header based on memory type
        row_to_insert = self._generate_dynamic_header(memory_type)

        with open(csv_file_path, "a+", newline='') as fp:
            wr = csv.writer(fp, dialect='excel')
            wr.writerow(row_to_insert)

    def report_result_benchmark(self, to_csv: int, csv_file_path: str, cell_cfg_path: str, 
                              mem_cfg_path: str, access_pattern: "PatternConfig"):
        """
        Report results for benchmark studies
        
        Configuration for memory access patterns
        
        Args:
            to_csv: Flag for CSV output (1 for CSV, 0 for other)
            csv_file_path: Path to CSV output file
            cell_cfg_path: Path to cell configuration file
            mem_cfg_path: Path to memory configuration file
            access_pattern: Access pattern configuration
        """
        # Check if output is available
        if self.output is None:
            raise ValueError("nvsim_output is required for reporting results")
        # Remove empty lines from cfg file to make processing easier
        if os.path.exists(mem_cfg_path):
            for line in fileinput.FileInput(mem_cfg_path, inplace=True):
                if line.rstrip():
                    print(line, end="")

        cell_headers, cell_vals = parse_nvsim_input_file(cell_cfg_path)
        mem_headers, mem_vals = parse_nvsim_input_file(mem_cfg_path)

        # Extract bits per cell from filename
        if "1BPC" in csv_file_path:
            bits_per_cell = 1
        elif "2BPC" in csv_file_path:
            bits_per_cell = 2
        elif "3BPC" in csv_file_path:
            bits_per_cell = 3
        else:
            bits_per_cell = 1

        # Extract extended parameters from configurations
        extended_params = self._extract_extended_parameters(cell_cfg_path, mem_cfg_path, cell_vals, mem_vals)
        
        # Get memory type for dynamic row generation
        cell_param_map = dict(zip(cell_headers, cell_vals)) if len(cell_headers) == len(cell_vals) else {}
        memory_type = cell_param_map.get("MemCellType", "")
        
        # Generate dynamic row based on memory type
        row_to_insert = self._generate_dynamic_row(memory_type, extended_params, cell_cfg_path, access_pattern, bits_per_cell)

        # Don't append cell_vals and mem_vals since row_to_insert already contains all required data
        # row_to_insert already contains all the values in the correct order
        
        with open(csv_file_path, "a", newline='') as fp:
            wr = csv.writer(fp, dialect='excel')
            wr.writerow(row_to_insert)
    
    def _extract_extended_parameters(self, cell_cfg_path: str, mem_cfg_path: str, 
                                   cell_vals: List[str], mem_vals: List[str], 
                                   json_config: dict = None) -> dict:
        """
        Extract extended parameters from cell and memory configuration files based on unified schema
        
        Args:
            cell_cfg_path: Path to cell configuration file
            mem_cfg_path: Path to memory configuration file  
            cell_vals: Parsed cell configuration values
            mem_vals: Parsed memory configuration values
            json_config: JSON configuration for default values
            
        Returns:
            Dictionary containing all extracted parameters
        """
        params = {}
        
        # Create mapping from headers to values for cell parameters
        cell_headers, _ = parse_nvsim_input_file(cell_cfg_path)
        cell_param_map = dict(zip(cell_headers, cell_vals)) if len(cell_headers) == len(cell_vals) else {}
        
        # Create mapping from headers to values for memory parameters
        mem_headers, _ = parse_nvsim_input_file(mem_cfg_path)
        mem_param_map = dict(zip(mem_headers, mem_vals)) if len(mem_headers) == len(mem_vals) else {}
        
        # Universal config parameters (always shown for all memory types)
        universal_config_params = [
            "ProcessNode", "DeviceRoadmap", "DesignTarget", "OptimizationTarget",
            "LocalWireType", "LocalWireRepeaterType", "LocalWireUseLowSwing",
            "GlobalWireType", "GlobalWireRepeaterType", "GlobalWireUseLowSwing", 
            "Routing", "InternalSensing", "Temperature (K)", "BufferDesignOptimization",
            "RetentionTime (us)", "CacheAccessMode", "Associativity (for cache only)",
            "EnablePruning", "Capacity (KB)", "WordWidth (bit)"
        ]
        
        # Universal cell parameters (always shown for all memory types) 
        universal_cell_params = [
            "MemCellType", "CellArea (F^2)", "CellAspectRatio", "AccessType", "ReadMode"
        ]
        
        # Memory-specific parameters based on analysis
        memory_specific_params = {
            "SRAM": {
                "SRAMCellNMOSWidth (F)", "SRAMCellPMOSWidth (F)", "AccessCMOSWidth (F)", 
                "MinSenseVoltage (mV)", "ReadVoltage (V)", "Stitching"
            },
            "RRAM": {
                "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "ReadFloating"
            },
            "MRAM": {
                "ResistanceOn (ohm)", "ResistanceOff (ohm)", "ReadVoltage (V)", 
                "MinSenseVoltage (mV)", "ReadPower (uW)", "ResetMode", "ResetCurrent (uA)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetCurrent (uA)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "AccessCMOSWidth (F)", "VoltageDropAccessDevice (V)"
            },
            "FeFET": {
                "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "AccessCMOSWidth (F)", "VoltageDropAccessDevice (V)",
                "ReadFloating"
            },
            "MLCFeFET": {
                "CellLevels", "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "AccessCMOSWidth (F)", "VoltageDropAccessDevice (V)",
                "ReadFloating"
            },
            "PCRAM": {
                "ProcessNode", "ResistanceOn (ohm)", "ResistanceOff (ohm)", "ReadCurrent (uA)", 
                "ReadEnergy (pJ)", "ResetMode", "ResetCurrent (uA)", "ResetPulse (ns)", 
                "SetMode", "SetCurrent (uA)", "SetPulse (ns)", "AccessCMOSWidth (F)", 
                "VoltageDropAccessDevice (V)"
            },
            "CTT": set(),
            "MLCCTT": {"InputFingers", "CellLevels"},
            "MLCRRAM": {
                "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "ReadFloating"
            },
            "eDRAM": {
                "AccessCMOSWidth (F)", "DRAMCellCapacitance (F)", "MinSenseVoltage (mV)", 
                "MaxStorageNodeDrop (V)", "RetentionTime (us)"
            },
            "eDRAM3T": {
                "AccessCMOSWidth (F)", "AccessCMOSWidthR (F)", "DRAMCellCapacitance (F)", 
                "MinSenseVoltage (mV)", "MaxStorageNodeDrop (V)", "RetentionTime (us)"
            },
            "eDRAM3T333": {
                "AccessCMOSWidth (F)", "AccessCMOSWidthR (F)", "DRAMCellCapacitance (F)", 
                "MinSenseVoltage (mV)", "MaxStorageNodeDrop (V)", "RetentionTime (us)"
            }
        }
        
        # Extract universal config parameters
        for param in universal_config_params:
            value = mem_param_map.get(param, "")
            # Provide defaults for common config parameters
            if not value:
                if param == "ProcessNode" and self.input_cfg:
                    value = str(self.input_cfg.process_node)
                elif param == "OptimizationTarget" and self.input_cfg:
                    value = str(self.input_cfg.opt_target)
                elif param == "WordWidth (bit)" and self.input_cfg:
                    value = str(self.input_cfg.word_width)
                elif param == "Capacity (KB)" and self.input_cfg:
                    value = str(self.input_cfg.capacity)
                elif param == "DesignTarget":
                    value = "cache"
                elif param == "DeviceRoadmap":
                    value = "LOP"
                elif param == "LocalWireType":
                    value = "LocalAggressive"
                elif param == "GlobalWireType":
                    value = "GlobalAggressive"
                elif param == "Routing":
                    value = "H-tree"
                elif param == "Temperature (K)":
                    value = "300"
                elif param == "BufferDesignOptimization":
                    value = "latency"
            params[param] = value
        
        # Extract universal cell parameters (always show actual values)
        for param in universal_cell_params:
            value = cell_param_map.get(param, "")
            params[param] = value
        
        # Extract memory-specific parameters
        memory_type = cell_param_map.get("MemCellType", "")
        specific_params = memory_specific_params.get(memory_type, set())
        
        for param in specific_params:
            value = cell_param_map.get(param, "")
            params[param] = value
        
        return params
    
    def _generate_dynamic_header(self, memory_type: str) -> list:
        """
        Generate dynamic CSV header based on memory type to avoid unnecessary empty columns
        
        Args:
            memory_type: The memory cell type (e.g., SRAM, memristor, eDRAM, etc.)
            
        Returns:
            List of header names appropriate for the memory type
        """
        # Universal config parameters (always included)
        header = [
            "ProcessNode", "DeviceRoadmap", "DesignTarget", "OptimizationTarget",
            "LocalWireType", "LocalWireRepeaterType", "LocalWireUseLowSwing",
            "GlobalWireType", "GlobalWireRepeaterType", "GlobalWireUseLowSwing", 
            "Routing", "InternalSensing", "Temperature (K)", "BufferDesignOptimization",
            "RetentionTime (us)", "CacheAccessMode", "Associativity (for cache only)",
            "EnablePruning", "Capacity (KB)", "WordWidth (bit)",
            
            # Universal cell parameters (always included)
            "MemCellType", "CellArea (F^2)", "CellAspectRatio", "AccessType", "ReadMode"
        ]
        
        # Add memory-specific parameters based on type
        if memory_type == "SRAM":
            header.extend([
                "SRAMCellNMOSWidth (F)", "SRAMCellPMOSWidth (F)", "AccessCMOSWidth (F)", 
                "MinSenseVoltage (mV)", "ReadVoltage (V)", "Stitching"
            ])
        elif memory_type == "RRAM":
            header.extend([
                "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "ReadFloating"
            ])
        elif memory_type in ["MRAM", "STTRAM"]:
            header.extend([
                "ResistanceOn (ohm)", "ResistanceOff (ohm)", "ReadVoltage (V)", 
                "MinSenseVoltage (mV)", "ReadPower (uW)", "ResetMode", "ResetCurrent (uA)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetCurrent (uA)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "AccessCMOSWidth (F)", "VoltageDropAccessDevice (V)"
            ])
        elif memory_type == "FeFET":
            header.extend([
                "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "AccessCMOSWidth (F)", "VoltageDropAccessDevice (V)",
                "ReadFloating"
            ])
        elif memory_type == "MLCFeFET":
            header.extend([
                "CellLevels", "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "AccessCMOSWidth (F)", "VoltageDropAccessDevice (V)",
                "ReadFloating"
            ])
        elif memory_type == "PCRAM":
            header.extend([
                "ProcessNode", "ResistanceOn (ohm)", "ResistanceOff (ohm)", "ReadCurrent (uA)", 
                "ReadEnergy (pJ)", "ResetMode", "ResetCurrent (uA)", "ResetPulse (ns)", 
                "SetMode", "SetCurrent (uA)", "SetPulse (ns)", "AccessCMOSWidth (F)", 
                "VoltageDropAccessDevice (V)"
            ])
        elif memory_type == "CTT":
            pass  # CTT only has basic parameters
        elif memory_type == "MLCCTT":
            header.extend(["InputFingers", "CellLevels"])
        elif memory_type == "MLCRRAM":
            header.extend([
                "ResistanceOnAtSetVoltage (ohm)", "ResistanceOffAtSetVoltage (ohm)", 
                "ResistanceOnAtResetVoltage (ohm)", "ResistanceOffAtResetVoltage (ohm)",
                "ResistanceOnAtReadVoltage (ohm)", "ResistanceOffAtReadVoltage (ohm)",
                "ResistanceOnAtHalfResetVoltage (ohm)", "CapacitanceOn (F)", "CapacitanceOff (F)",
                "ReadVoltage (V)", "ReadPower (uW)", "ResetMode", "ResetVoltage (V)", 
                "ResetPulse (ns)", "ResetEnergy (pJ)", "SetMode", "SetVoltage (V)", 
                "SetPulse (ns)", "SetEnergy (pJ)", "ReadFloating"
            ])
        elif memory_type == "eDRAM":
            header.extend([
                "AccessCMOSWidth (F)", "DRAMCellCapacitance (F)", "MinSenseVoltage (mV)", 
                "MaxStorageNodeDrop (V)", "RetentionTime (us)"
            ])
        elif memory_type in ["eDRAM3T", "eDRAM3T333"]:
            header.extend([
                "AccessCMOSWidth (F)", "AccessCMOSWidthR (F)", "DRAMCellCapacitance (F)", 
                "MinSenseVoltage (mV)", "MaxStorageNodeDrop (V)", "RetentionTime (us)"
            ])
            
        # Add file reference and traffic evaluation results (always included)
        header.extend([
            "MemoryCellInputFile",
            "Benchmark Name", "Read Accesses", "Write Accesses", 
            "Total Dynamic Read Power (mW)", "Total Dynamic Write Power (mW)", "Total Power", 
            "Total Dynamic Read Energy (mJ)", "Total Dynamic Write Energy (mJ)", 
            "Total Read Latency (ms)", "Total Write Latency (ms)", 
            "Read BW Util", "Write BW Util", 
            "Area (mm^2)", "Area Efficiency (percent)", 
            "Read Latency (ns)", "Write Latency (ns)", 
            "Read Energy (pJ)", "Write Energy (pJ)", 
            "Leakage Power (mW)", "Bits Per Cell"
        ])
        
        return header
    
    def _generate_dynamic_row(self, memory_type: str, extended_params: dict, 
                              cell_cfg_path: str, access_pattern, bits_per_cell: int) -> list:
        """
        Generate dynamic CSV row data based on memory type to match the dynamic header
        
        Args:
            memory_type: The memory cell type
            extended_params: Dictionary of extracted parameters
            cell_cfg_path: Path to cell configuration file
            access_pattern: Access pattern configuration
            bits_per_cell: Number of bits per cell
            
        Returns:
            List of values matching the dynamic header
        """
        # Universal config parameters (always included)
        row = [
            extended_params.get("ProcessNode", self.input_cfg.process_node if self.input_cfg else ""),
            extended_params.get("DeviceRoadmap", ""),
            extended_params.get("DesignTarget", ""),
            extended_params.get("OptimizationTarget", self.input_cfg.opt_target if self.input_cfg else ""),
            extended_params.get("LocalWireType", ""),
            extended_params.get("LocalWireRepeaterType", ""), 
            extended_params.get("LocalWireUseLowSwing", ""),
            extended_params.get("GlobalWireType", ""), 
            extended_params.get("GlobalWireRepeaterType", ""),
            extended_params.get("GlobalWireUseLowSwing", ""), 
            extended_params.get("Routing", ""),
            extended_params.get("InternalSensing", ""), 
            extended_params.get("Temperature (K)", ""),
            extended_params.get("BufferDesignOptimization", ""),
            extended_params.get("RetentionTime (us)", ""),
            extended_params.get("CacheAccessMode", ""),
            extended_params.get("Associativity (for cache only)", ""),
            extended_params.get("EnablePruning", ""),
            extended_params.get("Capacity (KB)", self.input_cfg.capacity if self.input_cfg else ""),
            extended_params.get("WordWidth (bit)", self.input_cfg.word_width if self.input_cfg else ""),
            
            # Universal cell parameters (always included)
            extended_params.get("MemCellType", ""),
            extended_params.get("CellArea (F^2)", ""), 
            extended_params.get("CellAspectRatio", ""),
            extended_params.get("AccessType", ""),
            extended_params.get("ReadMode", "")
        ]
        
        # Add memory-specific parameters based on type
        if memory_type == "SRAM":
            row.extend([
                extended_params.get("SRAMCellNMOSWidth (F)", ""),
                extended_params.get("SRAMCellPMOSWidth (F)", ""), 
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("MinSenseVoltage (mV)", ""),
                extended_params.get("ReadVoltage (V)", ""), 
                extended_params.get("Stitching", "")
            ])
        elif memory_type == "RRAM":
            row.extend([
                extended_params.get("ResistanceOnAtSetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtSetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtResetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtResetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtReadVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtReadVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtHalfResetVoltage (ohm)", ""), 
                extended_params.get("CapacitanceOn (F)", ""),
                extended_params.get("CapacitanceOff (F)", ""),
                extended_params.get("ReadVoltage (V)", ""),
                extended_params.get("ReadPower (uW)", ""),
                extended_params.get("ResetMode", ""), 
                extended_params.get("ResetVoltage (V)", ""),
                extended_params.get("ResetPulse (ns)", ""), 
                extended_params.get("ResetEnergy (pJ)", ""),
                extended_params.get("SetMode", ""), 
                extended_params.get("SetVoltage (V)", ""),
                extended_params.get("SetPulse (ns)", ""), 
                extended_params.get("SetEnergy (pJ)", ""),
                extended_params.get("ReadFloating", "")
            ])
        elif memory_type in ["MRAM", "STTRAM"]:
            row.extend([
                extended_params.get("ResistanceOn (ohm)", ""),
                extended_params.get("ResistanceOff (ohm)", ""),
                extended_params.get("ReadVoltage (V)", ""),
                extended_params.get("MinSenseVoltage (mV)", ""),
                extended_params.get("ReadPower (uW)", ""),
                extended_params.get("ResetMode", ""),
                extended_params.get("ResetCurrent (uA)", ""), 
                extended_params.get("ResetPulse (ns)", ""),
                extended_params.get("ResetEnergy (pJ)", ""),
                extended_params.get("SetMode", ""),
                extended_params.get("SetCurrent (uA)", ""),
                extended_params.get("SetPulse (ns)", ""),
                extended_params.get("SetEnergy (pJ)", ""),
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("VoltageDropAccessDevice (V)", "")
            ])
        elif memory_type == "FeFET":
            row.extend([
                extended_params.get("ResistanceOnAtSetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtSetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtResetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtResetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtReadVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtReadVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtHalfResetVoltage (ohm)", ""), 
                extended_params.get("CapacitanceOn (F)", ""),
                extended_params.get("CapacitanceOff (F)", ""),
                extended_params.get("ReadVoltage (V)", ""),
                extended_params.get("ReadPower (uW)", ""),
                extended_params.get("ResetMode", ""), 
                extended_params.get("ResetVoltage (V)", ""),
                extended_params.get("ResetPulse (ns)", ""), 
                extended_params.get("ResetEnergy (pJ)", ""),
                extended_params.get("SetMode", ""), 
                extended_params.get("SetVoltage (V)", ""),
                extended_params.get("SetPulse (ns)", ""), 
                extended_params.get("SetEnergy (pJ)", ""),
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("VoltageDropAccessDevice (V)", ""),
                extended_params.get("ReadFloating", "")
            ])
        elif memory_type == "MLCFeFET":
            row.extend([
                extended_params.get("CellLevels", ""),
                extended_params.get("ResistanceOnAtSetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtSetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtResetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtResetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtReadVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtReadVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtHalfResetVoltage (ohm)", ""), 
                extended_params.get("CapacitanceOn (F)", ""),
                extended_params.get("CapacitanceOff (F)", ""),
                extended_params.get("ReadVoltage (V)", ""),
                extended_params.get("ReadPower (uW)", ""),
                extended_params.get("ResetMode", ""), 
                extended_params.get("ResetVoltage (V)", ""),
                extended_params.get("ResetPulse (ns)", ""), 
                extended_params.get("ResetEnergy (pJ)", ""),
                extended_params.get("SetMode", ""), 
                extended_params.get("SetVoltage (V)", ""),
                extended_params.get("SetPulse (ns)", ""), 
                extended_params.get("SetEnergy (pJ)", ""),
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("VoltageDropAccessDevice (V)", ""),
                extended_params.get("ReadFloating", "")
            ])
        elif memory_type == "PCRAM":
            row.extend([
                extended_params.get("ProcessNode", ""),
                extended_params.get("ResistanceOn (ohm)", ""),
                extended_params.get("ResistanceOff (ohm)", ""),
                extended_params.get("ReadCurrent (uA)", ""),
                extended_params.get("ReadEnergy (pJ)", ""),
                extended_params.get("ResetMode", ""),
                extended_params.get("ResetCurrent (uA)", ""),
                extended_params.get("ResetPulse (ns)", ""),
                extended_params.get("SetMode", ""),
                extended_params.get("SetCurrent (uA)", ""),
                extended_params.get("SetPulse (ns)", ""),
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("VoltageDropAccessDevice (V)", "")
            ])
        elif memory_type == "CTT":
            pass  # CTT only has basic parameters
        elif memory_type == "MLCCTT":
            row.extend([
                extended_params.get("InputFingers", ""),
                extended_params.get("CellLevels", "")
            ])
        elif memory_type == "MLCRRAM":
            row.extend([
                extended_params.get("ResistanceOnAtSetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtSetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtResetVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtResetVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtReadVoltage (ohm)", ""), 
                extended_params.get("ResistanceOffAtReadVoltage (ohm)", ""),
                extended_params.get("ResistanceOnAtHalfResetVoltage (ohm)", ""), 
                extended_params.get("CapacitanceOn (F)", ""),
                extended_params.get("CapacitanceOff (F)", ""),
                extended_params.get("ReadVoltage (V)", ""),
                extended_params.get("ReadPower (uW)", ""),
                extended_params.get("ResetMode", ""), 
                extended_params.get("ResetVoltage (V)", ""),
                extended_params.get("ResetPulse (ns)", ""), 
                extended_params.get("ResetEnergy (pJ)", ""),
                extended_params.get("SetMode", ""), 
                extended_params.get("SetVoltage (V)", ""),
                extended_params.get("SetPulse (ns)", ""), 
                extended_params.get("SetEnergy (pJ)", ""),
                extended_params.get("ReadFloating", "")
            ])
        elif memory_type == "eDRAM":
            row.extend([
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("DRAMCellCapacitance (F)", ""),
                extended_params.get("MinSenseVoltage (mV)", ""),
                extended_params.get("MaxStorageNodeDrop (V)", ""),
                extended_params.get("RetentionTime (us)", "")
            ])
        elif memory_type in ["eDRAM3T", "eDRAM3T333"]:
            row.extend([
                extended_params.get("AccessCMOSWidth (F)", ""),
                extended_params.get("AccessCMOSWidthR (F)", ""),
                extended_params.get("DRAMCellCapacitance (F)", ""),
                extended_params.get("MinSenseVoltage (mV)", ""),
                extended_params.get("MaxStorageNodeDrop (V)", ""),
                extended_params.get("RetentionTime (us)", "")
            ])
            
        # Add file reference and traffic evaluation results (always included)
        row.extend([
            extended_params.get("MemoryCellInputFile", cell_cfg_path),
            access_pattern.benchmark_name, 
            access_pattern.read_freq, 
            access_pattern.write_freq, 
            self.total_dynamic_read_power, 
            self.total_dynamic_write_power, 
            self.total_power, 
            self.total_read_energy, 
            self.total_write_energy, 
            self.total_read_latency, 
            self.total_write_latency, 
            self.read_bw_utilization, 
            self.write_bw_utilization, 
            self.output.area, 
            self.output.area_efficiency, 
            self.output.read_latency, 
            self.output.write_latency, 
            self.output.read_energy, 
            self.output.write_energy, 
            self.output.leakage_power, 
            bits_per_cell
        ])
        
        return row