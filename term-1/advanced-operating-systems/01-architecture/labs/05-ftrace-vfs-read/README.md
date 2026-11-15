# Lab 01.5 — ftrace `function_graph` of `vfs_read()`

> **VM only (root).** This lab drives ftrace, a global kernel facility. The script always filters (`-g vfs_read`, `-l <read-path functions>`, `-F` on one PID), caps depth at 6, runs under `timeout 10` and calls `trace-cmd reset`. An unfiltered function trace can soft-lock a shared machine: never remove the filters, and never run this on a production server.

**Goal:** see the real kernel call tree under one `read()`, from `vfs_read()` down into the file system, and confirm that entry code marked `noinstr` is invisible to ftrace.

Runs on: the `aos-lab` VM (6.18.63, `CONFIG_FUNCTION_GRAPH_TRACER=y`). Time: 45 min.

## Steps

```bash
scp -r term-1/advanced-operating-systems/01-architecture/labs/05-ftrace-vfs-read aos-lab:~/work/01-architecture/lab05
ssh aos-lab
cd ~/work/01-architecture/lab05
sudo bash ftrace-vfs-read.sh /etc/hostname cat.graph        # lists every vfs_read(), prints #1
sudo N=6 bash ftrace-vfs-read.sh /etc/hostname cat.graph    # print another one (records again)
sudo bash ftrace-vfs-read.sh /proc/version proc.graph       # a procfs file
# which entry functions can ftrace hook at all?
sudo grep -c -w -e do_syscall_64 /sys/kernel/tracing/available_filter_functions
sudo grep -w -e x64_sys_call -e ksys_read -e vfs_read /sys/kernel/tracing/available_filter_functions
```

## Code

- [`ftrace-vfs-read.sh`](ftrace-vfs-read.sh): one filtered `trace-cmd record`, then two `awk` passes over `trace-cmd report`. The safety rules for a shared machine are built in:
  - `-g vfs_read` (`set_graph_function`): graphs start only at `vfs_read`.
  - `-l …` (`set_ftrace_filter`): only about 120 read-path functions are patched. Enabling `function_graph` with no function filter took ~40 s of system time on this guest, because every one of the kernel's traceable functions gets patched.
  - `-F cat …` (`set_ftrace_pid`): only the `cat` process is traced.
  - `--max-graph-depth 6`, the record wrapped in `timeout 10`, and `trace-cmd reset` in an `EXIT` trap.

  The first `awk` prints one line per `vfs_read()` (by brace counting) with its total time and the first `*_read_iter()`/`*_read()` it reached. The second prints the tree you pick with `N=`.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15, minutes after the VM was restarted, so `/etc/hostname` was not in the page cache yet. The tree printed for `N=6` comes from the same `cat.graph` file. Times are unedited.

```text
$ sudo bash ftrace-vfs-read.sh /etc/hostname cat.graph
full trace: cat.graph (107 lines)
vfs_read() calls (n, lines, total time, first ->read_iter/->read reached):
  #1   15 lines    6.204 us  ext4_file_read_iter()
  #2   15 lines    1.916 us  ext4_file_read_iter()
  #3   15 lines    1.985 us  ext4_file_read_iter()
  #4   16 lines    4.782 us  ext4_file_read_iter()
  #5   12 lines    1.473 us  ext4_file_read_iter()
  #6   21 lines  ! 949.028 us  ext4_file_read_iter()
  #7   12 lines    1.866 us  ext4_file_read_iter()
call tree of vfs_read() #1 (set N=<k> to pick another):
                  |  vfs_read() {
                  |    rw_verify_area() {
       0.385 us   |      security_file_permission();
       0.743 us   |    }
                  |    ext4_file_read_iter() {
                  |      generic_file_read_iter() {
                  |        filemap_read() {
                  |          filemap_get_pages() {
       0.716 us   |            filemap_get_read_batch();
       0.967 us   |          }
       0.127 us   |          touch_atime();
       2.283 us   |        }
       2.558 us   |      }
       2.836 us   |    }
       6.204 us   |  }

# tree #6 = read(3, "aos-lab\n", 131072): the page was not cached
                  |  vfs_read() {
                  |    rw_verify_area() {
       0.147 us   |      security_file_permission();
       0.424 us   |    }
                  |    ext4_file_read_iter() {
                  |      generic_file_read_iter() {
                  |        filemap_read() {
                  |          filemap_get_pages() {
       0.131 us   |            filemap_get_read_batch();
       0.730 us   |            filemap_alloc_folio_noprof();
     ! 152.831 us |            filemap_add_folio();
       0.593 us   |            filemap_get_read_batch();
     ! 548.053 us |            filemap_update_page();
       0.608 us   |            filemap_get_read_batch();
     ! 940.586 us |          }
       0.566 us   |          touch_atime();
     ! 946.902 us |        }
     ! 947.164 us |      }
     ! 947.449 us |    }
       0.152 us   |    fsnotify();
     ! 949.028 us |  }

$ sudo bash ftrace-vfs-read.sh /proc/version proc.graph | head -9
full trace: proc.graph (90 lines)
vfs_read() calls (n, lines, total time, first ->read_iter/->read reached):
  #1   15 lines    5.855 us  ext4_file_read_iter()
  ...
  #5   12 lines    2.554 us  ext4_file_read_iter()
  #6    8 lines    7.925 us  proc_reg_read_iter()
  #7    8 lines  ! 325.087 us  proc_reg_read_iter()

$ sudo grep -c -w -e do_syscall_64 /sys/kernel/tracing/available_filter_functions
0
$ sudo grep -w -e x64_sys_call -e ksys_read -e vfs_read /sys/kernel/tracing/available_filter_functions
vfs_read
ksys_read
```

## What to observe

- **Seven `vfs_read()` calls, but strace showed five `read`s.** The other two are the loader's `pread64(3, …, 784, 64)` calls (lab 01 trace, lines 11 and 13): `ksys_pread64()` calls `vfs_read()` too. Calls #1–#5 are the loader and locale files, #6 is `read(3, "aos-lab\n", 131072)` and #7 is the EOF read.
- **`vfs_read()` → `ext4_file_read_iter()` directly.** `new_sync_read()` (the `->read_iter` branch at `fs/read_write.c` L571–572) is inlined in this build, so it never appears; the indirect call lands straight in ext4. Then `generic_file_read_iter()` → `filemap_read()`: the page cache (Module 5).
- **Cached vs not cached.** Tree #1 takes 6 µs: `filemap_get_read_batch()` finds the folio in the page cache. Tree #6 takes 949 µs: the batch comes back empty, so the kernel allocates a folio (`filemap_alloc_folio_noprof`), inserts it (`filemap_add_folio`) and waits for the disk in `filemap_update_page()`. `!` marks entries over 100 µs. Run the script a second time and #6 should drop to a few µs (expected, not captured here).
- **Procfs takes a different branch.** For `/proc/version` the indirect call goes to `proc_reg_read_iter()`: same `vfs_read()`, different `file->f_op`.
- **The entry code is invisible.** `do_syscall_64` is missing from `available_filter_functions` (count `0`) because it is `noinstr`. `x64_sys_call` is missing too, for a different reason: `arch/x86/entry/Makefile` builds the whole file without ftrace hooks (`CFLAGS_REMOVE_syscall_64.o = $(CC_FLAGS_FTRACE)`, L11). The first traceable functions on the path are `ksys_read` and `vfs_read`.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `trace-cmd record failed`, `Failed to write …` | a `-l` pattern matches nothing (e.g. `new_sync_read` is inlined in this build) | check with `sudo grep -c '^name' /sys/kernel/tracing/available_filter_functions` and drop the pattern |
| the record takes the full 10 s | `trace-cmd` didn't notice `cat` exiting in this guest; `timeout` stops it and the data is still written | expected; the script accepts exit code 124 |
| `N=6 sudo bash …` ignores N | sudo drops the environment | `sudo N=6 bash …` |
| machine stalls when you "just remove the filter" | an unfiltered function(_graph) trace patches and fires on every kernel function on every CPU | never drop `-g`/`-l`/`-F`; keep `timeout 10`; run `sudo trace-cmd reset` if a run is interrupted |

## Extension task

Run the script on three kinds of file: `/etc/hostname` (ext4), `/proc/version` (procfs), and a pipe (`echo hi | sudo bash ftrace-vfs-read.sh /dev/stdin pipe.graph`). For each, name the `->read_iter`/`->read` function `vfs_read()` reached, and explain from `fs/read_write.c` L569–574 why the call goes there. Also: why is `__switch_to` absent from every function_graph trace, even when `cat` blocks?

Solution: [`solution/three-files.md`](solution/three-files.md).
