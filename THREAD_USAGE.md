# Running STREAM with Different Thread Counts

## Quick Start

The STREAM benchmark automatically detects and uses the number of threads specified by the `OMP_NUM_THREADS` environment variable.

### Method 1: Set Environment Variable

Run with a specific number of threads:

```bash
# 4 threads
OMP_NUM_THREADS=4 ./streammod1_bytebased

# 8 threads
OMP_NUM_THREADS=8 ./streammod1_bytebased

# 12 threads
OMP_NUM_THREADS=12 ./streammod1_bytebased
```

### Method 2: Use Helper Scripts

**Run with a single thread count:**
```bash
./run_stream_threads.sh 8
```

**Run with multiple thread counts (4, 8, 12) and compare:**
```bash
./run_all_threads.sh 4 8 12
```

Or use default (4, 8, 12):
```bash
./run_all_threads.sh
```

## Output Files

The program automatically creates output files with thread count in the filename:

- `stream_bandwidth_4threads.txt` - Bandwidth data for 4 threads
- `stream_bandwidth_8threads.txt` - Bandwidth data for 8 threads
- `stream_bandwidth_12threads.txt` - Bandwidth data for 12 threads
- `stream_timestamps_4threads.txt` - Timestamps for 4 threads
- (and so on...)

## Comparing Results

To quickly compare average bandwidth across different thread counts:

```bash
grep "Average Bandwidth" stream_bandwidth_*threads.txt
```

## Notes

- The program defaults to 4 threads if `OMP_NUM_THREADS` is not set
- Maximum available threads depends on your CPU/core count
- Each run creates separate output files, so you can compare results from different thread configurations


