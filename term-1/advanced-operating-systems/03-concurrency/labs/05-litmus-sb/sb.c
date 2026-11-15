// sb.c: store-buffering (SB) litmus test in C11.
//   init: x = y = 0
//   T0: x = 1; r0 = y;        T1: y = 1; r1 = x;
// Can r0 == 0 && r1 == 0? Under sequential consistency: no.
// On x86-TSO: yes, because each store can sit in the core's store buffer
// while the following load reads the other variable from cache.
//
// Modes:
//   relaxed : relaxed atomics + a compiler-only barrier between store and load,
//             so any 0/0 comes from the hardware, not from the compiler
//   fence   : atomic_thread_fence(memory_order_seq_cst) between them (x86-64 gcc: a locked no-op "lock or" or MFENCE)
//   seqcst  : seq_cst store and load (x86-64 gcc: XCHG for the store, MOV for the load)
//
// Build: gcc -Wall -Wextra -O2 -pthread sb.c -o sb
// Run:   ./sb <relaxed|fence|seqcst> <iterations> [cpuA cpuB]
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum mode { RELAXED, FENCE, SEQCST };

static enum mode g_mode;
static long g_iters;
static atomic_int *g_x, *g_y;          // fresh variables per iteration: no reset race
static int *g_r0, *g_r1;
static int g_cpu[2] = {0, 1};

// Two-thread sense-reversing spin barrier: starts both threads close together.
static atomic_int g_bar_count, g_bar_sense;

static void barrier_wait(int *local_sense)
{
    *local_sense = !*local_sense;
    if (atomic_fetch_add(&g_bar_count, 1) == 1) {
        atomic_store(&g_bar_count, 0);
        atomic_store(&g_bar_sense, *local_sense);
    } else {
        while (atomic_load(&g_bar_sense) != *local_sense)
            __builtin_ia32_pause();     // ARCH-SPECIFIC (x86-64)
    }
}

static void pin(int cpu)
{
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (pthread_setaffinity_np(pthread_self(), sizeof(set), &set) != 0)
        fprintf(stderr, "warning: cannot pin to CPU %d\n", cpu);
}

static void *thread_fn(void *arg)
{
    long me = (long)arg;
    atomic_int *mine = me == 0 ? g_x : g_y;      // the variable I write
    atomic_int *other = me == 0 ? g_y : g_x;     // the variable I read
    int *out = me == 0 ? g_r0 : g_r1;
    int sense = 0;
    pin(g_cpu[me]);

    for (long i = 0; i < g_iters; i++) {
        barrier_wait(&sense);
        switch (g_mode) {
        case RELAXED:
            atomic_store_explicit(&mine[i], 1, memory_order_relaxed);
            atomic_signal_fence(memory_order_seq_cst);   // compiler barrier only
            out[i] = atomic_load_explicit(&other[i], memory_order_relaxed);
            break;
        case FENCE:
            atomic_store_explicit(&mine[i], 1, memory_order_relaxed);
            atomic_thread_fence(memory_order_seq_cst);   // full barrier (StoreLoad)
            out[i] = atomic_load_explicit(&other[i], memory_order_relaxed);
            break;
        case SEQCST:
            atomic_store_explicit(&mine[i], 1, memory_order_seq_cst);
            out[i] = atomic_load_explicit(&other[i], memory_order_seq_cst);
            break;
        }
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc != 3 && argc != 5) {
        fprintf(stderr, "usage: %s <relaxed|fence|seqcst> <iterations> [cpuA cpuB]\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "relaxed") == 0)     g_mode = RELAXED;
    else if (strcmp(argv[1], "fence") == 0)  g_mode = FENCE;
    else if (strcmp(argv[1], "seqcst") == 0) g_mode = SEQCST;
    else { fprintf(stderr, "bad mode\n"); return 2; }
    g_iters = atol(argv[2]);
    if (argc == 5) { g_cpu[0] = atoi(argv[3]); g_cpu[1] = atoi(argv[4]); }
    if (g_iters < 1) return 2;

    g_x = calloc((size_t)g_iters, sizeof(atomic_int));
    g_y = calloc((size_t)g_iters, sizeof(atomic_int));
    g_r0 = calloc((size_t)g_iters, sizeof(int));
    g_r1 = calloc((size_t)g_iters, sizeof(int));
    if (!g_x || !g_y || !g_r0 || !g_r1) { perror("calloc"); return 1; }

    pthread_t t[2];
    for (long i = 0; i < 2; i++) pthread_create(&t[i], NULL, thread_fn, (void *)i);
    for (int i = 0; i < 2; i++) pthread_join(t[i], NULL);

    long hist[2][2] = {{0, 0}, {0, 0}};
    for (long i = 0; i < g_iters; i++)
        hist[g_r0[i]][g_r1[i]]++;
    printf("mode=%-7s iters=%ld cpus=%d,%d\n", argv[1], g_iters, g_cpu[0], g_cpu[1]);
    printf("  r0=0 r1=0 : %9ld  (%.4f%%)  <- forbidden under SC\n", hist[0][0],
           100.0 * (double)hist[0][0] / (double)g_iters);
    printf("  r0=0 r1=1 : %9ld\n", hist[0][1]);
    printf("  r0=1 r1=0 : %9ld\n", hist[1][0]);
    printf("  r0=1 r1=1 : %9ld\n", hist[1][1]);
    return 0;
}
