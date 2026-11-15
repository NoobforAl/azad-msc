# Lab 02.2 — `clone()` flags: what is shared, and what makes a thread

**Goal:** create children with different `CLONE_*` flags and prove, flag by flag, which resource (`mm`, fd table, cwd, thread group) each one shares, matching `copy_process()` in `kernel/fork.c`.

Runs on: the lab VM or any Linux box. User space only.

## Steps

```bash
cd ~/work/02-processes-threads && cp -r <repo>/.../labs/02-clone-flags . && cd 02-clone-flags
gcc -Wall -Wextra -O2 -o cloneflags cloneflags.c
./cloneflags
# what flags does glibc really pass for a thread?
cat > t.c <<'EOF'
#include <pthread.h>
static void *f(void *a) { return a; }
int main(void) { pthread_t t; pthread_create(&t, 0, f, 0); pthread_join(t, 0); return 0; }
EOF
gcc -Wall -Wextra -O2 -pthread -o t t.c
strace -f -e trace=clone,clone3 ./t
# which flag combinations does the kernel refuse?
strace -e trace=clone ./cloneflags 2>&1 | head -3
```

## Code

[`cloneflags.c`](cloneflags.c): for each flag set, the child (1) writes a global variable, (2) opens `/etc/hostname`, (3) `chdir("/tmp")`, and records its `getpid()`. The parent then checks:

- `mem`: does it see the new value of the global? (shared `mm`, `CLONE_VM`)
- `fds`: is the lowest free fd number now in use in *its* table? (`CLONE_FILES`)
- `cwd`: is its own cwd now `/tmp`? (`CLONE_FS`)
- `child_tgid`: did the child report the same `getpid()`? (`CLONE_THREAD`; `n/a` means the child's write was in its own private memory)

The last row uses the flag set of `pthread_create()`. A `CLONE_THREAD` child sends no `SIGCHLD` and cannot be `waitpid()`ed, so the parent sleeps on the futex word that the kernel clears at thread exit (`CLONE_CHILD_CLEARTID`), which is the mechanism `pthread_join()` uses.

## Expected output

Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15:

```text
$ ./cloneflags
0 (like fork)                      mem=no  fds=no  cwd=no    parent_tgid=5091 child_tgid=n/a tid=5092
CLONE_VM                           mem=yes fds=no  cwd=no    parent_tgid=5091 child_tgid=other tid=5093
CLONE_FILES                        mem=no  fds=yes cwd=no    parent_tgid=5091 child_tgid=n/a tid=5094
CLONE_FS                           mem=no  fds=no  cwd=yes   parent_tgid=5091 child_tgid=n/a tid=5095
CLONE_VM|CLONE_FILES|CLONE_FS      mem=yes fds=yes cwd=yes   parent_tgid=5091 child_tgid=other tid=5096
pthread set (+SIGHAND|THREAD|...)  mem=yes fds=yes cwd=yes   parent_tgid=5091 child_tgid=same tid=5097
```

`strace` of `pthread_create()`:

```text
$ strace -f -e trace=clone,clone3 ./t
clone3({flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID, child_tid=0x785b8f9ff990, parent_tid=0x785b8f9ff990, exit_signal=0, stack=0x785b8f1ff000, stack_size=0x7fff80, tls=0x785b8f9ff6c0} => {parent_tid=[5107]}, 88) = 5107
[pid  5107] +++ exited with 0 +++
+++ exited with 0 +++
```

## What to observe

- One flag, one resource. `CLONE_VM` → `copy_mm()` takes `mmget(oldmm)`; `CLONE_FILES` → `copy_files()` shares `files_struct`; `CLONE_FS` → `copy_fs()` does `fs->users++`.
- `CLONE_VM` without `CLONE_THREAD` is a **separate process sharing memory** (different TGID). This is legal, and it is what `vfork()` and `posix_spawn()` use.
- Only the pthread row reports `child_tgid=same`. `copy_process()` sets `p->tgid = current->tgid` for `CLONE_THREAD` (L2261–2263).
- In the `strace` output glibc uses **`clone3`** with `CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID`, the same set as the last row plus TLS.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `clone: Invalid argument` | `CLONE_THREAD` without `CLONE_SIGHAND`, or `CLONE_SIGHAND` without `CLONE_VM` | `copy_process()` L1963–1972 rejects them |
| segfault in the child | stack pointer must be the **top** of the stack (it grows down) | pass `stack + STACK_SIZE` |
| `waitpid: No child processes` for the thread row | threads never become waitable children | wait on the `CLONE_CHILD_CLEARTID` futex |
| printf from a `CLONE_VM` child corrupts output | the child shares the parent's stdio buffers | don't call stdio in the child; write results to memory |

## Extension task

Add a row with `CLONE_VFORK | CLONE_VM` and show, by timing, that the parent is blocked until the child calls `_exit()`. Then make the child sleep 1 s before `_exit()` and measure how long `clone()` takes to return in the parent.

Solution: [`solution/vfork_block.c`](solution/vfork_block.c).
