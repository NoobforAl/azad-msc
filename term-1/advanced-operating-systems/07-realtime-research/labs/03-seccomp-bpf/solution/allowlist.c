// allowlist.c: extension solution. Default-deny seccomp filter: only the syscalls
// that `cat FILE` needs (from `strace -f -c cat /etc/hostname`) are allowed.
// Everything else returns ENOSYS, which libc treats as "not implemented" and
// often falls back from, instead of crashing the program.
//
// Build: gcc -Wall -Wextra -O2 -o allowlist allowlist.c -lseccomp
// Run:   ./allowlist cat /etc/hostname     # works
//        ./allowlist ls /                  # fails: ls needs getdents64, ioctl, statx...
#include <errno.h>
#include <seccomp.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <unistd.h>

/* execve must be allowed: the filter is installed before we exec the target.
 * The rest is what the dynamic loader + cat use on Ubuntu 24.04 (glibc 2.39). */
static const char *const allowed[] = {
    "execve", "brk", "mmap", "munmap", "mprotect", "arch_prctl", "set_tid_address",
    "set_robust_list", "rseq", "prlimit64", "getrandom", "access", "openat", "newfstatat",
    "fstat", "read", "pread64", "write", "close", "fadvise64", "futex", "exit_group", "exit",
};

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s cmd [args...]\n", argv[0]);
        return 2;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return 1;
    }
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ERRNO(ENOSYS));
    if (ctx == NULL) {
        fprintf(stderr, "seccomp_init failed\n");
        return 1;
    }
    for (size_t i = 0; i < sizeof(allowed) / sizeof(allowed[0]); i++) {
        int nr = seccomp_syscall_resolve_name(allowed[i]);
        if (nr == __NR_SCMP_ERROR)
            continue;   /* not on this arch */
        int rc = seccomp_rule_add(ctx, SCMP_ACT_ALLOW, nr, 0);
        if (rc < 0) {
            fprintf(stderr, "allow %s: %s\n", allowed[i], strerror(-rc));
            return 1;
        }
    }
    int rc = seccomp_load(ctx);
    seccomp_release(ctx);
    if (rc < 0) {
        fprintf(stderr, "seccomp_load: %s\n", strerror(-rc));
        return 1;
    }
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 127;
}
