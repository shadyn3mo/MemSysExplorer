"""
MSXFI Controller for integrating fault injection capabilities with the integrate framework.

This controller provides a non-invasive way to add fault injection to memory system evaluation
while maintaining backward compatibility with existing functionality.
"""

from typing import Dict, Any, Optional, Union
import logging

try:
    # Import msxFI components using relative paths from the 'tech' package
    from tech.msxFI import fault_injection, fi_config, fi_utils
    
    # Import specific components
    mat_fi = fault_injection.mat_fi
    dnn_fi = fault_injection.dnn_fi
    mem_model_dict = fi_config.mem_dict  # Correct attribute name
    mem_model = fi_config.mem_model
    device = fi_config.pt_device  # Correct attribute name
    validate_config = fi_utils.validate_config
    get_error_map = fi_utils.get_error_map
    
    MSXFI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"msxFI components not available: {e}")
    MSXFI_AVAILABLE = False
    # Create dummy variables to prevent NameError
    mat_fi = dnn_fi = mem_model_dict = mem_model = device = None
    validate_config = get_error_map = None

class MSXFIController:
    """
    Controller for integrating msxFI fault injection with memory characterization.
    
    This controller acts as a bridge between the integrate framework and msxFI,
    providing fault-aware memory system evaluation capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MSXFI Controller with configuration.
        
        Args:
            config: Configuration dictionary containing fault injection parameters
        """
        self.config = config
        self.fault_config = config.get('fault_injection', {})
        self.enabled = self.fault_config.get('enabled', False)
        
        if self.enabled and not MSXFI_AVAILABLE:
            raise ImportError("Fault injection is enabled but msxFI components are not available")
        
        self._validate_configuration()
        
    def _validate_configuration(self):
        """Validate fault injection configuration parameters."""
        if not self.enabled:
            return
            
        required_params = ['memory_model', 'quantization']
        for param in required_params:
            if param not in self.fault_config:
                raise ValueError(f"Required fault injection parameter '{param}' not found in configuration")
        
        # Validate memory model
        memory_model = self.fault_config['memory_model']
        if mem_model_dict is not None and memory_model not in mem_model_dict:
            available_models = list(mem_model_dict.keys())
            raise ValueError(f"Invalid memory model '{memory_model}'. Available models: {available_models}")
        elif mem_model_dict is None:
            logging.warning("Memory model dictionary not available - skipping model validation")
        
        # Validate quantization parameters
        quant_config = self.fault_config['quantization']
        required_quant_params = ['q_type', 'int_bits', 'frac_bits']
        for param in required_quant_params:
            if param not in quant_config:
                raise ValueError(f"Required quantization parameter '{param}' not found")
    
    def is_enabled(self) -> bool:
        """Check if fault injection is enabled."""
        return self.enabled and MSXFI_AVAILABLE
    
    def inject_memory_faults(self, memory_data: Any, seed: Optional[int] = None) -> Any:
        """
        Inject faults into memory data using msxFI.
        
        Args:
            memory_data: Memory data to inject faults into (numpy array or compatible)
            seed: Random seed for reproducible fault injection
            
        Returns:
            Faulty memory data with injected faults
        """
        if not self.is_enabled():
            return memory_data
        
        try:
            # Extract fault injection parameters
            quant_config = self.fault_config['quantization']
            memory_model = self.fault_config['memory_model']
            
            # Set up fault injection parameters
            fault_params = {
                'seed': seed or 0,
                'int_bits': quant_config['int_bits'],
                'frac_bits': quant_config['frac_bits'],
                'q_type': quant_config['q_type'],
                'encode': self.fault_config.get('encoding', 'dense'),
            }
            
            # Add memory-specific parameters
            if 'rep_conf' in self.fault_config:
                fault_params['rep_conf'] = self.fault_config['rep_conf']
            
            if 'dram' in memory_model.lower():
                fault_params['refresh_time'] = self.fault_config.get('refresh_time', None)
                fault_params['vth_sigma'] = self.fault_config.get('vth_sigma', 0.05)
                fault_params['custom_vdd'] = self.fault_config.get('custom_vdd', None)
            
            # Inject faults using msxFI
            if mat_fi is not None:
                faulty_data = mat_fi(memory_data, **fault_params)
            else:
                logging.warning("mat_fi not available - returning original data")
                faulty_data = memory_data
            
            logging.info(f"Applied fault injection with model: {memory_model}")
            return faulty_data
            
        except Exception as e:
            logging.error(f"Fault injection failed: {e}")
            return memory_data
    
    def inject_dnn_faults(self, model_def_path: str, model_path: str, seed: Optional[int] = None) -> str:
        """
        Inject faults into a deep neural network model.
        
        Args:
            model_def_path: Path to model definition file
            model_path: Path to trained model file
            seed: Random seed for reproducible fault injection
            
        Returns:
            Path to faulty model or original path if fault injection disabled
        """
        if not self.is_enabled():
            return model_path
        
        try:
            # Extract fault injection parameters
            quant_config = self.fault_config['quantization']
            
            # Set up fault injection parameters
            fault_params = {
                'seed': seed or 0,
                'int_bits': quant_config['int_bits'],
                'frac_bits': quant_config['frac_bits'],
                'q_type': quant_config['q_type'],
                'encode': self.fault_config.get('encoding', 'dense'),
            }
            
            # Add memory-specific parameters
            if 'rep_conf' in self.fault_config:
                fault_params['rep_conf'] = self.fault_config['rep_conf']
            
            # Inject faults using msxFI DNN function
            if dnn_fi is not None:
                faulty_model = dnn_fi(model_def_path, model_path, **fault_params)
            else:
                logging.warning("dnn_fi not available - returning original model path")
                faulty_model = model_path
            
            logging.info(f"Applied DNN fault injection to model: {model_path}")
            return faulty_model
            
        except Exception as e:
            logging.error(f"DNN fault injection failed: {e}")
            return model_path
    
    def get_fault_statistics(self, original_data: Any, faulty_data: Any) -> Dict[str, float]:
        """
        Calculate fault injection statistics.
        
        Args:
            original_data: Original data before fault injection
            faulty_data: Data after fault injection
            
        Returns:
            Dictionary containing fault statistics
        """
        if not self.is_enabled():
            return {}
        
        try:
            import numpy as np
            
            # Convert to numpy arrays if needed
            orig_array = np.asarray(original_data)
            fault_array = np.asarray(faulty_data)
            
            # Calculate statistics
            total_elements = orig_array.size
            different_elements = np.sum(orig_array != fault_array)
            fault_rate = different_elements / total_elements if total_elements > 0 else 0.0
            
            # Calculate error metrics
            if orig_array.dtype in [np.float32, np.float64]:
                mse = np.mean((orig_array - fault_array) ** 2)
                mae = np.mean(np.abs(orig_array - fault_array))
                relative_error = np.mean(np.abs((orig_array - fault_array) / (orig_array + 1e-10)))
            else:
                mse = mae = relative_error = float('nan')
            
            return {
                'fault_rate': fault_rate,
                'affected_elements': int(different_elements),
                'total_elements': int(total_elements),
                'mse': float(mse),
                'mae': float(mae),
                'relative_error': float(relative_error)
            }
            
        except Exception as e:
            logging.error(f"Failed to calculate fault statistics: {e}")
            return {}
    
    def get_memory_model_info(self) -> Dict[str, Any]:
        """Get information about the current memory model."""
        if not self.is_enabled():
            return {}
        
        memory_model = self.fault_config.get('memory_model', 'unknown')
        return {
            'memory_model': memory_model,
            'available_models': list(mem_model_dict.keys()) if (MSXFI_AVAILABLE and mem_model_dict is not None) else [],
            'device': device if (MSXFI_AVAILABLE and device is not None) else 'cpu',
            'quantization': self.fault_config.get('quantization', {}),
            'encoding': self.fault_config.get('encoding', 'dense')
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update fault injection configuration."""
        self.fault_config.update(new_config.get('fault_injection', {}))
        self.enabled = self.fault_config.get('enabled', False)
        self._validate_configuration()
        
        logging.info("Updated fault injection configuration")