// cloneflags.c: one child per flag set, each child changes three things,
// and the parent checks which changes it can see.
//
//   memory : child writes a global variable         (shared with CLONE_VM)
//   fds    : child opens a file -> a new fd number  (shared with CLONE_FILES)
//   cwd    : child chdir("/tmp")                    (shared with CLONE_FS)
//
// The last row uses the flag set glibc's pthread_create() passes, so the child
// is a thread: same TGID (getpid), its own TID. It cannot be waitpid()'d, so the
// parent waits on the futex word the kernel clears at exit (CLONE_CHILD_CLEARTID).
//
// Build: gcc -Wall -Wextra -O2 -o cloneflags cloneflags.c
// Run:   ./cloneflags
#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/futex.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#define STACK_SIZE (256 * 1024)

static volatile int g_value = 0;     // "memory"
static int g_child_fd = -1;          // child stores its new fd number here (visible only with CLONE_VM)
static pid_t g_child_tgid, g_child_tid;
static volatile pid_t g_tid_word;    // cleared + futex-woken by the kernel when a CLONE_THREAD child exits

static int child_fn(void *arg) {
    (void)arg;
    g_value = 42;
    g_child_fd = open("/etc/hostname", O_RDONLY);
    if (chdir("/tmp") != 0) perror("chdir");
    g_child_tgid = getpid();
    g_child_tid = gettid();
    return 0;
}

static void run(const char *name, int flags) {
    char cwd[256];
    char *stack = mmap(NULL, STACK_SIZE, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK, -1, 0);
    if (stack == MAP_FAILED) { perror("mmap"); exit(1); }

    // Reset parent-side state before each experiment.
    g_value = 0;
    g_child_fd = -1;
    g_child_tgid = g_child_tid = 0;
    if (chdir("/") != 0) perror("chdir /");
    int probe = open("/dev/null", O_RDONLY);   // lowest free fd *before* the child runs
    close(probe);

    int is_thread = (flags & CLONE_THREAD) != 0;
    int sig = is_thread ? 0 : SIGCHLD;
    g_tid_word = 1;
    pid_t ret = clone(child_fn, stack + STACK_SIZE, flags | sig, NULL,
                      NULL, NULL, (pid_t *)&g_tid_word);
    if (ret < 0) { perror("clone"); exit(1); }

    if (is_thread) {
        // Wait until the kernel zeroes g_tid_word at thread exit.
        while (g_tid_word != 0) {
            syscall(SYS_futex, &g_tid_word, FUTEX_WAIT, g_tid_word, NULL, NULL, 0);
        }
    } else {
        if (waitpid(ret, NULL, __WALL) != ret) { perror("waitpid"); exit(1); }
    }

    // Did the child's open() land in *our* fd table? Then fd `probe` is now taken.
    int fd_shared = fcntl(probe, F_GETFD) != -1;
    if (fd_shared) close(probe);
    if (getcwd(cwd, sizeof cwd) == NULL) strcpy(cwd, "?");

    printf("%-34s mem=%-3s fds=%-3s cwd=%-5s parent_tgid=%d child_tgid=%s tid=%d\n",
           name,
           g_value == 42 ? "yes" : "no",
           fd_shared ? "yes" : "no",
           strcmp(cwd, "/tmp") == 0 ? "yes" : "no",
           (int)getpid(),
           g_child_tgid ? (g_child_tgid == getpid() ? "same" : "other") : "n/a",
           (int)ret);
    // The stack is left mapped on purpose: a CLONE_THREAD child may still be
    // on it for a few instructions after clearing g_tid_word.
}

int main(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    run("0 (like fork)", 0);
    run("CLONE_VM", CLONE_VM);
    run("CLONE_FILES", CLONE_FILES);
    run("CLONE_FS", CLONE_FS);
    run("CLONE_VM|CLONE_FILES|CLONE_FS", CLONE_VM | CLONE_FILES | CLONE_FS);
    run("pthread set (+SIGHAND|THREAD|...)",
        CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD |
        CLONE_SYSVSEM | CLONE_CHILD_CLEARTID);
    return 0;
}
