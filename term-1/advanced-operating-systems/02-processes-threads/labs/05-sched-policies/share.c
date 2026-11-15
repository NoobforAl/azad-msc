// share.c: how does the scheduler split ONE CPU between busy tasks?
//
// Each argument creates one child pinned to the same CPU that spins for
// DURATION seconds. The argument is either a nice value (SCHED_OTHER, the EEVDF
// fair class) or "fifo" (SCHED_FIFO priority 10, the RT class; needs root).
// At the end every child reports the CPU time it really received.
//
// The expected fair share comes from sched_prio_to_weight[] in
// kernel/sched/core.c (nice 0 = 1024, nice 5 = 335, nice 10 = 110, ...).
//
// Usage: ./share [-c CPU] [-t SECONDS] arg...
//   ./share 0 0          two equal tasks           -> 50 / 50
//   ./share 0 5          nice 0 vs nice 5          -> 1024 : 335
//   sudo ./share fifo 0  RT spinner vs fair task   -> fair task only gets the
//                                                     fair_server reserve
// Build: gcc -Wall -Wextra -O2 -o share share.c
#define _GNU_SOURCE
#include <errno.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define MAXT 8

// Copy of the nice -> weight table (kernel/sched/core.c, sched_prio_to_weight[]).
static const int weight[40] = {
    88761, 71755, 56483, 46273, 36291, 29154, 23254, 18705, 14949, 11916,
    9548,  7620,  6100,  4904,  3906,  3121,  2501,  1991,  1586,  1277,
    1024,  820,   655,   526,   423,   335,   272,   215,   172,   137,
    110,   87,    70,    56,    45,    36,    29,    23,    18,    15,
};

static double ts_sec(const struct timespec *t) {
    return (double)t->tv_sec + (double)t->tv_nsec / 1e9;
}

int main(int argc, char **argv) {
    int cpu = 3;
    double duration = 3.0;
    int opt;
    while ((opt = getopt(argc, argv, "c:t:")) != -1) {
        if (opt == 'c') cpu = atoi(optarg);
        else if (opt == 't') duration = atof(optarg);
        else return 2;
    }
    int n = argc - optind;
    if (n < 1 || n > MAXT) {
        fprintf(stderr, "usage: %s [-c CPU] [-t SEC] nice|fifo ...\n", argv[0]);
        return 2;
    }

    // Shared result slots, written by the children.
    double *cpu_s = mmap(NULL, sizeof(double) * MAXT, PROT_READ | PROT_WRITE,
                         MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    // go: start flag; end: common end time (CLOCK_MONOTONIC, seconds) for every child.
    volatile int *go = mmap(NULL, sizeof(int) + sizeof(double) * 2, PROT_READ | PROT_WRITE,
                            MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (cpu_s == MAP_FAILED || go == MAP_FAILED) { perror("mmap"); return 1; }
    *go = 0;
    volatile double *end = (volatile double *)(go + 2);

    pid_t pids[MAXT];
    for (int i = 0; i < n; i++) {
        const char *a = argv[optind + i];
        pid_t p = fork();
        if (p < 0) { perror("fork"); return 1; }
        if (p == 0) {
            cpu_set_t set;
            CPU_ZERO(&set);
            CPU_SET(cpu, &set);
            if (sched_setaffinity(0, sizeof set, &set) != 0) { perror("affinity"); _exit(1); }
            if (strcmp(a, "fifo") == 0) {
                struct sched_param sp = {.sched_priority = 10};
                if (sched_setscheduler(0, SCHED_FIFO, &sp) != 0) { perror("SCHED_FIFO (root?)"); _exit(1); }
            } else if (setpriority(PRIO_PROCESS, 0, atoi(a)) != 0) {
                perror("setpriority"); _exit(1);
            }
            while (*go == 0) { }           // spin until everyone is ready
            // Count only CPU time between "go" and the common end time. A starved task may
            // see "go" late, but it must stop at the same moment as everyone else.
            struct timespec now, used0, used1;
            clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &used0);
            do {
                clock_gettime(CLOCK_MONOTONIC, &now);
            } while (ts_sec(&now) < *end);
            clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &used1);
            cpu_s[i] = ts_sec(&used1) - ts_sec(&used0);
            _exit(0);
        }
        pids[i] = p;
    }

    usleep(200 * 1000);   // let every child pin itself and set its policy
    struct timespec t0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    *end = ts_sec(&t0) + duration;
    *go = 1;
    for (int i = 0; i < n; i++) waitpid(pids[i], NULL, 0);

    double total = 0.0, wsum = 0.0;
    for (int i = 0; i < n; i++) {
        total += cpu_s[i];
        const char *a = argv[optind + i];
        if (strcmp(a, "fifo") != 0) wsum += weight[atoi(a) + 20];
    }
    printf("CPU %d, %.1f s wall, %d busy tasks\n", cpu, duration, n);
    printf("%-6s %-8s %8s %8s %10s\n", "task", "policy", "cpu_s", "share", "fair_pred");
    for (int i = 0; i < n; i++) {
        const char *a = argv[optind + i];
        int fifo = strcmp(a, "fifo") == 0;
        char pred[16] = "-";
        if (!fifo) snprintf(pred, sizeof pred, "%.1f%%", 100.0 * weight[atoi(a) + 20] / wsum);
        char pol[16];
        snprintf(pol, sizeof pol, fifo ? "FIFO:10" : "nice:%s", a);
        printf("%-6d %-8s %8.3f %7.1f%% %10s\n", i, pol, cpu_s[i], 100.0 * cpu_s[i] / total, pred);
    }
    return 0;
}
