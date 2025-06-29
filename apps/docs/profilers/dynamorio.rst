DynamoRIO Documentation
==============================

**DynamoRIO** is a dynamic binary instrumentation framework that inserts analysis code at runtime, allowing fine-grained monitoring of program execution.
It provides valuable insights into instruction-level behavior, memory access patterns, and control flow, enabling detailed performance and security analysis. 

The profiling workflow in MemSysExplorer consists of two core actions, as provided by the main interface:

1. **Profiling (`profiling`)** – Captures runtime execution metrics by specifying the required executable.
2. **Metric Extraction (`extract_metrics`)** – Analyzes generated reports to extract memory and performance-related metrics.

When using the `both` action, profiling and metric extraction are performed sequentially.

.. important::

   **MemSysExplorer GitHub Repository**

   Refer to the codebase for the latest update: https://github.com/lpentecost/MemSys-Playground/tree/gpu-app/apps/profilers/dynamorio

   To learn more about license terms and third-party attribution, refer to the :doc:`../licensing` page.


Required Arguments
------------------

To execute Nsight Profilers, specific arguments are required based on the chosen action. The necessary arguments are defined in the code as follows:
Perf can analyze three lavels of memory: l1, l2, and l3. The level of memory to be analyzed is specified using the `level` argument.

.. code-block:: python

    @classmethod
    def required_profiling_args(cls):
        """
        Return required arguments for the profiling method.
        """
        return ["executable"]

    @classmethod
    def required_extract_args(cls, action):
        """
        Return required arguments for the extract_metrics method.
        """
        if action == "extract_metrics":
            return ["report_file"]
        else:
            return []

Example Usage
-------------

Below are three examples of how to execute the profiling tool with different actions:

- **Profiling the application:**

  .. code-block:: bash

     python main.py --profiler dynamorio --action profiling  --executable ./executable 

- **Extracting metrics from an existing report:**

  .. code-block:: bash

     python main.py --profiler dynamorio --action extract_metrics --level l1 --report_file ./report_file.ncu-rep

- **Performing both profiling and metric extraction:**

  .. code-block:: bash

     python main.py --profiler dynamorio --action both --level l1 --executable ./executable

Sample Output
-------------

This profiler generates output traces that follow the standardized format defined by the MemSysExplorer Application Interface.


Additional Notes
----------------

- The **DynamoRIO** must be correctly installed and accessible via the system `PATH` variable.

Troubleshooting
---------------

If you encounter issues when building the DynamoRIO profiler:

- **Ensure that the environment has been set up properly** using:

  .. code-block:: tcsh

     source setup/setup.csh dynamorio

  or

  .. code-block:: bash

     source setup/setup.sh dynamorio

- **Verify that the correct GCC version is installed and exported** in your environment. The profiler expects a compatible GCC version as configured in your setup script (e.g., GCC 11.2.0).

- **Check for missing compiler paths**: Make sure `PATH`, `LD_LIBRARY_PATH`, `LIBRARY_PATH`, and `C_INCLUDE_PATH` are configured to include your GCC installation directories.

If problems persist, rebuild the profiler after re-sourcing your environment.

