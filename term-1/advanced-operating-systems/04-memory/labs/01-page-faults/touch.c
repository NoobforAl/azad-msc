// touch.c: map a region, touch every page once, and report how many page
// faults that cost (minor/major from getrusage) plus the resident size.
//
// Build: gcc -Wall -Wextra -O2 -o touch touch.c
// Usage: ./touch anon      <MiB>          write 1 byte per 4 KiB page (no THP)
//        ./touch anon-read <MiB>          read only -> shared zero page
//        ./touch thp       <MiB>          write, with MADV_HUGEPAGE (2 MiB pages)
//        ./touch file      <MiB> <path>   read a file mapping, readahead on
//        ./touch file-rand <MiB> <path>   same, but MADV_RANDOM (no readahead)
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

#define PAGE ((size_t)4096)
#define HUGE ((size_t)2 << 20)

static long rss_kib(void)
{
    long size = 0, resident = 0;
    FILE *f = fopen("/proc/self/statm", "r");
    if (f == NULL)
        return -1;
    if (fscanf(f, "%ld %ld", &size, &resident) != 2)
        resident = -1;
    fclose(f);
    return resident * (long)(PAGE / 1024);
}

static double now_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e3 + (double)ts.tv_nsec / 1e6;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s anon|anon-read|thp|file|file-rand <MiB> [path]\n", argv[0]);
        return 2;
    }
    const char *mode = argv[1];
    size_t len = (size_t)strtoul(argv[2], NULL, 10) << 20;
    int is_file = strncmp(mode, "file", 4) == 0;
    int fd = -1;
    uint8_t *p;

    if (is_file) {
        if (argc < 4) {
            fprintf(stderr, "file mode needs a path\n");
            return 2;
        }
        fd = open(argv[3], O_RDONLY);
        if (fd < 0) { perror("open"); return 1; }
        // Drop this file's clean pages from the page cache so the
        // first touch must go to disk (a major fault).
        fdatasync(fd);
        posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
        p = mmap(NULL, len, PROT_READ, MAP_PRIVATE, fd, 0);
    } else {
        // Over-allocate by 2 MiB so we can align to a huge-page boundary.
        uint8_t *raw = mmap(NULL, len + HUGE, PROT_READ | PROT_WRITE,
                            MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (raw == MAP_FAILED) { perror("mmap"); return 1; }
        p = (uint8_t *)(((uintptr_t)raw + HUGE - 1) & ~(uintptr_t)(HUGE - 1));
    }
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    if (strcmp(mode, "thp") == 0)
        madvise(p, len, MADV_HUGEPAGE);
    else if (!is_file)
        madvise(p, len, MADV_NOHUGEPAGE);
    if (strcmp(mode, "file-rand") == 0)
        madvise(p, len, MADV_RANDOM);

    struct rusage r0, r1;
    long rss0 = rss_kib();
    getrusage(RUSAGE_SELF, &r0);
    double t0 = now_ms();

    volatile uint64_t sink = 0;
    for (size_t off = 0; off < len; off += PAGE) {
        if (strcmp(mode, "anon") == 0 || strcmp(mode, "thp") == 0)
            p[off] = 1;               // write fault: allocate a private page
        else
            sink += p[off];           // read fault
    }

    double t1 = now_ms();
    getrusage(RUSAGE_SELF, &r1);
    long rss1 = rss_kib();

    printf("mode=%-9s pages=%zu  minflt=%ld  majflt=%ld  rss: %ld -> %ld KiB  %.1f ms\n",
           mode, len / PAGE, r1.ru_minflt - r0.ru_minflt, r1.ru_majflt - r0.ru_majflt,
           rss0, rss1, t1 - t0);
    (void)sink;
    if (fd >= 0)
        close(fd);
    return 0;
}
