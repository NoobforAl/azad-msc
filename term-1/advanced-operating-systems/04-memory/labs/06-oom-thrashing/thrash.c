// thrash.c: read every page of a file mapping, several passes, and report
// major faults and time per pass. If the working set (file size) is larger
// than the memory limit, every pass refaults the pages that were just evicted.
//
// Build: gcc -Wall -Wextra -O2 -o thrash thrash.c
// Usage: ./thrash <file> [passes=3]
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define PAGE ((size_t)4096)

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s <file> [passes]\n", argv[0]);
        return 2;
    }
    int passes = argc > 2 ? atoi(argv[2]) : 3;
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    struct stat st;
    if (fstat(fd, &st) != 0) { perror("fstat"); return 1; }
    size_t len = (size_t)st.st_size;
    // Page-cache pages are charged to the cgroup that first faulted them in.
    // Drop this file's clean pages so every page is read (and charged) here.
    fdatasync(fd);
    posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
    const volatile uint8_t *p = mmap(NULL, len, PROT_READ, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    madvise((void *)p, len, MADV_RANDOM);   // no readahead: 1 major fault = 1 page

    uint64_t sum = 0;
    for (int pass = 1; pass <= passes; pass++) {
        struct rusage r0, r1;
        struct timespec t0, t1;
        getrusage(RUSAGE_SELF, &r0);
        clock_gettime(CLOCK_MONOTONIC, &t0);
        for (size_t off = 0; off < len; off += PAGE)
            sum += p[off];
        clock_gettime(CLOCK_MONOTONIC, &t1);
        getrusage(RUSAGE_SELF, &r1);
        double ms = (double)(t1.tv_sec - t0.tv_sec) * 1e3 + (double)(t1.tv_nsec - t0.tv_nsec) / 1e6;
        printf("pass %d: pages=%zu majflt=%ld minflt=%ld  %.0f ms\n", pass, len / PAGE,
               r1.ru_majflt - r0.ru_majflt, r1.ru_minflt - r0.ru_minflt, ms);
        fflush(stdout);
    }
    return sum == 42 ? 3 : 0;
}
