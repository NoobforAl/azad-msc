// mp.c: extension solution for lab 03.5: the message-passing (MP) litmus test.
//   T0: data = 1; flag = 1;      T1: r0 = flag; r1 = data;
// Outcome r0 == 1 && r1 == 0 ("saw the flag, missed the data") is ALLOWED by
// C11 with relaxed atomics, but x86-TSO never produces it: TSO keeps
// store->store and load->load order. On Arm/POWER it does appear.
// So relaxed code that "works" on x86 can still be wrong: use release/acquire.
// Build: gcc -Wall -Wextra -O2 -pthread mp.c -o mp
// Run:   ./mp <iterations>
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>

static long g_iters;
static atomic_int *g_data, *g_flag;
static int *g_r0, *g_r1;
static atomic_int g_bar_count, g_bar_sense;

static void barrier_wait(int *s)
{
    *s = !*s;
    if (atomic_fetch_add(&g_bar_count, 1) == 1) {
        atomic_store(&g_bar_count, 0);
        atomic_store(&g_bar_sense, *s);
    } else {
        while (atomic_load(&g_bar_sense) != *s)
            __builtin_ia32_pause();
    }
}

static void pin(int cpu)
{
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
}

static void *writer(void *arg)
{
    (void)arg;
    int s = 0;
    pin(0);
    for (long i = 0; i < g_iters; i++) {
        barrier_wait(&s);
        atomic_store_explicit(&g_data[i], 1, memory_order_relaxed);
        atomic_signal_fence(memory_order_seq_cst);          // compiler barrier only
        atomic_store_explicit(&g_flag[i], 1, memory_order_relaxed);
    }
    return NULL;
}

static void *reader(void *arg)
{
    (void)arg;
    int s = 0;
    pin(1);
    for (long i = 0; i < g_iters; i++) {
        barrier_wait(&s);
        g_r0[i] = atomic_load_explicit(&g_flag[i], memory_order_relaxed);
        atomic_signal_fence(memory_order_seq_cst);
        g_r1[i] = atomic_load_explicit(&g_data[i], memory_order_relaxed);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    g_iters = argc > 1 ? atol(argv[1]) : 1000000;
    if (g_iters < 1) return 2;
    g_data = calloc((size_t)g_iters, sizeof(atomic_int));
    g_flag = calloc((size_t)g_iters, sizeof(atomic_int));
    g_r0 = calloc((size_t)g_iters, sizeof(int));
    g_r1 = calloc((size_t)g_iters, sizeof(int));
    if (!g_data || !g_flag || !g_r0 || !g_r1) return 1;

    pthread_t a, b;
    pthread_create(&a, NULL, writer, NULL);
    pthread_create(&b, NULL, reader, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);

    long h[2][2] = {{0, 0}, {0, 0}};
    for (long i = 0; i < g_iters; i++)
        h[g_r0[i]][g_r1[i]]++;
    printf("MP iters=%ld\n", g_iters);
    printf("  flag=0 data=0 : %9ld\n", h[0][0]);
    printf("  flag=0 data=1 : %9ld\n", h[0][1]);
    printf("  flag=1 data=0 : %9ld  <- allowed by C11 relaxed, never on x86-TSO\n", h[1][0]);
    printf("  flag=1 data=1 : %9ld\n", h[1][1]);
    return 0;
}
