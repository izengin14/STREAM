/* Byte-based STREAM benchmark version */
/* Based on streammod1.c but runs until target bytes are completed */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <float.h>
#include <limits.h>
#include <sys/time.h>
#include <time.h>
#include <stdint.h>
#ifdef _OPENMP
#include <omp.h>
#endif

/* Configuration - can be overridden at compile time */
#ifndef STREAM_ARRAY_SIZE
#   define STREAM_ARRAY_SIZE    10000000
#endif

#ifndef TARGET_TOTAL_BYTES
#   define TARGET_TOTAL_BYTES   (STREAM_ARRAY_SIZE * sizeof(double) * 10)
#endif

#ifndef STREAM_TYPE
#define STREAM_TYPE double
#endif

static STREAM_TYPE  a[STREAM_ARRAY_SIZE],
            b[STREAM_ARRAY_SIZE],
            c[STREAM_ARRAY_SIZE];

extern double mysecond();
extern void print_timestamp(double timestamp, FILE *fp);

#ifdef _OPENMP
extern int omp_get_num_threads();
extern int omp_get_max_threads();
extern int omp_get_thread_num();
#endif

int main()
{
    ssize_t     j;
    unsigned long long iterations = 0;
    unsigned long long total_bytes = 0;
    unsigned long long target_bytes = TARGET_TOTAL_BYTES;
    double      t1, t2, start_time, elapsed;
    
    /* Force thread count and debug OpenMP settings */
#ifdef _OPENMP
    char *omp_threads = getenv("OMP_NUM_THREADS");
    int requested_threads = 4;
    if (omp_threads != NULL) {
        requested_threads = atoi(omp_threads);
    }
    omp_set_num_threads(requested_threads);
    omp_set_dynamic(0);
    printf("Environment OMP_NUM_THREADS: %s\n", omp_threads ? omp_threads : "not set");
    printf("Requested threads: %d\n", requested_threads);
    printf("Max threads available: %d\n", omp_get_max_threads());
    
    int actual_threads = 1;
    #pragma omp parallel
    {
        if (omp_get_thread_num() == 0) {
            actual_threads = omp_get_num_threads();
        }
    }
    printf("Using %d OpenMP threads\n", actual_threads);
#else
    int actual_threads = 1;
    int requested_threads = 1;
#endif

    /* Initialize arrays */
#pragma omp parallel for
    for (j=0; j<STREAM_ARRAY_SIZE; j++) {
        a[j] = 1.0;
        c[j] = 0.0;
    }
   
    /* Warmup */
#pragma omp parallel for
    for (j=0; j<STREAM_ARRAY_SIZE; j++)
        c[j] = a[j];

    /* MAIN LOOP - run until target bytes are copied */
    start_time = mysecond();
    elapsed = 0.0;
   
    /* Create output filenames with thread count */
    char timestamp_filename[256];
    char bandwidth_filename[256];
    snprintf(timestamp_filename, sizeof(timestamp_filename), "stream_timestamps_%dthreads.txt", actual_threads);
    snprintf(bandwidth_filename, sizeof(bandwidth_filename), "stream_bandwidth_%dthreads.txt", actual_threads);
   
    FILE *fp = fopen(timestamp_filename, "w");
    if (fp == NULL) {
        printf("Error: Could not create output file\n");
        return 1;
    }
    
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
    
    printf("Running STREAM benchmark until %llu bytes are copied...\n", target_bytes);
    printf("Array size: %d elements (%llu bytes per array)\n", 
           STREAM_ARRAY_SIZE, (unsigned long long)(STREAM_ARRAY_SIZE * sizeof(STREAM_TYPE)));
    printf("Timestamp\t\t\t\tIteration\tElapsed\t\tIteration Time\tBytes Copied\n");
    printf("--------------------------------------------------------------------\n");
   
    while (total_bytes < target_bytes)
    {
        t1 = mysecond();

#pragma omp parallel for
        for (j=0; j<STREAM_ARRAY_SIZE; j++) {
            c[j] = a[j];
            // Multiple intensive operations for maximum CPU load - matches original streammod1.c
            b[j] = c[j] * 2.0;
            a[j] = b[j] + c[j];
            c[j] = a[j] * b[j];
            b[j] = c[j] / 2.0;
            a[j] = b[j] + c[j] + a[j];
        }
        t2 = mysecond();
           
        iterations++;
        elapsed = t2 - start_time;
        
        /* Calculate bytes transferred per iteration
         * Matches standard STREAM benchmark calculation:
         * Copy operation: read from a[], write to c[]
         * bytes = array_size × sizeof(element) × 2
         * where 2 represents one read operation and one write operation
         */
        unsigned long long bytes_this_iteration = STREAM_ARRAY_SIZE * sizeof(STREAM_TYPE) * 2;
        total_bytes += bytes_this_iteration;
        
        /* Calculate bandwidth for this iteration */
        double iter_time = t2 - t1;
        double bandwidth_mbs = 0.0, bandwidth_gbs = 0.0;
        if (iter_time > 0.0) {
            bandwidth_mbs = (double)bytes_this_iteration / iter_time / (1024.0 * 1024.0);
            bandwidth_gbs = (double)bytes_this_iteration / iter_time / (1024.0 * 1024.0 * 1024.0);
        }
        
        /* Calculate overall average bandwidth */
        double avg_bandwidth_mbs = 0.0, avg_bandwidth_gbs = 0.0;
        if (elapsed > 0.0) {
            avg_bandwidth_mbs = (double)total_bytes / elapsed / (1024.0 * 1024.0);
            avg_bandwidth_gbs = (double)total_bytes / elapsed / (1024.0 * 1024.0 * 1024.0);
        }
        
        printf("Iteration %llu: ", iterations);
        print_timestamp(t2, NULL);
        printf("\t\tElapsed: %.6f\t\tTime: %.6f\t%llu/%llu bytes\tBW: %.2f MB/s\n", 
               elapsed, t2 - t1, total_bytes, target_bytes, bandwidth_mbs);
        
        /* Write bandwidth data to file */
        fprintf(fp_bandwidth, "%llu\t\t%.6f\t\t%.6f\t\t%llu\t\t%.2f\t\t%.4f\n",
                iterations, elapsed, iter_time, bytes_this_iteration, 
                bandwidth_mbs, bandwidth_gbs);
        
        fflush(stdout);
        fflush(fp);
        fflush(fp_bandwidth);
        usleep(10000);  // 10ms delay per iteration - matches original streammod1
    }

    double t_end = mysecond();
    double total_time = t_end - start_time;
   
    printf("\n------------------------------------------------------------\n");
    printf("SUMMARY: ");
    print_timestamp(start_time, NULL);
    printf(" to ");
    print_timestamp(t_end, NULL);
    printf(", iterations=%llu, time_taken=%.6f, total_bytes=%llu\n", 
           iterations, total_time, total_bytes);
    
    /* Calculate final average bandwidth */
    double final_avg_mbs = 0.0, final_avg_gbs = 0.0;
    if (total_time > 0.0) {
        final_avg_mbs = (double)total_bytes / total_time / (1024.0 * 1024.0);
        final_avg_gbs = (double)total_bytes / total_time / (1024.0 * 1024.0 * 1024.0);
    }
    printf("Average Bandwidth: %.2f MB/s (%.4f GB/s)\n", final_avg_mbs, final_avg_gbs);
    
    print_timestamp(start_time, fp);
    fprintf(fp, "\n");
    print_timestamp(t_end, fp);
    fprintf(fp, "\n");
    fclose(fp);
    
    /* Write summary to bandwidth file */
    fprintf(fp_bandwidth, "\n----------------------------------------------------------------------------\n");
    fprintf(fp_bandwidth, "SUMMARY\n");
    fprintf(fp_bandwidth, "Total Iterations: %llu\n", iterations);
    fprintf(fp_bandwidth, "Total Time: %.6f seconds\n", total_time);
    fprintf(fp_bandwidth, "Total Bytes: %llu\n", total_bytes);
    fprintf(fp_bandwidth, "Average Bandwidth: %.2f MB/s (%.4f GB/s)\n", final_avg_mbs, final_avg_gbs);
    fclose(fp_bandwidth);
    
    printf("Data saved to: %s\n", timestamp_filename);
    printf("Bandwidth data saved to: %s\n", bandwidth_filename);
    
    return 0;
}

/* Helper functions from streammod1.c */
double mysecond()
{
    struct timeval tp;
    struct timezone tzp;
    gettimeofday(&tp, &tzp);
    return ((double)tp.tv_sec + (double)tp.tv_usec * 1.e-6);
}

void print_timestamp(double timestamp, FILE *fp)
{
    time_t sec = (time_t)timestamp;
    struct tm *tm_info = localtime(&sec);
    double microseconds = (timestamp - sec) * 1000000;
    
    if (fp) {
        fprintf(fp, "%02d:%02d:%02d.%06ld",
                tm_info->tm_hour, tm_info->tm_min, tm_info->tm_sec,
                (long)microseconds);
    } else {
        printf("%02d:%02d:%02d.%06ld",
               tm_info->tm_hour, tm_info->tm_min, tm_info->tm_sec,
               (long)microseconds);
    }
}

