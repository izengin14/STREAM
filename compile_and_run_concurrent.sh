#!/bin/bash
# Compile streammod1 and run concurrent benchmark
# Usage: ./compile_and_run_concurrent.sh [threads1] [threads2] [duration]

set -e

echo "============================================================"
echo "Compiling STREAM benchmark..."
echo "============================================================"

# Compile
gcc -fopenmp -O3 -o streammod1 streammod1.c

if [ $? -eq 0 ]; then
    echo "✓ Compilation successful"
    echo ""
    
    # Run concurrent benchmark
    THREADS1=${1:-4}
    THREADS2=${2:-4}
    DURATION=${3:-10}
    
    echo "Running concurrent benchmark..."
    echo "  Threads: $THREADS1 & $THREADS2"
    echo "  Duration: $DURATION seconds"
    echo ""
    
    ./run_concurrent_benchmark.sh $THREADS1 $THREADS2 $DURATION
else
    echo "✗ Compilation failed"
    exit 1
fi


