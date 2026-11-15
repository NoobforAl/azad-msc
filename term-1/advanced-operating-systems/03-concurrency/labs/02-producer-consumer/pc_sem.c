// pc_sem.c: bounded-buffer Producer-Consumer with POSIX semaphores.
// "empty" counts free slots, "full" counts filled slots, a mutex guards the indices.
// Build: gcc -Wall -Wextra -O2 -pthread pc_sem.c -o pc_sem
// Run:   ./pc_sem <items> <buffer-size>
#define _GNU_SOURCE
#include <pthread.h>
#include <semaphore.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static long *g_buf;
static long g_cap, g_items;
static long g_head, g_tail;          // head: next slot to fill, tail: next slot to drain
static sem_t g_empty, g_full;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;

static void *producer(void *arg)
{
    (void)arg;
    for (long i = 1; i <= g_items; i++) {
        sem_wait(&g_empty);                 // P(empty): wait for a free slot
        pthread_mutex_lock(&g_lock);
        g_buf[g_head] = i;
        g_head = (g_head + 1) % g_cap;
        pthread_mutex_unlock(&g_lock);
        sem_post(&g_full);                  // V(full): one more item
    }
    return NULL;
}

static void *consumer(void *arg)
{
    long *sum = arg;
    for (long i = 0; i < g_items; i++) {
        sem_wait(&g_full);
        pthread_mutex_lock(&g_lock);
        long v = g_buf[g_tail];
        g_tail = (g_tail + 1) % g_cap;
        pthread_mutex_unlock(&g_lock);
        sem_post(&g_empty);
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
    sem_init(&g_empty, 0, (unsigned int)g_cap);
    sem_init(&g_full, 0, 0);

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
    printf("sem   items=%ld cap=%ld sum=%ld %s time=%.3fs ns/item=%.0f\n",
           g_items, g_cap, sum, sum == want ? "OK" : "WRONG", dt, dt * 1e9 / (double)g_items);
    free(g_buf);
    return sum == want ? 0 : 1;
}
