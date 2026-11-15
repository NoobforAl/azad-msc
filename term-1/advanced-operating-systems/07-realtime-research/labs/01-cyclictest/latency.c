// latency.c: a ~70-line "mini cyclictest".
// One SCHED_FIFO thread sleeps until an absolute deadline every INTERVAL_US,
// then measures how late it actually woke up (the wake-up latency).
//
// Build: gcc -Wall -Wextra -O2 -o latency latency.c
// Run:   sudo ./latency 80 1000 10000     # prio 80, 1000 us period, 10000 loops
#define _GNU_SOURCE
#include <errno.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

#define NSEC_PER_SEC 1000000000LL
#define BUCKETS 8

static int64_t ts_ns(const struct timespec *t) {
    return (int64_t)t->tv_sec * NSEC_PER_SEC + t->tv_nsec;
}

static void ts_add_ns(struct timespec *t, int64_t ns) {
    int64_t v = ts_ns(t) + ns;
    t->tv_sec = (time_t)(v / NSEC_PER_SEC);
    t->tv_nsec = (long)(v % NSEC_PER_SEC);
}

int main(int argc, char **argv) {
    int prio = argc > 1 ? atoi(argv[1]) : 80;
    int64_t interval_us = argc > 2 ? atoll(argv[2]) : 1000;
    long loops = argc > 3 ? atol(argv[3]) : 10000;
    /* Histogram bucket upper bounds in microseconds. */
    const int64_t bound_us[BUCKETS] = {5, 10, 20, 50, 100, 500, 1000, INT64_MAX};
    long hist[BUCKETS] = {0};

    /* Page faults are latency: lock all current and future pages in RAM. */
    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0)
        fprintf(stderr, "mlockall: %s (continuing)\n", strerror(errno));

    struct sched_param sp = {.sched_priority = prio};
    if (sched_setscheduler(0, SCHED_FIFO, &sp) != 0) {
        fprintf(stderr, "sched_setscheduler(SCHED_FIFO, %d): %s (need root)\n",
                prio, strerror(errno));
        return 1;
    }

    struct timespec next, now;
    int64_t min_ns = INT64_MAX, max_ns = 0, sum_ns = 0;
    long overruns = 0;   /* whole periods skipped because we woke up too late */
    clock_gettime(CLOCK_MONOTONIC, &next);
    for (long i = 0; i < loops; i++) {
        ts_add_ns(&next, interval_us * 1000);
        /* TIMER_ABSTIME: no drift, the deadline is fixed in advance. */
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL);
        clock_gettime(CLOCK_MONOTONIC, &now);
        int64_t lat = ts_ns(&now) - ts_ns(&next);
        if (lat < min_ns) min_ns = lat;
        if (lat > max_ns) max_ns = lat;
        sum_ns += lat;
        for (int b = 0; b < BUCKETS; b++)
            if (lat / 1000 < bound_us[b]) { hist[b]++; break; }
        /* Woke up after the NEXT deadline too: skip the missed periods instead of
         * firing late ones back-to-back (otherwise one stall poisons every later sample). */
        while (ts_ns(&next) + interval_us * 1000 <= ts_ns(&now)) {
            ts_add_ns(&next, interval_us * 1000);
            overruns++;
        }
    }

    printf("policy=SCHED_FIFO prio=%d interval=%lldus loops=%ld overruns=%ld\n",
           prio, (long long)interval_us, loops, overruns);
    printf("latency us: min=%lld avg=%lld max=%lld\n", (long long)(min_ns / 1000),
           (long long)(sum_ns / loops / 1000), (long long)(max_ns / 1000));
    for (int b = 0; b < BUCKETS; b++) {
        if (bound_us[b] == INT64_MAX)
            printf("  >=%5lld us : %ld\n", (long long)bound_us[b - 1], hist[b]);
        else
            printf("  < %5lld us : %ld\n", (long long)bound_us[b], hist[b]);
    }
    return 0;
}
