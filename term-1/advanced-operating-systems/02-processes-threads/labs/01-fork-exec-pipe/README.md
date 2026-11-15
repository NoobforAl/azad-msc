# Lab 02.1 — fork, exec, pipe, and what `/proc` shows

**Goal:** build the shell pattern fork → `dup2` → exec → pipe → `waitpid` in C, and watch the fd table, the memory map and a zombie through `/proc`.

Runs on: the lab VM (`aos-lab`) or any Linux box. User space only.

## Steps

```bash
mkdir -p ~/work/02-processes-threads && cd ~/work/02-processes-threads
cp -r <repo>/term-1/advanced-operating-systems/02-processes-threads/labs/01-fork-exec-pipe . && cd 01-fork-exec-pipe
gcc -Wall -Wextra -O2 -o fep fep.c          # must print no warnings
./fep
strace -f -e trace=pipe2,clone,clone3,dup2,execve,wait4,exit_group ./fep >/dev/null
```

Look at a live process the same way:

```bash
sleep 300 & P=$!
grep -E '^(Name|State|Tgid|Pid|PPid|Threads|voluntary|nonvoluntary)' /proc/$P/status
ls -l /proc/$P/fd
head -5 /proc/$P/maps
cat /proc/$P/maps | wc -l
kill $P
```

## Code

[`fep.c`](fep.c): the parent creates a pipe with `pipe2(O_CLOEXEC)` and forks. The child redirects stdout to the write end with `dup2()` and execs `ls -l /proc/self/fd`. The parent closes its copy of the write end, reads until EOF, then prints the child's `/proc/<pid>/status` **before** and **after** `waitpid()`.

## Expected output

Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15:

```text
$ ./fep
parent pid=4266 forked child pid=4267
--- child's fd table after exec (read through the pipe) ---
total 0
lr-x------ 1 fred fred 64 Nov 15 16:15 0 -> pipe:[15744]
l-wx------ 1 fred fred 64 Nov 15 16:15 1 -> pipe:[13197]
l-wx------ 1 fred fred 64 Nov 15 16:15 2 -> pipe:[15746]
lr-x------ 1 fred fred 64 Nov 15 16:15 3 -> /proc/4267/fd
--- EOF after 237 bytes: every write end is closed ---
before waitpid, /proc/4267/status:
  Name:	ls
  State:	Z (zombie)
  Pid:	4267
  PPid:	4266
  Threads:	1
waitpid: child 4267 exited with status 0
after waitpid, /proc/4267/status:
  /proc/4267/status: No such file or directory
```

`strace -f` (trimmed):

```text
$ strace -f -e trace=pipe2,clone,clone3,dup2,execve,wait4,exit_group ./fep >/dev/null
execve("./fep", ["./fep"], 0x7ffcde0c5fe8 /* 17 vars */) = 0
pipe2([3, 4], O_CLOEXEC)                = 0
clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x7ffb68ecea10) = 4284
[pid  4284] dup2(4, 1)                  = 1
[pid  4284] execve("/usr/local/sbin/ls", ["ls", "-l", "/proc/self/fd"], 0x7fff1e5aae98 /* 17 vars */) = -1 ENOENT (No such file or directory)
...
[pid  4284] execve("/usr/bin/ls", ["ls", "-l", "/proc/self/fd"], 0x7fff1e5aae98 /* 17 vars */) = 0
[pid  4284] exit_group(0)               = ?
[pid  4284] +++ exited with 0 +++
--- SIGCHLD {si_signo=SIGCHLD, si_code=CLD_EXITED, si_pid=4284, si_uid=1000, si_status=0, si_utime=0, si_stime=0} ---
wait4(4284, [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], 0, NULL) = 4284
exit_group(0)                           = ?
+++ exited with 0 +++
```

The live `sleep`:

```text
$ sleep 300 & P=$!
$ grep -E '^(Name|State|Tgid|Pid|PPid|Threads|voluntary|nonvoluntary)' /proc/$P/status
Name:	sleep
State:	S (sleeping)
Tgid:	4300
Pid:	4300
PPid:	4261
Threads:	1
voluntary_ctxt_switches:	3
nonvoluntary_ctxt_switches:	0
$ ls -l /proc/$P/fd
total 0
lr-x------ 1 fred fred 64 Nov 15 16:15 0 -> /dev/null
l-wx------ 1 fred fred 64 Nov 15 16:15 1 -> pipe:[15745]
l-wx------ 1 fred fred 64 Nov 15 16:15 2 -> pipe:[15746]
$ head -5 /proc/$P/maps
5f3590047000-5f3590049000 r--p 00000000 08:01 1952                       /usr/bin/sleep
5f3590049000-5f359004d000 r-xp 00002000 08:01 1952                       /usr/bin/sleep
5f359004d000-5f359004e000 r--p 00006000 08:01 1952                       /usr/bin/sleep
5f359004e000-5f359004f000 r--p 00007000 08:01 1952                       /usr/bin/sleep
5f359004f000-5f3590050000 rw-p 00008000 08:01 1952                       /usr/bin/sleep
$ cat /proc/$P/maps | wc -l
38
```

## What to observe

- **fd table after exec.** fd 1 is `pipe:[...]` (from `dup2`). The original pipe fds 3 and 4 are gone because of `O_CLOEXEC`: `do_close_on_exec()` in `begin_new_exec()` closed them. fd 3 in the listing is the directory `ls` opened.
- **fds 0 and 2.** In the capture above they are pipes because the commands ran through a non-interactive `ssh aos-lab '...'` session. In a terminal they point at `/dev/pts/N`. Only fd 1 comes from `dup2()`.
- **`clone`, not `fork`.** glibc's `fork()` is `clone(... SIGCHLD)`. The `kernel_clone()` path is the same.
- **EOF.** The parent's last `read()` returns 0 only because no write end is left: the child's fd 1 closed when `ls` exited, and the parent closed its copy. Delete the `close(fds[1])` line and the program hangs (quiz Q11).
- **Zombie.** Before `waitpid()` the child is `Z (zombie)`, still with its PID, its PPID and the name `ls` (set by exec). After `waitpid()` the `/proc` entry is gone: `release_task()` ran.
- **`sleep`** is `S (sleeping)`: `TASK_INTERRUPTIBLE` in `hrtimer_nanosleep()`. Its switches are all voluntary.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| program hangs after the listing | parent kept `fds[1]` open | `close(fds[1])` right after `fork()` |
| child sees extra fds 3 and 4 | pipe made without `O_CLOEXEC` | `pipe2(fds, O_CLOEXEC)`; `dup2` clears CLOEXEC on the new fd only |
| output appears twice | `printf` buffered before `fork()` and flushed by both | `fflush(stdout)` before `fork()`, or use `_exit` in the child |
| `State:` line missing after exit | the child was already reaped | read `/proc` before `waitpid()` |

## Extension task

Write `pipeline.c` that runs the equivalent of `ls -l /proc/self/fd | wc -l` with **two** children and one pipe, without a shell. The parent must not read or write the pipe. Prove with `ls -l /proc/<pid>/fd` (pause the children with `SIGSTOP`) that each process holds only the ends it needs.

Solution: [`solution/pipeline.c`](solution/pipeline.c).
