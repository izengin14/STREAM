# New Code Added to streammod1_bytebased.c

## Summary
I added bandwidth calculation and output functionality. Here are the specific sections:

---

## 1. Thread Count Variables (Lines 73-76)
**NEW CODE:**
```c
#else
    int actual_threads = 1;
    int requested_threads = 1;
#endif
```
**Purpose:** Handle thread count when OpenMP is not available

---

## 2. Dynamic Filename Creation (Lines 94-98)
**NEW CODE:**
```c
/* Create output filenames with thread count */
char timestamp_filename[256];
char bandwidth_filename[256];
snprintf(timestamp_filename, sizeof(timestamp_filename), "stream_timestamps_%dthreads.txt", actual_threads);
snprintf(bandwidth_filename, sizeof(bandwidth_filename), "stream_bandwidth_%dthreads.txt", actual_threads);
```
**Purpose:** Create filenames that include thread count (e.g., `stream_bandwidth_4threads.txt`)

---

## 3. Bandwidth Output File Creation (Lines 106-116)
**NEW CODE:**
```c
FILE *fp_bandwidth = fopen(bandwidth_filename, "w");
if (fp_bandwidth == NULL) {
    printf("Error: Could not create bandwidth output file\n");
    fclose(fp);
    return 1;
}

fprintf(fp_bandwidth, "STREAM Bandwidth Output (%d threads)\n", actual_threads);
fprintf(fp_bandwidth, "=====================================\n");
fprintf(fp_bandwidth, "Iteration\tElapsed Time (s)\tIteration Time (s)\tBytes\t\tMB/s\t\tGB/s\n");
fprintf(fp_bandwidth, "----------------------------------------------------------------------------\n");
```
**Purpose:** Create and initialize the bandwidth output file with headers

---

## 4. Bandwidth Calculation Per Iteration (Lines 152-158)
**NEW CODE:**
```c
/* Calculate bandwidth for this iteration */
double iter_time = t2 - t1;
double bandwidth_mbs = 0.0, bandwidth_gbs = 0.0;
if (iter_time > 0.0) {
    bandwidth_mbs = (double)bytes_this_iteration / iter_time / (1024.0 * 1024.0);
    bandwidth_gbs = (double)bytes_this_iteration / iter_time / (1024.0 * 1024.0 * 1024.0);
}
```
**Purpose:** Calculate MB/s and GB/s for each iteration

---

## 5. Overall Average Bandwidth Calculation (Lines 160-165)
**NEW CODE:**
```c
/* Calculate overall average bandwidth */
double avg_bandwidth_mbs = 0.0, avg_bandwidth_gbs = 0.0;
if (elapsed > 0.0) {
    avg_bandwidth_mbs = (double)total_bytes / elapsed / (1024.0 * 1024.0);
    avg_bandwidth_gbs = (double)total_bytes / elapsed / (1024.0 * 1024.0 * 1024.0);
}
```
**Purpose:** Calculate cumulative average bandwidth (currently calculated but not used in output)

---

## 6. Bandwidth Display in Console (Line 169)
**MODIFIED:**
```c
printf("\t\tElapsed: %.6f\t\tTime: %.6f\t%llu/%llu bytes\tBW: %.2f MB/s\n", 
       elapsed, t2 - t1, total_bytes, target_bytes, bandwidth_mbs);
```
**Purpose:** Added `\tBW: %.2f MB/s` to show bandwidth in console output

---

## 7. Write Bandwidth Data to File (Lines 172-175)
**NEW CODE:**
```c
/* Write bandwidth data to file */
fprintf(fp_bandwidth, "%llu\t\t%.6f\t\t%.6f\t\t%llu\t\t%.2f\t\t%.4f\n",
        iterations, elapsed, iter_time, bytes_this_iteration, 
        bandwidth_mbs, bandwidth_gbs);
```
**Purpose:** Write bandwidth data for each iteration to the file

---

## 8. Flush Bandwidth File (Line 179)
**NEW CODE:**
```c
fflush(fp_bandwidth);
```
**Purpose:** Ensure bandwidth data is written immediately

---

## 9. Final Average Bandwidth Calculation (Lines 194-199)
**NEW CODE:**
```c
/* Calculate final average bandwidth */
double final_avg_mbs = 0.0, final_avg_gbs = 0.0;
if (total_time > 0.0) {
    final_avg_mbs = (double)total_bytes / total_time / (1024.0 * 1024.0);
    final_avg_gbs = (double)total_bytes / total_time / (1024.0 * 1024.0 * 1024.0);
}
```
**Purpose:** Calculate final average bandwidth for summary

---

## 10. Display Average Bandwidth (Line 200)
**NEW CODE:**
```c
printf("Average Bandwidth: %.2f MB/s (%.4f GB/s)\n", final_avg_mbs, final_avg_gbs);
```
**Purpose:** Display average bandwidth in console summary

---

## 11. Write Summary to Bandwidth File (Lines 208-214)
**NEW CODE:**
```c
/* Write summary to bandwidth file */
fprintf(fp_bandwidth, "\n----------------------------------------------------------------------------\n");
fprintf(fp_bandwidth, "SUMMARY\n");
fprintf(fp_bandwidth, "Total Iterations: %llu\n", iterations);
fprintf(fp_bandwidth, "Total Time: %.6f seconds\n", total_time);
fprintf(fp_bandwidth, "Total Bytes: %llu\n", total_bytes);
fprintf(fp_bandwidth, "Average Bandwidth: %.2f MB/s (%.4f GB/s)\n", final_avg_mbs, final_avg_gbs);
fclose(fp_bandwidth);
```
**Purpose:** Write summary statistics to bandwidth file

---

## 12. Updated Output Messages (Lines 217-218)
**MODIFIED:**
```c
printf("Data saved to: %s\n", timestamp_filename);
printf("Bandwidth data saved to: %s\n", bandwidth_filename);
```
**Purpose:** Use dynamic filenames instead of hardcoded names

---

## Summary
All new code is for **calculation and output only**. No changes were made to:
- The actual STREAM benchmark operations
- The timing measurements
- The loop structures
- Any performance-critical code

The bandwidth is calculated using the standard formula:
- **MB/s** = (bytes transferred) / (time in seconds) / (1024 × 1024)
- **GB/s** = (bytes transferred) / (time in seconds) / (1024 × 1024 × 1024)

