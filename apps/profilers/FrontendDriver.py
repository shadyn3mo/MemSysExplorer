"""
Profiler Registration Module for MemSysExplorer.

This module handles dynamic registration of profiler frontends, pattern
config classes, and metadata collectors based on the available profiler builds
listed in `built_profilers.json`.

Supported Profilers:
- Nsight Compute (ncu)
- Linux perf (perf)
- NVBit (nvbit)
- DynamoRIO (dynamorio)
- Sniper simulator (sniper)
"""

import json
import os
import importlib

from profilers.FrontendInterface import FrontendInterface
from profilers.PatternConfig import PatternConfig
from profilers.BaseMetadata import BaseMetadata

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
JSON_FILE = os.path.join(BASE_DIR, "..", "built_profilers.json")

# Unified registry for all profilers: profiler logic, pattern config, and metadata
PROFILER_REGISTRY = {
    "ncu": {
        "profiler": ("profilers.ncu.ncu_profilers", "NsightComputeProfilers"),
        "config": ("profilers.ncu.ncu_PatternConfig", "NsightComputeConfig"),
        "metadata": ("profilers.ncu.ncu_Metadata", "NsightMetadata")
    },
    "perf": {
        "profiler": ("profilers.perf.perf_profilers", "PerfProfilers"),
        "config": ("profilers.perf.perf_PatternConfig", "PerfConfig"),
        "metadata": ("profilers.perf.perf_Metadata", "PerfMetadata")
    },
    "nvbit": {
        "profiler": ("profilers.nvbit.nvbit_profilers", "NVBitProfilers"),
        "config": ("profilers.nvbit.nvbit_PatternConfig", "NVBitConfig"),
        "metadata": ("profilers.nvbit.nvbit_Metadata", "NVBitMetadata")
    },
    "dynamorio": {
        "profiler": ("profilers.dynamorio.drio_profilers", "DrioProfilers"),
        "config": ("profilers.dynamorio.drio_PatternConfig", "DrioConfig"),
        "metadata": ("profilers.dynamorio.drio_Metadata", "DrioMetadata")
    },
    "sniper": {
        "profiler": ("profilers.sniper.sniper_profilers", "SniperProfilers"),
        "config": ("profilers.sniper.sniper_PatternConfig", "SniperConfig"),
        "metadata": ("profilers.sniper.sniper_Metadata", "SniperMetadata")
    }
}

def load_built_profilers():
    """
    Load the set of available profilers from the JSON file.

    Returns
    -------
    dict
        A dictionary of profiler names with boolean flags indicating if
        the profiler is built (e.g., {"ncu": true, "perf": false}).
        Returns an empty dictionary if the file does not exist.
    """
    if not os.path.exists(JSON_FILE):
        return {}

    with open(JSON_FILE, "r") as f:
        return json.load(f)


def register_profilers():
    """
    Dynamically register all enabled profilers using the class
    definitions listed in `PROFILER_REGISTRY`.

    This function reads the profiler flags from `built_profilers.json`,
    imports the corresponding modules and classes, and registers them
    with `FrontendInterface`.

    Output
    ------
    Prints a list of successfully registered profiler names.
    Logs warnings for any missing modules or classes.
    """
    built_profilers = load_built_profilers()
    registered_profilers = []

    for profiler, entries in PROFILER_REGISTRY.items():
        if built_profilers.get(profiler, False):
            module_name, class_name = entries["profiler"]
            try:
                module = importlib.import_module(module_name)
                profiler_class = getattr(module, class_name)
                FrontendInterface.register_profiler(profiler, profiler_class)
                registered_profilers.append(profiler)
            except (ModuleNotFoundError, AttributeError) as e:
                print(f"Warning: Failed to register {profiler}: {e}")

    print("Registered Profilers:", registered_profilers)


def register_PatternConfig():
    """
    Dynamically register PatternConfig classes associated with each profiler.

    This function reads profiler availability from `built_profilers.json`,
    then imports the pattern configuration class for each supported profiler
    and registers it with the `PatternConfig` registry.

    Output
    ------
    Prints a list of successfully registered PatternConfig class names.
    Logs warnings for any import or attribute errors.
    """
    built_profilers = load_built_profilers()
    registered_configs = []

    for profiler, entries in PROFILER_REGISTRY.items():
        if built_profilers.get(profiler, False):
            module_name, class_name = entries["config"]
            try:
                module = importlib.import_module(module_name)
                config_class = getattr(module, class_name)
                PatternConfig.register_config(profiler, config_class)
                registered_configs.append(profiler)
            except (ModuleNotFoundError, AttributeError) as e:
                print(f"Warning: Failed to register config for {profiler}: {e}")

    print("Registered PatternConfig Classes:", registered_configs)


def register_MetadataClasses():
    """
    Dynamically register metadata classes for profilers.

    This function imports metadata collection classes for each profiler
    and registers them with `FrontendInterface`. These classes collect
    runtime system and environment information.

    Output
    ------
    Prints a list of profilers that successfully registered their metadata class.
    Logs warnings for any profilers that fail registration.
    """
    built_profilers = load_built_profilers()
    registered_metadata = []

    for profiler, entries in PROFILER_REGISTRY.items():
        if built_profilers.get(profiler, False):
            module_name, class_name = entries["metadata"]
            try:
                module = importlib.import_module(module_name)
                metadata_class = getattr(module, class_name)
                FrontendInterface.register_metadata(profiler, metadata_class)
                print(f"Registered Metadata for: {profiler}")
                registered_metadata.append(profiler)
            except (ModuleNotFoundError, AttributeError) as e:
                print(f"Warning: Failed to register metadata for {profiler}: {e}")

    print("Registered Metadata Classes:", registered_metadata)

