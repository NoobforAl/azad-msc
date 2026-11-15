// pipeline.c: `ls -l /proc/self/fd | wc -l` without a shell.
// Solution to the lab 02.1 extension.
//
// Two children, one pipe. Each child keeps exactly the end it needs and closes
// the other; the parent closes both, so wc sees EOF as soon as ls exits.
// Set PAUSE=1 to stop both children right before exec, so you can inspect them:
//   PAUSE=1 ./pipeline &   then   ls -l /proc/<child>/fd ; kill -CONT <child>
//
// Build: gcc -Wall -Wextra -O2 -o pipeline pipeline.c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

static void die(const char *w) { perror(w); exit(1); }

static pid_t spawn(int in_fd, int out_fd, int close_fd, char *const argv[]) {
    pid_t p = fork();
    if (p < 0) die("fork");
    if (p == 0) {
        if (in_fd >= 0 && dup2(in_fd, STDIN_FILENO) < 0) die("dup2 in");
        if (out_fd >= 0 && dup2(out_fd, STDOUT_FILENO) < 0) die("dup2 out");
        close(close_fd);                      // the end this child must not hold
        if (in_fd >= 0) close(in_fd);
        if (out_fd >= 0) close(out_fd);
        if (getenv("PAUSE") != NULL) {
            fprintf(stderr, "child %d (%s) stopped, inspect /proc/%d/fd then kill -CONT %d\n",
                    (int)getpid(), argv[0], (int)getpid(), (int)getpid());
            raise(SIGSTOP);
        }
        execvp(argv[0], argv);
        die("execvp");
    }
    return p;
}

int main(void) {
    int fds[2];
    if (pipe(fds) != 0) die("pipe");
    char *const ls[] = {"ls", "-l", "/proc/self/fd", NULL};
    char *const wc[] = {"wc", "-l", NULL};
    pid_t a = spawn(-1, fds[1], fds[0], ls);   // writer: keeps only fds[1] (as fd 1)
    pid_t b = spawn(fds[0], -1, fds[1], wc);   // reader: keeps only fds[0] (as fd 0)
    close(fds[0]);                             // parent holds neither end
    close(fds[1]);
    int st;
    waitpid(a, &st, 0);
    waitpid(b, &st, 0);
    fprintf(stderr, "both children reaped, wc exit status %d\n", WEXITSTATUS(st));
    return 0;
}
