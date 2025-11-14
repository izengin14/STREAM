#!/bin/bash
# Script to run STREAM benchmark with multiple thread counts and compare results
# Usage: ./run_all_threads.sh [thread_counts...]
# Example: ./run_all_threads.sh 4 8 12

# Default thread counts if none specified
THREAD_COUNTS="${@:-4 8 12}"

echo "=========================================="
echo "STREAM Benchmark - Multiple Thread Counts"
echo "=========================================="
echo ""

for THREADS in $THREAD_COUNTS; do
    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "Running with $THREADS threads..."
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo ""
    
    export OMP_NUM_THREADS=$THREADS
    ./streammod1_bytebased
    
    echo ""
    echo "----------------------------------------"
done

echo ""
echo "=========================================="
echo "All runs completed!"
echo "=========================================="
echo ""
echo "Output files created:"
ls -lh stream_bandwidth_*threads.txt stream_timestamps_*threads.txt 2>/dev/null | tail -20
echo ""
echo "To compare bandwidth results:"
echo "  grep 'Average Bandwidth' stream_bandwidth_*threads.txt"


