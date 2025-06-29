# LeNet MNIST Fault Injection Example using msxFI

This directory contains a standalone example demonstrating how to use the `msxFI` framework to inject faults into a LeNet Convolutional Neural Network (CNN) trained on the MNIST dataset.

The main script for this example is `run_eval.py`.

## Objective

This example aims to:
1.  Showcase an end-to-end workflow: from a pre-trained model to a fault-injected model and its evaluation.
2.  Demonstrate how `msxFI` can be integrated into a typical DNN evaluation pipeline.
3.  Provide a practical use case for DNN fault injection with `msxFI`.

## Pre-requisite: Training the Model

Before running the fault injection experiment, you need a pre-trained LeNet model.
The model checkpoint is expected at `msxFI/example_nn/lenet/checkpoints/lenet.pth`.

If this pre-trained model is not available, you can train it by running the `train.py` script from within this directory:

```bash
# Navigate to the lenet example directory
cd path/to/your/workspace/msxFI/example_nn/lenet/

# Run the training script
python train.py
```
This script will train the LeNet model on the MNIST dataset (downloading it if necessary) and save the trained model checkpoint to the `checkpoints/` subdirectory.

## Running the Fault Injection and Evaluation Experiment

The `run_eval.py` script automates the process of:
1.  Invoking `msxFI` (specifically `run_msxfi.py` from the repository root) to inject faults into the weights of the pre-trained LeNet model based on specified fault injection parameters.
2.  Loading the original (fault-free) LeNet model.
3.  Loading the newly generated faulty LeNet model.
4.  Evaluating both models on the MNIST test dataset.
5.  Printing the accuracy of both the original and the faulty models.

**To run the experiment:**

Navigate to this example directory (`msxFI/example_nn/lenet/`) and execute the `run_eval.py` script:

```bash
# Ensure you are in the msxFI/example_nn/lenet/ directory
python run_eval.py
```

The script handles setting up the correct paths for `run_msxfi.py` and the model files, assuming you run it from its location within the `msxFI` project structure.

## Customizing Fault Injection Parameters

The fault injection parameters (such as memory `mode`, random `seed`, quantization settings like `int_bits` and `frac_bits`, `q_type`, and DRAM-specific parameters like `refresh_t` and `sigma`) are configured **directly within the `run_eval.py` script**.

To experiment with different fault scenarios:
1.  Open `msxFI/example_nn/lenet/run_eval.py`.
2.  Locate the `# --- Configuration ---` section near the beginning of the `main()` function.
3.  Modify the values of variables like `MODE`, `SEED`, `INT_BITS`, `FRAC_BITS`, `Q_TYPE`, `REFRESH_TIME`, etc., according to your requirements.
4.  Save the changes to `run_eval.py` and re-run the script as described above.

Refer to the main `msxFI` [README.md](../../README.md) for a comprehensive list and explanation of all available fault injection parameters.

## Expected Output

The `run_eval.py` script will:
- Print messages indicating the steps it's performing (generating faulty model, evaluating models).
- Show the command used to run `run_msxfi.py`.
- Output the accuracy of the original LeNet model.
- Output the accuracy of the fault-injected LeNet model.

The faulty model itself will be saved by `run_msxfi.py` in the `msxFI/example_nn/lenet/checkpoints/` directory, with a filename indicating the fault injection parameters used (e.g., `lenet_dram1t_s0_qafloat_i2_f4_rf80.0.pth`). 