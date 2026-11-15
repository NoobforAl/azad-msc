// readone.c: open a file, read() it in fixed-size chunks, print what happened.
// A deliberately tiny program so ftrace/bpftrace output contains only our read() calls.
// Build: gcc -Wall -Wextra -O2 -o readone readone.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s FILE [chunk_bytes=4096] [max_reads=1]\n", argv[0]);
        return 2;
    }
    size_t chunk = (argc > 2) ? strtoul(argv[2], NULL, 0) : 4096;
    long max_reads = (argc > 3) ? strtol(argv[3], NULL, 0) : 1;

    char *buf = malloc(chunk);
    if (buf == NULL) {
        perror("malloc");
        return 1;
    }
    int fd = open(argv[1], O_RDONLY);          // openat(2): path walk + fd_install
    if (fd < 0) {
        perror("open");
        return 1;
    }
    long total = 0;
    for (long i = 0; i < max_reads; i++) {
        ssize_t n = read(fd, buf, chunk);       // read(2) -> ksys_read -> vfs_read
        if (n < 0) {
            perror("read");
            return 1;
        }
        if (n == 0)
            break;                              // EOF
        total += (long)n;
    }
    printf("pid=%d fd=%d read %ld bytes in chunks of %zu\n", (int)getpid(), fd, total, chunk);
    close(fd);
    free(buf);
    return 0;
}
