/* ******************************************************************************
 * Copyright (c) 2011-2024 Google, Inc.  All rights reserved.
 * Copyright (c) 2010 Massachusetts Institute of Technology  All rights reserved.
 * ******************************************************************************/

/*
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of VMware, Inc. nor the names of its contributors may be
 *   used to endorse or promote products derived from this software without
 *   specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL VMWARE, INC. OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
 * DAMAGE.
 */

#include <stdio.h>
#include <string.h> /* for memset */
#include <stddef.h> /* for offsetof */
#include <stdint.h>
#include "dr_api.h"
#include "drmgr.h"
#include "drreg.h"
#include "drutil.h"
#include "drx.h"
#include "utils.h"

#define CACHE_LINE_SIZE 64
#define WORKING_SET_TABLE_SIZE 1048576  // 2^20 entries = ~8 MB

//File Settings
static file_t global_trace_file = INVALID_FILE;
static void *trace_file_mutex;
static bool enable_tracing = true;

//Sampling Settings
static bool sampling_enabled = false; 
static uint64 sampling_interval = 10; // sample every 100th memory reference
static uint64 global_ref_counter = 0;

//Working Set Settings
static uintptr_t working_set_table[WORKING_SET_TABLE_SIZE];
static void *working_set_mutex;
static uint64 start_time_ms = 0;
static uint64 end_time_ms = 0;

/* Each mem_ref_t includes the type of reference (read or write),
 * the address referenced, and the size of the reference.
 */ // FIXME: can this be shortened?
typedef struct _mem_ref_t {
    bool write;
    void *addr;
    size_t size;
    app_pc pc;
} mem_ref_t;

/* Max number of mem_ref a buffer can have */
#define MAX_NUM_MEM_REFS 8192
/* The size of memory buffer for holding mem_refs. When it fills up,
 * we dump data from the buffer to the file.
 */
#define MEM_BUF_SIZE (sizeof(mem_ref_t) * MAX_NUM_MEM_REFS)

/* thread private counter */
typedef struct {
    char *buf_ptr;
    char *buf_base;
    /* buf_end holds the negative value of real address of buffer end. */
    ptr_int_t buf_end;
    void *cache;
    uint64 num_refs;
    uint64 num_reads;
    uint64 num_writes;
    uint64 working_set;
} per_thread_t;

/* Cross-instrumentation-phase data. */
typedef struct {
    app_pc last_pc;
} instru_data_t;

static size_t page_size;
static client_id_t client_id;
static app_pc code_cache;
static void *mutex;            /* for multithread support */
static uint64 global_num_refs; /* keep a global memory reference count */
static uint64 global_num_reads;
static uint64 global_num_writes;
static uint64 global_working_set;
static int tls_index;

static void
event_exit(void);
static void
event_thread_init(void *drcontext);
static void
event_thread_exit(void *drcontext);
static dr_emit_flags_t
event_bb_app2app(void *drcontext, void *tag, instrlist_t *bb, bool for_trace,
                 bool translating);
static dr_emit_flags_t
event_bb_analysis(void *drcontext, void *tag, instrlist_t *bb, bool for_trace,
                  bool translating, void **user_data);
static dr_emit_flags_t
event_bb_insert(void *drcontext, void *tag, instrlist_t *bb, instr_t *instr,
                bool for_trace, bool translating, void *user_data);

static void
clean_call(void);
static void
memtrace(void *drcontext);
static void
code_cache_init(void);
static void
code_cache_exit(void);
static void
instrument_mem(void *drcontext, instrlist_t *ilist, instr_t *where, app_pc pc,
               instr_t *memref_instr, int pos, bool write);

DR_EXPORT void

dr_client_main(client_id_t id, int argc, const char *argv[])
{
   drreg_options_t ops = { sizeof(ops), 2, false};
    /* Specify priority relative to other instrumentation operations: */
    drmgr_priority_t priority = { sizeof(priority), /* size of struct */
                                  "memcount",       /* name of our operation */
                                  NULL, /* optional name of operation we should precede */
                                  NULL, /* optional name of operation we should follow */
                                  0 };  /* numeric priority */
    dr_set_client_name("Custom Client 'memcount'", NULL);
        page_size = dr_page_size();
    drmgr_init();
    drutil_init();
    client_id = id;
    mutex = dr_mutex_create();
    working_set_mutex = dr_mutex_create();
    memset(working_set_table, 0, sizeof(working_set_table));

    //start_time_ms = dr_get_milliseconds();
    dr_set_client_name("Custom Client 'memcount'", NULL);
    trace_file_mutex = dr_mutex_create();
    
    dr_register_exit_event(event_exit);
    if (!drmgr_register_thread_init_event(event_thread_init) ||
        !drmgr_register_thread_exit_event(event_thread_exit) ||
        !drmgr_register_bb_app2app_event(event_bb_app2app, &priority) ||
        !drmgr_register_bb_instrumentation_event(event_bb_analysis, event_bb_insert,
                                                 &priority) ||
        drreg_init(&ops) != DRREG_SUCCESS || !drx_init()) {
        /* something is wrong: can't continue */
        DR_ASSERT(false);
        return;
    }
    tls_index = drmgr_register_tls_field();
    DR_ASSERT(tls_index != -1);

    code_cache_init();
    /* make it easy to tell, by looking at log file, which client executed */
    dr_log(NULL, DR_LOG_ALL, 1, "Client 'countcalls' initializing\n");
    /* also give notification to stderr */
    if (dr_is_notify_on()) {
#    ifdef WINDOWS
        /* ask for best-effort printing to cmd window.  must be called at init. */
        dr_enable_console_printing();
#    endif
        dr_fprintf(STDERR, "Client memcount is running\n");
    }
}

static void 
event_exit()
{
    char msg[512];
    int len;

    end_time_ms = dr_get_milliseconds();

    uint64 elapsed_ms = end_time_ms - start_time_ms;

    len = dr_snprintf(msg, sizeof(msg) / sizeof(msg[0]),
                        "Instrumentation results:\n"
                        "  saw %llu memory references\n"
                        "  number of reads: %llu\n"
                        "  number of writes: %llu\n"
                        "  working set size: %llu\n"
			"  execution time: %llu ms\n",
                        global_num_refs, global_num_reads, global_num_writes, global_working_set, elapsed_ms);
    DR_ASSERT (len > 0);
    NULL_TERMINATE_BUFFER(msg);
    DISPLAY_STRING(msg);
    code_cache_exit();

    if (!drmgr_unregister_tls_field(tls_index) ||
    !drmgr_unregister_thread_init_event(event_thread_init) ||
    !drmgr_unregister_thread_exit_event(event_thread_exit) ||
    !drmgr_unregister_bb_insertion_event(event_bb_insert) ||
    drreg_exit() != DRREG_SUCCESS)
    DR_ASSERT(false);

    if (enable_tracing && global_trace_file != INVALID_FILE) {
	    dr_close_file(global_trace_file);
	    global_trace_file = INVALID_FILE;
    }

    dr_mutex_destroy(trace_file_mutex);
    dr_mutex_destroy(working_set_mutex);
    dr_mutex_destroy(mutex);
    drutil_exit();
    drmgr_exit();
    drx_exit();
}

#ifdef WINDOWS
#    define IF_WINDOWS(x) x
#else
#    define IF_WINDOWS(x) /* nothing */
#endif

static void
event_thread_init(void *drcontext)
{
    per_thread_t *data;

    /* allocate thread private data */
    data = dr_thread_alloc(drcontext, sizeof(per_thread_t));
    drmgr_set_tls_field(drcontext, tls_index, data);
    data->buf_base = dr_thread_alloc(drcontext, MEM_BUF_SIZE);
    data->buf_ptr = data->buf_base;
    /* set buf_end to be negative of address of buffer end for the lea later */
    data->buf_end = -(ptr_int_t)(data->buf_base + MEM_BUF_SIZE);
    data->num_refs = 0;
    data->num_reads = 0;
    data->num_writes = 0;
    data->working_set = 0;
    start_time_ms = dr_get_milliseconds();

    if (enable_tracing && global_trace_file == INVALID_FILE) {
	    dr_mutex_lock(trace_file_mutex);
	    if (global_trace_file == INVALID_FILE) { 
		    global_trace_file = dr_open_file("maap_trace.out", DR_FILE_WRITE_APPEND);
		    DR_ASSERT(global_trace_file != INVALID_FILE);
	    }    
	    dr_mutex_unlock(trace_file_mutex);
    }

    dr_log(drcontext, DR_LOG_ALL, 1, "memcount: set up for thread " TIDFMT "\n",
           dr_get_thread_id(drcontext));

}

static void 
event_thread_exit(void *drcontext) 
{
    per_thread_t *data;

    memtrace(drcontext);
    data = drmgr_get_tls_field(drcontext, tls_index);
    dr_mutex_lock(mutex);
    global_num_refs += data->num_refs;
    global_num_reads += data->num_reads;
    global_num_writes += data->num_writes; 
    global_working_set += data->working_set;
    dr_mutex_unlock(mutex);

    dr_thread_free(drcontext, data->buf_base, MEM_BUF_SIZE);
    dr_thread_free(drcontext, data, sizeof(per_thread_t));
}

/* we transform string loops into regular loops so we can more easily
 * monitor every memory reference they make
 */
static dr_emit_flags_t
event_bb_app2app(void *drcontext, void *tag, instrlist_t *bb, bool for_trace,
                 bool translating)
{
    if (!drutil_expand_rep_string(drcontext, bb)) {
        DR_ASSERT(false);
        /* in release build, carry on: we'll just miss per-iter refs */
    }
    if (!drx_expand_scatter_gather(drcontext, bb, NULL)) {
        DR_ASSERT(false);
    }
    return DR_EMIT_DEFAULT;
}

static dr_emit_flags_t
event_bb_analysis(void *drcontext, void *tag, instrlist_t *bb, bool for_trace,
                  bool translating, void **user_data)
{
    instru_data_t *data = (instru_data_t *)dr_thread_alloc(drcontext, sizeof(*data));
    data->last_pc = NULL;
    *user_data = (void *)data;
    return DR_EMIT_DEFAULT;
}

/* event_bb_insert calls instrument_mem to instrument every
 * application memory reference.
 */
static dr_emit_flags_t
event_bb_insert(void *drcontext, void *tag, instrlist_t *bb, instr_t *where,
                bool for_trace, bool translating, void *user_data)
{
    int i;
    instru_data_t *data = (instru_data_t *)user_data;
    /* Use the drmgr_orig_app_instr_* interface to properly handle our own use
     * of drutil_expand_rep_string() and drx_expand_scatter_gather() (as well
     * as another client/library emulating the instruction stream).
     */
    instr_t *instr_fetch = drmgr_orig_app_instr_for_fetch(drcontext);
    if (instr_fetch != NULL)
        data->last_pc = instr_get_app_pc(instr_fetch);
    app_pc last_pc = data->last_pc;
    if (drmgr_is_last_instr(drcontext, where))
        dr_thread_free(drcontext, data, sizeof(*data));

    instr_t *instr_operands = drmgr_orig_app_instr_for_operands(drcontext);
    if (instr_operands == NULL ||
        (!instr_writes_memory(instr_operands) && !instr_reads_memory(instr_operands)))
        return DR_EMIT_DEFAULT;
    DR_ASSERT(instr_is_app(instr_operands));
    DR_ASSERT(last_pc != NULL);

    if (instr_reads_memory(instr_operands)) {
        for (i = 0; i < instr_num_srcs(instr_operands); i++) {
            if (opnd_is_memory_reference(instr_get_src(instr_operands, i))) {
                instrument_mem(drcontext, bb, where, last_pc, instr_operands, i, false);
            }
        }
    }
    if (instr_writes_memory(instr_operands)) {
        for (i = 0; i < instr_num_dsts(instr_operands); i++) {
            if (opnd_is_memory_reference(instr_get_dst(instr_operands, i))) {
                instrument_mem(drcontext, bb, where, last_pc, instr_operands, i, true);
            }
        }
    }
    return DR_EMIT_DEFAULT;
}

static bool insert_line_addr(uintptr_t line_addr) {
    size_t idx = (line_addr >> 6) % WORKING_SET_TABLE_SIZE;

    for (size_t i = 0; i < WORKING_SET_TABLE_SIZE; i++) {
        size_t probe_idx = (idx + i) % WORKING_SET_TABLE_SIZE;

        if (working_set_table[probe_idx] == 0) {
            working_set_table[probe_idx] = line_addr;
            return true;  // new unique line
        } else if (working_set_table[probe_idx] == line_addr) {
            return false; // already seen
        }
    }
    return false;
}

static void 
memtrace(void *drcontext)
{
    per_thread_t *data = drmgr_get_tls_field(drcontext, tls_index);
    mem_ref_t *mem_ref = (mem_ref_t *)data->buf_base;
    int num_refs = (int)((mem_ref_t *)data->buf_ptr - mem_ref);
    int num_reads = 0;
    int num_writes = 0;
    
    dr_fprintf(STDERR, "Thread %d saw %d refs\n", dr_get_thread_id(drcontext), num_refs);
    dr_fprintf(STDERR, "Current global_working_set = %llu\n", global_working_set);

    thread_id_t tid = dr_get_thread_id(drcontext);

//    for (int i = 0; i < num_refs; i++) {
//	    uintptr_t addr = (uintptr_t)mem_ref->addr;    
//	    uintptr_t line_addr = addr & ~(CACHE_LINE_SIZE - 1); // align

//	    dr_mutex_lock(working_set_mutex);
//	    if (insert_line_addr(line_addr)) {
//		    global_working_set++;    
//	    }
//	    dr_mutex_unlock(working_set_mutex);
//	    if (mem_ref->write)
//		    num_writes++;
//	    else
//		    num_reads++;
//	    ++mem_ref;
//	    //   }


    uint64 timestamp = dr_get_milliseconds();

    for (int i = 0; i < num_refs; i++) {    
	    global_ref_counter++;
   
	    if (sampling_enabled && (global_ref_counter % sampling_interval != 0)) {        
		    ++mem_ref;
		    continue;    
	    }

	    uintptr_t addr = (uintptr_t)mem_ref->addr;
	    uintptr_t line_addr = addr & ~(CACHE_LINE_SIZE - 1); // align
	    
	    dr_mutex_lock(working_set_mutex);
	    if (insert_line_addr(line_addr)) {
		    global_working_set++;
	    }
    
	    dr_mutex_unlock(working_set_mutex);
	    if (mem_ref->write)
		    num_writes++;
	    else
		    num_reads++;
	    
	    char trace_line[128];
	    int len;
   
	    if (enable_tracing && global_trace_file != INVALID_FILE) {
		    len = dr_snprintf(trace_line, sizeof(trace_line),
                          "%llu,%p,%c,%zu,%d,%p\n",
                          timestamp,              // Timestamp
                          mem_ref->addr,          // Address
                          mem_ref->write ? 'W' : 'R',  // Access Type
                          mem_ref->size,          // Access Size
                          tid,                    // Thread ID
                          mem_ref->pc);           // Instruction PC  
		    if (len > 0)        
			    dr_write_file(global_trace_file, trace_line, len);
	    }

	    DR_ASSERT(len > 0);
	    dr_mutex_lock(trace_file_mutex);
	    dr_write_file(global_trace_file, trace_line, len);
	    dr_mutex_unlock(trace_file_mutex);
	    ++mem_ref;
    }

    memset(data->buf_base, 0, MEM_BUF_SIZE);
    data->num_refs += num_refs;
    data->num_reads += num_reads;
    data->num_writes += num_writes;
    data->buf_ptr = data->buf_base;
}

/* clean_call dumps the memory reference info to the log file */ // FIXME: may not be necessary
static void
clean_call(void)
{
    void *drcontext = dr_get_current_drcontext();
    memtrace(drcontext);
}

static void
code_cache_init(void)
{
    void *drcontext;
    instrlist_t *ilist;
    instr_t *where;
    byte *end;

    drcontext = dr_get_current_drcontext();
    code_cache =
        dr_nonheap_alloc(page_size, DR_MEMPROT_READ | DR_MEMPROT_WRITE | DR_MEMPROT_EXEC);
    ilist = instrlist_create(drcontext);
    /* The lean procedure simply performs a clean call, and then jumps back
     * to the DR code cache.
     */
    where = INSTR_CREATE_jmp_ind(drcontext, opnd_create_reg(DR_REG_XCX));
    instrlist_meta_append(ilist, where);
    /* clean call */
    dr_insert_clean_call(drcontext, ilist, where, (void *)clean_call, false, 0);
    /* Encodes the instructions into memory and then cleans up. */
    end = instrlist_encode(drcontext, ilist, code_cache, false);
    DR_ASSERT((size_t)(end - code_cache) < page_size);
    instrlist_clear_and_destroy(drcontext, ilist);
    /* set the memory as just +rx now */
    dr_memory_protect(code_cache, page_size, DR_MEMPROT_READ | DR_MEMPROT_EXEC);
}

static void
code_cache_exit(void)
{
    dr_nonheap_free(code_cache, page_size);
}

/*
 * instrument_mem is called whenever a memory reference is identified.
 * It inserts code before the memory reference to to fill the memory buffer
 * and jump to our own code cache to call the clean_call when the buffer is full.
 */
static void // FIXME: can this be simplified?
instrument_mem(void *drcontext, instrlist_t *ilist, instr_t *where, app_pc pc,
               instr_t *memref_instr, int pos, bool write)
{
    instr_t *instr, *call, *restore;
    opnd_t ref, opnd1, opnd2;
    reg_id_t reg1, reg2;
    drvector_t allowed;

    /* Steal two scratch registers.
     * reg2 must be ECX or RCX for jecxz.
     */
    drreg_init_and_fill_vector(&allowed, false);
    drreg_set_vector_entry(&allowed, DR_REG_XCX, true);
    if (drreg_reserve_register(drcontext, ilist, where, &allowed, &reg2) !=
            DRREG_SUCCESS ||
        drreg_reserve_register(drcontext, ilist, where, NULL, &reg1) != DRREG_SUCCESS) {
        DR_ASSERT(false); /* cannot recover */
        drvector_delete(&allowed);
        return;
    }
    drvector_delete(&allowed);

    if (write)
        ref = instr_get_dst(memref_instr, pos);
    else
        ref = instr_get_src(memref_instr, pos);

    /* use drutil to get mem address */
    drutil_insert_get_mem_addr(drcontext, ilist, where, ref, reg1, reg2);

    /* The following assembly performs the following instructions
     * buf_ptr->write = write;
     * buf_ptr->addr  = addr;
     * buf_ptr->size  = size;
     * buf_ptr->pc    = pc;
     * buf_ptr++;
     * if (buf_ptr >= buf_end_ptr)
     *    clean_call();
     */
    drmgr_insert_read_tls_field(drcontext, tls_index, ilist, where, reg2);
    opnd1 = opnd_create_reg(reg2);
    opnd2 = OPND_CREATE_MEMPTR(reg2, offsetof(per_thread_t, buf_ptr));
    instr = INSTR_CREATE_mov_ld(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    /* Move write/read to write field */
    opnd1 = OPND_CREATE_MEM32(reg2, offsetof(mem_ref_t, write));
    opnd2 = OPND_CREATE_INT32(write);
    instr = INSTR_CREATE_mov_imm(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    /* Store address in memory ref */
    opnd1 = OPND_CREATE_MEMPTR(reg2, offsetof(mem_ref_t, addr));
    opnd2 = opnd_create_reg(reg1);
    instr = INSTR_CREATE_mov_st(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    /* Store size in memory ref */
    opnd1 = OPND_CREATE_MEMPTR(reg2, offsetof(mem_ref_t, size));
    /* drutil_opnd_mem_size_in_bytes handles OP_enter */
    opnd2 = OPND_CREATE_INT32(drutil_opnd_mem_size_in_bytes(ref, memref_instr));
    instr = INSTR_CREATE_mov_st(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    /* Store pc in memory ref */
    /* For 64-bit, we can't use a 64-bit immediate so we split pc into two halves.
     * We could alternatively load it into reg1 and then store reg1.
     * We use a convenience routine that does the two-step store for us.
     */
    opnd1 = OPND_CREATE_MEMPTR(reg2, offsetof(mem_ref_t, pc));
    instrlist_insert_mov_immed_ptrsz(drcontext, (ptr_int_t)pc, opnd1, ilist, where, NULL,
                                     NULL);

    /* Increment reg value by pointer size using lea instr */
    opnd1 = opnd_create_reg(reg2);
    opnd2 = opnd_create_base_disp(reg2, DR_REG_NULL, 0, sizeof(mem_ref_t), OPSZ_lea);
    instr = INSTR_CREATE_lea(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    drmgr_insert_read_tls_field(drcontext, tls_index, ilist, where, reg1);
    opnd1 = OPND_CREATE_MEMPTR(reg1, offsetof(per_thread_t, buf_ptr));
    opnd2 = opnd_create_reg(reg2);
    instr = INSTR_CREATE_mov_st(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    /* we use lea + jecxz trick for better performance
     * lea and jecxz won't disturb the eflags, so we won't insert
     * code to save and restore application's eflags.
     */
    /* lea [reg2 - buf_end] => reg2 */
    opnd1 = opnd_create_reg(reg1);
    opnd2 = OPND_CREATE_MEMPTR(reg1, offsetof(per_thread_t, buf_end));
    instr = INSTR_CREATE_mov_ld(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);
    opnd1 = opnd_create_reg(reg2);
    opnd2 = opnd_create_base_disp(reg1, reg2, 1, 0, OPSZ_lea);
    instr = INSTR_CREATE_lea(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);

    /* jecxz call */
    call = INSTR_CREATE_label(drcontext);
    opnd1 = opnd_create_instr(call);
    instr = INSTR_CREATE_jecxz(drcontext, opnd1);
    instrlist_meta_preinsert(ilist, where, instr);

    /* jump restore to skip clean call */
    restore = INSTR_CREATE_label(drcontext);
    opnd1 = opnd_create_instr(restore);
    instr = INSTR_CREATE_jmp(drcontext, opnd1);
    instrlist_meta_preinsert(ilist, where, instr);

    /* clean call */
    /* We jump to lean procedure which performs full context switch and
     * clean call invocation. This is to reduce the code cache size.
     */
    instrlist_meta_preinsert(ilist, where, call);
    /* mov restore DR_REG_XCX */
    opnd1 = opnd_create_reg(reg2);
    /* this is the return address for jumping back from lean procedure */
    opnd2 = opnd_create_instr(restore);
    /* We could use instrlist_insert_mov_instr_addr(), but with a register
     * destination we know we can use a 64-bit immediate.
     */
    instr = INSTR_CREATE_mov_imm(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(ilist, where, instr);
    /* jmp code_cache */
    opnd1 = opnd_create_pc(code_cache);
    instr = INSTR_CREATE_jmp(drcontext, opnd1);
    instrlist_meta_preinsert(ilist, where, instr);

    /* Restore scratch registers */
    instrlist_meta_preinsert(ilist, where, restore);
    if (drreg_unreserve_register(drcontext, ilist, where, reg1) != DRREG_SUCCESS ||
        drreg_unreserve_register(drcontext, ilist, where, reg2) != DRREG_SUCCESS)
        DR_ASSERT(false);
}
