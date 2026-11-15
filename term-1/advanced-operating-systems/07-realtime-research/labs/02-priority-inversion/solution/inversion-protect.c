// inversion-protect.c: extension solution. inversion.c plus a third mode,
// "protect": PTHREAD_PRIO_PROTECT (priority ceiling) with ceiling 30.
// L is raised to the ceiling when it LOCKS (no contention needed), so M can never
// preempt it inside the critical section.
//
//   L (SCHED_FIFO 10) takes the mutex and needs 200 ms of CPU inside it.
//   H (SCHED_FIFO 30) wants the same mutex 20 ms later and blocks.
//   M (SCHED_FIFO 20) never touches the mutex; it just burns 800 ms of CPU.
// All threads run on ONE CPU (run under taskset -c N), so M preempts L.
//
// Build: gcc -Wall -Wextra -O2 -pthread -o inversion-protect inversion-protect.c
// Run:   sudo taskset -c 7 ./inversion-protect protect
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static pthread_mutex_t lock;
static struct timespec t0;

static double now_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)(t.tv_sec - t0.tv_sec) * 1e3 + (double)(t.tv_nsec - t0.tv_nsec) / 1e6;
}

/* Burn `ms` of this thread's own CPU time; time spent preempted does not count. */
static void burn_cpu_ms(double ms) {
    struct timespec s, c;
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &s);
    do {
        clock_gettime(CLOCK_THREAD_CPUTIME_ID, &c);
    } while ((double)(c.tv_sec - s.tv_sec) * 1e3 + (double)(c.tv_nsec - s.tv_nsec) / 1e6 < ms);
}

static void *low(void *arg) {
    (void)arg;
    pthread_mutex_lock(&lock);
    struct sched_param sp;
    int pol;
    pthread_getschedparam(pthread_self(), &pol, &sp);
    printf("%8.1f ms  L  locked (now FIFO %d), working 200 ms (CPU time)\n", now_ms(),
           sp.sched_priority);
    burn_cpu_ms(200.0);
    printf("%8.1f ms  L  unlock\n", now_ms());
    pthread_mutex_unlock(&lock);
    return NULL;
}

static void *medium(void *arg) {
    (void)arg;
    printf("%8.1f ms  M  start, burning 800 ms (no lock)\n", now_ms());
    burn_cpu_ms(800.0);
    printf("%8.1f ms  M  done\n", now_ms());
    return NULL;
}

static void *high(void *arg) {
    (void)arg;
    double t = now_ms();
    printf("%8.1f ms  H  wants the lock\n", t);
    pthread_mutex_lock(&lock);
    double waited = now_ms() - t;
    printf("%8.1f ms  H  got the lock after %.1f ms\n", now_ms(), waited);
    pthread_mutex_unlock(&lock);
    return NULL;
}

static pthread_t spawn(void *(*fn)(void *), int prio) {
    pthread_attr_t a;
    struct sched_param sp = {.sched_priority = prio};
    pthread_t t;
    pthread_attr_init(&a);
    pthread_attr_setinheritsched(&a, PTHREAD_EXPLICIT_SCHED);
    pthread_attr_setschedpolicy(&a, SCHED_FIFO);
    pthread_attr_setschedparam(&a, &sp);
    int err = pthread_create(&t, &a, fn, NULL);
    if (err != 0) {
        fprintf(stderr, "pthread_create(prio %d): %s (need root)\n", prio, strerror(err));
        exit(1);
    }
    pthread_attr_destroy(&a);
    return t;
}

int main(int argc, char **argv) {
    const char *mode = argc > 1 ? argv[1] : "none";
    pthread_mutexattr_t ma;
    pthread_mutexattr_init(&ma);
    int err = 0;
    if (strcmp(mode, "inherit") == 0) {
        err = pthread_mutexattr_setprotocol(&ma, PTHREAD_PRIO_INHERIT);
    } else if (strcmp(mode, "protect") == 0) {
        err = pthread_mutexattr_setprotocol(&ma, PTHREAD_PRIO_PROTECT);
        if (err == 0)
            err = pthread_mutexattr_setprioceiling(&ma, 30);   /* highest user: H */
    } else {
        err = pthread_mutexattr_setprotocol(&ma, PTHREAD_PRIO_NONE);
    }
    if (err != 0) {
        fprintf(stderr, "mutexattr(%s): %s\n", mode, strerror(err));
        return 1;
    }
    pthread_mutex_init(&lock, &ma);

    /* main runs above all three so it can keep creating threads on the single CPU. */
    struct sched_param sp = {.sched_priority = 50};
    if (sched_setscheduler(0, SCHED_FIFO, &sp) != 0) {
        perror("sched_setscheduler (need root)");
        return 1;
    }
    printf("protocol=%s cpu=%d\n", mode, sched_getcpu());
    clock_gettime(CLOCK_MONOTONIC, &t0);

    pthread_t l = spawn(low, 10);
    usleep(20 * 1000);                  /* L runs and takes the lock */
    pthread_t h = spawn(high, 30);      /* H preempts L and blocks on the lock */
    usleep(1000);
    pthread_t m = spawn(medium, 20);    /* M preempts L (unless L is boosted to 30) */

    pthread_join(h, NULL);
    pthread_join(l, NULL);
    pthread_join(m, NULL);
    return 0;
}
