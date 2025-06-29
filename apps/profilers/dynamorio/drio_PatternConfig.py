from profilers.PatternConfig import PatternConfig 

class DrioConfig(PatternConfig):
    @classmethod
    def populating(cls, report_data, metadata=None):
        """
        Populate the PatternConfig attributes using DynamoRIO raw data.

        Parameters
        ----------
        report_data : dict
            Dictionary of memory access metrics, typically returned from
            `DrioProfilers.extract_metrics()`. Expected keys include:
            - 'read_freq'
            - 'write_freq'
            - 'total_reads'
            - 'total_writes'
            - 'workingset_size'
            - 'Memory' (used as the benchmark name)

        metadata : BaseMetadata, optional
            Optional system metadata object (e.g., CPU, cache, DRAM info).

        Returns
        -------
        DrioConfig
            A fully populated configuration object for downstream modeling.
        """

         # Unit overrides for this config
        unit_overrides = {
            "read_freq": "ratio",
            "write_freq": "ratio",
            "total_reads": "count",
            "total_write": "count",
            "workingset_size": "count"
        }


        return cls(
            exp_name="DynamoRIOProfilers",
            benchmark_name=report_data.get("Memory", " "),
            read_freq=report_data.get("read_freq"),
            total_reads=report_data.get("total_reads"),
            write_freq=report_data.get("write_freq"),
            total_writes=report_data.get("total_writes"),
            workingset_size=report_data.get("workingset_size"),
            read_size=32,  # Assuming 32 bytes as default
            write_size=32,  # Assuming 32 bytes as default
            metadata=metadata,
            unit=unit_overrides
        )



