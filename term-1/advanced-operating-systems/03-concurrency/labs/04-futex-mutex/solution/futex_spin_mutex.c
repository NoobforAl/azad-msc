// futex_spin_mutex.c: extension solution for lab 03.4.
// Same futex mutex, but lock() first spins SPIN times on the word before it
// goes to sleep (the user-space analogue of the kernel mutex's optimistic spin).
// Build: gcc -Wall -Wextra -O2 -pthread futex_spin_mutex.c -o futex_spin_mutex
// Run:   ./futex_spin_mutex <threads> <iters> <spin>
#define _GNU_SOURCE
#include <linux/futex.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static atomic_long g_wait_calls, g_wake_calls;
static int g_spin;

static long futex(atomic_uint *uaddr, int op, uint32_t val)
{
    return syscall(SYS_futex, (uint32_t *)uaddr, op, val, NULL, NULL, 0);
}

static void fmutex_lock(atomic_uint *m)
{
    for (int i = 0; i < g_spin; i++) {           // bounded spin before sleeping
        uint32_t z = 0;
        if (atomic_load_explicit(m, memory_order_relaxed) == 0 &&
            atomic_compare_exchange_weak(m, &z, 1))
            return;
        __builtin_ia32_pause();                  // ARCH-SPECIFIC (x86-64): PAUSE
    }
    uint32_t c = 0;
    if (atomic_compare_exchange_strong(m, &c, 1))
        return;
    if (c != 2)
        c = atomic_exchange(m, 2);
    while (c != 0) {
        atomic_fetch_add(&g_wait_calls, 1);
        futex(m, FUTEX_WAIT_PRIVATE, 2);
        c = atomic_exchange(m, 2);
    }
}

static void fmutex_unlock(atomic_uint *m)
{
    if (atomic_fetch_sub(m, 1) != 1) {
        atomic_store(m, 0);
        atomic_fetch_add(&g_wake_calls, 1);
        futex(m, FUTEX_WAKE_PRIVATE, 1);
    }
}

static atomic_uint g_mutex;
static long g_counter, g_iters;

static void *worker(void *arg)
{
    (void)arg;
    for (long i = 0; i < g_iters; i++) {
        fmutex_lock(&g_mutex);
        g_counter++;
        fmutex_unlock(&g_mutex);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 4) { fprintf(stderr, "usage: %s <threads> <iters> <spin>\n", argv[0]); return 2; }
    int n = atoi(argv[1]);
    g_iters = atol(argv[2]);
    g_spin = atoi(argv[3]);
    if (n < 1 || n > 64 || g_iters < 1 || g_spin < 0) return 2;

    struct timespec a, b;
    pthread_t t[64];
    clock_gettime(CLOCK_MONOTONIC, &a);
    for (int i = 0; i < n; i++) pthread_create(&t[i], NULL, worker, NULL);
    for (int i = 0; i < n; i++) pthread_join(t[i], NULL);
    clock_gettime(CLOCK_MONOTONIC, &b);
    double dt = (double)(b.tv_sec - a.tv_sec) + (double)(b.tv_nsec - a.tv_nsec) / 1e9;

    long want = (long)n * g_iters;
    printf("spin=%-5d threads=%d %s futex_wait=%ld futex_wake=%ld time=%.3fs\n",
           g_spin, n, g_counter == want ? "OK" : "WRONG",
           atomic_load(&g_wait_calls), atomic_load(&g_wake_calls), dt);
    return g_counter == want ? 0 : 1;
}
