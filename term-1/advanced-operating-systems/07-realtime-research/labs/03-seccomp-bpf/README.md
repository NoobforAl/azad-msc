# Lab 07.3 — A seccomp-BPF sandbox, with libseccomp and by hand

**Goal:** confine a program with a seccomp filter, see the three outcomes (errno, kill, allow) from user space, and read the classic-BPF program the kernel actually runs.

Runs on: the `aos-lab` VM (6.18.63) or any Linux ≥ 3.17 with `libseccomp-dev`. Unprivileged: the filter only restricts the process you start. Safe on a shared machine.

## Files

| File | What |
|---|---|
| `sandbox.c` | libseccomp: default ALLOW; `socket` → `EACCES`, `mkdir`/`mkdirat` → kill process, `ptrace` → `EPERM`; then `execvp()` the command |
| `raw-bpf.c` | the same idea in 7 hand-written BPF instructions: arch check, `uname` → `EPERM` |
| `solution/allowlist.c` | extension solution |

## Steps

```bash
cd ~/work/07-realtime-research/03-seccomp-bpf
gcc -Wall -Wextra -O2 -o sandbox sandbox.c -lseccomp
gcc -Wall -Wextra -O2 -o raw-bpf raw-bpf.c

./sandbox grep -E '^(NoNewPrivs|Seccomp)' /proc/self/status   # mode 2 = filter
./sandbox python3 -c 'import socket; socket.socket()'           # ERRNO(EACCES)
./sandbox mkdir /tmp/seccomp-test; echo "exit=$?"                # KILL_PROCESS
./sandbox strace -f true 2>&1 | tail -2                           # ptrace -> EPERM
SANDBOX_DUMP=1 ./sandbox true 2>&1 | head -30                     # the generated filter (PFC)

./raw-bpf
```

## Code

The rules (`sandbox.c`):

```c
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);          /* required without CAP_SYS_ADMIN */
scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
rule(ctx, SCMP_ACT_ERRNO(EACCES), "socket");
rule(ctx, SCMP_ACT_KILL_PROCESS, "mkdir");
rule(ctx, SCMP_ACT_KILL_PROCESS, "mkdirat");
rule(ctx, SCMP_ACT_ERRNO(EPERM), "ptrace");
seccomp_load(ctx);                               /* seccomp(SECCOMP_SET_MODE_FILTER, ...) */
execvp(argv[1], &argv[1]);                       /* the filter survives execve() */
```

The raw program (`raw-bpf.c`), what `seccomp_run_filters()` executes per syscall:

```c
BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 0, 3),      /* else kill */
BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_uname, 2, 0),              /* -> errno */
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
```

Kernel path: `syscall_trace_enter()` → `__secure_computing()` → `__seccomp_filter()` → `seccomp_run_filters()` (walkthrough §5).

## Expected output

> Captured on aos-lab (VirtualBox on Hyper-V, Ubuntu 24.04, Linux 6.18.63 `PREEMPT_DYNAMIC`, 8 vCPU, shared with other users), 2026-11-15. Your numbers will differ.

```text
$ ./sandbox grep -E "^(NoNewPrivs|Seccomp)" /proc/self/status
NoNewPrivs:	1
Seccomp:	2
Seccomp_filters:	1
$ ./sandbox python3 -c "import socket; socket.socket()"
Traceback (most recent call last):
  ...
PermissionError: [Errno 13] Permission denied
$ ./sandbox mkdir /tmp/seccomp-test; echo "exit=$?"
bash: line 1:  2244 Bad system call         (core dumped) ./sandbox mkdir /tmp/seccomp-test
exit=159
$ ./sandbox strace -f true 2>&1 | tail -2
strace: PTRACE_SETOPTIONS: Operation not permitted
strace: cleanup: waitpid(-1, __WALL): No child processes
$ SANDBOX_DUMP=1 ./sandbox true 2>&1 | head -30
# filter for arch x86_64 (3221225534)
if ($arch == 3221225534)
  # filter for syscall "mkdirat" (258) [priority: 65535]
  if ($syscall == 258)
    action KILL_PROCESS;
  ...
  # filter for syscall "socket" (41) [priority: 65535]
  if ($syscall == 41)
    action ERRNO(13);
  # default action
  action ALLOW;
# invalid architecture action
action KILL;
$ ./raw-bpf
filter loaded: 7 instructions
getpid() = 5367
uname: Operation not permitted
```

## What to observe

1. **`Seccomp: 2`, `NoNewPrivs: 1`** in `/proc/self/status` of the *exec'd* program: the filter and NNP survived `execve()`. `Seccomp_filters: 1` counts the stacked filters.
2. **Three outcomes.** `socket()` returns `-1/EACCES` (the syscall never ran, `SECCOMP_RET_ERRNO` → `syscall_set_return_value()`); `mkdir` dies with `SIGSYS` and the shell prints "Bad system call", exit 159 = 128 + 31; `strace` cannot set up tracing (`PTRACE_SETOPTIONS: Operation not permitted`).
3. **The generated filter** (`SANDBOX_DUMP=1`) starts with an **arch check** (`$arch == 3221225534` = `AUDIT_ARCH_X86_64`) before any syscall number, and ends with `invalid architecture action KILL`: libseccomp protects you from the i386-ABI bypass that a hand-written filter must handle itself.
4. **`raw-bpf`**: `getpid()` works, `uname()` fails with "Operation not permitted". 7 instructions, no library.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `seccomp_load: Permission denied` / `EACCES` | no `no_new_privs` and no `CAP_SYS_ADMIN` | call `prctl(PR_SET_NO_NEW_PRIVS, 1)` first |
| `fatal error: seccomp.h: No such file` | header missing | `sudo apt install libseccomp-dev` |
| filter "doesn't work" for `open` | libc calls `openat` | trace with `strace` first; filter what really happens |
| `mkdir` blocked but `python3 -c 'os.mkdir(...)'` works? | it uses `mkdirat`? both are in the filter; check the PFC dump | always add the `*at` variants |
| program dies at start-up | you killed a syscall the dynamic loader needs (`mmap`, `mprotect`, `openat`) | build allow-lists from an `strace -f -c` run |

## Extension task

Write `allowlist.c`: default action `SCMP_ACT_ERRNO(ENOSYS)`, and allow **only** the syscalls that `/bin/cat` needs to print a file. Find the list with `strace -f -c cat /etc/hostname`. Verify that `./allowlist cat /etc/hostname` works and `./allowlist ls /` fails. Why is `ENOSYS` a better default than `KILL` for an allow-list?

Solution: [`solution/allowlist.c`](solution/allowlist.c), [`solution/answers.md`](solution/answers.md).
