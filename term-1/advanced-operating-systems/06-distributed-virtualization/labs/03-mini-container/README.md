# Lab 06.3 — A container without Docker

> **VM ONLY.** Needs root: it creates a cgroup, changes mount propagation inside a new mount namespace, calls `pivot_root`, and OOM-kills a process on purpose (inside its own `memory.max` group). Run it in `aos-lab`, never on a shared server you care about.

**Goal:** build a working container from four kernel features you can name: namespaces (`unshare`), a new root (`pivot_root`), and cgroup v2 limits (`memory.max`, `pids.max`, `cpu.max`), then watch each limit fire.

## Steps

```bash
cd ~/work/06-distributed-virtualization/03-mini-container

# 0. rootfs: Alpine minirootfs (~3 MB download, 8 MB unpacked), checksum verified
bash get-rootfs.sh

# 1. a static memory hog and the demo script go into the rootfs
gcc -Wall -Wextra -O2 -static -o hog hog.c
sudo install -m 755 hog demo.sh rootfs/usr/local/bin/

# 2. run the demo inside the container (or no argument for an interactive /bin/sh)
bash minictr.sh /usr/local/bin/demo.sh

# 3. clean up
sudo rmdir /sys/fs/cgroup/aos-m06-ctr
sudo rm -rf rootfs hog alpine-minirootfs-*.tar.gz
```

What `minictr.sh` does, in order:

| Step | Command | Kernel (v6.18.63) |
|---|---|---|
| 1 | `mkdir /sys/fs/cgroup/aos-m06-ctr`; write `memory.max=64M`, `memory.swap.max=0`, `pids.max=20`, `cpu.max="20000 100000"` | `kernel/cgroup/cgroup.c` `cgroup_mkdir()`; `mm/memcontrol.c` `memory_max_write()` |
| 2 | `echo $$ > cgroup.procs`, then `exec unshare` (so every container process starts **inside** the group) | `__cgroup_procs_write()` → `cgroup_attach_task()` |
| 3 | `unshare --mount --uts --ipc --net --pid --cgroup --fork` | `ksys_unshare()` → `unshare_nsproxy_namespaces()` → `create_new_namespaces()` |
| 4 | `mount --make-rprivate /` | stops our mounts propagating to the host (systemd makes `/` shared) |
| 5 | `mount --bind rootfs rootfs`; `pivot_root . .oldroot` | `pivot_root(2)` needs `new_root` to be a mount point |
| 6 | mount `/proc`, `/tmp`, a tiny `/dev` (`null`, `zero`); `umount -l /.oldroot` | the host filesystem becomes unreachable |
| 7 | `hostname aos-ctr`; `exec "$@"` | UTS namespace |

The cgroup namespace is created **after** joining the group (step 2 before 3), so inside, `/proc/self/cgroup` shows `0::/`.

## Code

- [`minictr.sh`](minictr.sh): the launcher (host side + the inner script that runs as PID 1).
- [`demo.sh`](demo.sh): runs inside; identity checks, then tries to exceed each limit. The fork test runs in a child shell and counts sleepers with shell builtins only, because once `pids.max` is reached even `ps` cannot fork.
- [`hog.c`](hog.c): touches memory 4 MiB at a time. Touching (not `malloc`) is what charges the memcg.
- [`get-rootfs.sh`](get-rootfs.sh): Alpine 3.20.3 minirootfs + `sha256sum -c`.

## Expected output

> Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Shared 8-vCPU guest: timings and interleavings differ on every run; the invariants do not.

```
$ bash minictr.sh /usr/local/bin/demo.sh
cgroup /sys/fs/cgroup/aos-m06-ctr: memory.max=67108864 pids.max=20 cpu.max=20000 100000
== identity
my pid: 1   hostname: aos-ctr
PID   COMMAND
    1 demo.sh
   15 ps
cgroup: 0::/
lo: DOWN
ls: /.oldroot: No such file or directory
== pids.max: try to start 30 sleepers
sleepers running: 12
sh: can't fork: Resource temporarily unavailable
== cpu.max: busy loop for 2 s of wall time
== memory.max: touch up to 256 MiB
Terminated
hog: 16 MiB touched
hog: 32 MiB touched
hog: 48 MiB touched
Killed
hog exit status: 137
== host view of /sys/fs/cgroup/aos-m06-ctr after exit
oom 1
oom_kill 1
pids.events: max 1   pids.peak: 20
usage_usec 1274743
nr_throttled 62
throttled_usec 7709667
```

`Terminated` (from `timeout 2`) and `Killed` are written to stderr, so they interleave with stdout. Cleanup afterwards left no `aos-m06` cgroup (`ls /sys/fs/cgroup | grep -c aos-m06` → `0`).

Extension solution (`sudo solution/ctr $PWD/rootfs /sys/fs/cgroup/aos-m06-ctr /bin/sh -c '...'`, same VM):

```
pid=1 host=aos-ctr-c
0::/
PID   COMMAND
    1 ps
ctr: child exited with 0
```

## What to observe

- **`my pid: 1`, and `ps` shows only two processes.** The PID namespace plus a fresh `/proc` mount. On the host, `ps -ef | grep demo.sh` shows the same process under a normal host PID.
- **`cgroup: 0::/`.** The cgroup namespace's root is `aos-m06-ctr`; the container cannot see where it sits in the host hierarchy.
- **`lo: DOWN` only.** A new network namespace has just a loopback, down. Connecting it needs a `veth` pair (extension idea).
- **`/.oldroot` is gone.** `pivot_root` + lazy unmount: unlike `chroot`, there is no path back to the host's files.
- **pids.max = 20.** Only 12 sleepers are alive when we count, because the forking shell and its short-lived children also held PIDs at the moment `fork()` failed (`pids.peak: 20` is the proof that the group hit the limit). The child shell dies with `can't fork: Resource temporarily unavailable` (`EAGAIN` from `pids_try_charge()`), and the host sees `pids.events: max 1`, `pids.peak: 20`.
- **cpu.max = 20%.** `usage_usec` is the CPU time of the whole group (busy loop, hog, shells): 1.27 s over roughly 6–7 s of wall time, never more than 20 ms per 100 ms period. `nr_throttled 62` counts the periods in which the group used up its quota and was stopped.
- **memory.max = 64M.** `hog` gets to ~48–60 MiB and is killed (exit status 137 = 128 + `SIGKILL`). The host counts `oom_kill 1` in `memory.events`. Without `memory.swap.max=0` it would swap instead of dying.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `pivot_root: Invalid argument` | `new_root` not a mount point, or `/` has shared propagation | `mount --bind rootfs rootfs` and `mount --make-rprivate /` first (quiz Q11) |
| `ps` shows host processes | `/proc` not remounted in the new PID namespace | mount proc **after** `pivot_root` |
| `echo +memory > cgroup.subtree_control: Device or resource busy` | no-internal-process rule: the parent has processes of its own | create the group under a parent with no member processes (the root cgroup is exempt) |
| hog never killed, system slows | swap enabled, `memory.swap.max` unset | `echo 0 > memory.swap.max` |
| `sleep: can't open '/dev/null'` | empty `/dev` in the rootfs | the minimal `/dev` mount in step 6 |
| `rmdir: Device or resource busy` | a process is still in the group | `cat /sys/fs/cgroup/aos-m06-ctr/cgroup.procs`, kill it, retry |

## Extension

Replace `unshare(1)` with your own launcher in C: `clone()` with `CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWNET | CLONE_NEWPID`, move the child into the cgroup **before** it runs anything (use a pipe to make it wait), then `unshare(CLONE_NEWCGROUP)`, `sethostname`, make `/` private, bind-mount the rootfs, `pivot_root(2)` (glibc has no wrapper: use `syscall(SYS_pivot_root, ...)`), mount `/proc`, detach the old root, `execv`. Bonus: add `CLONE_NEWUSER` with a uid map so it runs without `sudo`.

Solution: [`solution/ctr.c`](solution/ctr.c) (`gcc -Wall -Wextra -O2 -o ctr ctr.c`, zero warnings).

Related: [note 08](../../notes/08-containers-namespaces-cgroups.en.md) · [walkthrough §3–4](../../kernel-walkthrough.en.md) · quiz Q8, Q11, Q12.
