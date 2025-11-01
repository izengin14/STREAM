/*-----------------------------------------------------------------------*/
/* Program: STREAM Modified                                               */
/* This is a modified version of STREAM that runs continuously for 10s   */
/* and outputs timing data in CSV format                                 */
/*-----------------------------------------------------------------------*/

# include <stdio.h>
# include <unistd.h>
# include <math.h>
# include <float.h>
# include <limits.h>
# include <sys/time.h>
# include <sys/types.h>

/*-----------------------------------------------------------------------
 * INSTRUCTIONS:
 *
 *      1) STREAM requires different amounts of memory to run
 *         depending on both the system and the intended operation.
 *         The STREAM_ARRAY_SIZE should be chosen to be larger than
 *         the available cache size.  There are a variety of ways to
 *         determine the relevant cache sizes, as well as user
 *         preferences, but the relevant point is that it should be
 *         larger than the available cache size for good performance.&&
 *         In the distributed version of STREAM, the array size is
 *         set to give good performance on a variety of systems.
 *
 *      2) STREAM_ARRAY_SIZE should be >= 4 million, giving
 *         an array size of ~32 MB when using 8-byte double precision.
 *         STREAM_ARRAY_SIZE should be >= 20 million, giving
 *         an array size of ~160 MB when using 8-byte double precision.
 *         There are no rules about maximum allowable values for
 *         STREAM_ARRAY_SIZE, but you should check that you have
 *         sufficient virtual memory space allocated for it to be
 *         able to access the entire array.
 *
 *      3) You can set STREAM_ARRAY_SIZE from the command line
 *         with an argument to the executable as:
 *                gcc -O -DSTREAM_ARRAY_SIZE=100000000 stream.c -o stream.100M
 *         or
 *                gcc -O -DSTREAM_ARRAY_SIZE=100000000 stream.c -o stream.100M
 */

#ifndef STREAM_ARRAY_SIZE
#   define STREAM_ARRAY_SIZE	10000000
#endif

/*  2) STREAM runs each kernel "NTIMES" times and reports the *best* result
 *         for NTIMES can also be set on the compile line without changing the source
 *         code using, for example, "-DNTIMES=7".
 */

#ifdef NTIMES
#if NTIMES<=10
#   define NTIMES	100
#endif
#endif

#ifndef NTIMES
#   define NTIMES	100
#endif

/*  Users are allowed to modify the "OFFSET" variable, which *may* change the
 *         relative alignment of the arrays (though compilers may change the
 *         effective offset from your specified value).  Use of non-zero values
 *         for OFFSET can be especially helpful if the STREAM_ARRAY_SIZE is set
 *         to a value close to a large power of 2.  OFFSET can also be set on
 *         the compile line without changing the source code using, for example,
 *         "-DOFFSET=56".
 */

#ifndef OFFSET
#   define OFFSET	0
#endif

/*-----------------------------------------------------------------------*/

#ifndef STREAM_TYPE
#define STREAM_TYPE double
#endif

# define HLINE "-------------------------------------------------------------\n"

# ifndef MIN
# define MIN(x,y) ((x)<(y)?(x):(y))
# endif
# ifndef MAX
# define MAX(x,y) ((x)>(y)?(x):(y))
# endif

static STREAM_TYPE  a[STREAM_ARRAY_SIZE+OFFSET],
            b[STREAM_ARRAY_SIZE+OFFSET],
            c[STREAM_ARRAY_SIZE+OFFSET];

static double   avgtime[4] = {0}, maxtime[4] = {0},
        mintime[4] = {FLT_MAX,FLT_MAX,FLT_MAX,FLT_MAX};

static char *label[4] = {"Copy:      ", "Scale:     ",
    "Add:       ", "Triad:     "};

static double   bytes[4] = {
    2 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE,
    2 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE,
    3 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE,
    3 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE
    };

extern double mysecond();
extern void checkSTREAMresults();
#ifdef TUNED
extern void tuned_STREAM_Copy();
extern void tuned_STREAM_Scale(STREAM_TYPE scalar);
extern void tuned_STREAM_Add();
extern void tuned_STREAM_Triad(STREAM_TYPE scalar);
#endif
#ifdef _OPENMP
extern int omp_get_num_threads();
#endif

int
main()
    {
    ssize_t     j;
    unsigned long long iterations = 0;
    unsigned long long total_bytes;
    double      t1, t2, start_time, elapsed;

    /* Initialize arrays */
#pragma omp parallel for
    for (j=0; j<STREAM_ARRAY_SIZE; j++) {
        a[j] = 1.0;
        c[j] = 0.0;
    }
   
    // Run a quick warmup and make sure all pages are hit.
#pragma omp parallel for
    for (j=0; j<STREAM_ARRAY_SIZE; j++)
        c[j] = a[j];

    /*  --- MAIN LOOP --- run continuously for 10 seconds --- */
    start_time = mysecond();
    elapsed = 0.0;
   
    while (elapsed < 10.0)
    {
    t1 = mysecond();

#pragma omp parallel for
    for (j=0; j<STREAM_ARRAY_SIZE; j++)
        c[j] = a[j];
    t2 = mysecond();
       
    iterations++;
    elapsed = t2 - start_time;
    }

    double t_end = mysecond();

    /* Calculate total bytes copied (read from a[] + write to c[]) */
    total_bytes = iterations * STREAM_ARRAY_SIZE * sizeof(STREAM_TYPE) * 2;
   
    printf("start_t,end_t,iterations,time_taken, total_bytes\n");
    printf("%f,%f,%llu,%f,%llu\n", start_time, t_end, iterations, t_end - start_time, total_bytes);

    return 0;
}

# define    M   20

int
checktick()
    {
    int     i, minDelta, Delta;
    double  t1, t2, timesfound[M];

/*  Collect a sequence of M unique time values from the system. */

    for (i = 0; i < M; i++) {
    t1 = mysecond();
    while( ((t2=mysecond()) - t1) < 1.0E-6 )
        ;
    timesfound[i] = t1 = t2;
    }

/*
 * Determine the minimum difference between these M values.
 * This result will be our estimate (in microseconds) for the
 * clock granularity.
 */

    minDelta = 1000000;
    for (i = 1; i < M; i++) {
    Delta = (int)( 1.0E6 * (timesfound[i]-timesfound[i-1]));
    minDelta = MIN(minDelta, MAX(Delta,0));
    }

   return(minDelta);
    }


/* A gettimeofday routine to give access to the wall
   clock timer on most UNIX-like systems.  */

double mysecond()
{
        struct timeval tp;
        struct timezone tzp;
        int i;

        i = gettimeofday(&tp,&tzp);
        return ( (double) tp.tv_sec + (double) tp.tv_usec * 1.e-6 );
}

#ifndef abs
#define abs(a) ((a) >= 0 ? (a) : -(a))
#endif

void checkSTREAMresults ()
{
    STREAM_TYPE aj,bj,cj,scalar;
    STREAM_TYPE aSumErr,bSumErr,cSumErr;
    STREAM_TYPE aAvgErr,bAvgErr,cAvgErr;
    double epsilon;
    ssize_t j;
    int k,ierr,err;

    /* reproduce initialization */
    aj = 1.0;
    bj = 2.0;
    cj = 0.0;
    /* a[] is modified during timing check */
    aj = 2.0E0 * aj;
    /* now execute timing loop */
    scalar = 3.0;
    for (k=0; k<NTIMES; k++)
        {
            cj = aj;
            bj = scalar*cj;
            cj = aj+bj;
            aj = bj+scalar*cj;
        }

    /* accumulate deltas between observed and expected results */
    aSumErr = 0.0;
    bSumErr = 0.0;
    cSumErr = 0.0;
    for (j=0; j<STREAM_ARRAY_SIZE; j++) {
        aSumErr += abs(a[j] - aj);
        bSumErr += abs(b[j] - bj);
        cSumErr += abs(c[j] - cj);
        // if (j == 417) printf("Index 417: c[j]: %f, cj: %f\n",c[j],cj);   // MCCALPIN
    }
    aAvgErr = aSumErr / (STREAM_TYPE) STREAM_ARRAY_SIZE;
    bAvgErr = bSumErr / (STREAM_TYPE) STREAM_ARRAY_SIZE;
    cAvgErr = cSumErr / (STREAM_TYPE) STREAM_ARRAY_SIZE;

    if (sizeof(STREAM_TYPE) == 4) {
        epsilon = 1.e-6;
    }
    else if (sizeof(STREAM_TYPE) == 8) {
        epsilon = 1.e-13;
    }
    else {
        printf("WEIRD: sizeof(STREAM_TYPE) = %lu\n",sizeof(STREAM_TYPE));
        epsilon = 1.e-6;
    }

    err = 0;
    if (abs(aAvgErr/aj) > epsilon) {
        err++;
        printf ("Failed Validation on array a[], AvgRelAbsErr > epsilon (%e)\n",epsilon);
        printf ("     Expected Value: %e, AvgAbsErr: %e, AvgRelAbsErr: %e\n",aj,aAvgErr,abs(aAvgErr)/aj);
        ierr = 0;
        for (j=0; j<STREAM_ARRAY_SIZE; j++) {
            if (abs(a[j]/aj-1.0) > epsilon) {
                ierr++;
#ifdef VERBOSE
                if (ierr < 10) {
                    printf("         array a: index: %ld, expected: %e, observed: %e, relative error: %e\n",
                        j,aj,a[j],abs((aj-a[j])/aAvgErr));
                }
#endif
            }
        }
        printf("     For array a[], %d errors were found.\n",ierr);
    }
    if (abs(bAvgErr/bj) > epsilon) {
        err++;
        printf ("Failed Validation on array b[], AvgRelAbsErr > epsilon (%e)\n",epsilon);
        printf ("     Expected Value: %e, AvgAbsErr: %e, AvgRelAbsErr: %e\n",bj,bAvgErr,abs(bAvgErr)/bj);
        printf ("     AvgRelAbsErr > Epsilon (%e)\n",epsilon);
        ierr = 0;
        for (j=0; j<STREAM_ARRAY_SIZE; j++) {
            if (abs(b[j]/bj-1.0) > epsilon) {
                ierr++;
#ifdef VERBOSE
                if (ierr < 10) {
                    printf("         array b: index: %ld, expected: %e, observed: %e, relative error: %e\n",
                        j,bj,b[j],abs((bj-b[j])/bAvgErr));
                }
#endif
            }
        }
        printf("     For array b[], %d errors were found.\n",ierr);
    }
    if (abs(cAvgErr/cj) > epsilon) {
        err++;
        printf ("Failed Validation on array c[], AvgRelAbsErr > epsilon (%e)\n",epsilon);
        printf ("     Expected Value: %e, AvgAbsErr: %e, AvgRelAbsErr: %e\n",cj,cAvgErr,abs(cAvgErr)/cj);
        printf ("     AvgRelAbsErr > Epsilon (%e)\n",epsilon);
        ierr = 0;
        for (j=0; j<STREAM_ARRAY_SIZE; j++) {
            if (abs(c[j]/cj-1.0) > epsilon) {
                ierr++;
#ifdef VERBOSE
                if (ierr < 10) {
                    printf("         array c: index: %ld, expected: %e, observed: %e, relative error: %e\n",
                        j,cj,c[j],abs((cj-c[j])/cAvgErr));
                }
#endif
            }
        }
        printf("     For array c[], %d errors were found.\n",ierr);
    }
    if (err == 0) {
        printf ("Solution Validates: avg error less than %e on all three arrays\n",epsilon);
    }
#ifdef VERBOSE
    printf ("Results Validation Verbose Results: \n");
    printf ("    Expected a(1), b(1), c(1): %f %f %f \n",aj,bj,cj);
    printf ("    Observed a(1), b(1), c(1): %f %f %f \n",a[1],b[1],c[1]);
    printf ("    Rel Errors on a, b, c:     %e %e %e \n",abs(aAvgErr/aj),abs(bAvgErr/bj),abs(cAvgErr/cj));
#endif
}