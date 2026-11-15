// latency-dl.c: extension solution. Same measurement as latency.c, but the
// thread runs under SCHED_DEADLINE (EDF + CBS) instead of SCHED_FIFO.
// Each period it sleeps with sched_yield(): under SCHED_DEADLINE that means
// "this job is done, wake me at the next period" (the kernel replenishes the budget).
//
// Build: gcc -Wall -Wextra -O2 -o latency-dl latency-dl.c
// Run:   sudo ./latency-dl 200 1000 10000   # runtime 200 us, period 1000 us, 10000 loops
#define _GNU_SOURCE
#include <errno.h>
#include <linux/sched.h>       /* SCHED_DEADLINE */
#include <linux/sched/types.h> /* struct sched_attr */
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#define NSEC_PER_SEC 1000000000LL

static int64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (int64_t)t.tv_sec * NSEC_PER_SEC + t.tv_nsec;
}

int main(int argc, char **argv) {
    uint64_t runtime_us = argc > 1 ? strtoull(argv[1], NULL, 10) : 200;
    uint64_t period_us = argc > 2 ? strtoull(argv[2], NULL, 10) : 1000;
    long loops = argc > 3 ? atol(argv[3]) : 10000;

    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0)
        fprintf(stderr, "mlockall: %s (continuing)\n", strerror(errno));

    struct sched_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.size = sizeof(attr);
    attr.sched_policy = SCHED_DEADLINE;
    attr.sched_runtime = runtime_us * 1000;
    attr.sched_deadline = period_us * 1000;
    attr.sched_period = period_us * 1000;
    /* glibc 2.39 has no sched_setattr() wrapper. */
    if (syscall(SYS_sched_setattr, 0, &attr, 0) != 0) {
        fprintf(stderr, "sched_setattr(SCHED_DEADLINE): %s\n", strerror(errno));
        return 1;
    }

    /* The first sched_yield() aligns us to a period boundary. */
    sched_yield();
    int64_t prev = now_ns(), min_ns = INT64_MAX, max_ns = 0, sum_ns = 0;
    for (long i = 0; i < loops; i++) {
        sched_yield();                         /* job done; next job at next period */
        int64_t t = now_ns();
        int64_t lat = (t - prev) - (int64_t)period_us * 1000;   /* lateness vs. ideal period */
        if (lat < 0) lat = -lat;               /* jitter in either direction */
        if (lat < min_ns) min_ns = lat;
        if (lat > max_ns) max_ns = lat;
        sum_ns += lat;
        prev = t;
    }
    printf("policy=SCHED_DEADLINE runtime=%lluus period=%lluus loops=%ld\n",
           (unsigned long long)runtime_us, (unsigned long long)period_us, loops);
    printf("period jitter us: min=%lld avg=%lld max=%lld\n", (long long)(min_ns / 1000),
           (long long)(sum_ns / loops / 1000), (long long)(max_ns / 1000));
    return 0;
}
