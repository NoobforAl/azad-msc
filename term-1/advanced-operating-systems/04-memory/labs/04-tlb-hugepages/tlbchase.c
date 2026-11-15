// tlbchase.c: TLB-reach benchmark without hardware counters.
// A random pointer chase touches exactly ONE cache line per page, over a
// growing number of pages. The data footprint (pages * 64 B) is the same for
// 4 KiB and 2 MiB pages, so the difference between the two runs is the cost of
// TLB misses and page walks, not of data-cache misses.
//
// Build: gcc -Wall -Wextra -O2 -o tlbchase tlbchase.c
// Usage: ./tlbchase 4k  <MiB>     MADV_NOHUGEPAGE (4 KiB pages)
//        ./tlbchase thp <MiB>     MADV_HUGEPAGE   (2 MiB pages if THP allows)
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

#define PAGE ((size_t)4096)
#define HUGE ((size_t)2 << 20)
#define STEPS ((uint64_t)20 * 1000 * 1000)

static double now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

// AnonHugePages of the VMA that contains addr, from /proc/self/smaps.
static long anon_huge_kib(const void *addr)
{
    FILE *f = fopen("/proc/self/smaps", "r");
    char line[512];
    int in = 0;
    long kib = -1;
    if (f == NULL)
        return -1;
    while (fgets(line, sizeof(line), f) != NULL) {
        unsigned long lo, hi;
        char perms[8];
        if (sscanf(line, "%lx-%lx %7s", &lo, &hi, perms) == 3) {
            if (in)
                break;
            in = (uintptr_t)addr >= lo && (uintptr_t)addr < hi;
            continue;
        }
        if (in)
            sscanf(line, "AnonHugePages: %ld", &kib);
    }
    fclose(f);
    return kib;
}

static uint64_t rng_state = 88172645463325252ULL;
static uint64_t xorshift(void)
{
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return rng_state;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s 4k|thp <MiB>\n", argv[0]);
        return 2;
    }
    int thp = strcmp(argv[1], "thp") == 0;
    size_t len = (size_t)strtoul(argv[2], NULL, 10) << 20;
    size_t max_pages = len / PAGE;

    uint8_t *raw = mmap(NULL, len + HUGE, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (raw == MAP_FAILED) { perror("mmap"); return 1; }
    uint8_t *buf = (uint8_t *)(((uintptr_t)raw + HUGE - 1) & ~(uintptr_t)(HUGE - 1));
    madvise(buf, len, thp ? MADV_HUGEPAGE : MADV_NOHUGEPAGE);
    memset(buf, 0, len);   // fault everything in before timing

    size_t *order = malloc(max_pages * sizeof(size_t));
    if (order == NULL) { perror("malloc"); return 1; }

    printf("# mode=%s region=%zu MiB AnonHugePages=%ld kB\n",
           thp ? "thp" : "4k", len >> 20, anon_huge_kib(buf));
    printf("# %8s %10s %12s\n", "pages", "span_MiB", "ns/access");

    for (size_t n = 16; n <= max_pages; n *= 2) {
        // Random cyclic order over n pages (Fisher-Yates).
        for (size_t i = 0; i < n; i++)
            order[i] = i;
        for (size_t i = n - 1; i > 0; i--) {
            size_t j = (size_t)(xorshift() % (i + 1));
            size_t t = order[i]; order[i] = order[j]; order[j] = t;
        }
        // Cache-line offset varies per page so lines spread over cache sets.
        for (size_t i = 0; i < n; i++) {
            size_t from = order[i], to = order[(i + 1) % n];
            void **src = (void **)(buf + from * PAGE + (from % 64) * 64);
            *src = buf + to * PAGE + (to % 64) * 64;
        }
        void **p = (void **)(buf + order[0] * PAGE + (order[0] % 64) * 64);
        for (uint64_t s = 0; s < n * 4; s++)   // warm up
            p = (void **)*p;
        double t0 = now_ns();
        for (uint64_t s = 0; s < STEPS; s++)
            p = (void **)*p;
        double t1 = now_ns();
        printf("  %8zu %10.1f %12.2f%s\n", n, (double)(n * PAGE) / (1 << 20),
               (t1 - t0) / (double)STEPS, p == NULL ? "!" : "");
    }
    free(order);
    return 0;
}
