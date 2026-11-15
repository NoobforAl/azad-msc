// sandbox.c: run a command under a seccomp-BPF filter built with libseccomp.
// Default ALLOW, with three targeted rules:
//   socket()        -> fails with EACCES      (SCMP_ACT_ERRNO)
//   mkdir/mkdirat   -> process killed, SIGSYS  (SCMP_ACT_KILL_PROCESS)
//   ptrace()        -> fails with EPERM
// The filter survives execve(), so it constrains whatever program we exec.
//
// Build: gcc -Wall -Wextra -O2 -o sandbox sandbox.c -lseccomp
// Run:   ./sandbox python3 -c 'import socket; socket.socket()'
//        ./sandbox mkdir /tmp/x
//        ./sandbox grep Seccomp /proc/self/status
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <unistd.h>

static void rule(scmp_filter_ctx ctx, uint32_t action, const char *name) {
    int nr = seccomp_syscall_resolve_name(name);
    if (nr == __NR_SCMP_ERROR) {
        fprintf(stderr, "unknown syscall %s\n", name);
        exit(1);
    }
    int rc = seccomp_rule_add(ctx, action, nr, 0);
    if (rc < 0) {
        fprintf(stderr, "seccomp_rule_add(%s): %s\n", name, strerror(-rc));
        exit(1);
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s cmd [args...]\n", argv[0]);
        return 2;
    }
    /* Unprivileged filters need no_new_privs: a setuid binary can no longer gain rights. */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return 1;
    }
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
    if (ctx == NULL) {
        fprintf(stderr, "seccomp_init failed\n");
        return 1;
    }
    rule(ctx, SCMP_ACT_ERRNO(EACCES), "socket");
    rule(ctx, SCMP_ACT_KILL_PROCESS, "mkdir");
    rule(ctx, SCMP_ACT_KILL_PROCESS, "mkdirat");
    rule(ctx, SCMP_ACT_ERRNO(EPERM), "ptrace");

    if (getenv("SANDBOX_DUMP") != NULL)
        seccomp_export_pfc(ctx, STDERR_FILENO);   /* human-readable filter */
    int rc = seccomp_load(ctx);                   /* seccomp(SECCOMP_SET_MODE_FILTER, ...) */
    seccomp_release(ctx);
    if (rc < 0) {
        fprintf(stderr, "seccomp_load: %s\n", strerror(-rc));
        return 1;
    }
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 127;
}
