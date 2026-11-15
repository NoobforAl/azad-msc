// mapcount.c: N child processes increment one 64-bit counter through mmap().
// The mapping type decides who sees the increments and whether the file changes.
//
// Build: gcc -Wall -Wextra -O2 -o mapcount mapcount.c
// Usage: ./mapcount file-shared  counter.bin [children] [iters]
//        ./mapcount file-private counter.bin
//        ./mapcount anon-shared
//        ./mapcount anon-private
#define _GNU_SOURCE
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

#define LEN ((size_t)4096)

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s file-shared|file-private|anon-shared|anon-private [path] [children] [iters]\n", argv[0]);
        return 2;
    }
    const char *mode = argv[1];
    int is_file = strncmp(mode, "file", 4) == 0;
    int shared = strstr(mode, "shared") != NULL;
    int argi = is_file ? 3 : 2;
    int children = argc > argi ? atoi(argv[argi]) : 4;
    long iters = argc > argi + 1 ? atol(argv[argi + 1]) : 1000000L;
    int fd = -1;
    int flags = shared ? MAP_SHARED : MAP_PRIVATE;

    if (is_file) {
        if (argc < 3) { fprintf(stderr, "file modes need a path\n"); return 2; }
        fd = open(argv[2], O_RDWR | O_CREAT | O_TRUNC, 0644);
        if (fd < 0) { perror("open"); return 1; }
        if (ftruncate(fd, (off_t)LEN) != 0) { perror("ftruncate"); return 1; }
    } else {
        flags |= MAP_ANONYMOUS;
    }

    uint64_t *ctr = mmap(NULL, LEN, PROT_READ | PROT_WRITE, flags, fd, 0);
    if (ctr == MAP_FAILED) { perror("mmap"); return 1; }

    for (int i = 0; i < children; i++) {
        pid_t pid = fork();
        if (pid < 0) { perror("fork"); return 1; }
        if (pid == 0) {
            for (long n = 0; n < iters; n++)
                __atomic_fetch_add(ctr, 1, __ATOMIC_RELAXED);
            _exit(0);
        }
    }
    while (wait(NULL) > 0)
        ;

    uint64_t from_file = 0;
    if (is_file) {
        msync(ctr, LEN, MS_SYNC);   // push dirty shared pages to the file now
        if (pread(fd, &from_file, sizeof(from_file), 0) != (ssize_t)sizeof(from_file))
            from_file = UINT64_MAX;
    }
    printf("%-12s children=%d iters=%ld  expected=%ld  parent sees=%" PRIu64,
           mode, children, iters, (long)children * iters, *ctr);
    if (is_file)
        printf("  file has=%" PRIu64, from_file);
    printf("\n");
    return 0;
}
