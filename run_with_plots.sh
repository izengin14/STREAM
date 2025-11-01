#!/bin/bash

# High Current Consumption Settings
export OMP_NUM_THREADS=4
export OMP_AFFINITY=1,2
export OMP_SCHEDULE=dynamic
export OMP_PROC_BIND=close
export OMP_DYNAMIC=false
export OMP_NESTED=false

echo "=== High Current STREAM Benchmark with Plots ==="
echo "Threads: $OMP_NUM_THREADS"
echo "Affinity: $OMP_AFFINITY (cores 1,2)"
echo "Array Size: 100M elements (~2.4GB memory)"
echo "================================================"

# Compile with maximum optimization
gcc -O3 -fopenmp -o streammod1 streammod1.c

# Run current monitoring in background with sudo
echo "Starting current monitoring..."
sudo python3 streamtime.py &
MONITOR_PID=$!

# Wait a moment for monitoring to start
sleep 2

# Run STREAM benchmark
echo "Starting STREAM benchmark..."
./streammod1

# Wait for monitoring to finish
wait $MONITOR_PID

echo "Benchmark and monitoring completed!"
echo "Check the following plot files:"
ls -la /home/izengin/Desktop/STREAM/*.png
