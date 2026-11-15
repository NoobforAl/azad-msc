// raw-bpf.c: the same idea as sandbox.c, but with hand-written classic BPF.
// This is exactly what the kernel runs in seccomp_run_filters(): a program over
// struct seccomp_data { int nr; __u32 arch; __u64 instruction_pointer; __u64 args[6]; }.
//
// Build: gcc -Wall -Wextra -O2 -o raw-bpf raw-bpf.c
// Run:   ./raw-bpf          # prints getpid(), then uname() fails with EPERM
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <unistd.h>

int main(void) {
    struct sock_filter prog[] = {
        /* [0] A = arch; a filter that skips this check can be bypassed via the i386 ABI. */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        /* [1] if (A != x86-64) goto kill */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 0, 3),
        /* [2] A = syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        /* [3] if (A == __NR_uname) goto errno */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_uname, 2, 0),
        /* [4] allow everything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
        /* [5] kill */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* [6] errno: the low 16 bits are the errno value (SECCOMP_RET_DATA) */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
    };
    struct sock_fprog fprog = {
        .len = (unsigned short)(sizeof(prog) / sizeof(prog[0])),
        .filter = prog,
    };

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return 1;
    }
    /* glibc has no seccomp() wrapper: call the system call directly. */
    if (syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &fprog) != 0) {
        perror("seccomp");
        return 1;
    }
    printf("filter loaded: %u instructions\n", (unsigned)fprog.len);
    printf("getpid() = %ld\n", (long)getpid());
    fflush(stdout);   /* keep stdout and perror() (stderr) in order when piped */

    struct utsname u;
    if (uname(&u) != 0)
        perror("uname");
    else
        printf("uname() = %s (filter did not match?)\n", u.release);
    return 0;
}
