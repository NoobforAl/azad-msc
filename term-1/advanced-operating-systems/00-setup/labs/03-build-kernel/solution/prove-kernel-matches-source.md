# Solution: prove the running kernel matches the source you read

```bash
# 1. symbol + address (kptr_restrict=0 from lab 02, run as root to see real addresses)
sudo grep -w do_syscall_64 /proc/kallsyms
#   ffffffff81xxxxxx T do_syscall_64

# 2. can ftrace trace it?  do_syscall_64 is marked "noinstr" in the source:
bash ../../../../../_shared/sources/cite.sh linux arch/x86/entry/syscall_64.c do_syscall_64 1
#   linux/arch/x86/entry/syscall_64.c · do_syscall_64() · v6.18.63 · L87-87
#      87  __visible noinstr bool do_syscall_64(struct pt_regs *regs, int nr)
sudo grep -w do_syscall_64 /sys/kernel/tracing/available_filter_functions   # -> no output
```

**This is the instructive part:** `noinstr` puts the function in the `.noinstr.text` section, which is compiled **without** ftrace hooks, because entry code must not be traced before the kernel state is fully set up. So the *absence* from `available_filter_functions` is itself proof that the running kernel was built from source that has `noinstr` there. Trace a function one level down instead:

```bash
sudo grep -w x64_sys_call /sys/kernel/tracing/available_filter_functions || true
sudo trace-cmd record -p function_graph -g __x64_sys_getpid -F /bin/true && trace-cmd report | head
```

```bash
# 3. source line from DWARF in the -dbg package
sudo dpkg -i ~/src/linux-image-6.18.63-aos-lab-dbg_*.deb
gdb -batch -ex 'info line do_syscall_64' /usr/lib/debug/lib/modules/$(uname -r)/vmlinux
#   Line 87 of "arch/x86/entry/syscall_64.c" starts at address 0xffffffff81xxxxxx <do_syscall_64>
```

Line 87 here equals line 87 in `_shared/sources/linux/arch/x86/entry/syscall_64.c`, so you're reading the same code that runs. Verified in the pinned source: `x64_sys_call()` (`syscall_64.c` L35) and `#define noinstr __noinstr_section(".noinstr.text")` (`include/linux/compiler_types.h` L417). `UNVERIFIED` until run: whether `x64_sys_call` is traceable (it may be inlined), and the `-dbg` path layout. Check them with `ls /usr/lib/debug/lib/modules/`.
