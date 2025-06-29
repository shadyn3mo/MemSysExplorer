import os
import sys
import argparse
import subprocess
import csv
import inspect

from profilers.FrontendInterface import FrontendInterface

class SniperProfilers(FrontendInterface):
    def __init__(self, **kwargs):
        """
        Initialize the SniperProfiler with configuration.

        Parameters
        ----------
        config : str
            Path to the Sniper configuration directory.
        level : str
            Cache level to extract metrics from (default: 'l3').
        executable : list
            List of strings for the target executable and its arguments.
        """
        super().__init__(**kwargs)
        self.config_path = self.config.get("config", "")  # Config path
        self.levels = self.config.get("level", "l3")       # Default to L3
        self.executable_cmd = " ".join(self.config.get("executable", []))
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.sniper_path = os.path.join(self.script_dir, "snipersim", "run-sniper")
        self.metrics = None

    def construct_command(self):
        """
        Construct the Sniper simulation command based on provided executable and config.

        Returns
        -------
        list
            Complete command list for subprocess execution.
        """
        command = [self.sniper_path]

        if self.config_path:
            command += ["-c", self.config_path]

        command.append("--")

        if isinstance(self.executable_cmd, str):
            command += self.executable_cmd.split()
        else:
            command += self.executable_cmd

        return command

    def profiling(self, **kwargs):
        """
        Run Sniper with the constructed command and user-defined config.

        Raises
        ------
        CalledProcessError
            If the subprocess call to Sniper fails.
        FileNotFoundError
            If Sniper executable is missing.
        """
        command = self.construct_command()
        try:
            print(f"Executing: {' '.join(command)}")
            subprocess.run(command, check=True, text=True, env=os.environ)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")
            raise
        except FileNotFoundError:
            print("Error: Sniper executable not found.")
            raise

    def extract_metrics(self, results_dir=".", level=None, **kwargs):
        """
        Run snipermem.py to extract memory stats and parse the CSV output.

        Parameters
        ----------
        results_dir : str, optional
            Path to Sniper output directory (default: ".").
        level : str, optional
            Cache/memory level to analyze (L1, L2, L3, dram). Overrides default level.

        Returns
        -------
        dict
            Dictionary mapping metric names to numeric values.

        Raises
        ------
        FileNotFoundError
            If `snipermem.py` or the expected output CSV is missing.
        CalledProcessError
            If snipermem.py execution fails.
        """
        stats_script = os.path.join(self.script_dir, "snipersim", "tools", "snipermem.py")
        csv_file = os.path.join(results_dir, "memsys_stats.out")

        # Override with provided level if available
        level = kwargs.get("level", self.levels)

        if not os.path.isfile(stats_script):
            raise FileNotFoundError(f"Stats extraction script not found: {stats_script}")

        # Build extraction command
        cmd = [sys.executable, stats_script, "-d", results_dir]
        if level:
            cmd += ["-l", level]

        try:
            print(f"Extracting memory stats from {results_dir} at level {level}")
            subprocess.run(cmd, check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Stats extraction failed with exit code {e.returncode}")
            raise

        if not os.path.isfile(csv_file):
            raise FileNotFoundError(f"Expected stats output not found: {csv_file}")

        metrics = {}
        with open(csv_file, mode="r", newline="") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    key = row[0].strip()
                    value = row[1].strip()
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    metrics[key] = value

        # --- Parse per-core time from sim.out ---
        sim_out_file = os.path.join(results_dir, "sim.out")
        core_times = []

        if os.path.isfile(sim_out_file):
            with open(sim_out_file, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.strip().startswith("Time (ns)"):
                        # This line contains core times
                        time_line = line.strip()
                        # Next line contains core values separated by '|' columns
                        value_line = lines[i+1].strip()
                        parts = [x.strip() for x in value_line.split("|")[1:]]  # Skip label column
                        core_times = [int(x) for x in parts if x.isdigit()]
                        break

        if not core_times:
            raise ValueError("Could not extract per-core execution times from sim.out.")

        metrics["core_time"] = core_times

        print("Extracted metrics keys:", metrics.keys())

        return metrics

    @classmethod
    def required_profiling_args(cls):
        """
        Define required arguments to perform profiling.

        Returns
        -------
        list of str
            Required argument names: ['config', 'executable']
        """
        return ["config", "executable"]

    @classmethod
    def required_extract_args(cls, action):
        """
        Define required arguments to extract metrics based on action.

        Parameters
        ----------
        action : str
            Either "extract_metrics" or "both".

        Returns
        -------
        list of str
            Required argument names: ['results_dir', 'level']
        """
        args = []
        if action in ["extract_metrics", "both"]:
            args.append("results_dir")  # default handled in code
            args.append("level")
        return args

