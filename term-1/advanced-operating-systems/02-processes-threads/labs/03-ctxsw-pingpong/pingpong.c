// pingpong.c: measure the cost of a blocking round trip between two processes.
//
// Parent and child pass one byte back and forth over two pipes. Each side blocks
// in read() until the other side writes, so every round trip forces the kernel to
// put one task to sleep and wake the other: two context switches if both run on
// the same CPU, two cross-CPU wakeups (IPI or idle-exit) if they run on different CPUs.
//
// Usage: ./pingpong <mode> [iterations]
//   mode = same   both tasks pinned to CPU 0      (real context switches)
//          split  parent on CPU 0, child on CPU 1 (wakeups across CPUs)
//          free   no pinning, the scheduler decides
//
// Build: gcc -Wall -Wextra -O2 -o pingpong pingpong.c
#define _GNU_SOURCE
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static void die(const char *what) {
    perror(what);
    exit(1);
}

static void pin(int cpu) {
    if (cpu < 0) return;
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof set, &set) != 0) die("sched_setaffinity");
}

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s same|split|free [iterations]\n", argv[0]);
        return 2;
    }
    const char *mode = argv[1];
    long iters = argc > 2 ? strtol(argv[2], NULL, 10) : 200000;
    int pcpu = -1, ccpu = -1;
    if (strcmp(mode, "same") == 0) { pcpu = 0; ccpu = 0; }
    else if (strcmp(mode, "split") == 0) { pcpu = 0; ccpu = 1; }
    else if (strcmp(mode, "free") != 0) { fprintf(stderr, "bad mode\n"); return 2; }

    int p2c[2], c2p[2];
    if (pipe(p2c) != 0 || pipe(c2p) != 0) die("pipe");
    char b = 'x';

    pid_t child = fork();
    if (child < 0) die("fork");
    if (child == 0) {
        pin(ccpu);
        close(p2c[1]);
        close(c2p[0]);
        for (long i = 0; i < iters; i++) {
            if (read(p2c[0], &b, 1) != 1) die("child read");
            if (write(c2p[1], &b, 1) != 1) die("child write");
        }
        _exit(0);
    }

    pin(pcpu);
    close(p2c[0]);
    close(c2p[1]);
    // Warm up: let both sides reach their read() loop once.
    if (write(p2c[1], &b, 1) != 1 || read(c2p[0], &b, 1) != 1) die("warmup");

    uint64_t t0 = now_ns();
    for (long i = 1; i < iters; i++) {
        if (write(p2c[1], &b, 1) != 1) die("parent write");
        if (read(c2p[0], &b, 1) != 1) die("parent read");
    }
    uint64_t t1 = now_ns();

    int st;
    if (waitpid(child, &st, 0) != child) die("waitpid");

    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
    double per_rt = (double)(t1 - t0) / (double)(iters - 1);
    printf("mode=%-5s iters=%ld  round_trip=%.0f ns  per_switch~%.0f ns  parent vcsw=%ld ivcsw=%ld\n",
           mode, iters - 1, per_rt, per_rt / 2.0, ru.ru_nvcsw, ru.ru_nivcsw);
    return 0;
}
