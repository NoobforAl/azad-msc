// deadlock.c: AB-BA deadlock between two "bank transfer" threads.
//   transfer(a, b) locks a then b; the other thread calls transfer(b, a).
// Modes:
//   hang    : each thread sleeps between its two locks -> deadlock is certain
//   quick   : no sleep; usually finishes, but the lock ORDER is still inverted
//             (TSan / helgrind report it without ever hanging)
//   ordered : the fix: always lock the lower address first
// Build: gcc -Wall -Wextra -O2 -g -pthread deadlock.c -o deadlock
//        gcc -Wall -Wextra -O1 -g -fsanitize=thread -pthread deadlock.c -o deadlock-tsan
// Run:   ./deadlock <hang|quick|ordered>
#define _GNU_SOURCE
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct account {
    pthread_mutex_t lock;
    long balance;
    const char *name;
};

static struct account g_acc_a = { PTHREAD_MUTEX_INITIALIZER, 1000, "A" };
static struct account g_acc_b = { PTHREAD_MUTEX_INITIALIZER, 1000, "B" };
static int g_sleep, g_ordered;

static void transfer(struct account *from, struct account *to, long amount)
{
    struct account *first = from, *second = to;
    if (g_ordered && (uintptr_t)to < (uintptr_t)from) {   // global order: by address
        first = to;
        second = from;
    }
    pthread_mutex_lock(&first->lock);
    if (g_sleep)
        usleep(100000);            // widen the window: the other thread takes its first lock
    pthread_mutex_lock(&second->lock);
    from->balance -= amount;
    to->balance += amount;
    pthread_mutex_unlock(&second->lock);
    pthread_mutex_unlock(&first->lock);
}

static void *a_to_b(void *arg)
{
    (void)arg;
    transfer(&g_acc_a, &g_acc_b, 10);
    return NULL;
}

static void *b_to_a(void *arg)
{
    (void)arg;
    transfer(&g_acc_b, &g_acc_a, 20);
    return NULL;
}

int main(int argc, char **argv)
{
    const char *mode = argc > 1 ? argv[1] : "hang";
    g_sleep = strcmp(mode, "hang") == 0;
    g_ordered = strcmp(mode, "ordered") == 0;
    printf("pid=%d mode=%s\n", getpid(), mode);
    fflush(stdout);

    pthread_t t1, t2;
    pthread_create(&t1, NULL, a_to_b, NULL);
    if (!g_sleep)
        pthread_join(t1, NULL);    // quick/ordered: run one after the other
    pthread_create(&t2, NULL, b_to_a, NULL);
    if (g_sleep)
        pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    printf("done: A=%ld B=%ld\n", g_acc_a.balance, g_acc_b.balance);
    return 0;
}
