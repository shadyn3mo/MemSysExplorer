from profilers.PatternConfig import PatternConfig

class PerfConfig(PatternConfig):
    @classmethod 
    def populating(cls, report_data, metadata=None, level="custom"):
        """
        Populate the PatternConfig attributes using Perf raw data.

        Parameters
        ----------
        report_data : dict
            Dictionary containing raw event counts (e.g., cache hits, misses, memory IO).
        metadata : BaseMetadata, optional
            Optional system metadata.
        level : str
            Cache/memory level to focus on: "l1", "l2", "l3", or "dram".

        Returns
        -------
        PerfConfig
            An initialized config object containing read/write frequencies and totals.
        """
        l1_dcache_loads = report_data.get('l1_dcache_loads', 0)
        l1_dcache_load_misses = report_data.get('l1_dcache_load_misses', 0)
        l1_icache_loads = report_data.get('l1_icache_loads', 0)
        l1_icache_load_misses = report_data.get('l1_icache_load_misses', 0)
        l1_dcache_prefetches = report_data.get('l1_dcache_prefetches', 0)
        l1_icache_prefetches = report_data.get('l1_icache_prefetches', 0)
        l2_ic_dc_hit_in_l2 = report_data.get('l2_ic_dc_hit_in_l2', 0)
        l2_ic_dc_miss_in_l2 = report_data.get('l2_ic_dc_miss_in_l2', 0)
        l2_pf_miss_l2_hit_l3 = report_data.get('l2_pf_miss_l2_hit_l3', 0)
        l2_pf_miss_l2_l3 = report_data.get('l2_pf_miss_l2_l3', 0)
        l3_request_miss = report_data.get('l3_request_miss', 0)
        xi_ccx_sdp_req1 = report_data.get('xi_ccx_sdp_req1', 0)
        mem_io_local_dmnd = report_data.get('mem_io_local_dmnd', 0)
        mem_io_remote_dmnd = report_data.get('mem_io_remote_dmnd', 0)
        mem_io_remote_any = report_data.get('mem_io_remote_any', 0)
        mem_io_local_any = report_data.get('mem_io_local_any', 0)
        time_elapsed = report_data.get('time_elapsed', 0)

        read_freq = 0
        write_freq = 0
        total_reads=0,
        total_writes=0,
    
        # For L1 cache
        total_reads_d = 0
        total_reads_i = 0
        total_writes_d = 0
        total_writes_i = 0

        if level == "l1":
            total_reads_d = l1_dcache_loads + l1_dcache_load_misses
            total_reads_i = l1_icache_loads + l1_icache_load_misses
            total_reads = total_reads_d + total_reads_i

            total_writes_d = l1_dcache_load_misses + l1_dcache_prefetches
            total_writes_i = l1_icache_loads + l1_icache_prefetches
            total_writes = total_writes_d + total_writes_i

            read_freq = total_reads / time_elapsed if time_elapsed else 0
            write_freq = total_writes / time_elapsed if time_elapsed else 0

        elif level == "l2":
            total_reads = l2_ic_dc_hit_in_l2 + l2_ic_dc_miss_in_l2
            total_writes = l2_ic_dc_miss_in_l2 + l2_pf_miss_l2_hit_l3 + l2_pf_miss_l2_l3

            read_freq = total_reads / time_elapsed if time_elapsed else 0
            write_freq = total_writes / time_elapsed if time_elapsed else 0

        elif level == "l3":
            total_reads = l2_pf_miss_l2_hit_l3 + l2_pf_miss_l2_l3 + l3_request_miss
            total_writes = l2_pf_miss_l2_l3 + l3_request_miss + xi_ccx_sdp_req1

            read_freq = total_reads / time_elapsed if time_elapsed else 0
            write_freq = total_writes / time_elapsed if time_elapsed else 0

        elif level == "dram":
            total_reads = (
                mem_io_local_dmnd + mem_io_remote_dmnd +
                mem_io_remote_any + mem_io_local_any +
                l2_pf_miss_l2_l3 + l3_request_miss + xi_ccx_sdp_req1
            )
            total_writes = 0  # Not provided yet

            read_freq = total_reads / time_elapsed if time_elapsed else 0
            write_freq = total_writes / time_elapsed if time_elapsed else 0


        return cls(
            exp_name="PerfProfilers",
            benchmark_name=report_data.get("benchmark", " Benachmark1"),  # Updated key
            total_reads=total_reads,
            total_writes=total_writes,
            read_freq = read_freq,
            write_freq = write_freq,
            total_reads_d = total_reads_d,
            total_reads_i = total_reads_i, 
            total_writes_d = total_writes_d,
            total_writes_i = total_writes_i,
            read_size=32,  # Assuming 32 bytes per sector
            write_size=32,  # Assuming 32 bytes per sector
            metadata=metadata
        )
