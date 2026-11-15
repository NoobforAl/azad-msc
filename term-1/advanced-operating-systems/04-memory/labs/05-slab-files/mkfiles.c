// mkfiles.c: create or delete N empty files in a directory, fast.
// Each new file costs kernel objects (dentry, inode, ...) from slab caches,
// but no data blocks.
//
// Build: gcc -Wall -Wextra -O2 -o mkfiles mkfiles.c
// Usage: ./mkfiles create <dir> <N>
//        ./mkfiles delete <dir> <N>
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s create|delete <dir> <N>\n", argv[0]);
        return 2;
    }
    int create = strcmp(argv[1], "create") == 0;
    const char *dir = argv[2];
    long n = atol(argv[3]);
    char name[64];

    if (create && mkdir(dir, 0755) != 0) {
        perror("mkdir");
        return 1;
    }
    int dfd = open(dir, O_RDONLY | O_DIRECTORY);
    if (dfd < 0) { perror("open dir"); return 1; }

    for (long i = 0; i < n; i++) {
        snprintf(name, sizeof(name), "f%07ld", i);
        if (create) {
            int fd = openat(dfd, name, O_CREAT | O_WRONLY | O_EXCL, 0644);
            if (fd < 0) { perror("openat"); return 1; }
            close(fd);
        } else if (unlinkat(dfd, name, 0) != 0) {
            perror("unlinkat");
            return 1;
        }
    }
    close(dfd);
    if (!create && rmdir(dir) != 0) {
        perror("rmdir");
        return 1;
    }
    printf("%s %ld files in %s\n", create ? "created" : "deleted", n, dir);
    return 0;
}
