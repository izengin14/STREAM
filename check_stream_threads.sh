#!/bin/bash
# Check how many threads a running STREAM process is actually using

echo "Checking for running STREAM processes..."
echo ""

# Find STREAM processes
STREAM_PIDS=$(pgrep -f streammod)

if [ -z "$STREAM_PIDS" ]; then
    echo "No STREAM processes found running."
    echo ""
    echo "To check threads while STREAM runs:"
    echo "1. In one terminal: python3 run_stream_experiment.py 8 streammod1 30"
    echo "2. In another terminal: OMP_NUM_THREADS=8 ./seeThread"
    exit 0
fi

echo "Found STREAM process(es):"
for pid in $STREAM_PIDS; do
    echo "  PID: $pid"
    ps -p $pid -o pid,cmd,pcpu,pmem
    echo ""
done

echo "To see thread usage matching your experiment:"
echo "  OMP_NUM_THREADS=8 ./seeThread"
echo ""
echo "Note: seeThread shows its own OpenMP configuration."
echo "Set OMP_NUM_THREADS to match what you're using in the experiment."



