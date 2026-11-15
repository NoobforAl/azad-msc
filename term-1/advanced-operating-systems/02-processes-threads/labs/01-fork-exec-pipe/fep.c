// fep.c: fork + exec + pipe, then look at the processes through /proc.
//
// The parent creates a pipe and forks. The child points its stdout at the
// pipe's write end (dup2) and execs `ls -l /proc/self/fd`, so the listing
// you see is the fd table of the *child after exec*. The parent reads the
// pipe until EOF, then shows the child's state from /proc BEFORE reaping it
// (it is a zombie), reaps it with waitpid(), and checks /proc again.
//
// Build: gcc -Wall -Wextra -O2 -o fep fep.c
// Run:   ./fep
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static void die(const char *what) {
    perror(what);
    exit(1);
}

// Print the lines of /proc/<pid>/status whose key is in `keys`.
static void show_status(pid_t pid, const char *const keys[]) {
    char path[64];
    char line[256];
    snprintf(path, sizeof path, "/proc/%d/status", (int)pid);
    FILE *f = fopen(path, "r");
    if (f == NULL) {
        printf("  %s: %s\n", path, strerror(errno));
        return;
    }
    while (fgets(line, sizeof line, f) != NULL) {
        for (size_t i = 0; keys[i] != NULL; i++) {
            size_t n = strlen(keys[i]);
            if (strncmp(line, keys[i], n) == 0 && line[n] == ':') {
                printf("  %s", line);
            }
        }
    }
    fclose(f);
}

int main(void) {
    static const char *const keys[] = {"Name", "State", "Pid", "PPid", "Threads", NULL};
    int fds[2];

    if (pipe2(fds, O_CLOEXEC) != 0) die("pipe2");

    pid_t child = fork();
    if (child < 0) die("fork");

    if (child == 0) {
        // Child: stdout -> pipe write end. dup2() clears O_CLOEXEC on the new fd 1,
        // while the original fds[0]/fds[1] still carry it and vanish at exec.
        if (dup2(fds[1], STDOUT_FILENO) < 0) die("dup2");
        char *const argv[] = {"ls", "-l", "/proc/self/fd", NULL};
        execvp(argv[0], argv);
        die("execvp");  // only reached if exec failed
    }

    // Parent: close our copy of the write end, or read() never sees EOF.
    close(fds[1]);
    printf("parent pid=%d forked child pid=%d\n", (int)getpid(), (int)child);
    printf("--- child's fd table after exec (read through the pipe) ---\n");

    char buf[4096];
    ssize_t n;
    size_t total = 0;
    while ((n = read(fds[0], buf, sizeof buf)) > 0) {
        fwrite(buf, 1, (size_t)n, stdout);
        total += (size_t)n;
    }
    if (n < 0) die("read");
    close(fds[0]);
    printf("--- EOF after %zu bytes: every write end is closed ---\n", total);

    // The child has exited by now, but nobody has called wait() yet.
    usleep(100 * 1000);
    printf("before waitpid, /proc/%d/status:\n", (int)child);
    show_status(child, keys);

    int st = 0;
    if (waitpid(child, &st, 0) != child) die("waitpid");
    if (WIFEXITED(st)) {
        printf("waitpid: child %d exited with status %d\n", (int)child, WEXITSTATUS(st));
    }
    printf("after waitpid, /proc/%d/status:\n", (int)child);
    show_status(child, keys);
    return 0;
}
