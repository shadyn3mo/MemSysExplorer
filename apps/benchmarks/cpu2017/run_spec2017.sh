#!/bin/bash

# -------- Configurable Paths --------
SPEC_ROOT="/r/tcal/archgroup/archtools/benchmarks/cpu2017"
MAIN_SCRIPT="/r/tcal/work/dnguye/projects/MemSys-Playground/apps/main.py"
CONFIG_PATH="/r/tcal/work/dnguye/projects/MemSys-Playground/apps/config/skylake.cfg"
CMD_DIR="./commands"
WORKDIR="./spec_runs"
FILTER_DIR="intrate"   # One of: intrate, intspeed, fprate, fpspeed
RUN_TYPE="refrate"     # One of: refrate, testrate, trainrate
mkdir -p "$WORKDIR"

CMD_TYPE=$(echo "$RUN_TYPE" | sed 's/rate//')  # refrate -> ref, etc.

# -------- Loop through .<CMD_TYPE>.cmd files --------
find "$CMD_DIR/$FILTER_DIR" -name "*.${CMD_TYPE}.cmd" | while read -r CMD_FILE; do
    CMD_NAME=$(basename "$CMD_FILE" .${CMD_TYPE}.cmd)
    echo -e "\n==> Processing $CMD_NAME (${RUN_TYPE})"

    BENCH_ID="${CMD_NAME}"
    BENCH_DIR="$SPEC_ROOT/benchspec/CPU/$BENCH_ID"
    EXE_DIR="$BENCH_DIR/exe"
    INPUT_DIR="$BENCH_DIR/data/${RUN_TYPE}/input"
    OUTPUT_DIR="$BENCH_DIR/data/${RUN_TYPE}/output"

    # Locate executable (assume only one)
    EXE_PATH=$(find "$EXE_DIR" -maxdepth 1 -type f -executable | head -n 1)
    [[ ! -x "$EXE_PATH" ]] && echo " Skipping $CMD_NAME: Executable not found" && continue
    EXE_BASENAME=$(basename "$EXE_PATH")

    # Setup run directory
    RUN_DIR="$WORKDIR/${BENCH_ID}.${RUN_TYPE}"
    mkdir -p "$RUN_DIR"
    cp "$EXE_PATH" "$RUN_DIR/"

    # Copy input files
    if [[ -d "$INPUT_DIR" ]]; then
        echo "  Copying inputs from: $INPUT_DIR"
        cp -r "$INPUT_DIR/"* "$RUN_DIR/" 2>/dev/null
    fi

    # Copy expected output files
    if [[ -d "$OUTPUT_DIR" ]]; then
        echo "  Copying golden outputs from: $OUTPUT_DIR"
        cp -r "$OUTPUT_DIR/"* "$RUN_DIR/" 2>/dev/null
    fi

    # Copy .out/.err references if present
    CMD_DIRNAME=$(dirname "$CMD_FILE")
    for ext in out err; do
        AUX_FILE="${CMD_DIRNAME}/${CMD_NAME}.${CMD_TYPE}.${ext}"
        [[ -f "$AUX_FILE" ]] && cp "$AUX_FILE" "$RUN_DIR/"
    done

    # ---------- Generate run script ----------
    RUN_SH="$RUN_DIR/${BENCH_ID}.${RUN_TYPE}.sh"
    echo "#!/bin/bash" > "$RUN_SH"
    echo "# Generated from $CMD_FILE" >> "$RUN_SH"
    echo "# Executable: $EXE_BASENAME" >> "$RUN_SH"
    echo "" >> "$RUN_SH"
    chmod +x "$RUN_SH"

    # Wrap each line with executable
    while IFS= read -r line || [[ -n "$line" ]]; do
        trimmed=$(echo "$line" | sed 's/^[ \t]*//;s/[ \t]*$//')
        [[ -z "$trimmed" ]] && continue
        echo "./$EXE_BASENAME $trimmed" >> "$RUN_SH"
    done < "$CMD_FILE"



    # Log the script
    cp "$RUN_SH" "$RUN_DIR/${BENCH_ID}.${RUN_TYPE}.sh.log"

    # Execute using the renamed script
    cd "$RUN_DIR"
    echo "   → Entering dir: $(pwd)"
    echo "   → Executing ${BENCH_ID}.${RUN_TYPE}.sh with Sniper..."

    python3 "$MAIN_SCRIPT" \
        -p sniper -a both --level l3 \
        --config "$CONFIG_PATH" --results_dir . --executable "./${BENCH_ID}.${RUN_TYPE}.sh"

    cd - > /dev/null
done
