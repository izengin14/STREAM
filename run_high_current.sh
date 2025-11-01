#!/bin/bash

# High Current Consumption Settings
export OMP_NUM_THREADS=4
export OMP_AFFINITY=1,2
export OMP_SCHEDULE=dynamic
export OMP_PROC_BIND=close
export OMP_DYNAMIC=false
export OMP_NESTED=false

echo "=== High Current STREAM Benchmark ==="
echo "Threads: $OMP_NUM_THREADS"
echo "Affinity: $OMP_AFFINITY (cores 1,2)"
echo "Array Size: 100M elements (~2.4GB memory)"
echo "====================================="

# Compile with maximum optimization
gcc -O3 -fopenmp -march=native -mtune=native -o streammod1 streammod1.c

# Run the benchmark
./streammod1

echo "Benchmark completed!"
