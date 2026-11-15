// futex_mutex.c: a mutex on top of the raw futex(2) system call.
// State word: 0 = unlocked, 1 = locked (no waiters), 2 = locked (maybe waiters).
// This is "mutex 3" from Ulrich Drepper, "Futexes Are Tricky" (2011).
// The fast paths are one atomic instruction and no system call;
// the kernel is entered only when a thread must sleep or wake a sleeper.
// Build: gcc -Wall -Wextra -O2 -pthread futex_mutex.c -o futex_mutex
// Run:   ./futex_mutex <threads> <iters-per-thread>
#define _GNU_SOURCE
#include <linux/futex.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <unistd.h>

static atomic_long g_wait_calls, g_wake_calls;   // user-side count of futex() calls

static long futex(atomic_uint *uaddr, int op, uint32_t val)
{
    return syscall(SYS_futex, (uint32_t *)uaddr, op, val, NULL, NULL, 0);
}

static uint32_t cas(atomic_uint *p, uint32_t expected, uint32_t desired)
{
    // returns the old value, like the kernel's cmpxchg()
    atomic_compare_exchange_strong(p, &expected, desired);
    return expected;
}

static void fmutex_lock(atomic_uint *m)
{
    uint32_t c = cas(m, 0, 1);                   // fast path: 0 -> 1
    if (c == 0)
        return;
    if (c != 2)
        c = atomic_exchange(m, 2);               // announce "there may be waiters"
    while (c != 0) {
        atomic_fetch_add(&g_wait_calls, 1);
        futex(m, FUTEX_WAIT_PRIVATE, 2);         // sleeps only if *m is still 2
        c = atomic_exchange(m, 2);               // woke up: try to take it, keep "2"
    }
}

static void fmutex_unlock(atomic_uint *m)
{
    if (atomic_fetch_sub(m, 1) != 1) {           // was 2: someone may sleep
        atomic_store(m, 0);
        atomic_fetch_add(&g_wake_calls, 1);
        futex(m, FUTEX_WAKE_PRIVATE, 1);         // wake exactly one waiter
    }
}

static atomic_uint g_mutex;
static long g_counter;                           // protected by g_mutex
static long g_iters;

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
    int n = argc > 1 ? atoi(argv[1]) : 4;
    g_iters = argc > 2 ? atol(argv[2]) : 1000000;
    if (n < 1 || n > 64 || g_iters < 1) { fprintf(stderr, "usage: %s <threads> <iters>\n", argv[0]); return 2; }

    pthread_t t[64];
    for (int i = 0; i < n; i++) pthread_create(&t[i], NULL, worker, NULL);
    for (int i = 0; i < n; i++) pthread_join(t[i], NULL);

    long want = (long)n * g_iters;
    printf("threads=%d counter=%ld expected=%ld %s futex_wait=%ld futex_wake=%ld\n",
           n, g_counter, want, g_counter == want ? "OK" : "WRONG",
           atomic_load(&g_wait_calls), atomic_load(&g_wake_calls));
    return g_counter == want ? 0 : 1;
}
