#define _GNU_SOURCE
#include <stdio.h>
#include <omp.h>
#include <unistd.h>     // for syscall()
#include <sys/syscall.h>
#include <sched.h>      // for sched_getcpu()
 
int main() {
#ifdef _OPENMP
 Use all CPU cores
    #pragma omp parallel
    {
        int cpu = sched_getcpu();  // current CPU core
        printf("Thread %d running on CPU %d\n", tid, cpu);
    }
    printf("OpenMP is enabled. Total threads: %d\n");
#else
    printf("Running without OpenMP (single-threaded).\n");
#endif
 
    return 0;
}