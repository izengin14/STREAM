# Empirical-Roofline-Toolkit (ERT) Usage Guide

## Overview

The Empirical-Roofline-Toolkit (ERT) empirically determines your system's performance characteristics:
- **Peak Memory Bandwidth** (at different memory hierarchy levels)
- **Peak Computational Throughput** (for different operation types)
- These metrics are used to construct a **Roofline Model** that visualizes performance limits

ERT complements your STREAM benchmarks by providing the theoretical "roofline" against which your application performance can be compared.

## Installation

### 1. Clone the Repository

```bash
cd ~/Desktop
git clone https://github.com/ebugger/Empirical-Roofline-Toolkit.git ER
cd ER
```

### 2. Prerequisites

ERT typically requires:
- A C compiler (gcc, clang, or icc)
- **Python 2** (ERT is written for Python 2, not Python 3)
- Make

**Important Note**: ERT requires Python 2. If your system defaults to Python 3, you may need to:
- Install Python 2: `sudo apt-get install python2`
- Or modify the ERT script's shebang line to use `python2` explicitly

### 3. Build ERT

**Note**: ERT does not need to be manually built. It automatically compiles the drivers and kernels when you run it with a configuration file. Just run ERT directly!

## Configuration

### 1. Configuration Files

ERT uses configuration files to specify:
- Number of threads/cores to use
- Memory hierarchy details
- System-specific parameters

Configuration files are typically located in the `ERT/` directory. Look for files like:
- `config.txt`
- `config_*.txt`
- Or create your own based on examples

### 2. Example Configuration

Create or edit a configuration file (`config_tegra.txt` for your Tegra system):

```
# Number of threads
threads: 1, 2, 4, 8, 12

# Problem sizes (optional - ERT typically auto-selects)
# sizes: 1000000, 10000000, 100000000

# Memory hierarchy (ERT will probe automatically, but you can specify)
# cache_levels: L1, L2, L3, DRAM
```

## Running ERT

### Basic Usage

```bash
cd ~/Desktop/ER/ERT

# Run ERT with default configuration
./ERT

# Or specify a configuration file
./ERT config_tegra.txt

# Run with specific number of threads
./ERT --threads 4

# Run for specific operation types
./ERT --ops FMA,ADD,MUL  # FMA=Fused Multiply-Add, ADD, MUL
```

### What ERT Measures

ERT runs micro-benchmarks to measure:

1. **Memory Bandwidth** (similar to STREAM):
   - Reads
   - Writes
   - Read+Write (triad-like operations)
   - At different memory hierarchy levels (L1, L2, L3, DRAM)

2. **Computational Throughput**:
   - Single Precision (SP) operations
   - Double Precision (DP) operations
   - Different operation types: ADD, MUL, FMA (Fused Multiply-Add)

### Output Files

ERT typically generates:
- `ERT_*.dat` - Raw performance data
- `ERT_*.txt` - Summary reports
- Bandwidth measurements in GB/s
- Computational throughput in GFLOP/s

## Integrating with Your STREAM Results

### 1. Compare STREAM Results with ERT

Your STREAM benchmarks measure **actual application performance**, while ERT measures **theoretical peak performance**.

```bash
# Run ERT to get peak memory bandwidth
cd ~/Desktop/ER/ERT
./ERT --memory-only > ert_bandwidth.txt

# Compare with your STREAM results
# Your STREAM results show achieved bandwidth
# ERT shows the theoretical peak (roofline)
```

### 2. Calculate Efficiency

```
Efficiency = (STREAM Bandwidth) / (ERT Peak Bandwidth) × 100%
```

If STREAM achieves 80% of ERT's peak, your application is performing well.

### 3. Identify Bottlenecks

- If STREAM bandwidth << ERT peak bandwidth → Memory-bound
- If computational performance is low → Compute-bound
- Use roofline model to visualize where your application sits

## Visualizing Results

### Using Roofline Visualizer

The Roofline Visualizer can create plots from ERT data:

```bash
# If available in the ER repository
cd ~/Desktop/ER/RooflineVisualizer
python roofline.py --ert ERT/ERT_*.dat
```

### Manual Plotting

You can create roofline plots using:
- Python with matplotlib
- The data from ERT output files
- Your STREAM bandwidth measurements

## Example Workflow

```bash
# 1. Measure peak bandwidth with ERT
cd ~/Desktop/ER/ERT
./ERT --threads 12 > ert_results.txt

# 2. Extract peak bandwidth from ERT output
grep "Peak Bandwidth" ert_results.txt

# 3. Run your STREAM benchmark
cd ~/Desktop/STREAM
./streammod > stream_results.txt

# 4. Compare results
# ERT peak bandwidth = theoretical maximum
# STREAM bandwidth = achieved performance
# Efficiency = STREAM / ERT × 100%
```

## Troubleshooting

### Common Issues

1. **ERT fails to compile**:
   - Check compiler version
   - Review Makefile for system-specific flags
   - May need to adjust for ARM architecture (Tegra)

2. **Results seem unrealistic**:
   - Ensure proper thread affinity
   - Check for thermal throttling
   - Verify system is idle during measurements

3. **Memory hierarchy not detected**:
   - ERT may need manual configuration for your architecture
   - Check `/proc/cpuinfo` for cache sizes
   - Manually specify in config file

## Advanced Usage

### Multi-threaded Analysis

```bash
# Test different thread counts
for threads in 1 2 4 8 12; do
    ./ERT --threads $threads > ert_${threads}threads.txt
done
```

### Specific Operation Types

```bash
# Measure only memory bandwidth
./ERT --memory-only

# Measure only computational throughput
./ERT --compute-only

# Measure specific operations
./ERT --ops FMA,ADD
```

## Resources

- **ERT Repository**: https://github.com/ebugger/Empirical-Roofline-Toolkit
- **LBL Roofline Software**: https://crd.lbl.gov/divisions/amcr/computer-science-amcr/par/research/roofline/software/
- **Roofline Model Paper**: Look for "Roofline: An Insightful Visual Performance Model"
- **User's Manual**: Included in the ER repository

## Notes for Tegra Systems

Your Tegra system may require:
- ARM-specific compiler flags
- Different memory hierarchy configuration
- Power/frequency scaling considerations
- Consider using `taskset` or `numactl` for thread affinity

```bash
# Example with thread affinity
taskset -c 0-11 ./ERT --threads 12
```

