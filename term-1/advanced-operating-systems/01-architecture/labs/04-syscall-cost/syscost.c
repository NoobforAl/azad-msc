// syscost.c: what does crossing the user/kernel boundary cost?
// Compares a real syscall (getpid), clock_gettime() through the vDSO,
// the same clock_gettime() forced through the SYSCALL instruction, and an empty loop.
// Timing uses clock_gettime(CLOCK_MONOTONIC) only (no PMU counters needed).
//
// Build: gcc -Wall -Wextra -O2 -o syscost syscost.c
// Run:   ./syscost              (default 2,000,000 calls per round, 7 rounds)
//        taskset -c 2 ./syscost 5000000
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/auxv.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#define ROUNDS 7

typedef void (*bench_fn)(long n);

static volatile long sink;

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

static void b_empty(long n) {
    for (long i = 0; i < n; i++) sink += i;
}

static void b_getpid(long n) {
    for (long i = 0; i < n; i++) sink += syscall(SYS_getpid);
}

static void b_vdso_clock(long n) {
    struct timespec ts;
    for (long i = 0; i < n; i++) {
        clock_gettime(CLOCK_MONOTONIC, &ts);
        sink += ts.tv_nsec;
    }
}

static void b_sys_clock(long n) {
    struct timespec ts;
    for (long i = 0; i < n; i++) {
        syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &ts);
        sink += ts.tv_nsec;
    }
}

static int cmp_double(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static void run(const char *name, bench_fn fn, long n) {
    double r[ROUNDS];
    fn(n / 10); // warm-up: page in code, settle the CPU frequency
    for (int k = 0; k < ROUNDS; k++) {
        double t0 = now_ns();
        fn(n);
        r[k] = (now_ns() - t0) / (double)n;
    }
    qsort(r, ROUNDS, sizeof r[0], cmp_double);
    printf("%-34s min %7.1f  median %7.1f ns/call\n", name, r[0], r[ROUNDS / 2]);
}

static void print_file(const char *label, const char *path) {
    char buf[256] = "?";
    FILE *f = fopen(path, "r");
    if (f) {
        if (!fgets(buf, sizeof buf, f)) buf[0] = '\0';
        fclose(f);
    }
    printf("%-22s %s", label, buf);
    if (buf[0] == '\0' || buf[0] == '?') printf("\n");
}

int main(int argc, char **argv) {
    long n = (argc > 1) ? strtol(argv[1], NULL, 10) : 2000000L;

    printf("vDSO mapped at         0x%lx\n", getauxval(AT_SYSINFO_EHDR));
    print_file("clocksource", "/sys/devices/system/clocksource/clocksource0/current_clocksource");
    print_file("meltdown (PTI)", "/sys/devices/system/cpu/vulnerabilities/meltdown");
    printf("calls per round        %ld x %d rounds\n\n", n, ROUNDS);

    run("empty loop", b_empty, n);
    run("clock_gettime() via vDSO", b_vdso_clock, n);
    run("syscall(SYS_clock_gettime)", b_sys_clock, n);
    run("syscall(SYS_getpid)", b_getpid, n);
    return 0;
}
