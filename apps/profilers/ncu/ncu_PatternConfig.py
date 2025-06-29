from profilers.PatternConfig import PatternConfig

class NsightComputeConfig(PatternConfig):
    @classmethod
    def populating(cls, report_data, metadata=None, level="custom"):
        """
        Populate the PatternConfig attributes using Nsight Compute raw data.

        Parameters
        ----------
        report_data : dict
            Parsed metric data extracted from Nsight Compute JSON or CSV.
        metadata : BaseMetadata, optional
            Optional metadata about system configuration.
        level : str
            Target memory level to extract metrics for. One of:
                - "l2": for L2 cache metrics
                - "dram": for DRAM-level metrics
                - "custom": fallback/default if not targeting specific level

        Returns
        -------
        NsightComputeConfig
            An instance of the config with fields filled from profiler data.
        """

        if not report_data:
            print("Error: No valid report data received in PatternConfig.")
            return None

        # Ensure level is valid
        if level not in ["l2", "dram", "custom"]:
            print(f"Warning: Invalid level '{level}' provided. Defaulting to 'custom'.")
            level = "custom"

        print(f"Populating PatternConfig for level: {level}")

        kernel_name = report_data.get("Kernel", "Unknown Kernel")

        execution_time = report_data.get("gpu__time_active.sum", 0) / 1e9

        # ------------------- L2 Metrics -------------------
        l2_read_sectors = report_data.get("lts__t_requests_op_read.sum", 0)
        l2_write_sectors = report_data.get("lts__t_requests_op_write.sum", 0)
        l2_atomic_alu_sectors = report_data.get("lts__t_requests_op_atom_dot_alu.sum", 0)
        l2_atomic_cas_sectors = report_data.get("lts__t_requests_op_atom_dot_cas.sum", 0)
        l2_reduction_sectors = report_data.get("lts__t_requests_op_red.sum", 0)

        #l2_read_throughput = report_data.get("lts__t_sectors_op_read.sum.per_second", 0)
        #l2_write_throughput = report_data.get("lts__t_sectors_op_write.sum.per_second", 0)
        #l2_atomic_alu_throughput = report_data.get("lts__t_sectors_op_atom_dot_alu.sum.per_second", 0)
        #l2_atomic_cas_throughput = report_data.get("lts__t_sectors_op_atom_dot_cas.sum.per_second", 0)
        #l2_reduction_throughput = report_data.get("lts__t_sectors_op_red.sum.per_second", 0)

        total_mio_sectors_accessed = report_data.get("lts__t_sectors.sum", 0)

        # ------------------- DRAM Metrics -------------------
        dram_read_bytes = report_data.get("dram__sectors_read.sum", 0)
        dram_write_bytes = report_data.get("dram__sectors_write.sum", 0)
        dram_workingset = report_data.get("dram__sectors.sum", 0) 
        dram_active_write = report_data.get("dram__cycles_active_read.sum",0)
        dram_active_read = report_data.get("dram__cycles_active_write.sum",0)


        # ------------------- Compute Read/Write Frequencies -------------------
        read_freq = 0
        write_freq = 0
        total_reads = 0
        total_writes = 0
        workingset_size = 0

        if level == "l2":
            total_reads = l2_read_sectors + l2_atomic_cas_sectors + l2_atomic_alu_sectors + l2_reduction_sectors
            total_writes = l2_write_sectors + l2_atomic_cas_sectors + l2_atomic_alu_sectors + l2_reduction_sectors

            read_freq = (l2_read_sectors + l2_atomic_cas_sectors + l2_atomic_alu_sectors + l2_reduction_sectors) / execution_time
            write_freq = (l2_write_sectors + l2_atomic_cas_sectors + l2_atomic_alu_sectors + l2_reduction_sectors) /execution_time

            workingset_size = total_mio_sectors_accessed  # Convert sectors to bytes

        ##TODO - NEED TO FIX THIS FORMULA
        elif level == "dram":
            read_freq = dram_read_bytes / dram_active_read if dram_active_read != 0 else 0
            write_freq = dram_write_bytes / dram_active_write if dram_active_write != 0 else 0

            total_reads = dram_read_bytes  # Convert bytes to sectors
            total_writes = dram_write_bytes

            workingset_size = dram_workingset  # DRAM total footprint

        return cls(
            exp_name="NsightComputeProfilers",
            benchmark_name=kernel_name,
            read_freq=read_freq,
            total_reads=total_reads,
            write_freq=write_freq,
            total_writes=total_writes,
            workingset_size=workingset_size,
            read_size=32,  # Assuming 32 bytes per sector
            write_size=32,  # Assuming 32 bytes per sector
            metadata=metadata
        )

