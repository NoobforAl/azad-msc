# Lab 07.4 — An unprivileged file-system sandbox with Landlock

**Goal:** restrict a process tree to "read + execute everywhere, write only in one directory" without root, and see where and how the kernel says no.

Runs on: the `aos-lab` VM (6.18.63) or any kernel with `landlock` in `/sys/kernel/security/lsm` (the program handles `LANDLOCK_ACCESS_FS_TRUNCATE`, which needs ABI ≥ 3 per docs.kernel.org — `UNVERIFIED` locally; the program prints the running ABI). Unprivileged and safe on a shared machine.

## Files

| File | What |
|---|---|
| `landlock-sandbox.c` | `landlock_create_ruleset` → `landlock_add_rule` ×2 → `prctl(NO_NEW_PRIVS)` → `landlock_restrict_self` → `execvp` |
| `solution/landlock-net.c` | extension solution (TCP port rules; network rights arrived in ABI 4 per docs.kernel.org, `UNVERIFIED` locally) |

## Steps

```bash
cd ~/work/07-realtime-research/04-landlock
cat /sys/kernel/security/lsm; echo                   # must contain landlock
gcc -Wall -Wextra -O2 -o landlock-sandbox landlock-sandbox.c
mkdir -p /tmp/ll-rw

./landlock-sandbox /tmp/ll-rw sh -c '
  echo ok > /tmp/ll-rw/a && echo "write inside: ok";
  echo no > /tmp/ll-b    || echo "write outside: denied";
  cat /etc/hostname      && echo "read outside: ok";
  rm /tmp/ll-rw/a        && echo "remove inside: ok";
  mkdir /tmp/ll-dir      || echo "mkdir outside: denied"'

./landlock-sandbox /tmp/ll-rw sh -c 'echo hi 2>/dev/null'; echo "exit=$?"   # surprise
strace -f -e trace=landlock_create_ruleset,landlock_add_rule,landlock_restrict_self,openat \
  ./landlock-sandbox /tmp/ll-rw sh -c 'echo no > /tmp/ll-b' 2>&1 | grep -E 'landlock|ll-b'
```

## Code

```c
struct landlock_ruleset_attr attr = {.handled_access_fs = FS_READ | FS_WRITE};
int rs = ll_create_ruleset(&attr, sizeof(attr), 0);   /* handled = denied unless granted */
allow(rs, "/", FS_READ);                              /* read + exec everywhere */
allow(rs, argv[1], FS_READ | FS_WRITE);               /* write only beneath argv[1] */
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
ll_restrict_self(rs, 0);                              /* new domain layer on our creds */
execvp(argv[2], &argv[2]);                            /* inherited across execve() */
```

glibc 2.39 has no wrappers, so the program calls `syscall(SYS_landlock_*)`. Kernel side: `landlock_restrict_self()` (`security/landlock/syscalls.c` L478) and the `file_open` hook `hook_file_open()` (`security/landlock/fs.c` L1626); creating a file is checked by `hook_path_mknod()` (`MAKE_REG`), registered at fs.c L1862 next to `path_mkdir`, `path_unlink`, `path_truncate`.

## Expected output

> Captured on aos-lab (VirtualBox on Hyper-V, Ubuntu 24.04, Linux 6.18.63 `PREEMPT_DYNAMIC`, 8 vCPU, shared with other users), 2026-11-15. Your numbers will differ.

```text
$ cat /sys/kernel/security/lsm; echo
lockdown,capability,landlock,yama,apparmor,ima,evm
$ ./landlock-sandbox /tmp/ll-rw sh -c '...'
landlock ABI version: 7
write inside: ok
sh: 3: cannot create /tmp/ll-b: Permission denied
write outside: denied
aos-lab
read outside: ok
remove inside: ok
mkdir: cannot create directory ‘/tmp/ll-dir’: Permission denied
mkdir outside: denied
$ ./landlock-sandbox /tmp/ll-rw sh -c 'echo hi 2>/dev/null'; echo "exit=$?"
landlock ABI version: 7
sh: 1: cannot create /dev/null: Permission denied
exit=2
$ strace -f -e trace=landlock_create_ruleset,landlock_add_rule,landlock_restrict_self,openat ... | grep -E 'landlock|ll-b'
landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION) = 7
landlock_create_ruleset({handled_access_fs=LANDLOCK_ACCESS_FS_EXECUTE|...|LANDLOCK_ACCESS_FS_TRUNCATE, handled_access_net=0}, 16, 0) = 3
landlock_add_rule(3, LANDLOCK_RULE_PATH_BENEATH, {allowed_access=LANDLOCK_ACCESS_FS_EXECUTE|LANDLOCK_ACCESS_FS_READ_FILE|LANDLOCK_ACCESS_FS_READ_DIR, parent_fd=4}, 0) = 0
landlock_add_rule(3, LANDLOCK_RULE_PATH_BENEATH, {allowed_access=LANDLOCK_ACCESS_FS_EXECUTE|LANDLOCK_ACCESS_FS_WRITE_FILE|...|LANDLOCK_ACCESS_FS_TRUNCATE, parent_fd=4}, 0) = 0
landlock_restrict_self(3, 0)            = 0
openat(AT_FDCWD, "/tmp/ll-b", O_WRONLY|O_CREAT|O_TRUNC, 0666) = -1 EACCES (Permission denied)
sh: 1: cannot create /tmp/ll-b: Permission denied
```

## What to observe

1. **ABI version** printed first. v6.18.63 has `landlock_abi_version = 7`. Your program must drop rights the running ABI doesn't know.
2. **Inside vs outside.** Creating `/tmp/ll-b` fails with "Permission denied" (`EACCES`): `/tmp` is covered only by the read rule on `/`. Reading `/etc/hostname` works.
3. **`2>/dev/null` fails.** `/dev/null` is a file beneath `/` with only read rights: opening it for writing is denied, so the shell can't even set up the redirection. Real sandboxes add a rule for `/dev/null` (or `/dev`).
4. **strace**: three Landlock syscalls happen in the sandbox launcher; the denial shows as `openat(..., "/tmp/ll-b", O_WRONLY|O_CREAT|O_TRUNC, 0666) = -1 EACCES`. The path lookup happened, and the LSM said no.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `Landlock unavailable: Operation not supported` | Landlock not in the active LSM list | boot with `lsm=landlock,...` (Ubuntu 24.04 enables it) |
| `landlock_create_ruleset: Invalid argument` | you handle a right the running ABI doesn't know | mask `handled_access_fs` by ABI version (best effort) |
| `landlock_restrict_self: Operation not permitted` | forgot `PR_SET_NO_NEW_PRIVS` | call `prctl()` first |
| everything denied, even `exec` | no rule grants `EXECUTE` / `READ_FILE` on `/usr` | add a read rule on `/` or on `/usr`, `/lib`, `/etc` |
| writes still work somewhere | that right isn't in `handled_access_fs` | rights you don't handle are allowed |

## Extension task

Landlock can also restrict TCP (`handled_access_net`, `LANDLOCK_RULE_NET_PORT` in `include/uapi/linux/landlock.h`): add `handled_access_net = LANDLOCK_ACCESS_NET_CONNECT_TCP` and allow connecting only to port 443. Show that `python3 -c "import socket; socket.create_connection(('127.0.0.1', 22), 1)"` fails with `PermissionError` while a connection attempt to port 443 is **not** rejected by Landlock (it may still fail with "Connection refused" if nothing listens). Which error tells you who said no?

Solution: [`solution/landlock-net.c`](solution/landlock-net.c), [`solution/answers.md`](solution/answers.md).
