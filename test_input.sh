#!/bin/bash
# test_input.sh — run input.py through debug scenarios, log gmap.json after each

LOG="log.txt"
> "$LOG"

run() {
    echo "=== $1 ===" >> "$LOG"
    python3 input.py "$1"
    cat gmap.json >> "$LOG"
    echo "" >> "$LOG"
}

run "britomart"
run "britomart + ellerslie"
run "britomart + ellerslie 0900"
run "britomart + ellerslie 0900 MON"
run "britomart + ellerslie ARR 0900"
run "britomart + ellerslie ARR 0900 FRI"
run "britomart + ellerslie 0900 LAST"
run "ELZ"
run "ELZ + HOM"
run "MODE=BUS"
run "MODE=WLK"
run "CITY=Wellington"
run "CODE=WAI:ChIJsRdro_5HDW0RpFmy0CRiKRE"
