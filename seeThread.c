/*
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#include <unistd.h>     // for syscall()
#include <sys/syscall.h>
#include <sched.h>      // for sched_getcpu()
 
int main(int argc, char *argv[]) {
#ifdef _OPENMP
    int max_available = omp_get_max_threads();
    char *omp_threads_env = getenv("OMP_NUM_THREADS");
    
    printf("========================================\n");
    printf("OpenMP Thread Detection:\n");
    printf("  Max threads available: %d\n", max_available);
    if (omp_threads_env != NULL && strlen(omp_threads_env) > 0) {
        printf("  OMP_NUM_THREADS env var: %s\n", omp_threads_env);
    } else {
        printf("  OMP_NUM_THREADS env var: not set\n");
    }
    printf("========================================\n\n");
    
    int actual_threads = 0;
    
    printf("Detecting active threads...\n\n");
    
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();  // thread ID
        int cpu = sched_getcpu();        // current CPU core
        
        // Get actual thread count (from any thread, but use single to avoid race)
        #pragma omp single
        {
            actual_threads = omp_get_num_threads();
            printf("✓ ACTIVE THREADS: %d\n\n", actual_threads);
        }
        
        #pragma omp critical
        {
            printf("Thread %2d running on CPU %2d\n", tid, cpu);
        }
    }
    
    printf("\n========================================\n");
    printf("Summary:\n");
    printf("  Threads currently in use: %d\n", actual_threads);
    printf("  Max threads available: %d\n", max_available);
    if (omp_threads_env != NULL) {
        printf("  OMP_NUM_THREADS was set to: %s\n", omp_threads_env);
    }
    printf("========================================\n");
#else
    printf("Running without OpenMP (single-threaded).\n");
#endif
 
    return 0;
}


*/

#include <stdio.h>
#include <omp.h>
#include <unistd.h>     // for syscall()
#include <sys/syscall.h>
#include <sched.h>      // for sched_getcpu()

int main() {
#ifdef _OPENMP
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int cpu = sched_getcpu();  // current CPU core
        printf("Thread %d running on CPU %d\n", tid, cpu);
    }
#else
    printf("Running without OpenMP (single-threaded).\n");
#endif

    return 0;
}