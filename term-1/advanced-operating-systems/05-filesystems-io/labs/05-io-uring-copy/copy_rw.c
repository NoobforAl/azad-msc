// copy_rw.c: baseline file copy with a read()/write() loop. Two syscalls per block.
//   copy_rw SRC DST [block_bytes=131072]
// Build: gcc -Wall -Wextra -O2 -o copy_rw copy_rw.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s SRC DST [block_bytes]\n", argv[0]);
        return 2;
    }
    size_t bs = (argc > 3) ? strtoul(argv[3], NULL, 0) : 131072;
    int in = open(argv[1], O_RDONLY);
    int out = open(argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (in < 0 || out < 0) {
        perror("open");
        return 1;
    }
    char *buf = malloc(bs);
    if (buf == NULL)
        return 1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t total = 0, calls = 0;
    for (;;) {
        ssize_t n = read(in, buf, bs);
        calls++;
        if (n < 0) {
            perror("read");
            return 1;
        }
        if (n == 0)
            break;
        for (ssize_t off = 0; off < n;) {            // handle short writes
            ssize_t w = write(out, buf + off, (size_t)(n - off));
            calls++;
            if (w < 0) {
                perror("write");
                return 1;
            }
            off += w;
        }
        total += (uint64_t)n;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double dt = (double)(t1.tv_sec - t0.tv_sec) + (double)(t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("copy_rw:    %llu MiB, block %zu KiB, %llu read/write syscalls, %.3f s, %.0f MiB/s\n",
           (unsigned long long)(total >> 20), bs / 1024, (unsigned long long)calls, dt,
           (double)total / 1048576.0 / dt);
    close(in);
    close(out);
    free(buf);
    return 0;
}
