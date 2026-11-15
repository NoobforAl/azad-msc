// sharded.c: extension solution for lab 03.1.
// Each thread counts into its own slot and the main thread sums at the end.
// "packed" puts the slots next to each other (false sharing: one cache line
// bounces between cores); "padded" gives each slot its own 64-byte line.
// Build: gcc -Wall -Wextra -O2 -pthread sharded.c -o sharded
// Run:   ./sharded <packed|padded> <threads> <iters-per-thread>
#define _GNU_SOURCE
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_THREADS 64
#define CACHE_LINE 64

struct packed_slot { atomic_long v; };
struct padded_slot { _Alignas(CACHE_LINE) atomic_long v; char pad[CACHE_LINE - sizeof(atomic_long)]; };

static struct packed_slot g_packed[MAX_THREADS];
static struct padded_slot g_padded[MAX_THREADS];
static int g_use_padded;
static long g_iters;

static void *worker(void *arg)
{
    long id = (long)arg;
    atomic_long *slot = g_use_padded ? &g_padded[id].v : &g_packed[id].v;
    for (long i = 0; i < g_iters; i++)
        atomic_fetch_add_explicit(slot, 1, memory_order_relaxed);
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s <packed|padded> <threads> <iters>\n", argv[0]);
        return 2;
    }
    g_use_padded = strcmp(argv[1], "padded") == 0;
    int n = atoi(argv[2]);
    g_iters = atol(argv[3]);
    if (n < 1 || n > MAX_THREADS) { fprintf(stderr, "threads 1..%d\n", MAX_THREADS); return 2; }

    pthread_t tid[MAX_THREADS];
    struct timespec a, b;
    clock_gettime(CLOCK_MONOTONIC, &a);
    for (long i = 0; i < n; i++)
        pthread_create(&tid[i], NULL, worker, (void *)i);
    for (int i = 0; i < n; i++)
        pthread_join(tid[i], NULL);
    clock_gettime(CLOCK_MONOTONIC, &b);

    long sum = 0;
    for (int i = 0; i < n; i++)
        sum += g_use_padded ? atomic_load(&g_padded[i].v) : atomic_load(&g_packed[i].v);
    double dt = (double)(b.tv_sec - a.tv_sec) + (double)(b.tv_nsec - a.tv_nsec) / 1e9;
    printf("layout=%-6s threads=%d sum=%ld time=%.3fs ns/inc=%.2f\n",
           argv[1], n, sum, dt, dt * 1e9 / (double)((long)n * g_iters));
    return 0;
}
