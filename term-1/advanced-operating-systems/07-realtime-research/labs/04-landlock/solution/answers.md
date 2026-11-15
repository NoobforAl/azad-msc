# Lab 07.4 — answers

## What to observe

1. `landlock ABI version: 7` on v6.18.63 (`landlock_abi_version`, security/landlock/syscalls.c L164). A portable program builds `handled_access_fs` from the rights that exist at the running ABI and drops the rest (best-effort sandboxing).
2. Inside `/tmp/ll-rw` the shell can create, write and remove files; outside, `echo no > /tmp/ll-b` fails with `Permission denied` and `mkdir /tmp/ll-dir` fails with `Permission denied`. Reading `/etc/hostname` works because the rule on `/` grants `READ_FILE`.
3. `echo hi 2>/dev/null` fails: the shell must open `/dev/null` for writing, and `WRITE_FILE` is handled but granted only beneath `/tmp/ll-rw`. Landlock has no notion of "harmless" files; real sandboxes add `allow(rs, "/dev/null", WRITE_FILE)`.
4. The denial is `openat(AT_FDCWD, "/tmp/ll-b", O_WRONLY|O_CREAT|O_TRUNC, 0666) = -1 EACCES (Permission denied)`. The path was resolved first (LSM hooks run after lookup), then `hook_path_mknod()` refused `MAKE_REG` in `/tmp`.

## Extension: TCP rules

`solution/landlock-net.c` handles `LANDLOCK_ACCESS_NET_CONNECT_TCP` and grants it only for the given port.

- Port 22 → `PermissionError: [Errno 13] Permission denied`: Landlock (`EACCES`) refused `connect()` before any packet was sent.
- Port 443 with no listener → `ConnectionRefusedError: [Errno 111]`: Landlock allowed it; the TCP stack got a RST. The **errno** tells you who said no: `EACCES` = policy, `ECONNREFUSED` = network.
- UDP and other protocols are not covered by these rights; they stay allowed (only what is handled is restricted).
