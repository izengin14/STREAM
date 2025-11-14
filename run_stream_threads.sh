#!/bin/bash
# Script to run STREAM benchmark with different thread counts
# Usage: ./run_stream_threads.sh [thread_count]
# Example: ./run_stream_threads.sh 8

THREADS="${1:-4}"  # Default to 4 threads if not specified

echo "=========================================="
echo "Running STREAM with $THREADS threads"
echo "=========================================="
echo ""

# Set thread count and run
export OMP_NUM_THREADS=$THREADS

# Create output filename with thread count
OUTPUT_BANDWIDTH="stream_bandwidth_${THREADS}threads.txt"
OUTPUT_TIMESTAMPS="stream_timestamps_${THREADS}threads.txt"

# Run the benchmark
./streammod1_bytebased

# Rename output files to include thread count
if [ -f stream_bandwidth.txt ]; then
    mv stream_bandwidth.txt "$OUTPUT_BANDWIDTH"
    echo "Bandwidth data saved to: $OUTPUT_BANDWIDTH"
fi

if [ -f stream_timestamps.txt ]; then
    mv stream_timestamps.txt "$OUTPUT_TIMESTAMPS"
    echo "Timestamps saved to: $OUTPUT_TIMESTAMPS"
fi

echo ""
echo "=========================================="
echo "Completed run with $THREADS threads"
echo "=========================================="


