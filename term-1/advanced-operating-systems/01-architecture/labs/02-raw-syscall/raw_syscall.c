// raw_syscall.c: the same system call three ways (libc wrapper, syscall(3), inline asm).
// Shows the x86-64 Linux syscall ABI and the errno convention, then times each path.
//
// Build: gcc -Wall -Wextra -O2 -o raw_syscall raw_syscall.c
// Run:   ./raw_syscall            (default 5,000,000 iterations)
//        ./raw_syscall 20000000
//
// ARCH-SPECIFIC (x86-64): register usage follows arch/x86/entry/entry_64.S
// ("rax system call number, rdi arg0, rsi arg1, rdx arg2, r10 arg3, r8 arg4, r9 arg5").
#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

// SYSCALL clobbers rcx (gets the return RIP) and r11 (gets RFLAGS).
// The kernel returns the result in rax; errors are -errno (-4095..-1).
static inline long raw_syscall0(long nr) {
    long ret;
    __asm__ volatile("syscall"
                     : "=a"(ret)
                     : "a"(nr)
                     : "rcx", "r11", "memory");
    return ret;
}

static inline long raw_syscall3(long nr, long a0, long a1, long a2) {
    long ret;
    __asm__ volatile("syscall"
                     : "=a"(ret)
                     : "a"(nr), "D"(a0), "S"(a1), "d"(a2)
                     : "rcx", "r11", "memory");
    return ret;
}

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

int main(int argc, char **argv) {
    const long iters = (argc > 1) ? strtol(argv[1], NULL, 10) : 5000000L;

    // 1) The same write(2) three ways.
    const char m1[] = "libc   write()\n";
    const char m2[] = "syscall(SYS_write)\n";
    const char m3[] = "inline asm syscall\n";
    ssize_t r1 = write(1, m1, strlen(m1));
    long r2 = syscall(SYS_write, 1, m2, strlen(m2));
    long r3 = raw_syscall3(SYS_write, 1, (long)m3, (long)strlen(m3));
    printf("returns: %zd %ld %ld\n", r1, r2, r3);

    // 2) Error convention: fd 999 is not open.
    errno = 0;
    ssize_t e1 = write(999, m1, 1);
    int saved = errno;
    long e3 = raw_syscall3(SYS_write, 999, (long)m1, 1);
    printf("libc write(999): ret=%zd errno=%d (%s)\n", e1, saved, strerror(saved));
    printf("raw  write(999): ret=%ld  (kernel returns -errno)\n", e3);

    // 3) Same answer from all three getpid paths.
    pid_t p1 = getpid();
    long p2 = syscall(SYS_getpid);
    long p3 = raw_syscall0(SYS_getpid);
    printf("getpid: %d %ld %ld\n", (int)p1, p2, p3);

    // 4) Timing. getpid() is a real syscall in glibc >= 2.25 (no PID cache).
    volatile long sink = 0;
    for (long i = 0; i < iters / 10; i++) sink += getpid();  // warm-up: settle CPU/VM scheduling
    double t0 = now_ns();
    for (long i = 0; i < iters; i++) sink += getpid();
    double t1 = now_ns();
    for (long i = 0; i < iters; i++) sink += syscall(SYS_getpid);
    double t2 = now_ns();
    for (long i = 0; i < iters; i++) sink += raw_syscall0(SYS_getpid);
    double t3 = now_ns();
    for (long i = 0; i < iters; i++) sink += i;
    double t4 = now_ns();

    printf("iterations: %ld\n", iters);
    printf("libc getpid()        %7.1f ns/call\n", (t1 - t0) / (double)iters);
    printf("syscall(SYS_getpid)  %7.1f ns/call\n", (t2 - t1) / (double)iters);
    printf("inline asm syscall   %7.1f ns/call\n", (t3 - t2) / (double)iters);
    printf("empty loop           %7.1f ns/iter\n", (t4 - t3) / (double)iters);
    return (sink == 42) ? 1 : 0;
}
