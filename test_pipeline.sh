#!/bin/bash
# test_pipeline.sh — run full pipeline and log output.json after each query

LOG="pipeline_log.txt"
> "$LOG"

reset_state() {
    python3 -c "
import state
state.write('_START', None)
state.write('_DES', None)
state.write('_START_ID', None)
state.write('_DES_ID', None)
state.write('_MODE', 'TRN')
"
}

run() {
    echo "=== $1 ===" >> "$LOG"
    reset_state
    python3 input.py "$1"
    python3 resolver.py
    python3 directions.py
    python3 format.py
    cat output.json >> "$LOG"
    echo "" >> "$LOG"
}

# basic destination only — needs _START set first
python3 input.py "britomart + ellerslie"
python3 resolver.py

run "britomart"
run "britomart + ellerslie"
run "ELZ + HOM"
run "ELZ"
