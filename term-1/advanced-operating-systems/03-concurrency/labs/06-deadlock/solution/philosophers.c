// philosophers.c: extension solution for lab 03.6 (Dining Philosophers).
// Modes:
//   naive   : everyone takes left then right -> can deadlock (all hold left)
//   ordered : take the lower-numbered fork first (breaks circular wait)
//   waiter  : a counting semaphore lets at most N-1 sit down (breaks hold-and-wait cycle)
// Build: gcc -Wall -Wextra -O2 -pthread philosophers.c -o philosophers
// Run:   ./philosophers <naive|ordered|waiter> <seconds>
#define _GNU_SOURCE
#include <pthread.h>
#include <semaphore.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define N 5

static pthread_mutex_t g_fork[N];
static sem_t g_seats;
static int g_mode;                 // 0 naive, 1 ordered, 2 waiter
static atomic_int g_stop;
static atomic_long g_meals[N];

static void *philosopher(void *arg)
{
    long id = (long)arg;
    int left = (int)id, right = (int)((id + 1) % N);
    int first = left, second = right;
    if (g_mode == 1 && second < first) {   // global order: lower fork first
        first = right;
        second = left;
    }
    while (!atomic_load(&g_stop)) {
        if (g_mode == 2)
            sem_wait(&g_seats);
        pthread_mutex_lock(&g_fork[first]);
        if (g_mode == 0)
            usleep(1000);                  // make the naive deadlock likely
        pthread_mutex_lock(&g_fork[second]);
        atomic_fetch_add(&g_meals[id], 1);
        pthread_mutex_unlock(&g_fork[second]);
        pthread_mutex_unlock(&g_fork[first]);
        if (g_mode == 2)
            sem_post(&g_seats);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 3) { fprintf(stderr, "usage: %s <naive|ordered|waiter> <seconds>\n", argv[0]); return 2; }
    g_mode = strcmp(argv[1], "ordered") == 0 ? 1 : strcmp(argv[1], "waiter") == 0 ? 2 : 0;
    int secs = atoi(argv[2]);
    for (int i = 0; i < N; i++) pthread_mutex_init(&g_fork[i], NULL);
    sem_init(&g_seats, 0, N - 1);

    pthread_t t[N];
    for (long i = 0; i < N; i++) pthread_create(&t[i], NULL, philosopher, (void *)i);
    sleep((unsigned int)secs);
    atomic_store(&g_stop, 1);

    long before[N], total = 0;
    for (int i = 0; i < N; i++) before[i] = atomic_load(&g_meals[i]);
    sleep(1);                              // let non-deadlocked threads leave
    for (int i = 0; i < N; i++) total += before[i];

    printf("mode=%-7s meals:", argv[1]);
    for (int i = 0; i < N; i++) printf(" %ld", before[i]);
    printf(" total=%ld\n", total);
    // A deadlocked philosopher never returns: try to join, never block.
    int blocked = 0;
    for (int i = 0; i < N; i++) if (pthread_tryjoin_np(t[i], NULL) != 0) blocked++;
    if (blocked) {
        printf("DEADLOCK: %d philosophers still blocked after stop\n", blocked);
        fflush(stdout);
        _exit(1);
    }
    printf("all philosophers left the table\n");
    return 0;
}
