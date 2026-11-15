// wbench.c: cost of durability. Write N records of B bytes with one of five policies
// and report total time and per-record latency (mean, p50, p99, max).
//   wbench MODE FILE [records=2000] [bytes=4096]
//   MODE: buffered | fsync | fdatasync | osync | odsync
//     buffered   write() only: data sits dirty in the page cache, writeback does the rest
//     fsync      write() + fsync() after every record (data + all metadata)
//     fdatasync  write() + fdatasync() after every record (data + size-changing metadata)
//     osync      open with O_SYNC  (every write behaves like write+fsync)
//     odsync     open with O_DSYNC (every write behaves like write+fdatasync)
// Build: gcc -Wall -Wextra -O2 -o wbench wbench.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int cmp_u64(const void *a, const void *b)
{
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s buffered|fsync|fdatasync|osync|odsync FILE [records] [bytes]\n",
                argv[0]);
        return 2;
    }
    const char *mode = argv[1];
    long n = (argc > 3) ? strtol(argv[3], NULL, 0) : 2000;
    size_t bs = (argc > 4) ? strtoul(argv[4], NULL, 0) : 4096;
    int flags = O_WRONLY | O_CREAT | O_TRUNC;
    int sync_call = 0; // 1 = fsync, 2 = fdatasync

    if (strcmp(mode, "fsync") == 0)
        sync_call = 1;
    else if (strcmp(mode, "fdatasync") == 0)
        sync_call = 2;
    else if (strcmp(mode, "osync") == 0)
        flags |= O_SYNC;
    else if (strcmp(mode, "odsync") == 0)
        flags |= O_DSYNC;
    else if (strcmp(mode, "buffered") != 0) {
        fprintf(stderr, "unknown mode %s\n", mode);
        return 2;
    }

    int fd = open(argv[2], flags, 0644);
    if (fd < 0) {
        perror("open");
        return 1;
    }
    char *buf = malloc(bs);
    uint64_t *lat = malloc((size_t)n * sizeof(*lat));
    if (buf == NULL || lat == NULL)
        return 1;
    memset(buf, 'x', bs);

    uint64_t t0 = now_ns();
    for (long i = 0; i < n; i++) {
        uint64_t s = now_ns();
        if (write(fd, buf, bs) != (ssize_t)bs) {
            perror("write");
            return 1;
        }
        if (sync_call == 1 && fsync(fd) != 0) {
            perror("fsync");
            return 1;
        }
        if (sync_call == 2 && fdatasync(fd) != 0) {
            perror("fdatasync");
            return 1;
        }
        lat[i] = now_ns() - s;
    }
    uint64_t total = now_ns() - t0;
    close(fd);

    qsort(lat, (size_t)n, sizeof(*lat), cmp_u64);
    printf("%-9s %5ld x %zu B: total %8.1f ms | per record: mean %8.1f us  p50 %8.1f us"
           "  p99 %8.1f us  max %8.1f us\n",
           mode, n, bs, (double)total / 1e6, (double)total / (double)n / 1e3,
           (double)lat[n / 2] / 1e3, (double)lat[(n * 99) / 100] / 1e3,
           (double)lat[n - 1] / 1e3);
    free(buf);
    free(lat);
    return 0;
}
