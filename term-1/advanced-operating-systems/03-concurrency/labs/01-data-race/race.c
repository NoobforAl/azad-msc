// race.c: N threads increment one shared counter.
// Modes: race (plain load/add/store), mutex (pthread_mutex), atomic (C11 fetch_add).
// Build: gcc -Wall -Wextra -O2 -pthread race.c -o race
//        gcc -Wall -Wextra -O1 -g -fsanitize=thread -pthread race.c -o race-tsan
// Run:   ./race <race|mutex|atomic> <threads> <iters-per-thread>
#define _GNU_SOURCE
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum mode { MODE_RACE, MODE_MUTEX, MODE_ATOMIC };

static enum mode g_mode;
static long g_iters;

// volatile forces one load and one store per iteration, so the
// compiler cannot fold the loop into "counter += iters". It does NOT
// make the increment atomic: that is the bug this lab shows.
static volatile long g_plain;
static atomic_long g_atomic;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;

static void *worker(void *arg)
{
    (void)arg;
    for (long i = 0; i < g_iters; i++) {
        switch (g_mode) {
        case MODE_RACE:
            g_plain++;                      // load, add, store: 3 steps
            break;
        case MODE_MUTEX:
            pthread_mutex_lock(&g_lock);
            g_plain++;
            pthread_mutex_unlock(&g_lock);
            break;
        case MODE_ATOMIC:
            atomic_fetch_add_explicit(&g_atomic, 1, memory_order_relaxed);
            break;
        }
    }
    return NULL;
}

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s <race|mutex|atomic> <threads> <iters>\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "race") == 0)        g_mode = MODE_RACE;
    else if (strcmp(argv[1], "mutex") == 0)  g_mode = MODE_MUTEX;
    else if (strcmp(argv[1], "atomic") == 0) g_mode = MODE_ATOMIC;
    else { fprintf(stderr, "bad mode %s\n", argv[1]); return 2; }

    int nthreads = atoi(argv[2]);
    g_iters = atol(argv[3]);
    if (nthreads < 1 || nthreads > 256 || g_iters < 1) {
        fprintf(stderr, "threads must be 1..256, iters >= 1\n");
        return 2;
    }

    pthread_t tid[256];
    double t0 = now_sec();
    for (int i = 0; i < nthreads; i++)
        pthread_create(&tid[i], NULL, worker, NULL);
    for (int i = 0; i < nthreads; i++)
        pthread_join(tid[i], NULL);
    double dt = now_sec() - t0;

    long expected = (long)nthreads * g_iters;
    long got = (g_mode == MODE_ATOMIC) ? atomic_load(&g_atomic) : g_plain;
    printf("mode=%-6s threads=%d expected=%ld got=%ld lost=%ld time=%.3fs ns/inc=%.1f\n",
           argv[1], nthreads, expected, got, expected - got, dt,
           dt * 1e9 / (double)expected);
    return got == expected ? 0 : 1;
}
