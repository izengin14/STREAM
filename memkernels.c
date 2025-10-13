// memkernels.c  (kernel-bazlı fingerprint için)
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <unistd.h>

#ifndef N
#define N 100000000   // 100M eleman
#endif
#ifndef NTIMES
#define NTIMES 30     // 30 tekrar
#endif

static double *a, *b, *c;

void alloc() {
    a = (double*) aligned_alloc(64, N*sizeof(double));
    b = (double*) aligned_alloc(64, N*sizeof(double));
    c = (double*) aligned_alloc(64, N*sizeof(double));
    #pragma omp parallel for
    for (long i=0;i<N;i++){ a[i]=1.0; b[i]=2.0; c[i]=0.0; }
}

void do_copy(){
    puts("[MARK] COPY_BEGIN"); fflush(stdout);
    for(int k=0;k<NTIMES;k++){
        #pragma omp parallel for
        for(long i=0;i<N;i++) c[i]=a[i];
    }
    puts("[MARK] COPY_END"); fflush(stdout);
}

void do_scale(double s){
    puts("[MARK] SCALE_BEGIN"); fflush(stdout);
    for(int k=0;k<NTIMES;k++){
        #pragma omp parallel for
        for(long i=0;i<N;i++) b[i]=s*c[i];
    }
    puts("[MARK] SCALE_END"); fflush(stdout);
}

void do_add(){
    puts("[MARK] ADD_BEGIN"); fflush(stdout);
    for(int k=0;k<NTIMES;k++){
        #pragma omp parallel for
        for(long i=0;i<N;i++) c[i]=a[i]+b[i];
    }
    puts("[MARK] ADD_END"); fflush(stdout);
}

void do_triad(double s){
    puts("[MARK] TRIAD_BEGIN"); fflush(stdout);
    for(int k=0;k<NTIMES;k++){
        #pragma omp parallel for
        for(long i=0;i<N;i++) a[i]=b[i]+s*c[i];
    }
    puts("[MARK] TRIAD_END"); fflush(stdout);
}

int main(){
    alloc();
    sleep(1); // logger stabilize olsun
    do_copy();   sleep(1);
    do_scale(3.0); sleep(1);
    do_add();    sleep(1);
    do_triad(3.0); sleep(1);
    return 0;
}
