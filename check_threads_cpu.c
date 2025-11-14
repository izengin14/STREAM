#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <sched.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
#ifdef _OPENMP
    int num_threads = 0;
    
    // Get thread count from environment or default
    char *omp_threads = getenv("OMP_NUM_THREADS");
    if (omp_threads != NULL) {
        num_threads = atoi(omp_threads);
        omp_set_num_threads(num_threads);
    }
    
    int thread_cpu_map[64] = {0};  // Store thread->CPU mapping
    int cpu_thread_count[64] = {0};  // Count threads per CPU
    
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int cpu = sched_getcpu();
        
        #pragma omp critical
        {
            thread_cpu_map[tid] = cpu;
            cpu_thread_count[cpu]++;
            if (omp_get_thread_num() == 0) {
                num_threads = omp_get_num_threads();
            }
        }
    }
    
    // Output in a parseable format
    printf("THREAD_COUNT:%d\n", num_threads);
    for (int i = 0; i < num_threads; i++) {
        printf("THREAD_%d_CPU:%d\n", i, thread_cpu_map[i]);
    }
    
    // Summary: threads per CPU
    printf("CPU_THREAD_COUNTS:");
    for (int cpu = 0; cpu < 64; cpu++) {
        if (cpu_thread_count[cpu] > 0) {
            printf(" CPU%d:%d", cpu, cpu_thread_count[cpu]);
        }
    }
    printf("\n");
    
#else
    printf("THREAD_COUNT:1\n");
    printf("THREAD_0_CPU:%d\n", sched_getcpu());
#endif
    return 0;
}



