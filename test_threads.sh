#!/bin/bash
echo "=== Test 1: 4 threads on cores 1-4 ==="
OMP_NUM_THREADS=4 taskset -c 1-4 ./streammod1 2>&1 | head -3
echo ""
echo "=== Test 2: 12 threads on cores 1-4 ==="  
OMP_NUM_THREADS=12 taskset -c 1-4 ./streammod1 2>&1 | head -3
