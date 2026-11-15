// enosys.c: the fixed price of crossing the boundary, measured three ways:
//   getpid (tiny body), an unknown syscall number (no body at all: -ENOSYS),
//   and getpid while being traced (run this binary under strace to see that cost).
//
// Build: gcc -Wall -Wextra -O2 -o enosys enosys.c
// Run:   ./enosys
//        strace -c -o /dev/null ./enosys 200000
//
// Kernel path for nr = 1000: do_syscall_64() -> do_syscall_x64() returns false
// (1000 >= NR_syscalls) -> do_syscall_x32() false -> regs->ax = __x64_sys_ni_syscall(regs).
//
// Real run on aos-lab (shared VirtualBox guest, Linux 6.18.63), 2026-11-15:
//   $ taskset -c 2 ./enosys
//   syscall(1000) = -1, errno = 38 (Function not implemented)
//   calls: 2000000
//   getpid             90.3 ns/call
//   nr 1000 ENOSYS     80.5 ns/call
// An unknown number skips only the tiny getpid body (~10 ns here). Everything else is the
// same: SYSCALL, entry_SYSCALL_64, syscall_enter_from_user_mode(), the exit work loop,
// SYSRET. The boundary crossing *is* the cost of a cheap syscall.
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

int main(int argc, char **argv) {
    const long n = (argc > 1) ? strtol(argv[1], NULL, 10) : 2000000L;
    volatile long sink = 0;

    errno = 0;
    long r = syscall(1000);
    printf("syscall(1000) = %ld, errno = %d (%s)\n", r, errno, strerror(errno));

    double t0 = now_ns();
    for (long i = 0; i < n; i++) sink += syscall(SYS_getpid);
    double t1 = now_ns();
    for (long i = 0; i < n; i++) sink += syscall(1000);
    double t2 = now_ns();

    printf("calls: %ld\n", n);
    printf("getpid         %8.1f ns/call\n", (t1 - t0) / (double)n);
    printf("nr 1000 ENOSYS %8.1f ns/call\n", (t2 - t1) / (double)n);
    return (sink == 42) ? 1 : 0;
}
