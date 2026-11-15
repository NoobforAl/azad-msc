# Lab 04.6 — Thrashing and the OOM killer, inside a cgroup

> **VM ONLY.** This lab deliberately drives a process out of memory. It always runs inside a throw-away cgroup v2 with `memory.max` and `memory.swap.max=0`, so only that cgroup is affected. Never run the hog without the cgroup on a shared machine.

**Goal:**

- Watch the OOM killer pick and kill a process inside a 128 MiB cgroup.
- Show thrashing: a 64 MiB cgroup repeatedly reads a 128 MiB file and refaults it from disk on every pass, with **no swap at all**.

Runs on: the aos-lab VM (`~/work/04-memory/06-oom-thrashing`). Peak allocation is 128 MiB (the limit) plus a 128 MiB data file on disk, which is deleted at the end.

## Steps

```bash
mkdir -p ~/work/04-memory/06-oom-thrashing && cd ~/work/04-memory/06-oom-thrashing
gcc -Wall -Wextra -O2 -o hog hog.c
gcc -Wall -Wextra -O2 -o thrash thrash.c

# A: OOM kill inside the cgroup
bash mem-cgroup.sh 128M ./hog 512
sudo dmesg | grep -E 'Memory cgroup out of memory|oom-kill:' | tail -2

# B: thrashing; the working set (128 MiB file) is bigger than the limit (64 MiB)
dd if=/dev/urandom of=big.bin bs=1M count=128 status=none
bash mem-cgroup.sh 64M  ./thrash big.bin 3
# C: same program, limit larger than the working set
bash mem-cgroup.sh 256M ./thrash big.bin 3
rm -f big.bin
```

## Code

- [`hog.c`](hog.c): `mmap` + `memset` 16 MiB at a time up to a maximum, printing progress.
- [`thrash.c`](thrash.c): drop the file's own cached pages (`posix_fadvise(DONTNEED)`), `mmap` the file `MAP_SHARED` with `MADV_RANDOM` (no readahead), read one byte per page, and run several passes. Each pass reports major and minor faults and the time it took.
- [`mem-cgroup.sh`](mem-cgroup.sh):
  - creates `/sys/fs/cgroup/aos04-<pid>` with `memory.max` and `memory.swap.max=0`;
  - moves a shell into it and `exec`s the command as your user;
  - prints the exit status, `memory.events`, `memory.peak`, selected `memory.stat` lines and `memory.pressure`;
  - removes the cgroup.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute numbers on your machine.

**A: OOM kill inside a 128 MiB cgroup**

```
$ bash mem-cgroup.sh 128M ./hog 512
== cgroup /sys/fs/cgroup/aos04-11677  memory.max=134217728
hog pid=11690 touched 16 MiB
hog pid=11690 touched 32 MiB
hog pid=11690 touched 48 MiB
hog pid=11690 touched 64 MiB
hog pid=11690 touched 80 MiB
hog pid=11690 touched 96 MiB
hog pid=11690 touched 112 MiB
mem-cgroup.sh: line 21: 11688 Killed                  sudo sh -c "echo \$\$ > $CG/cgroup.procs && exec sudo -u $USER $*"
== exit status: 137
== memory.events
  low 0
  high 0
  max 36
  oom 1
  oom_kill 1
  oom_group_kill 0
== memory.peak:  134217728
== memory.stat (selected)
  anon 0
  file 0
  workingset_refault_file 0
  workingset_activate_file 0
  pgmajfault 0
== memory.pressure
  some avg10=0.00 avg60=0.00 avg300=0.00 total=7286
  full avg10=0.00 avg60=0.00 avg300=0.00 total=7286
```

```
$ sudo dmesg | grep -E 'Memory cgroup out of memory|oom-kill:' | tail -2
[  444.502033] oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=/,mems_allowed=0,oom_memcg=/aos04-11677,task_memcg=/aos04-11677,task=hog,pid=11690,uid=1000
[  444.502143] Memory cgroup out of memory: Killed process 11690 (hog) total-vm:133764kB, anon-rss:129152kB, file-rss:1572kB, shmem-rss:0kB, UID:1000 pgtables:304kB oom_score_adj:0
```

The `memory.stat` values are read after the hog was killed and its memory freed, so they are 0.

**B: 64 MiB limit, 128 MiB file (working set > limit)**

```
$ dd if=/dev/urandom of=big.bin bs=1M count=128 status=none
$ bash mem-cgroup.sh 64M ./thrash big.bin 3
== cgroup /sys/fs/cgroup/aos04-12048  memory.max=67108864
pass 1: pages=32768 majflt=32768 minflt=3  223870 ms
pass 2: pages=32768 majflt=32768 minflt=0  52152 ms
pass 3: pages=32768 majflt=32768 minflt=0  63778 ms
== exit status: 0
== memory.events
  low 0
  high 0
  max 1502
  oom 0
  oom_kill 0
  oom_group_kill 0
== memory.peak:  67108864
== memory.stat (selected)
  anon 0
  file 65003520
  workingset_refault_file 64381
  workingset_activate_file 0
  pgmajfault 98305
== memory.pressure
  some avg10=1.48 avg60=1.87 avg300=1.02 total=5269248
  full avg10=1.48 avg60=1.87 avg300=1.02 total=5269248
```

**C: 256 MiB limit (working set fits)**

```
$ bash mem-cgroup.sh 256M ./thrash big.bin 3
== cgroup /sys/fs/cgroup/aos04-24995  memory.max=268435456
pass 1: pages=32768 majflt=32768 minflt=3  26193 ms
pass 2: pages=32768 majflt=0 minflt=0  2 ms
pass 3: pages=32768 majflt=0 minflt=0  4 ms
== exit status: 0
== memory.events
  low 0
  high 0
  max 0
  oom 0
  oom_kill 0
  oom_group_kill 0
== memory.peak:  137142272
== memory.stat (selected)
  anon 0
  file 134365184
  workingset_refault_file 0
  workingset_activate_file 0
  pgmajfault 32770
== memory.pressure
  some avg10=0.00 avg60=0.00 avg300=0.00 total=0
  full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

## What to observe

- **A:** the hog gets to about 112 MiB, then dies with exit status 137 (128 + `SIGKILL`). `memory.events` shows `oom 1`, `oom_kill 1`. `dmesg` names the cgroup (`oom_memcg=/aos04-…`) and the victim's `anon-rss`. The kill came from `mem_cgroup_out_of_memory()` → `oom_badness()` (walkthrough §8). The rest of the VM never noticed.
- **B (64 MiB):** **every pass** has 32 768 major faults, because the cgroup cannot hold the 128 MiB file and each pass evicts what the next pass needs first. That is thrashing. `workingset_refault_file` = 64 381 ≈ passes 2 and 3 (pass 1 is a first read, not a refault). `memory.events max 1502` counts the times the cgroup hit its limit, and `memory.pressure` shows non-zero `some`/`full` (avg60 1.87 %). Pass 1 was even slower than in C (224 s vs 26 s) because reclaim ran inside every fault.
- **C (256 MiB):** pass 1 has the major faults, and passes 2–3 have none and are much faster. The working set fits.
- No swap was used anywhere (`memory.swap.max=0`). Thrashing does not need swap; file pages are enough.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `mkdir: ... Permission denied` | not root | the script uses `sudo` |
| `echo +memory ... Device or resource busy` | the controller is already enabled, or the root has processes | check `cat /sys/fs/cgroup/cgroup.subtree_control`. On Ubuntu `memory` is already there. |
| thrash pass 1 shows 0 major faults | `big.bin` is still in the page cache, charged to *your* login cgroup (page-cache pages are charged to the cgroup that first brought them in) | `thrash.c` calls `fdatasync` + `posix_fadvise(DONTNEED)` first, so the pages are re-read and charged to the test cgroup |
| hog survives to 512 MiB | the shell didn't land in the cgroup | `cat /proc/self/cgroup` inside; check `cgroup.procs` |

## Extension task

Replace `memory.max` with `memory.high=64M` (and `memory.max=max`) for part B. What changes: kill, throttling, or both? Then add `memory.oom.group=1` and run *two* hogs in the same cgroup. How many die? No solution is given.

Solution notes: [`solution/answers.md`](solution/answers.md).
