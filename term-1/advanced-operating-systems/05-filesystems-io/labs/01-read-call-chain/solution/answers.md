# Lab 05.1 — Solution to the extension

Checked against Linux v6.18.63 (`_shared/sources/linux`). Line numbers are for that tag.

| File | `f_op` table | `vfs_read()` branch | Function that produces the bytes |
|---|---|---|---|
| ext4 regular file | `ext4_file_operations` (`fs/ext4/file.c` L970) | `->read_iter` via `new_sync_read()` | `filemap_read()` → `copy_folio_to_iter()` |
| `/dev/null` | `null_fops` (`drivers/char/mem.c` L644) | `->read` (the table has both; `vfs_read()` tests `->read` first) | `read_null()` L412: `return 0;` (EOF) |
| `/proc/uptime` | `proc_iter_file_ops` (`fs/proc/inode.c`, `.read_iter = proc_reg_read_iter`), chosen because the entry has `proc_read_iter` | `->read_iter` | `proc_reg_read_iter()` (L289) → `pde->proc_ops->proc_read_iter` = `seq_read_iter()` (`fs/seq_file.c` L171) → `uptime_proc_show()` (`fs/proc/uptime.c` L12), which formats the text on every read |
| anonymous pipe (`echo hi \| ./readone /dev/stdin`) | `pipeanon_fops` (`fs/pipe.c` L1259); named FIFOs use `pipefifo_fops` (L1248) | `->read_iter` | `anon_pipe_read()` (`fs/pipe.c` L269): copies from the pipe ring, sleeps on `pipe->rd_wait` if empty |

How to see it yourself:

```bash
sudo timeout 10 trace-cmd record -p function_graph -g vfs_read -l vfs_read -l read_null -l new_sync_read --max-graph-depth 3 -F ./readone /dev/null
sudo trace-cmd report | grep -E 'vfs_read|read_null|new_sync_read'
sudo timeout 10 trace-cmd record -p function_graph -g vfs_read -l vfs_read -l proc_reg_read_iter -l seq_read_iter -l uptime_proc_show --max-graph-depth 4 -F ./readone /proc/uptime
sudo trace-cmd report | grep -E 'proc_reg_read_iter|seq_read_iter|uptime_proc_show'
sudo trace-cmd reset      # always filter ftrace (-l) and reset afterwards
```

Key observations:

- `/dev/null` takes the old `.read` branch: no `kiocb`, no `iov_iter`, the cheapest path in `vfs_read()`.
- `/proc` files have no page cache: `seq_file` builds the text into a kernel buffer on each read. That is why `cat /proc/uptime` changes every time and why `stat` reports size 0.
- A pipe's `struct file` has no position (`FMODE_STREAM`, so `file_ppos()` returns `NULL`); `ksys_read()` passes `ppos = NULL` and never updates `f_pos`.
