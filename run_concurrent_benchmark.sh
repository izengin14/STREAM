#!/bin/bash
# Script to run two concurrent STREAM benchmark instances
# Usage: ./run_concurrent_benchmark.sh <threads1> <threads2> [duration] [cpu_list1] [cpu_list2]
# Example: ./run_concurrent_benchmark.sh 4 4 10 "0-3" "4-7"

set -e

# Get arguments
THREADS1=${1:-4}
THREADS2=${2:-4}
DURATION=${3:-10}

# CPU core assignment (default: auto-assign, or custom if provided)
if [ -n "$4" ] && [ -n "$5" ]; then
    # Custom CPU lists provided
    CPU_LIST1=$4
    CPU_LIST2=$5
else
    # Auto-assign: first instance gets first N cores, second gets next N cores
    CPU_LIST1="0-$((THREADS1-1))"
    CPU_LIST2="$THREADS1-$((THREADS1+THREADS2-1))"
fi

# Check if streammod1 exists
if [ ! -f "./streammod1" ]; then
    echo "Error: streammod1 not found. Please compile it first with:"
    echo "  gcc -fopenmp -O3 -o streammod1 streammod1.c"
    exit 1
fi

echo "============================================================"
echo "CONCURRENT STREAM BENCHMARK"
echo "============================================================"
echo "Instance 1: $THREADS1 threads on CPUs $CPU_LIST1"
echo "Instance 2: $THREADS2 threads on CPUs $CPU_LIST2"
echo "Duration: $DURATION seconds"
echo "============================================================"
echo ""

# Create temporary output files
OUTPUT1=$(mktemp)
OUTPUT2=$(mktemp)
RESULTS1=$(mktemp)
RESULTS2=$(mktemp)

# Function to parse bandwidth from output
parse_bandwidth() {
    local output_file=$1
    grep -E "BANDWIDTH:|GiB/s|GB/s|MB/s" "$output_file" | tail -3
}

# Function to extract bandwidth value
extract_bandwidth_gib() {
    local output_file=$1
    grep "GiB/s" "$output_file" | awk '{print $1}'
}

# Run first instance in background
echo "[Instance 1] Starting: $THREADS1 threads on CPUs $CPU_LIST1"
(
    OMP_NUM_THREADS=$THREADS1 taskset -c $CPU_LIST1 ./streammod1 $DURATION > "$OUTPUT1" 2>&1
    echo "[Instance 1] Completed" >> "$RESULTS1"
    parse_bandwidth "$OUTPUT1" >> "$RESULTS1"
) &
PID1=$!

# Run second instance in background
echo "[Instance 2] Starting: $THREADS2 threads on CPUs $CPU_LIST2"
(
    OMP_NUM_THREADS=$THREADS2 taskset -c $CPU_LIST2 ./streammod1 $DURATION > "$OUTPUT2" 2>&1
    echo "[Instance 2] Completed" >> "$RESULTS2"
    parse_bandwidth "$OUTPUT2" >> "$RESULTS2"
) &
PID2=$!

# Wait for both to complete
echo "Waiting for both instances to complete..."
wait $PID1
wait $PID2

echo ""
echo "============================================================"
echo "RESULTS"
echo "============================================================"
echo ""

# Display results
echo "--- Instance 1 ($THREADS1 threads on CPUs $CPU_LIST1) ---"
cat "$RESULTS1"
echo ""

echo "--- Instance 2 ($THREADS2 threads on CPUs $CPU_LIST2) ---"
cat "$RESULTS2"
echo ""

# Calculate combined bandwidth
BANDWIDTH1=$(extract_bandwidth_gib "$OUTPUT1")
BANDWIDTH2=$(extract_bandwidth_gib "$OUTPUT2")

if [ -n "$BANDWIDTH1" ] && [ -n "$BANDWIDTH2" ]; then
    # Use awk for floating point addition
    COMBINED=$(echo "$BANDWIDTH1 $BANDWIDTH2" | awk '{printf "%.2f", $1 + $2}')
    echo "--- Combined Bandwidth ---"
    echo "  Instance 1: ${BANDWIDTH1} GiB/s"
    echo "  Instance 2: ${BANDWIDTH2} GiB/s"
    echo "  Total: ${COMBINED} GiB/s"
    echo ""
    
    # Calculate percentage
    PERC1=$(echo "$BANDWIDTH1 $COMBINED" | awk '{printf "%.1f", ($1/$2)*100}')
    PERC2=$(echo "$BANDWIDTH2 $COMBINED" | awk '{printf "%.1f", ($1/$2)*100}')
    echo "  Instance 1: ${PERC1}%"
    echo "  Instance 2: ${PERC2}%"
fi

echo "============================================================"

# Cleanup
rm -f "$OUTPUT1" "$OUTPUT2" "$RESULTS1" "$RESULTS2"

