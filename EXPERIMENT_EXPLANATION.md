# Why Same Results with 4 vs 12 Threads?

## The Situation
When running:
- **4 threads on cores 1-4**: ~5.14 GB/s bandwidth
- **12 threads on cores 1-4**: ~5.15 GB/s bandwidth (almost identical!)

## Why This Happens (Expected Behavior)

### 1. **CPU Core Limitation**
- Only 4 physical cores (1-4) are available
- With 4 threads: 1 thread per core (optimal)
- With 12 threads: 12 threads compete for 4 cores (contention!)

### 2. **Memory Bandwidth Saturation**
- Memory bandwidth ~5 GB/s is likely the bottleneck
- 4 threads already saturate the memory bandwidth
- Adding more threads can't improve bandwidth - it's already maxed out

### 3. **Thread Contention Overhead**
- 12 threads on 4 cores = threads constantly context-switching
- Overhead cancels any potential benefits
- Result: similar performance

## What This Means for Your Experiment

This is **EXACTLY** what your professor wants you to observe:

### Single Instance Experiments (Baseline)
- 4 threads on cores 1-4 → baseline bandwidth
- 8 threads on cores 1-4 → same bandwidth (contention)
- 12 threads on cores 1-4 → same bandwidth (more contention)

**Finding**: More threads than cores = no improvement due to contention

### Concurrent Instance Experiments (Memory Contention)
- **Single instance**: 4 threads on cores 1-4 → measure bandwidth
- **Two concurrent instances**: Each with 4 threads on cores 1-4 → measure bandwidth

**Expected Finding**: Concurrent instances will show **bandwidth drop** due to memory contention

## Key Metrics to Track

1. **Bandwidth Drop**: Single vs Concurrent
   - Single: ~5.14 GB/s per instance
   - Concurrent: ~2.5-3 GB/s per instance (bandwidth shared)

2. **Energy per Byte**: Should increase with contention
   - More contention = less efficient = higher energy per byte

3. **Scaling Behavior**: 
   - 4 vs 8 vs 12 threads on same cores shows no improvement
   - This demonstrates contention effects

## Your Results Are Correct!

The similar results with 4 vs 12 threads show:
- ✅ Thread contention is occurring
- ✅ Memory bandwidth is the bottleneck
- ✅ Experimental setup is working correctly

The real comparison will be **single vs concurrent instances** - that's where you'll see the memory contention effects!

