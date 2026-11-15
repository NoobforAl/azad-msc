// wakelat.c: solution to the lab 02.5 extension.
// Wakeup latency of a periodic sleeper competing with two nice-0 spinners on one
// CPU, with the default EEVDF slice vs a custom slice set by sched_setattr().
//
// Usage: ./wakelat [slice_ns]      (0 or no argument = default slice)
// Build: gcc -Wall -Wextra -O2 -o wakelat wakelat.c
#define _GNU_SOURCE
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define CPU 3
#define N 2000

struct sched_attr {
    uint32_t size, sched_policy;
    uint64_t sched_flags;
    int32_t sched_nice;
    uint32_t sched_priority;
    uint64_t sched_runtime, sched_deadline, sched_period;
    uint32_t sched_util_min, sched_util_max;
};

static void pin(void) {
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(CPU, &s);
    if (sched_setaffinity(0, sizeof s, &s) != 0) { perror("affinity"); exit(1); }
}

static int64_t ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (int64_t)t.tv_sec * 1000000000LL + t.tv_nsec;
}

static int cmp(const void *a, const void *b) {
    int64_t x = *(const int64_t *)a, y = *(const int64_t *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    uint64_t slice = argc > 1 ? strtoull(argv[1], NULL, 10) : 0;
    pid_t hogs[2];
    for (int i = 0; i < 2; i++) {
        hogs[i] = fork();
        if (hogs[i] == 0) { pin(); for (;;) { } }
    }
    pin();
    if (slice > 0) {
        struct sched_attr a;
        memset(&a, 0, sizeof a);
        a.size = sizeof a;
        a.sched_policy = SCHED_OTHER;
        a.sched_runtime = slice;
        if (syscall(SYS_sched_setattr, 0, &a, 0) != 0) { perror("sched_setattr"); return 1; }
    }
    static int64_t lat[N];
    struct timespec req = {0, 1000000};   // 1 ms
    for (int i = 0; i < N; i++) {
        int64_t t0 = ns();
        nanosleep(&req, NULL);
        lat[i] = ns() - t0 - 1000000;      // lateness beyond the requested 1 ms
    }
    for (int i = 0; i < 2; i++) { kill(hogs[i], SIGKILL); waitpid(hogs[i], NULL, 0); }
    qsort(lat, N, sizeof lat[0], cmp);
    printf("slice=%-8s wakeups=%d  lateness p50=%.0f us  p90=%.0f us  p99=%.0f us\n",
           slice ? argv[1] : "default", N, lat[N / 2] / 1e3, lat[N * 9 / 10] / 1e3, lat[N * 99 / 100] / 1e3);
    return 0;
}
