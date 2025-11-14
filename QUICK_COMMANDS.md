# Quick Commands for Concurrent Benchmarks

## 4 & 4 Threads

```bash
# Same cores (maximum contention)
./run_concurrent_benchmark.sh 4 4 10 "0-3" "0-3"

# Separate cores (no contention)
./run_concurrent_benchmark.sh 4 4 10 "0-3" "4-7"

# Overlapping cores (moderate contention)
./run_concurrent_benchmark.sh 4 4 10 "0-3" "2-5"
```

## 8 & 8 Threads

```bash
# Same cores (maximum contention)
./run_concurrent_benchmark.sh 8 8 10 "0-7" "0-7"

# Separate cores (no contention) - Note: requires 16 cores, use overlap if you have 12
./run_concurrent_benchmark.sh 8 8 10 "0-7" "4-11"

# Overlapping cores (moderate contention)
./run_concurrent_benchmark.sh 8 8 10 "0-7" "2-9"
```

## 12 & 12 Threads

```bash
# Same cores (maximum contention - all 12 cores)
./run_concurrent_benchmark.sh 12 12 10 "0-11" "0-11"

# Split cores (6 cores each)
./run_concurrent_benchmark.sh 12 12 10 "0-5" "6-11"

# Overlapping cores
./run_concurrent_benchmark.sh 12 12 10 "0-11" "4-11"
```

## 8 & 4 Threads

```bash
# 8 threads on first 8 cores, 4 threads on same first 4 (overlap)
./run_concurrent_benchmark.sh 8 4 10 "0-7" "0-3"

# 8 threads on first 8 cores, 4 threads on separate cores
./run_concurrent_benchmark.sh 8 4 10 "0-7" "8-11"

# 8 threads on first 8 cores, 4 threads overlapping
./run_concurrent_benchmark.sh 8 4 10 "0-7" "4-7"
```

## Other Configurations

```bash
# 6 & 6 threads
./run_concurrent_benchmark.sh 6 6 10 "0-5" "6-11"

# 4 & 8 threads
./run_concurrent_benchmark.sh 4 8 10 "0-3" "4-11"

# 6 & 4 threads
./run_concurrent_benchmark.sh 6 4 10 "0-5" "6-9"
```

## Notes

- Duration (3rd argument) can be changed: 10, 20, 30, 60 seconds, etc.
- CPU lists use ranges (0-3) or individual cores (0,2,4,6)
- Check available cores: `nproc` or `lscpu`
- For systems with 12 cores, 12&12 will always have overlap/contention


