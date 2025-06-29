## Setting Up the Environment

MemSysExplorer provides shell-specific setup scripts to configure the required environment variables for each supported profiler. These scripts initialize toolchain paths, library paths, and compiler includes necessary for running and building different frontend tools.

Depending on your shell, use the appropriate setup script below.

### Using `tcsh` or `csh`

```tcsh
source setup/_setup.csh <option>
```

Available options:

* `1` or `dynamorio` – Sets up the GCC environment for building DynamoRIO-based tools.
* `2` or `cuda` – Sets up the CUDA and Nsight Compute environment.
* `3` or `sniper` – Sets up the environment for the Sniper simulator and Python integration.

Example:

```tcsh
source setup/setup.csh cuda
```

### Using `bash` or `sh`

```bash
source setup/setup.sh <option>
```

The available options are the same:

* `1` or `dynamorio`
* `2` or `cuda`
* `3` or `sniper`

Example:

```bash
source setup/setup.sh sniper
```

### Environment Summary

These scripts ensure that all necessary toolchains and runtime paths are correctly configured for MemSysExplorer's frontend profiling infrastructure. While you are free to configure your own environment manually, these scripts provide a reliable reference for the core variables required to run the profilers effectively.


