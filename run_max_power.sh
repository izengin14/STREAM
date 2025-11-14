#!/bin/bash

# Maximum Power Consumption Settings
export OMP_NUM_THREADS=16
export OMP_AFFINITY=granularity=fine,compact
export OMP_SCHEDULE=dynamic
export OMP_PROC_BIND=close

echo "=== Maximum Power STREAM Benchmark ==="
echo "Threads: $OMP_NUM_THREADS"
echo "Affinity: $OMP_AFFINITY"
echo "Array Size: 500M elements (~12GB memory)"
echo "======================================"

# Compile with maximum optimization
gcc -O3 -fopenmp -march=native -mtune=native -o streammod1 streammod1.c

# Run the benchmark
./streammod1

echo "Benchmark completed!"



