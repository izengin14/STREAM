# STREAM Memory Contention Experiment Suite

This experiment suite studies memory contention effects on bandwidth and energy efficiency using the STREAM benchmark.

## Experiment Design

### 1. Single Instance Experiments
- Run STREAM with 4, 8, and 12 threads
- Pin threads to same cores (e.g., cores 1-4)
- Measure: total bytes copied, execution time, VDDQ power consumption

### 2. Contention Experiments
- Run single STREAM instance (baseline)
- Run two concurrent STREAM instances (contention)
- Compare: bandwidth drop, energy per byte changes

### 3. Metrics Calculated
- **Bandwidth**: total bytes / execution time (MB/s)
- **Energy per byte**: total energy / total bytes (nJ/byte)
- **Contention impact**: bandwidth drop % and energy efficiency changes

## Files

### Experiment Scripts
- `run_stream_experiment.py` - Run single STREAM instance with CPU affinity
- `run_concurrent_experiment.py` - Run two concurrent STREAM instances
- `run_full_experiment.py` - Run complete experiment suite (all thread counts)
- `analyze_experiments.py` - Analyze and compare single vs concurrent results

### Usage

#### Run Single Experiment
```bash
# Run STREAM with 4 threads on CPUs 1-4, monitor for 60 seconds
python3 run_stream_experiment.py 4 1-4 streammod1 60

# Run with 8 threads
python3 run_stream_experiment.py 8 1-4 streammod1 60

# Run with 12 threads
python3 run_stream_experiment.py 12 1-4 streammod1 60
```

#### Run Concurrent Experiment
```bash
# Run two concurrent instances, each with 4 threads on CPUs 1-4
python3 run_concurrent_experiment.py 4 1-4 streammod1 60
```

#### Run Full Experiment Suite
```bash
# Run all single and concurrent experiments
python3 run_full_experiment.py 1-4 streammod1 60
```

#### Analyze Results
```bash
# Analyze all experiment results
python3 analyze_experiments.py
```

This will generate:
- `experiment_comparison.csv` - Comparison of single vs concurrent
- `detailed_results.csv` - All detailed results

## Output Format

Each experiment generates a JSON file with:
- Execution time (seconds)
- Total bytes copied
- Bandwidth (MB/s)
- VDDQ current statistics (avg, max, min, mA)
- Total energy consumption (mJ)
- Energy per byte (nJ/byte)

## Key Findings to Look For

1. **Bandwidth Drop**: When running concurrently, each instance should show reduced bandwidth
2. **Energy Efficiency**: Energy per byte may increase due to contention overhead
3. **Thread Scaling**: How bandwidth and energy scale with thread count
4. **Contention Overhead**: Difference between single and concurrent performance

## Example Analysis Output

The analysis script will show:
- Bandwidth drop percentage (single vs concurrent)
- Energy per byte changes
- Summary statistics across all thread counts

## Notes

- Ensure STREAM binary (`streammod1`) is compiled and executable
- VDDQ current sensor must be accessible at `/sys/bus/i2c/drivers/ina3221/1-0041/hwmon/hwmon4/curr2_input`
- CPU cores specified in `cpu_list` must exist on your system
- Experiments use `taskset` for CPU affinity control

## Requirements

- Python 3.x
- NumPy, Pandas (for analysis)
- STREAM benchmark binary (compiled with OpenMP)
- Access to VDDQ current sensor
- `taskset` command (usually in `util-linux` package)

