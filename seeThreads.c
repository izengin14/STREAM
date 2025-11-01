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