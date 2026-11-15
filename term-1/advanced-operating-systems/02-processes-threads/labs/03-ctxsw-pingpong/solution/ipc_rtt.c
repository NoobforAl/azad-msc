// ipc_rtt.c: solution to the lab 02.3 extension.
// Same ping-pong as pingpong.c, over three IPC mechanisms:
//   pipe    two pipes (one per direction)
//   unix    one AF_UNIX SOCK_STREAM socketpair
//   shm     a shared anonymous page + futex wait/wake (no data syscalls at all,
//           only the futex syscalls needed to sleep and wake)
// Both tasks are pinned to CPU <cpu> (default 0) so every round trip is two
// real context switches; with -s the child runs on CPU 1 instead.
//
// Build: gcc -Wall -Wextra -O2 -o ipc_rtt ipc_rtt.c
// Run:   ./ipc_rtt pipe 200000; ./ipc_rtt unix 200000; ./ipc_rtt shm 200000
#define _GNU_SOURCE
#include <linux/futex.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static void die(const char *w) { perror(w); exit(1); }

static void pin(int cpu) {
    cpu_set_t s;
    CPU_ZERO(&s);
    CPU_SET(cpu, &s);
    if (sched_setaffinity(0, sizeof s, &s) != 0) die("affinity");
}

static uint64_t now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}

// Shared word: 0 = parent's turn, 1 = child's turn.
static void futex_wait(_Atomic uint32_t *w, uint32_t val) {
    while (atomic_load(w) == val) {
        syscall(SYS_futex, w, FUTEX_WAIT, val, NULL, NULL, 0);
    }
}
static void futex_set_wake(_Atomic uint32_t *w, uint32_t val) {
    atomic_store(w, val);
    syscall(SYS_futex, w, FUTEX_WAKE, 1, NULL, NULL, 0);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s pipe|unix|shm [iters] [-s]\n", argv[0]); return 2; }
    const char *mode = argv[1];
    long iters = argc > 2 ? strtol(argv[2], NULL, 10) : 200000;
    int split = argc > 3 && strcmp(argv[3], "-s") == 0;
    int a[2], b[2];
    char c = 'x';
    _Atomic uint32_t *turn = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (turn == MAP_FAILED) die("mmap");
    atomic_store(turn, 0);

    int is_pipe = strcmp(mode, "pipe") == 0, is_unix = strcmp(mode, "unix") == 0;
    if (is_pipe) { if (pipe(a) || pipe(b)) die("pipe"); }
    else if (is_unix) { if (socketpair(AF_UNIX, SOCK_STREAM, 0, a)) die("socketpair"); }
    else if (strcmp(mode, "shm") != 0) { fprintf(stderr, "bad mode\n"); return 2; }

    pid_t ch = fork();
    if (ch < 0) die("fork");
    if (ch == 0) {
        pin(split ? 1 : 0);
        for (long i = 0; i < iters; i++) {
            if (is_pipe) {
                if (read(a[0], &c, 1) != 1 || write(b[1], &c, 1) != 1) die("child pipe");
            } else if (is_unix) {
                if (read(a[1], &c, 1) != 1 || write(a[1], &c, 1) != 1) die("child unix");
            } else {
                futex_wait(turn, 0);          // wait while it is the parent's turn
                futex_set_wake(turn, 0);      // hand the turn back
            }
        }
        _exit(0);
    }
    pin(0);
    uint64_t t0 = now_ns();
    for (long i = 0; i < iters; i++) {
        if (is_pipe) {
            if (write(a[1], &c, 1) != 1 || read(b[0], &c, 1) != 1) die("parent pipe");
        } else if (is_unix) {
            if (write(a[0], &c, 1) != 1 || read(a[0], &c, 1) != 1) die("parent unix");
        } else {
            futex_set_wake(turn, 1);
            futex_wait(turn, 1);
        }
    }
    uint64_t t1 = now_ns();
    waitpid(ch, NULL, 0);
    printf("%-4s %-5s iters=%ld round_trip=%.0f ns\n", mode, split ? "split" : "same",
           iters, (double)(t1 - t0) / (double)iters);
    return 0;
}
