"""
Data Module

This module contains workload data definitions for traffic evaluation.
"""

from .workload_data import (
    DNN_weights, DNN_weights_acts, graph8MB, spec8MBLLC,
    get_workload_by_name, get_all_workloads, list_available_workloads,
    get_benchmark_count, get_benchmark_data, iterate_benchmarks
)

__all__ = [
    'DNN_weights', 
    'DNN_weights_acts', 
    'graph8MB', 
    'spec8MBLLC',
    'get_workload_by_name', 
    'get_all_workloads', 
    'list_available_workloads',
    'get_benchmark_count', 
    'get_benchmark_data', 
    'iterate_benchmarks'
]