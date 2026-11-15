# Lab 01.2 — Raw `syscall` in C: libc wrapper vs `syscall(3)` vs inline asm

**Goal:** make the same system call three ways, see the x86-64 register ABI and the `-errno` convention with your own eyes, prove with `cpl.c` that user code runs at CPL 3, and time each path.

Runs on: the `aos-lab` VM (user space, nothing destructive). **ARCH-SPECIFIC (x86-64).** Time: 45 min.

## Steps

```bash
scp -r term-1/advanced-operating-systems/01-architecture/labs/02-raw-syscall aos-lab:~/work/01-architecture/lab02
ssh aos-lab
cd ~/work/01-architecture/lab02
gcc -Wall -Wextra -O2 -o raw_syscall raw_syscall.c
gcc -Wall -Wextra -O2 -o cpl cpl.c
taskset -c 3 ./raw_syscall                      # three writes, errno demo, timing
strace -e trace=write,getpid ./raw_syscall 3 > /dev/null   # the kernel sees identical calls
./cpl                                           # CS/SS and two privileged instructions
gdb -batch -ex 'disassemble read' /lib/x86_64-linux-gnu/libc.so.6 | head -10
```

## Code

- [`raw_syscall.c`](raw_syscall.c): `raw_syscall0/3` with `__asm__ volatile("syscall" ...)` and `"rcx", "r11", "memory"` clobbers. It does `write(2)` three ways, `write(999, …)` to compare error conventions, and times `getpid` three ways against an empty loop (after a warm-up loop).
- [`cpl.c`](cpl.c): reads `%cs`/`%ss` and decodes the RPL bits. It tries `cli` and `mov %cr3` in child processes and reports the signal.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute numbers. Two consecutive runs are shown so you can see the noise. Output is trimmed with `...` and the numbers are unedited.

```text
$ taskset -c 3 ./raw_syscall          # run 1
libc   write()
syscall(SYS_write)
inline asm syscall
returns: 15 19 19
libc write(999): ret=-1 errno=9 (Bad file descriptor)
raw  write(999): ret=-9  (kernel returns -errno)
getpid: 3159 3159 3159
iterations: 5000000
libc getpid()          151.6 ns/call
syscall(SYS_getpid)    189.3 ns/call
inline asm syscall     120.2 ns/call
empty loop               1.0 ns/iter

$ taskset -c 3 ./raw_syscall          # run 2
...
libc getpid()          103.3 ns/call
syscall(SYS_getpid)    110.8 ns/call
inline asm syscall     106.8 ns/call
empty loop               0.7 ns/iter

$ strace -e trace=write,getpid ./raw_syscall 3 > /dev/null
write(1, "libc   write()\n", 15)        = 15
write(1, "syscall(SYS_write)\n", 19)    = 19
write(1, "inline asm syscall\n", 19)    = 19
write(999, "l", 1)                      = -1 EBADF (Bad file descriptor)
write(999, "l", 1)                      = -1 EBADF (Bad file descriptor)
getpid()                                = 8490
getpid()                                = 8490
...

$ ./cpl
CS = 0x0033  -> index 6, RPL/CPL = 3
SS = 0x002b  -> index 5, RPL     = 3
cli            -> killed by signal 11 (Segmentation fault)
mov %cr3,reg   -> killed by signal 11 (Segmentation fault)

$ gdb -batch -ex 'disassemble read' /lib/x86_64-linux-gnu/libc.so.6 | head -10
Dump of assembler code for function __GI___libc_read:
   0x000000000011bce0 <+0>:	endbr64
   0x000000000011bce4 <+4>:	cmpb   $0x0,0xf0355(%rip)        # 0x20c040 <__libc_single_threaded>
   0x000000000011bceb <+11>:	je     0x11bd00 <__GI___libc_read+32>
   0x000000000011bced <+13>:	xor    %eax,%eax
   0x000000000011bcef <+15>:	syscall
   0x000000000011bcf1 <+17>:	cmp    $0xfffffffffffff000,%rax
   0x000000000011bcf7 <+23>:	ja     0x11bd48 <__GI___libc_read+104>
   0x000000000011bcf9 <+25>:	ret

$ gdb -batch -ex 'disassemble getpid' /lib/x86_64-linux-gnu/libc.so.6
Dump of assembler code for function __GI_getpid:
   0x00000000000f5b50 <+0>:	endbr64
   0x00000000000f5b54 <+4>:	mov    $0x27,%eax
   0x00000000000f5b59 <+9>:	syscall
   0x00000000000f5b5b <+11>:	ret
End of assembler dump.
```

## What to observe

- **Three paths, one kernel call.** strace can't tell the libc wrapper, `syscall(3)` and inline asm apart. It sees `write(1, …)` three times, because all three end in the same `syscall` instruction with `rax = 1`.
- **Two error conventions.** The kernel returns `-9` (`-EBADF`) in `rax`. glibc turns that into `-1` with `errno = 9`. The wrapper's `cmp $0xfffffffffffff000,%rax; ja` (see the gdb dump) is the test for "is this in `-4095..-1`?".
- **The wrapper is tiny.** `read` is `xor %eax,%eax` (`__NR_read` = 0) followed by `syscall`. The slow branch with `__pthread_enable_asynccancel` only runs in multi-threaded programs (`__libc_single_threaded` check). `getpid` is `mov $0x27,%eax; syscall; ret` (0x27 = 39), so there is **no** PID cache in glibc 2.39.
- **CPL is 3.** `CS = 0x33` and `SS = 0x2b` are exactly `__USER_CS` and `__USER_DS` from `arch/x86/include/asm/segment.h`. `cli` and `mov %cr3` raise `#GP`, which the kernel delivers as `SIGSEGV`.
- **Timing.** All three getpid paths cost about the same, roughly 100–190 ns on this guest. The empty loop costs about 1 ns. The difference is the boundary crossing plus the entry/exit work. On a shared VM the absolute numbers jump around between runs (compare run 1 and run 2: `syscall(SYS_getpid)` went from 189.3 to 110.8 ns with no code change), so only compare numbers taken in the same run.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| wrong results only at `-O2` | inline asm doesn't list `rcx`/`r11`, so the compiler keeps a live value there | add `"rcx", "r11", "memory"` to the clobbers |
| `syscall(SYS_x)` returns `-1` but raw returns `-22` | different conventions, not a bug | compare `-raw` with `errno` |
| strace shows fewer `getpid` lines than iterations | strace output is cut by `head` | expected; the full count is in `strace -c` |
| timings differ wildly between runs | shared VM, other tenants, CPU frequency | pin with `taskset`, repeat, compare inside one run |

## Extension task

Call `mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0)` with your own six-argument inline-asm wrapper. Do it once with the 4th argument wrongly placed in `rcx` (the C ABI register) and once correctly. Explain the wrong result from `SC_X86_64_REGS_TO_ARGS` in `arch/x86/include/asm/syscall_wrapper.h`.

Solution: [`solution/raw_mmap.c`](solution/raw_mmap.c).
