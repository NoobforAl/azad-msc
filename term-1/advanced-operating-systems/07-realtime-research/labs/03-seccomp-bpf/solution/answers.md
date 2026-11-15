# Lab 07.3 — answers

## What to observe

1. `/proc/self/status` of `grep` (the exec'd program) shows `NoNewPrivs: 1`, `Seccomp: 2` (filter mode) and `Seccomp_filters: 1`. Both the flag and the filter were inherited across `execve()`; nothing in the target program had to cooperate.
2. Outcomes:
   - `socket()` → Python raises `PermissionError: [Errno 13] Permission denied`. In the kernel, `__seccomp_filter()` took the `SECCOMP_RET_ERRNO` branch (seccomp.c L1279-1285), set the return value to `-13` and skipped the syscall.
   - `mkdir` → the shell reports `Bad system call` (core dumped if core dumps are enabled) and `$?` = 159 = 128 + `SIGSYS` (31). That's `SECCOMP_RET_KILL_PROCESS` → `force_sig_seccomp()`.
   - `strace` itself runs (it is the sandboxed process), but its ptrace calls return `EPERM` (`strace: PTRACE_SETOPTIONS: Operation not permitted`), so it cannot trace the child.
3. The PFC dump begins with `if ($arch == 3221225534)` (`AUDIT_ARCH_X86_64` = `0xC000003E`) and ends with `# invalid architecture action` / `action KILL;`. libseccomp adds the arch guard automatically (whether the compiled BPF also rejects x32 numbers is not visible in the PFC output: `UNVERIFIED`; dump it with `seccomp_export_bpf()` and decode it to check).
4. `raw-bpf`: `getpid() = <pid>`, then `uname: Operation not permitted`. The 7 instructions are: load arch, compare, load nr, compare with 63 (`__NR_uname`), and three returns.

## Extension: allow-list for `cat`

`strace -f -c cat /etc/hostname` on the VM lists: `access arch_prctl brk close execve fadvise64 fstat futex getrandom mmap mprotect munmap openat pread64 prlimit64 read rseq set_robust_list set_tid_address write` (plus `exit_group`, which `-c` doesn't count). `solution/allowlist.c` allows those. Real run:

```text
$ ./allowlist cat /etc/hostname; echo exit=$?
aos-lab
exit=0
$ ./allowlist ls /; echo exit=$?
ls: reading directory '/': Function not implemented
exit=2
```

`ls` needs `getdents64`, `ioctl`, `statx` and `statfs` (its `strace -c` list), which return `ENOSYS`.

Lesson learned while building it: the first version forgot `futex`, and **both** commands died with `Segmentation fault (core dumped)`: glibc does not expect `futex` to fail. A missing syscall in an allow-list does not always produce a clean error.

Why `ENOSYS` instead of `KILL`:
- libc and runtimes probe for new syscalls (`clone3`, `rseq`, `statx`, `faccessat2`) and **fall back** when they get `ENOSYS`; with `KILL`, any probe crashes the program on a newer libc.
- `ENOSYS` makes the failure visible as an error message you can debug (`strace` shows which call failed).
- For hostile code, `KILL_PROCESS` is fine for syscalls you know are dangerous (e.g. `ptrace`, `bpf`, `keyctl`), combined with an `ENOSYS` default for unknown ones.
