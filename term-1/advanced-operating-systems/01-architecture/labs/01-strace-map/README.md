# Lab 01.1 — Map every syscall of `cat` to its kernel entry

**Goal:** trace `cat` with `strace -f`, then map each system call name → x86-64 number → table entry point → the `__x64_sys_*` symbol that `x64_sys_call()` jumps to in the running kernel.

Runs on: the `aos-lab` VM (any Linux works; numbers are for x86-64 v6.18.63). Time: 30 min.

## Steps

```bash
# on your machine: copy the lab + the pinned syscall table to the VM
scp -r term-1/advanced-operating-systems/01-architecture/labs/01-strace-map aos-lab:~/work/01-architecture/lab01
scp _shared/sources/linux/arch/x86/entry/syscalls/syscall_64.tbl aos-lab:~/work/01-architecture/lab01/

# in the VM
cd ~/work/01-architecture/lab01
strace -f -o cat.trace cat /etc/hostname      # full log, one line per syscall
strace -c -f cat /etc/hostname > /dev/null    # summary table
bash map-syscalls.sh cat.trace                # name -> nr -> entry -> __x64_sys_* -> in kallsyms?
grep -w -e do_syscall_64 -e x64_sys_call -e __x64_sys_read /proc/kallsyms
```

## Code

- [`map-syscalls.sh`](map-syscalls.sh): parses the strace log (strips the `-f` PID prefix, skips `<... resumed>` halves), looks up each name in the `common`/`64` rows of `syscall_64.tbl`, builds `__x64_<entry>` and checks it in `/proc/kallsyms`.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Output is trimmed with `...` and the numbers are unedited.

```text
$ strace -c -f cat /etc/hostname > /dev/null
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 35.82    0.011664         507        23           mmap
 16.74    0.005452         175        31        12 openat
 ...
  3.81    0.001242         248         5           read
  ...
  0.19    0.000061          61         1           write
  ...
------ ----------- ----------- --------- --------- ----------------
100.00    0.032560         269       121        13 total

$ grep -n "hostname\|read(3\|execve" cat.trace | head
1:4564  execve("/usr/bin/cat", ["cat", "/etc/hostname"], 0x7ffdac8654f0 /* 17 vars */) = 0
10:4564  read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0\220\243\2\0\0\0\0\0"..., 832) = 832
39:4564  read(3, "# Locale name alias data base.\n#"..., 4096) = 2996
40:4564  read(3, "", 4096)                 = 0
111:4564  openat(AT_FDCWD, "/etc/hostname", O_RDONLY) = 3
115:4564  read(3, "aos-lab\n", 131072)      = 8
117:4564  read(3, "", 131072)               = 0

$ bash map-syscalls.sh cat.trace
count  syscall              nr  tbl entry            kernel symbol              in kallsyms
   31  openat              257  sys_openat           __x64_sys_openat           yes
   23  mmap                  9  sys_mmap             __x64_sys_mmap             yes
   21  close                 3  sys_close            __x64_sys_close            yes
   20  fstat                 5  sys_newfstat         __x64_sys_newfstat         yes
    5  read                  0  sys_read             __x64_sys_read             yes
    3  mprotect             10  sys_mprotect         __x64_sys_mprotect         yes
    3  brk                  12  sys_brk              __x64_sys_brk              yes
    2  pread64              17  sys_pread64          __x64_sys_pread64          yes
    2  munmap               11  sys_munmap           __x64_sys_munmap           yes
    1  write                 1  sys_write            __x64_sys_write            yes
    ...
    1  exit_group          231  sys_exit_group       __x64_sys_exit_group       yes
    1  execve               59  sys_execve           __x64_sys_execve           yes
    1  arch_prctl          158  sys_arch_prctl       __x64_sys_arch_prctl       yes
    1  access               21  sys_access           __x64_sys_access           yes

$ grep -w -e do_syscall_64 -e x64_sys_call -e __x64_sys_read /proc/kallsyms
ffffffffb5929b60 T x64_sys_call
ffffffffb5ea3d60 T __x64_sys_read
ffffffffb6c8a1d0 T do_syscall_64
```

## What to observe

- **`cat` itself makes only about 5 of the 121 syscalls.** The trace has 123 lines, and the file is opened at line 111. Everything before that is the dynamic loader mapping `libc.so.6` (`read(3, "\177ELF...", 832)`, `mmap`, `mprotect`) and the locale setup (12 failed `openat` calls for locale files). The work you asked for is `openat` + `read` ×2 + `write` + `close`.
- **Name ≠ entry point.** `fstat` is table entry `sys_newfstat`, so the kernel symbol is `__x64_sys_newfstat`. The table, not the name, decides the C function (walkthrough §4).
- **Every row maps to a real symbol.** Each `__x64_sys_*` exists because `SYSCALL_DEFINEn` generated it (walkthrough §5). Notice that `do_syscall_64` sits at a very different address from `x64_sys_call`: it is in `.noinstr.text`.
- **One `read` = one kernel path.** `read(3, "aos-lab\n", 131072) = 8` is `rax=0, rdi=3, rdx=131072` on entry and `rax=8` on return. The second `read` returning `0` is end-of-file.
- **`strace -c` and the log disagree by one.** The log has an `exit_group` line; `strace -c` leaves it out of its table (121 calls). The bpftrace extension sees it.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `missing ./syscall_64.tbl` | table not copied | `scp` it from `_shared/sources/linux/arch/x86/entry/syscalls/` |
| kallsyms addresses are all `0000000000000000` | `kptr_restrict` hides addresses from non-root (this VM shows them) | the script only needs names; use `sudo` to see addresses |
| every row says `no` | `syscall_64.tbl` copied from a Windows checkout has CRLF endings | the script strips them with `tr -d '\r'`; check with `file syscall_64.tbl` |
` with `tr -d '
'`; check with `file syscall_64.tbl` |
| a name shows `?` | the syscall is x32-only or newer than the table | check `uname -r` matches v6.18.x |
| counts differ between runs | locale files / `LD_PRELOAD` / cache state | compare shapes, not exact counts |

## Extension task

Prove that the **kernel** saw the same syscalls, with no ptrace stop: count `raw_syscalls:sys_enter` events by syscall **number** for the `cat` process only, using bpftrace, and compare with `strace -c`. Explain any difference.

Solution: [`solution/count-syscalls.bt`](solution/count-syscalls.bt).
