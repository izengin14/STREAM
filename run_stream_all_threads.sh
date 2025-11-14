#!/bin/bash
# Script to run STREAM benchmark with all available threads

# Get number of CPU cores
NUM_CORES=$(nproc)

echo "========================================="
echo "STREAM Benchmark - All Threads"
echo "========================================="
echo "CPU cores available: $NUM_CORES"
echo "Setting OMP_NUM_THREADS=$NUM_CORES"
echo ""

# Set OpenMP environment variables
export OMP_NUM_THREADS=$NUM_CORES
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# Run the benchmark
echo "Starting benchmark..."
echo ""
./streammod1

echo ""
echo "========================================="
echo "Benchmark completed!"
echo "========================================="


