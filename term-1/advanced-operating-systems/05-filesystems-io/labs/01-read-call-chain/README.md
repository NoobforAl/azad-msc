# Lab 05.1 — The full call chain of `read()`

**Goal:** see, on the running v6.18.63 kernel, every function between `read(2)` and the page cache (`vfs_read → new_sync_read → ext4_file_read_iter → filemap_read`), what changes on a cache miss, and how the VFS objects of notes 01–03 look from user space.

> **VM only for the ftrace step.** Always filter ftrace (`-g`/`-l`), keep `--max-graph-depth` ≤ 6, wrap it in `timeout 10`, and run `trace-cmd reset` afterwards. An *unfiltered* `function_graph` (every kernel function patched) put this course's VirtualBox guest into a 26 s soft lockup on 2026-11-15.

Runs on: the lab VM (`~/work/05-filesystems-io/labs/01-read-call-chain`). Needs `sudo` for ftrace/bpftrace; leaves the tracer off when done. Time: ~45 min.

## Steps

```bash
cd ~/work/05-filesystems-io/labs/01-read-call-chain
gcc -Wall -Wextra -O2 -static -o readone readone.c   # zero warnings; -static = no loader reads in the trace
bash trace.sh                                    # steps 1-5 below, in order
```

What `trace.sh` does:

1. **ftrace** `function_graph` rooted at `vfs_read` (`-g`), only for our pid (`-F`), and only for 10 listed functions (`-l`), depth ≤ 6, under `timeout 10`, then `trace-cmd reset`.
2. **bpftrace** kernel stack every time `filemap_read()` runs for `comm == readone`.
3. **Cold read:** evict `data.bin` from the page cache (this file only: `dd iflag=nocache count=0` = `POSIX_FADV_DONTNEED`), then count `block_bio_queue` events, `filemap_read` and `page_cache_sync_ra` calls.
4. **VFS objects:** `stat` on files from three filesystems; `/proc/$$/fdinfo/3` after reading 3 bytes.
5. **Negative dentry:** five `stat()`s of a missing name; count how many reach `ext4_lookup()`.

## Code

- [`readone.c`](readone.c): opens a file, does N `read()`s of a given size, prints the pid. Deliberately tiny so traces contain only our calls.
- [`trace.sh`](trace.sh): the five steps above.

## Expected output

Real run, `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Shared 8-vCPU guest: timings will differ. This run happened right after a VM reboot, so even the step-1 read was cold (note the 340 µs in `page_cache_sync_ra`).

```text
$ bash trace.sh
== 1. ftrace function_graph rooted at vfs_read, only our pid (-F), only 10 functions (-l)
cpus=8
  readone-3393 [000]    66.988385: funcgraph_entry:        3.430 us   |  rw_verify_area();
  readone-3393 [002]    66.994271: funcgraph_entry:                   |  vfs_read() {
  readone-3393 [002]    66.994273: funcgraph_entry:        0.765 us   |    rw_verify_area();
  readone-3393 [002]    66.994274: funcgraph_entry:                   |    ext4_file_read_iter() {
  readone-3393 [002]    66.994274: funcgraph_entry:                   |      generic_file_read_iter() {
  readone-3393 [002]    66.994275: funcgraph_entry:                   |        filemap_read() {
  readone-3393 [002]    66.994275: funcgraph_entry:                   |          filemap_get_pages() {
  readone-3393 [002]    66.994276: funcgraph_entry:      ! 339.997 us |            page_cache_sync_ra();
  readone-3393 [002]    66.996079: funcgraph_exit:       # 1802.014 us |          }
  readone-3393 [002]    66.996083: funcgraph_entry:        1.751 us   |          touch_atime();
  readone-3393 [002]    66.996085: funcgraph_exit:       # 1809.987 us |        }
  readone-3393 [002]    66.996085: funcgraph_exit:       # 1810.666 us |      }
  readone-3393 [002]    66.996085: funcgraph_exit:       # 1811.127 us |    }
  readone-3393 [002]    66.996086: funcgraph_exit:       # 1815.977 us |  }

== 2. bpftrace: kernel stack every time filemap_read() runs for comm=readone
pid=4126 fd=3 read 4096 bytes in chunks of 4096

@[
    filemap_read+1
    ext4_file_read_iter+88
    vfs_read+624
    ksys_read+113
    __x64_sys_read+25
    x64_sys_call+7040
    do_syscall_64+130
    entry_SYSCALL_64_after_hwframe+118
]: 1

== 3. cold read: evict data.bin from the page cache (this file only) and count bios
pid=4323 fd=3 read 4096 bytes in chunks of 4096

@bios: 1
@bytes: 16384
@filemap_read: 1
@sync_readahead: 1

== 4. VFS objects: three superblocks, and the open file behind an fd
inode=643      dev=801    type=regular file           /etc/hostname
inode=4026532025 dev=17     type=regular empty file     /proc/uptime
inode=5        dev=6      type=character special file /dev/null
ext4     /
proc     /proc
devtmpfs /dev
-- /proc/3314/fdinfo/3 after reading 3 bytes:
pos:	3
flags:	0100000
mnt_id:	29
ino:	643

== 5. negative dentry: 5 stat()s of a missing name, how many reach ext4_lookup?

@ext4_lookup: 1
```

## What to observe

- The **ftrace tree** is exactly the walkthrough's chain (§0). `ext4_file_read_iter` adds one level and goes straight to `generic_file_read_iter`/`filemap_read`: ext4 does nothing special for a buffered read.
- In this run the read was **cold** (the VM had just rebooted): `filemap_get_pages` took 1.8 ms, of which `page_cache_sync_ra` (allocate folios, submit the bio) took 340 µs and the rest was waiting for the I/O. On a warm read the same call takes well under a microsecond and calls no readahead. `touch_atime` appears because reads update atime (subject to `relatime`).
- The first `rw_verify_area()` line *without* a `vfs_read` parent comes from `execve()` reading the binary (`kernel_read()`), not from our `read()`.
- The **bpftrace stack** shows the x86-64 entry (`entry_SYSCALL_64 → do_syscall_64 → x64_sys_call → __x64_sys_read`) under `ksys_read`: Module 01's entry path meets this module's VFS path. `ARCH-SPECIFIC (x86-64)`.
- ftrace shows `generic_file_read_iter()` between `ext4_file_read_iter()` and `filemap_read()`, but the stack goes straight from `filemap_read+1` back to `ext4_file_read_iter+88`: `generic_file_read_iter()` ends with `return filemap_read(...)`, which the compiler turned into a **tail call** (a `jmp`), so it leaves no return address on the stack.
- **Cold read:** one 4 KiB `read()` produced **one bio of 16 384 bytes**: synchronous readahead (`page_cache_sync_ra`, 1 call) read the initial 4-page window (`get_init_ra_size()`, see Lab 05.2's extension).
- **fdinfo** `pos: 3` lives in `struct file`; `flags` shows `O_LARGEFILE` (0100000) added by the kernel on 64-bit.
- **Negative dentry:** `@ext4_lookup: 1`: only the first of five `stat()`s of the missing name reached ext4; the other four were answered by the negative dentry in the dcache.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `trace-cmd: ... Permission denied` | tracefs needs root | run with `sudo` (the script does) |
| ftrace output is empty | the program finished before tracing started, or `-F` missing | use `-F ./readone ...` so trace-cmd starts the command itself |
| VM freezes, `soft lockup ... [trace-cmd]` in `dmesg` | unfiltered `function_graph` patches every kernel function | always pass `-l`/`-g`, `--max-graph-depth` ≤ 6, `timeout 10`, then `trace-cmd reset` |
| trace full of `ld.so` reads of libc | dynamically linked binary | build with `-static` (as here) or filter on the fd |
| bpftrace: `kprobe:filemap_read` not found | symbol name changed in your kernel | `sudo bpftrace -l 'kprobe:filemap_read*'`; this lab is `VERSION-DEPENDENT` |
| cold read shows 0 bios | the file was still cached (dirty pages are not dropped) | `sync data.bin` first, then evict |
| `@ext4_lookup` = 0 | the name was already negative-cached from an earlier run | use a fresh name (the script adds `$$`) |

## Extension task

Repeat step 1 and 2 for `/dev/null`, `/proc/uptime` and a pipe (`echo hi | ./readone /dev/stdin`). For each, which branch of `vfs_read()` runs (`->read` or `->read_iter`) and which function finally produces the bytes? Explain from the source (`drivers/char/mem.c`, `fs/proc/`, `fs/pipe.c`).

Solution: [`solution/answers.md`](solution/answers.md).
