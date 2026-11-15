// pc_cond.c: the same bounded buffer with one mutex and two condition variables.
// Build: gcc -Wall -Wextra -O2 -pthread pc_cond.c -o pc_cond
// Run:   ./pc_cond <items> <buffer-size>
// The waits use while(), never if(): see README "What to observe" 3.
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static long *g_buf;
static long g_cap, g_items, g_count, g_head, g_tail;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t g_not_full = PTHREAD_COND_INITIALIZER;
static pthread_cond_t g_not_empty = PTHREAD_COND_INITIALIZER;
static long g_waits_full, g_waits_empty;   // how often each side had to sleep

static void *producer(void *arg)
{
    (void)arg;
    for (long i = 1; i <= g_items; i++) {
        pthread_mutex_lock(&g_lock);
        while (g_count == g_cap) {           // re-check after every wake-up
            g_waits_full++;
            pthread_cond_wait(&g_not_full, &g_lock);
        }
        g_buf[g_head] = i;
        g_head = (g_head + 1) % g_cap;
        g_count++;
        pthread_cond_signal(&g_not_empty);
        pthread_mutex_unlock(&g_lock);
    }
    return NULL;
}

static void *consumer(void *arg)
{
    long *sum = arg;
    for (long i = 0; i < g_items; i++) {
        pthread_mutex_lock(&g_lock);
        while (g_count == 0) {
            g_waits_empty++;
            pthread_cond_wait(&g_not_empty, &g_lock);
        }
        long v = g_buf[g_tail];
        g_tail = (g_tail + 1) % g_cap;
        g_count--;
        pthread_cond_signal(&g_not_full);
        pthread_mutex_unlock(&g_lock);
        *sum += v;
    }
    return NULL;
}

int main(int argc, char **argv)
{
    g_items = argc > 1 ? atol(argv[1]) : 1000000;
    g_cap = argc > 2 ? atol(argv[2]) : 16;
    if (g_items < 1 || g_cap < 1) { fprintf(stderr, "usage: %s <items> <cap>\n", argv[0]); return 2; }
    g_buf = calloc((size_t)g_cap, sizeof(long));
    if (!g_buf) return 1;

    long sum = 0;
    pthread_t p, c;
    struct timespec a, b;
    clock_gettime(CLOCK_MONOTONIC, &a);
    pthread_create(&p, NULL, producer, NULL);
    pthread_create(&c, NULL, consumer, &sum);
    pthread_join(p, NULL);
    pthread_join(c, NULL);
    clock_gettime(CLOCK_MONOTONIC, &b);

    double dt = (double)(b.tv_sec - a.tv_sec) + (double)(b.tv_nsec - a.tv_nsec) / 1e9;
    long want = g_items * (g_items + 1) / 2;
    printf("cond  items=%ld cap=%ld sum=%ld %s time=%.3fs ns/item=%.0f waits(full)=%ld waits(empty)=%ld\n",
           g_items, g_cap, sum, sum == want ? "OK" : "WRONG", dt, dt * 1e9 / (double)g_items,
           g_waits_full, g_waits_empty);
    free(g_buf);
    return sum == want ? 0 : 1;
}
