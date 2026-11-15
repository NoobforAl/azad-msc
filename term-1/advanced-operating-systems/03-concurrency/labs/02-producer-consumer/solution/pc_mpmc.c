// pc_mpmc.c: extension solution for lab 03.2.
// P producers, C consumers, one bounded buffer (mutex + 2 condvars), clean shutdown.
// Each producer pushes its own range; after joining the producers, main pushes
// C "poison pills" (value 0) so every consumer leaves its loop exactly once.
// Build: gcc -Wall -Wextra -O2 -pthread pc_mpmc.c -o pc_mpmc
// Run:   ./pc_mpmc <producers> <consumers> <items-per-producer> <cap>
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#define MAXT 64

static long *g_buf;
static long g_cap, g_count, g_head, g_tail, g_per;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t g_not_full = PTHREAD_COND_INITIALIZER;
static pthread_cond_t g_not_empty = PTHREAD_COND_INITIALIZER;

static void put(long v)
{
    pthread_mutex_lock(&g_lock);
    while (g_count == g_cap)             // while, not if: another producer may refill first
        pthread_cond_wait(&g_not_full, &g_lock);
    g_buf[g_head] = v;
    g_head = (g_head + 1) % g_cap;
    g_count++;
    pthread_cond_signal(&g_not_empty);
    pthread_mutex_unlock(&g_lock);
}

static long get(void)
{
    pthread_mutex_lock(&g_lock);
    while (g_count == 0)                 // while, not if: another consumer may drain first
        pthread_cond_wait(&g_not_empty, &g_lock);
    long v = g_buf[g_tail];
    g_tail = (g_tail + 1) % g_cap;
    g_count--;
    pthread_cond_signal(&g_not_full);
    pthread_mutex_unlock(&g_lock);
    return v;
}

static void *producer(void *arg)
{
    long id = (long)arg;
    for (long i = 1; i <= g_per; i++)
        put(id * g_per + i);             // values are unique and never 0
    return NULL;
}

static void *consumer(void *arg)
{
    long *sum = arg;
    for (;;) {
        long v = get();
        if (v == 0)                      // poison pill
            return NULL;
        *sum += v;
    }
}

int main(int argc, char **argv)
{
    if (argc != 5) { fprintf(stderr, "usage: %s <P> <C> <items/producer> <cap>\n", argv[0]); return 2; }
    int np = atoi(argv[1]), nc = atoi(argv[2]);
    g_per = atol(argv[3]);
    g_cap = atol(argv[4]);
    if (np < 1 || np > MAXT || nc < 1 || nc > MAXT || g_per < 1 || g_cap < 1) return 2;
    g_buf = calloc((size_t)g_cap, sizeof(long));
    if (!g_buf) return 1;

    pthread_t pt[MAXT], ct[MAXT];
    long sums[MAXT] = {0};
    for (long i = 0; i < np; i++) pthread_create(&pt[i], NULL, producer, (void *)i);
    for (int i = 0; i < nc; i++)  pthread_create(&ct[i], NULL, consumer, &sums[i]);
    for (int i = 0; i < np; i++)  pthread_join(pt[i], NULL);
    for (int i = 0; i < nc; i++)  put(0);
    for (int i = 0; i < nc; i++)  pthread_join(ct[i], NULL);

    long total = 0, n = (long)np * g_per;
    for (int i = 0; i < nc; i++) total += sums[i];
    long want = n * (n + 1) / 2;         // values are exactly 1..P*per
    printf("P=%d C=%d items=%ld sum=%ld %s\n", np, nc, n, total, total == want ? "OK" : "WRONG");
    free(g_buf);
    return total == want ? 0 : 1;
}
