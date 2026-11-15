# Solution — Lab 01.5 extension: three kinds of file, one `vfs_read()`

## Commands (VM, filtered as in the lab script)

```bash
cd ~/work/01-architecture/lab05
sudo bash ftrace-vfs-read.sh /etc/hostname ext4.graph            # ext4
sudo bash ftrace-vfs-read.sh /proc/version proc.graph            # procfs
echo hi | sudo bash ftrace-vfs-read.sh /dev/stdin pipe.graph     # an anonymous pipe: cat reads stdin
```

These summary lines were captured on aos-lab (Linux 6.18.63) on 2026-11-15. Calls #1–#5 are always the loader and locale reads that `cat` makes itself, so only the last two lines matter:

```text
# /etc/hostname
  #6   21 lines  ! 949.028 us  ext4_file_read_iter()
  #7   12 lines    1.866 us  ext4_file_read_iter()
# /proc/version
  #6    8 lines    7.925 us  proc_reg_read_iter()
  #7    8 lines  ! 325.087 us  proc_reg_read_iter()
# echo hi | ... /dev/stdin
  #6    6 lines    3.766 us  anon_pipe_read()
  #7    6 lines  ! 142.021 us  anon_pipe_read()
```

## Why each one goes there

`vfs_read()`, `fs/read_write.c` L569–574 (v6.18.63):

```c
	if (file->f_op->read)
		ret = file->f_op->read(file, buf, count, pos);
	else if (file->f_op->read_iter)
		ret = new_sync_read(file, buf, count, pos);
	else
		ret = -EINVAL;
```

When a file is opened, the kernel copies the inode's `file_operations` into `file->f_op`. None of the three tables below defines `.read`, so all three files take the `->read_iter` branch. This build inlines `new_sync_read()`, so the graph goes straight to the target function.

| File | `file->f_op` | `.read_iter` (source) | What the graph shows |
|---|---|---|---|
| `/etc/hostname` (ext4) | `ext4_file_operations` | `ext4_file_read_iter` (`fs/ext4/file.c` L972) | → `generic_file_read_iter()` → `filemap_read()` (page cache). #6 was a cache miss: `filemap_add_folio()` + `filemap_update_page()` = 949 µs |
| `/proc/version` | `proc_reg_file_ops` | `proc_reg_read_iter` (`fs/proc/inode.c` L569/L596) | the entry was created with `proc_create_single("version", 0, NULL, version_proc_show)` (`fs/proc/version.c` L23), so the read ends in `seq_read_iter()` → `version_proc_show()` |
| pipe (from `echo hi \| …`) | `pipeanon_fops` | `anon_pipe_read` (`fs/pipe.c` L1261). A named FIFO would use `pipefifo_fops` → `fifo_pipe_read` (L1250) | #6 returns the 3 bytes `hi\n`. #7 is the EOF read, which waits for the writer to close (142 µs) |

The script's filter list lets ftrace patch `seq_read*` and `*_read_iter`. Because of `--max-graph-depth 6`, deeper callees such as `version_proc_show()` may be cut off, so open `proc.graph` to see how deep your run went.

## Why `__switch_to` never shows up

When `cat` blocks (for example, on the pipe's EOF read while it waits for `echo` to exit), the task sleeps inside `anon_pipe_read()` → `wait_event_interruptible_exclusive()` (`fs/pipe.c` L388) → `schedule()`. The switch itself never appears in the trace, for three reasons:

1. `__switch_to()` is marked `__notrace_funcgraph` (`arch/x86/kernel/process_64.c` L610). function_graph traces a function by hooking both its call and its return, and `__switch_to` returns **on a different task's stack** from the one it was called on.
2. `-F` filters on `cat`'s PID. Whatever runs while `cat` sleeps belongs to other PIDs and is not recorded.
3. Our `-l` list leaves out the scheduler entirely. That is deliberate: patching fewer functions keeps the trace cheap.

`available_filter_functions` shows the same idea. `do_syscall_64` (`noinstr`) and `x64_sys_call` (its file is built with `CFLAGS_REMOVE_syscall_64.o = $(CC_FLAGS_FTRACE)`) can never be traced.
