# Lab 04.5 — Slab caches: what 200 000 empty files cost the kernel

**Goal:** see SLUB at work. Create and delete N empty files, and watch the `dentry` and inode caches in `/proc/slabinfo` and `slabtop` grow and shrink.

Runs on: the aos-lab VM (`~/work/04-memory/05-slab-files`). Empty files use inodes and directory blocks only: about 10 MB of disk for 200 000 files, and the script deletes them. The plan asked for 1 M files; this lab uses 200 000 to keep a shared VM's inode table and disk light. The effect scales linearly.

## Steps

```bash
mkdir -p ~/work/04-memory/05-slab-files && cd ~/work/04-memory/05-slab-files
gcc -Wall -Wextra -O2 -o mkfiles mkfiles.c
bash slab-watch.sh 200000
grep -E '^(Slab|SReclaimable|SUnreclaim):' /proc/meminfo
```

## Code

- [`mkfiles.c`](mkfiles.c): `openat(O_CREAT|O_EXCL)` + `close` N times in one directory, or `unlinkat` N times and then `rmdir`.
- [`slab-watch.sh`](slab-watch.sh): prints `active_objs`, `num_objs`, `objsize` and approximate MiB for the dentry and inode caches before, after create, and after delete, then `slabtop -o -s c`.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute numbers on your machine.

```
$ bash slab-watch.sh 200000
== filesystem of $HOME: ext2/ext3 ; N=200000
== before
  btrfs_inode        active=       0 total=       0 objsize=1016  ~    0.0 MiB
  ext4_inode_cache   active=    8068 total=    8207 objsize=1128  ~    8.8 MiB
  shmem_inode_cache  active=    1575 total=    1596 objsize= 768  ~    1.2 MiB
  inode_cache        active=    7185 total=    7280 objsize= 616  ~    4.3 MiB
  dentry             active=   33939 total=   34125 objsize= 192  ~    6.2 MiB
created 200000 files in /home/fred/work/04-memory/slabtest
== after create
  btrfs_inode        active=       0 total=       0 objsize=1016  ~    0.0 MiB
  ext4_inode_cache   active=  208075 total=  208075 objsize=1128  ~  223.8 MiB
  shmem_inode_cache  active=    1570 total=    1596 objsize= 768  ~    1.2 MiB
  inode_cache        active=    7228 total=    7280 objsize= 616  ~    4.3 MiB
  dentry             active=  233919 total=  233919 objsize= 192  ~   42.8 MiB
  files listed: 200000
deleted 200000 files in /home/fred/work/04-memory/slabtest
== after delete
  btrfs_inode        active=       0 total=       0 objsize=1016  ~    0.0 MiB
  ext4_inode_cache   active=    8433 total=    8671 objsize=1128  ~    9.3 MiB
  shmem_inode_cache  active=    1555 total=    1596 objsize= 768  ~    1.2 MiB
  inode_cache        active=    7228 total=    7280 objsize= 616  ~    4.3 MiB
  dentry             active=   34518 total=   35532 objsize= 192  ~    6.5 MiB
== top caches by size (slabtop -o -s c)
 Active / Total Objects (% used)    : 443739 / 455322 (97.5%)
 Active / Total Slabs (% used)      : 10562 / 10562 (100.0%)
 Active / Total Caches (% used)     : 335 / 415 (80.7%)
 Active / Total Size (% used)       : 93050.32K / 95328.45K (97.6%)
 Minimum / Average / Maximum Object : 0.01K / 0.21K / 10.62K

  OBJS ACTIVE  USE OBJ SIZE  SLABS OBJ/SLAB CACHE SIZE NAME                   
  8671   8433  97%    1.10K    299       29      9568K ext4_inode_cache       
 35532  34518  97%    0.19K   1692       21      6768K dentry                 
  8950   8950 100%    0.63K    358       25      5728K tracefs_inode_cache    
 35220  35089  99%    0.13K   1174       30      4696K kernfs_node_cache      
  7280   7228  99%    0.60K    280       26      4480K inode_cache            
 42588  42124  98%    0.10K   1092       39      4368K buffer_head            
  6552   6533  99%    0.57K    234       28      3744K radix_tree_node        
```

```
$ grep -E '^(Slab|SReclaimable|SUnreclaim):' /proc/meminfo
Slab:             110060 kB
SReclaimable:      39044 kB
SUnreclaim:        71016 kB
```

## What to observe

- **+N dentries and +N inodes**: each file costs one `dentry` (192 B) and one filesystem inode (`ext4_inode_cache`, 1128 B). In total that is ≈ 215 MiB (223.8 + 42.8 − 8.8 − 6.2) per 200 000 files, all in `SReclaimable`, none in any process's RSS.
- **After delete** the counts drop almost back to the starting values: unlink evicts each inode (`iput` → `evict` → `destroy_inode`) and frees its dentry. Because the objects were freed in bulk, whole slabs became empty and SLUB gave them back to the buddy allocator, so `total` fell too, not just `active`. In other workloads frees are scattered, slabs stay partially used and `total` stays high (internal fragmentation inside slabs).
- `objperslab` × `objsize` ≤ `pagesperslab` × 4096. The leftover is per-slab waste (internal fragmentation inside the slab).

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `Permission denied` on `/proc/slabinfo` | the file is 0400 root | the script uses `sudo` |
| no `ext4_inode_cache` line | `$HOME` is on another FS (xfs, btrfs, tmpfs) | the script greps for several inode caches. Check `stat -f -c %T ~`. |
| numbers barely move | caches merged (aliases), or N is too small | use a bigger N, or look at `/sys/kernel/slab/dentry/` |

## Extension task

Use `bpftrace` to count `kmem_cache_alloc` calls per cache name during `mkfiles create` (`tracepoint:kmem:kmem_cache_alloc`, field `name` or `bytes_alloc`). Which caches besides dentry and inode does creating a file touch? No solution is given.

Solution notes: [`solution/answers.md`](solution/answers.md).
