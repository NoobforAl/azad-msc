// vfork_block.c: solution to the lab 02.2 extension.
// With CLONE_VFORK the parent sleeps in kernel_clone() -> wait_for_vfork_done()
// until the child calls execve() or _exit(). We time how long clone() takes to
// return in the parent while the child sleeps for 1 s.
//
// Build: gcc -Wall -Wextra -O2 -o vfork_block vfork_block.c
#define _GNU_SOURCE
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define STACK_SIZE (256 * 1024)

static int child_fn(void *arg) {
    unsigned int secs = *(unsigned int *)arg;
    if (secs > 0) sleep(secs);
    _exit(0);          // never return or exit(): we are on borrowed memory
}

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static void run(int flags, unsigned int secs, const char *name) {
    char *stack = mmap(NULL, STACK_SIZE, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (stack == MAP_FAILED) { perror("mmap"); exit(1); }
    double t0 = now();
    pid_t p = clone(child_fn, stack + STACK_SIZE, flags | SIGCHLD, &secs);
    double t1 = now();
    if (p < 0) { perror("clone"); exit(1); }
    waitpid(p, NULL, 0);
    printf("%-22s child sleeps %u s: clone() returned in parent after %.3f s\n",
           name, secs, t1 - t0);
    munmap(stack, STACK_SIZE);
}

int main(void) {
    run(CLONE_VM, 1, "CLONE_VM");
    run(CLONE_VM | CLONE_VFORK, 1, "CLONE_VM|CLONE_VFORK");
    run(CLONE_VM | CLONE_VFORK, 0, "CLONE_VM|CLONE_VFORK");
    return 0;
}
