# Profilers Source

This directory provides developer guidelines for extending the **MemSysExplorer** framework by integrating new custom profilers. The repository supports modular extension through well-defined abstract interfaces and dynamic runtime registration.

## Key Components

To implement a new profiler, the following base interfaces are used:

1. **`FrontendInterface` Abstract Class**
   Acts as the execution core responsible for activating and managing profilers.

2. **`PatternConfig` Abstract Class**
   Provides a structured way to bridge raw profiler outputs to downstream modeling utilities.

3. **`BaseMetadata` Interface (optional)**
   Allows capturing hardware, runtime, and OS-level metadata alongside profile data.

> All profiler modules, pattern configurations, and metadata handlers should be placed under `profilers/` to ensure codebase consistency and maintainability.

---

## Adding Custom Profilers

To add support for a new profiler, subclass the following:

* `FrontendInterface` (defines profiling logic)
* `PatternConfig` (defines result processing or modeling)
* (Optional) `BaseMetadata` (extracts host/device information)

Once created, register your components using the dynamic registration mechanism described below.

---

## Dynamic Profiler Registration

Starting with v1.1, MemSysExplorer uses JSON-based dynamic registration to manage available profilers. The configuration file `built_profilers.json` indicates which profilers are active:

### Example: `built_profilers.json`

```json
{
  "ncu": true,
  "perf": true,
  "nvbit": true,
  "dynamorio": false,
  "sniper": true
}
```

Only entries set to `true` will be registered during runtime.

### Dynamic Registration Logic

```python
from profilers.FrontendInterface import FrontendInterface
from profilers.PatternConfig import PatternConfig
from profilers.BaseMetadata import BaseMetadata

def register_profilers():
    available_profilers = {
        "ncu": ("profilers.ncu.ncu_profilers", "NsightComputeProfilers"),
        ...
    }
    ...
    FrontendInterface.register_profiler("ncu", NsightComputeProfilers)

def register_PatternConfig():
    available_configs = {
        "ncu": ("profilers.ncu.ncu_PatternConfig", "NsightComputeConfig"),
        ...
    }
    ...
    PatternConfig.register_config("ncu", NsightComputeConfig)

def register_MetadataClasses():
    available_metadata = {
        "ncu": ("profilers.ncu.ncu_Metadata", "NsightMetadata"),
        ...
    }
    ...
    FrontendInterface.register_metadata("ncu", NsightMetadata)
```

---

## Directory Structure

Custom profilers should adhere to this file structure inside the `profilers/` directory:

```
profilers/
├── FrontendInterface.py
├── PatternConfig.py
├── BaseMetadata.py
├── registry.py
├── built_profilers.json
├── ncu/
│   ├── ncu_profilers.py
│   ├── ncu_PatternConfig.py
│   ├── ncu_Metadata.py
├── nvbit/
│   ├── nvbit_profilers.py
│   ├── nvbit_PatternConfig.py
│   ├── nvbit_Metadata.py
├── perf/
│   ├── perf_profilers.py
│   ├── perf_PatternConfig.py
│   ├── perf_Metadata.py
...
```

Each subdirectory should contain:

* `*_profilers.py` – Implements profiling logic.
* `*_PatternConfig.py` – Defines trace pattern extraction.
* `*_Metadata.py` – Captures system/hardware metadata.

---

## Further Reading

To begin implementing your first profiler, consult the `FrontendInterface Tutorial` in the documentation or view real examples in `profilers/ncu/`, `profilers/sniper/`, or `profilers/nvbit/`.

Happy profiling!
