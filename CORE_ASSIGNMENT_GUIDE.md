# CPU Core Assignment Guide

## How to Change CPU Cores

The `run_concurrent_benchmark.sh` script accepts CPU core lists as arguments.

### Basic Syntax
```bash
./run_concurrent_benchmark.sh <threads1> <threads2> [duration] [cpu_list1] [cpu_list2]
```

### Examples

#### 1. Default (Auto-assigned)
```bash
./run_concurrent_benchmark.sh 4 4
```
- Instance 1: CPUs 0-3 (4 threads)
- Instance 2: CPUs 4-7 (4 threads)

#### 2. Custom Sequential Cores
```bash
./run_concurrent_benchmark.sh 4 4 10 "0-3" "4-7"
```
- Instance 1: CPUs 0-3
- Instance 2: CPUs 4-7

#### 3. Overlapping Cores (Memory Contention)
```bash
./run_concurrent_benchmark.sh 4 4 10 "0-3" "2-5"
```
- Instance 1: CPUs 0-3
- Instance 2: CPUs 2-5 (overlaps on CPUs 2-3)
- Creates memory contention on shared cores

#### 4. Same Cores (Maximum Contention)
```bash
./run_concurrent_benchmark.sh 4 4 10 "0-3" "0-3"
```
- Both instances on same CPUs 0-3
- Maximum memory contention

#### 5. Specific Individual Cores
```bash
./run_concurrent_benchmark.sh 4 4 10 "0,2,4,6" "1,3,5,7"
```
- Instance 1: CPUs 0, 2, 4, 6
- Instance 2: CPUs 1, 3, 5, 7
- No overlap, even distribution

#### 6. Different Core Counts
```bash
./run_concurrent_benchmark.sh 8 8 10 "0-7" "4-11"
```
- Instance 1: CPUs 0-7 (8 cores)
- Instance 2: CPUs 4-11 (8 cores, overlaps on 4-7)

#### 7. Check Available Cores
```bash
# See how many cores you have:
nproc

# See CPU topology:
lscpu | grep -E "CPU\(s\)|Thread|Core|Socket"
```

### CPU List Formats

The `taskset -c` command accepts:
- **Ranges**: `"0-3"` (cores 0, 1, 2, 3)
- **Individual**: `"0,2,4,6"` (cores 0, 2, 4, 6)
- **Mixed**: `"0-3,8-11"` (cores 0-3 and 8-11)

### Common Use Cases

#### Memory Contention Experiment
```bash
# Run on same cores to create contention:
./run_concurrent_benchmark.sh 4 4 30 "0-3" "0-3"
```

#### Isolated Cores (No Contention)
```bash
# Run on completely separate cores:
./run_concurrent_benchmark.sh 4 4 30 "0-3" "4-7"
```

#### Partial Overlap
```bash
# Some overlap for moderate contention:
./run_concurrent_benchmark.sh 4 4 30 "0-3" "2-5"
```

### Tips

1. **Check system topology**: Use `lscpu` to see your CPU layout
2. **Avoid hyperthreading confusion**: Make sure you're using physical cores
3. **Test different configurations**: Try same, overlapping, and separate cores
4. **Monitor with `htop`**: Watch CPU usage during runs

