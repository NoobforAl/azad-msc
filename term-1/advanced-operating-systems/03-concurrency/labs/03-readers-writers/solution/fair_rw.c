// fair_rw.c: extension solution for lab 03.3.
// A no-starvation readers-writers lock built from three semaphores
// (the "turnstile" solution from Downey, The Little Book of Semaphores, 4.2.6).
// A waiting writer holds the turnstile, so new readers queue behind it.
// Build: gcc -Wall -Wextra -O2 -pthread fair_rw.c -o fair_rw
// Run:   ./fair_rw <readers> <seconds>
#define _GNU_SOURCE
#include <pthread.h>
#include <semaphore.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

struct fair_rw {
    sem_t turnstile;      // readers and writers pass through it in arrival order
    sem_t room_empty;     // 1 while no one is inside
    sem_t mutex;          // protects readers
    int readers;
};

static void frw_init(struct fair_rw *l)
{
    sem_init(&l->turnstile, 0, 1);
    sem_init(&l->room_empty, 0, 1);
    sem_init(&l->mutex, 0, 1);
    l->readers = 0;
}

static void frw_rdlock(struct fair_rw *l)
{
    sem_wait(&l->turnstile);              // blocks while a writer is waiting
    sem_post(&l->turnstile);
    sem_wait(&l->mutex);
    if (++l->readers == 1)
        sem_wait(&l->room_empty);         // first reader locks writers out
    sem_post(&l->mutex);
}

static void frw_rdunlock(struct fair_rw *l)
{
    sem_wait(&l->mutex);
    if (--l->readers == 0)
        sem_post(&l->room_empty);         // last reader lets a writer in
    sem_post(&l->mutex);
}

static void frw_wrlock(struct fair_rw *l)
{
    sem_wait(&l->turnstile);              // stop new readers from entering
    sem_wait(&l->room_empty);             // wait for current readers to drain
}

static void frw_wrunlock(struct fair_rw *l)
{
    sem_post(&l->turnstile);
    sem_post(&l->room_empty);
}

static struct fair_rw g_rw;
static atomic_int g_stop;
static atomic_long g_reads;
static long g_writes;
static double g_wait_max, g_wait_sum;

static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static void busy(double sec)
{
    double end = now() + sec;
    while (now() < end)
        ;
}

static void *reader(void *arg)
{
    (void)arg;
    while (!atomic_load(&g_stop)) {
        frw_rdlock(&g_rw);
        busy(100e-6);
        frw_rdunlock(&g_rw);
        atomic_fetch_add(&g_reads, 1);
    }
    return NULL;
}

static void *writer(void *arg)
{
    (void)arg;
    while (!atomic_load(&g_stop)) {
        double t0 = now();
        frw_wrlock(&g_rw);
        double w = now() - t0;
        g_writes++;
        if (w > g_wait_max) g_wait_max = w;
        g_wait_sum += w;
        busy(10e-6);
        frw_wrunlock(&g_rw);
        usleep(1000);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 3) { fprintf(stderr, "usage: %s <readers> <seconds>\n", argv[0]); return 2; }
    int nr = atoi(argv[1]), secs = atoi(argv[2]);
    if (nr < 1 || nr > 64 || secs < 1) return 2;
    frw_init(&g_rw);

    pthread_t rt[64], wt;
    for (int i = 0; i < nr; i++) pthread_create(&rt[i], NULL, reader, NULL);
    usleep(10000);
    pthread_create(&wt, NULL, writer, NULL);
    sleep((unsigned int)secs);
    atomic_store(&g_stop, 1);
    for (int i = 0; i < nr; i++) pthread_join(rt[i], NULL);
    pthread_join(wt, NULL);

    printf("pref=fair   readers=%d secs=%d reads=%ld writes=%ld writer_wait max=%.3fs avg=%.6fs\n",
           nr, secs, atomic_load(&g_reads), g_writes, g_wait_max,
           g_writes ? g_wait_sum / (double)g_writes : 0.0);
    return 0;
}
