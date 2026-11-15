// durable_save.c: replace a file so that after any crash it is either the old or the new
// version, never empty or partial.  write tmp -> fsync(tmp) -> rename -> fsync(dir).
//   durable_save PATH "new contents"
// Build: gcc -Wall -Wextra -O2 -o durable_save durable_save.c
#define _GNU_SOURCE
#include <fcntl.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int die(const char *what)
{
    perror(what);
    return 1;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s PATH CONTENTS\n", argv[0]);
        return 2;
    }
    char tmp[4096];
    snprintf(tmp, sizeof(tmp), "%s.tmp", argv[1]);

    int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0)
        return die("open tmp");
    size_t len = strlen(argv[2]);
    if (write(fd, argv[2], len) != (ssize_t)len)
        return die("write");
    if (write(fd, "\n", 1) != 1)
        return die("write");
    if (fsync(fd) != 0)                  // 1. data + inode of the new file are durable
        return die("fsync tmp");
    if (close(fd) != 0)
        return die("close");
    if (rename(tmp, argv[1]) != 0)       // 2. atomic name switch
        return die("rename");

    char dirbuf[4096];
    snprintf(dirbuf, sizeof(dirbuf), "%s", argv[1]);
    int dfd = open(dirname(dirbuf), O_RDONLY | O_DIRECTORY);
    if (dfd < 0)
        return die("open dir");
    if (fsync(dfd) != 0)                 // 3. the directory entry change is durable
        return die("fsync dir");
    close(dfd);
    return 0;
}
