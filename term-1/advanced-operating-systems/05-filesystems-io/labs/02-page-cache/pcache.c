// pcache.c: inspect and control the page cache for ONE file (no global drop_caches).
//   pcache resident FILE   -> pages of FILE in the page cache (mmap + mincore)
//   pcache evict FILE      -> posix_fadvise(POSIX_FADV_DONTNEED): drop clean cached pages
//   pcache read FILE       -> read the whole file with 1 MiB read()s, print time and MB/s
// Build: gcc -Wall -Wextra -O2 -o pcache pcache.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static int resident(int fd, off_t size)
{
    long page = sysconf(_SC_PAGESIZE);
    size_t npages = (size_t)((size + page - 1) / page);
    if (size == 0) {
        printf("resident: 0/0 pages\n");
        return 0;
    }
    // Mapping the file does not read it; mincore() only reports page-cache residency.
    void *map = mmap(NULL, (size_t)size, PROT_READ, MAP_SHARED, fd, 0);
    if (map == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    unsigned char *vec = malloc(npages);
    if (vec == NULL || mincore(map, (size_t)size, vec) != 0) {
        perror("mincore");
        return 1;
    }
    size_t in = 0;
    for (size_t i = 0; i < npages; i++)
        in += vec[i] & 1u;
    printf("resident: %zu/%zu pages (%.1f%%), %zu KiB of %lld KiB\n", in, npages,
           100.0 * (double)in / (double)npages, in * (size_t)page / 1024,
           (long long)size / 1024);
    free(vec);
    munmap(map, (size_t)size);
    return 0;
}

static int evict(int fd)
{
    // Dirty pages are not dropped: write them back first so DONTNEED can drop everything.
    if (fdatasync(fd) != 0)
        perror("fdatasync");
    int rc = posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
    if (rc != 0) {
        fprintf(stderr, "posix_fadvise: %s\n", strerror(rc));
        return 1;
    }
    printf("evict: POSIX_FADV_DONTNEED done\n");
    return 0;
}

static int read_all(int fd)
{
    const size_t chunk = 1u << 20;
    char *buf = malloc(chunk);
    if (buf == NULL)
        return 1;
    uint64_t total = 0;
    double t0 = now_s();
    for (;;) {
        ssize_t n = read(fd, buf, chunk);
        if (n < 0) {
            perror("read");
            return 1;
        }
        if (n == 0)
            break;
        total += (uint64_t)n;
    }
    double dt = now_s() - t0;
    printf("read: %llu MiB in %.3f s = %.0f MiB/s\n", (unsigned long long)(total >> 20), dt,
           (double)total / 1048576.0 / dt);
    free(buf);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s resident|evict|read FILE\n", argv[0]);
        return 2;
    }
    int fd = open(argv[2], O_RDONLY);
    if (fd < 0) {
        perror("open");
        return 1;
    }
    struct stat st;
    if (fstat(fd, &st) != 0) {
        perror("fstat");
        return 1;
    }
    int rc;
    if (strcmp(argv[1], "resident") == 0)
        rc = resident(fd, st.st_size);
    else if (strcmp(argv[1], "evict") == 0)
        rc = evict(fd);
    else if (strcmp(argv[1], "read") == 0)
        rc = read_all(fd);
    else {
        fprintf(stderr, "unknown command %s\n", argv[1]);
        rc = 2;
    }
    close(fd);
    return rc;
}
