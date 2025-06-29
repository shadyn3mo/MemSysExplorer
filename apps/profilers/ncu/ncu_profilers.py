import subprocess
import os
import json
from configparser import ConfigParser
from profilers.FrontendInterface import FrontendInterface
from profilers.ncu.ncu_parsing import parse_ncu_report
from profilers.ncu.ncu_Metadata import NsightMetadata

class NsightComputeProfilers(FrontendInterface):
    def __init__(self, **kwargs):
        """
        Initialize the profiler interface for Nsight Compute.

        Parameters
        ----------
        executable : list
            Command to run the kernel executable.
        level : str
            Profiling level ("l2", "dram", "custom").
        """
        super().__init__(**kwargs)
        self.executable_cmd = " ".join(self.config.get("executable", []))
        self.action = self.config.get("action")
        self.level = self.config.get("level", "custom")  # Default to custom if not provided
        self.metadata = NsightMetadata()

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.configs_dir = os.path.join(self.script_dir, "configs")  # Store configs in "configs/"
        self.sections_dir = os.path.join(self.script_dir, "sections")  # Store sections in "sections/"

        # Ensure both "configs/" and "sections/" directories exist
        os.makedirs(self.configs_dir, exist_ok=True)
        os.makedirs(self.sections_dir, exist_ok=True)

        # Mapping levels to their respective config files
        self.settings_files = {
            "l2": "l2_settings.conf",
            "dram": "dram_settings.conf",
            "custom": "custom_settings.conf"
        }
        self.config_file = os.path.join(self.configs_dir, self.settings_files.get(self.level, "custom_settings.conf"))

        self.report = None
        self.data = {}
        self.metrics = None

    def validate_paths(self):
        """
        Ensure the executable and configuration paths are valid.
        Raises informative errors if prerequisites are missing.
        """
        if not self.executable_cmd:
            raise ValueError("Executable path is required.")

        # Extract the actual executable path (first part of the command)
        executable = self.executable_cmd.split()[0]
        if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
            raise FileNotFoundError(f"'{self.executable_cmd}' is not valid or not executable.")

        if not os.path.isdir(self.configs_dir):
            raise FileNotFoundError(f"Configuration folder '{self.configs_dir}' does not exist.")
        
        if not os.path.isdir(self.sections_dir):
            raise FileNotFoundError(f"Sections folder '{self.sections_dir}' does not exist.")

        if not os.path.isfile(self.config_file):
            print(f"Configuration file '{self.config_file}' for level '{self.level}' does not exist.")
            self.create_config_file()

    def create_config_file(self):
        """
        Generate a default `.conf` settings file based on the selected level.

        Writes predefined metric mappings for L2, DRAM, or custom settings.
        """

        default_metrics = {
            "l2": {
                "L2 Cache Hit Rate": "lts__t_sectors_hit_rate.pct",
                "L2 Cache Miss Rate": "lts__t_sectors_miss_rate.pct",
            },
            "dram": {
                "DRAM Reads": "dram__bytes_read.sum",
                "DRAM Writes": "dram__bytes_write.sum",
            },
            "custom": {
                "Total MIO Requests": "lts__t_requests.sum",
                "Total MIO Sectors Accessed": "lts__t_sectors.sum",
                "Total Read Requested": "lts__t_requests_op_read.sum",
                "Total Write Requested": "lts__t_requests_op_write.sum",
            }
        }

        metrics_to_use = default_metrics.get(self.level, default_metrics["l2"])

        parser = ConfigParser()
        parser.add_section("Metrics")
        for label, name in metrics_to_use.items():
            parser.set("Metrics", label, name)

        with open(self.config_file, "w") as config_file:
            parser.write(config_file)

        print(f"Default settings file for {self.level} created at: {self.config_file}")

    def load_metrics(self):
        """
        Load metric labels and names from the level-specific `.conf` file.

        Returns
        -------
        list of dict
            List of metric dictionaries with 'label' and 'name'.
        """
        parser = ConfigParser()
        parser.read(self.config_file)
        metrics = []

        if "Metrics" in parser.sections():
            for key in parser.options("Metrics"):
                metrics.append({
                    "label": key,
                    "name": parser.get("Metrics", key)
                })

        if not metrics:
            raise ValueError(f"No metrics found in {self.config_file}.")

        return metrics

    def create_section_file(self, section_name="NsightComputeSection"):
        """
        Generate a `.section` file that tells Nsight Compute what to measure.

        Parameters
        ----------
        section_name : str
            Identifier for the section file to be generated.

        Returns
        -------
        str
            Section name (identifier).
        """
        filepath = os.path.join(self.sections_dir, f"{section_name}.section")

        # Static header details
        lines = [
            f'Identifier: "{section_name}"',
            'DisplayName: "Custom Section for generating metrics"',
            f'Description: "This section collects metrics from {self.config_file}"',
            "Header {",
        ]

        # Add metrics from the selected configuration file
        for metric in self.metrics:
            lines.append("  Metrics {")
            lines.append(f'    Label: "{metric["label"]}"')
            lines.append(f'    Name: "{metric["name"]}"')
            lines.append("  }")

        # Close the header
        lines.append("}")

        # Write the section file in the "sections/" folder
        with open(filepath, "w") as section_file:
            section_file.write("\n".join(lines) + "\n")

        print(f"Section file created: {filepath}")

        return section_name

    def construct_command(self):
        """
        Build the `ncu` command-line for profiling the given executable.

        Returns
        -------
        tuple
            - List of command-line arguments to run.
            - Report name (str) to be parsed later.
        """
        report = os.path.splitext(os.path.basename(self.executable_cmd.split()[0]))[0]
        section_name = self.create_section_file()
        print(section_name)
        executable_with_args = self.executable_cmd.split()  # Split executable and arguments into list
        ncu_command = [
            "ncu",
            "-f",
            "--replay-mode", "application",
            "--section-folder", self.sections_dir,  # Use the sections folder
            "--section", section_name,
            "--launch-count", "100",
            "--cache-control", "all",
            "--clock-control", "base",
            "--profile-from-start", "1",
            "-o", report,
        ] + executable_with_args  # Append executable and arguments separately
        
        return ncu_command, report

    def profiling(self, **kwargs):
        """
        Execute Nsight Compute profiler and generate `.ncu-rep` report file.
        """
        # Load metrics only when profiling starts
        self.validate_paths()
        
        if self.metrics is None:
            self.metrics = self.load_metrics()

        ncu_command, report = self.construct_command()
        try:
            print(f"Executing: {' '.join(ncu_command)}")
            subprocess.run(ncu_command, check=True, text=True)
            self.report = report + ".ncu-rep"
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")
            raise
        except FileNotFoundError:
            print("Error: ncu command not found. Make sure Nsight Compute is installed and available.")
            raise

    def extract_metrics(self, report_file=None, **kwargs):
        """
        Extract memory metrics from the `.ncu-rep` report file.

        Parameters
        ----------
        report_file : str, optional
            Path to a `.ncu-rep` file. If not given, uses self.report.

        Returns
        -------
        dict
            Parsed metric results.
        """
        # Logic to determine which report file to use
        if self.action == "extract_metrics":
            # Use user-provided report_file or raise an error if not provided
            if not report_file:
                raise ValueError("Report file is required for 'extract_metrics' action.")
            report_to_use = report_file
        else:
            # Use self.report for combined profiling and metrics extraction
            report_to_use = self.report
            if not report_to_use:
                raise RuntimeError("No profiling report available. Run profiling first or provide a report file.")

        # Parse the report file
        try:
            print(f"Parsing report: {report_to_use}")
            self.metrics = self.load_metrics()
            self.data = parse_ncu_report(report_to_use, self.metrics)
            return self.data
        
        except Exception as e:
            print(f"Error extracting metrics: {e}")
            raise

    def extract_metadata(self):
        """
        Parses the NCU report, extracts metrics, saves results to CSV, and returns structured data for PatternConfig.
    
        :param report_file: Path to the NCU report file.
        :param metrics: List of metrics to extract (each metric is a dictionary with 'label' and 'name').
        :param output_file: Path to the CSV file to store results.
        :return: List of extracted metrics structured for PatternConfig.
        """
        print(json.dumps(self.metadata.to_dict(), indent=2))

    @classmethod
    def required_profiling_args(cls):
        """
        Return the arguments required for the profiling interface.

        Returns
        -------
        list
            ["executable", "level"]
        """
        return ["executable", "level"]

    @classmethod
    def required_extract_args(cls, action):
        """
        Return the required arguments for metrics extraction.

        Parameters
        ----------
        action : str
            Profiling action type ("extract_metrics" or "both").

        Returns
        -------
        list
            List of required arguments.
        """
        if action == "extract_metrics":
            return ["report_file"]
        else:
            return []

