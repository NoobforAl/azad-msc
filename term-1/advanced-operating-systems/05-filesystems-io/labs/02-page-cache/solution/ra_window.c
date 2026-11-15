// ra_window.c: extension solution. Evict FILE, optionally set POSIX_FADV_RANDOM on the fd,
// read ONLY the first 4 KiB, then count how many pages of FILE became resident.
//   ra_window FILE normal|random
// Build: gcc -Wall -Wextra -O2 -o ra_window ra_window.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s FILE normal|random\n", argv[0]);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) {
        perror("open");
        return 1;
    }
    struct stat st;
    if (fstat(fd, &st) != 0)
        return 1;
    posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);          // cold start for this file
    if (strcmp(argv[2], "random") == 0)
        posix_fadvise(fd, 0, 0, POSIX_FADV_RANDOM);        // sets FMODE_RANDOM: no readahead

    char buf[4096];
    if (read(fd, buf, sizeof(buf)) != (ssize_t)sizeof(buf)) {
        perror("read");
        return 1;
    }

    long page = sysconf(_SC_PAGESIZE);
    size_t npages = (size_t)((st.st_size + page - 1) / page);
    void *map = mmap(NULL, (size_t)st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    unsigned char *vec = malloc(npages);
    if (map == MAP_FAILED || vec == NULL || mincore(map, (size_t)st.st_size, vec) != 0) {
        perror("mincore");
        return 1;
    }
    size_t in = 0;
    for (size_t i = 0; i < npages; i++)
        in += vec[i] & 1u;
    printf("%-6s: read 4 KiB -> %zu pages (%zu KiB) resident\n", argv[2], in,
           in * (size_t)page / 1024);
    return 0;
}
