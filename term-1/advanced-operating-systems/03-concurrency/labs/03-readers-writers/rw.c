// rw.c: Readers-Writers with pthread_rwlock; shows writer starvation.
// R readers hold the read lock back to back (always at least one inside),
// one writer tries to take the write lock every millisecond.
// Build: gcc -Wall -Wextra -O2 -pthread rw.c -o rw
// Run:   ./rw <reader|writer> <readers> <seconds>
//   reader = glibc default (PTHREAD_RWLOCK_PREFER_READER_NP)
//   writer = PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP
#define _GNU_SOURCE
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static pthread_rwlock_t g_rw;
static atomic_int g_stop;
static atomic_long g_reads;
static long g_writes, g_writes_late;          // late = acquired only after the stop flag
static double g_wait_max, g_wait_sum;

static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static void busy(double sec)                  // stay on-CPU inside the critical section
{
    double end = now() + sec;
    while (now() < end)
        ;
}

static void *reader(void *arg)
{
    (void)arg;
    while (!atomic_load(&g_stop)) {
        pthread_rwlock_rdlock(&g_rw);
        busy(100e-6);                         // 100 us read-side section
        pthread_rwlock_unlock(&g_rw);
        atomic_fetch_add(&g_reads, 1);
    }
    return NULL;
}

static void *writer(void *arg)
{
    (void)arg;
    while (!atomic_load(&g_stop)) {
        double t0 = now();
        pthread_rwlock_wrlock(&g_rw);
        double w = now() - t0;
        if (atomic_load(&g_stop)) g_writes_late++; else g_writes++;
        if (w > g_wait_max) g_wait_max = w;
        g_wait_sum += w;
        busy(10e-6);                          // 10 us write
        pthread_rwlock_unlock(&g_rw);
        usleep(1000);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 4) { fprintf(stderr, "usage: %s <reader|writer> <readers> <seconds>\n", argv[0]); return 2; }
    int writer_pref = strcmp(argv[1], "writer") == 0;
    int nr = atoi(argv[2]);
    int secs = atoi(argv[3]);
    if (nr < 1 || nr > 64 || secs < 1) return 2;

    pthread_rwlockattr_t at;
    pthread_rwlockattr_init(&at);
    pthread_rwlockattr_setkind_np(&at, writer_pref ? PTHREAD_RWLOCK_PREFER_WRITER_NONRECURSIVE_NP
                                                   : PTHREAD_RWLOCK_PREFER_READER_NP);
    pthread_rwlock_init(&g_rw, &at);

    pthread_t rt[64], wt;
    for (int i = 0; i < nr; i++) pthread_create(&rt[i], NULL, reader, NULL);
    usleep(10000);                            // let the readers fill the lock first
    pthread_create(&wt, NULL, writer, NULL);
    sleep((unsigned int)secs);
    atomic_store(&g_stop, 1);
    for (int i = 0; i < nr; i++) pthread_join(rt[i], NULL);
    pthread_join(wt, NULL);

    long n = g_writes + g_writes_late;
    printf("pref=%-6s readers=%d secs=%d reads=%ld writes=%ld (+%ld after stop) "
           "writer_wait max=%.3fs avg=%.6fs\n",
           argv[1], nr, secs, atomic_load(&g_reads), g_writes, g_writes_late,
           g_wait_max, n ? g_wait_sum / (double)n : 0.0);
    return 0;
}
