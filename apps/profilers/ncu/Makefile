# Required Versions
REQUIRED_DRIVER_VERSION := 560
REQUIRED_CUDA_VERSION := 12

# Paths to setup scripts (referencing but not sourcing)
SETUP_ENV_SCRIPT := $(APPS_HOME)/tools/

.PHONY: check_nvidia check_cuda check_ncu check_all

# Check if an NVIDIA GPU is available and has a supported driver version
check_nvidia:
	@echo "Checking for NVIDIA GPU and driver version..."
	@if ! command -v nvidia-smi > /dev/null 2>&1; then \
		echo "Error: No NVIDIA GPU detected or NVIDIA drivers are not installed."; \
		echo "Please install the correct driver: https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/index.html"; \
		exit 1; \
	else \
		DRIVER_VERSION=$$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | cut -d. -f1); \
		if [ "$$DRIVER_VERSION" -lt "$(REQUIRED_DRIVER_VERSION)" ]; then \
			echo "Warning: Installed NVIDIA driver version $$DRIVER_VERSION is lower than required ($(REQUIRED_DRIVER_VERSION))."; \
			echo "Update the driver: https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/index.html"; \
			exit 1; \
		else \
			echo "NVIDIA driver version $$DRIVER_VERSION is valid (>= $(REQUIRED_DRIVER_VERSION))."; \
		fi; \
		nvidia-smi; \
	fi

# Check if CUDA is installed and version is at least 12.x
check_cuda:
	@echo "Checking for CUDA installation..."
	@if ! command -v nvcc > /dev/null 2>&1; then \
		echo "CUDA is not available!"; \
		echo "You may need to source: $(SETUP_ENV_SCRIPT) or $(SETUP_CUDA_SCRIPT)"; \
		echo "Or install CUDA: https://developer.nvidia.com/cuda-downloads"; \
		exit 1; \
	else \
		CUDA_VERSION=$$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]*\)\..*/\1/p'); \
		if [ "$$CUDA_VERSION" -lt "$(REQUIRED_CUDA_VERSION)" ]; then \
			echo "Warning: CUDA version $$CUDA_VERSION is lower than required ($(REQUIRED_CUDA_VERSION))."; \
			echo "Update CUDA: https://developer.nvidia.com/cuda-downloads"; \
			exit 1; \
		else \
			echo "CUDA version $$CUDA_VERSION is valid (>= $(REQUIRED_CUDA_VERSION))."; \
		fi; \
	fi


check_ncu:
	@echo "Checking for Nsight Compute (ncu)..."
	@if ! command -v ncu > /dev/null 2>&1; then \
		echo "Error: Nsight Compute is not found!"; \
		echo "You may need to source the setup script in $(SETUP_ENV_SCRIPT)"; \
		echo "Install Nsight Compute using the CUDA-Toolkit at: https://developer.nvidia.com/cuda-downloads and make sure it matches your driver capabilities"; \
		exit 1; \
	else \
		echo "Nsight Compute (ncu) is installed."; \
		ncu --version; \
	fi


# Check everything: NVIDIA GPU, CUDA, and Nsight Compute
check_all: check_nvidia check_cuda check_ncu
	@echo "System is ready for Nsight Compute Profilers."

