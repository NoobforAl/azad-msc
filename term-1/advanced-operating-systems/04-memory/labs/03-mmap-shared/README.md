# Lab 04.3 — `mmap`: shared vs private, file vs anonymous

**Goal:** run the same 4 × 1 000 000 atomic increments through the four kinds of mapping, and show who sees the result and what reaches the file.

Runs on: the aos-lab VM (`~/work/04-memory/03-mmap-shared`). User space only; nothing in this lab is destructive.

## Steps

```bash
mkdir -p ~/work/04-memory/03-mmap-shared && cd ~/work/04-memory/03-mmap-shared
gcc -Wall -Wextra -O2 -o mapcount mapcount.c

./mapcount file-shared  counter.bin ; od -A d -t u8 -N 8 counter.bin
./mapcount file-private counter.bin ; od -A d -t u8 -N 8 counter.bin
./mapcount anon-shared
./mapcount anon-private

# what the kernel built: one VMA per mapping kind
strace -f -e trace=mmap,msync ./mapcount file-shared counter.bin 2 10 2>&1 | grep -E 'mmap\(NULL, 4096|msync'
rm -f counter.bin
```

## Code

[`mapcount.c`](mapcount.c) creates (or truncates) a 4 KiB file and maps it. File modes use `MAP_SHARED` or `MAP_PRIVATE`; anonymous modes add `MAP_ANONYMOUS`. It then forks N children. Each child runs `__atomic_fetch_add(ctr, 1, __ATOMIC_RELAXED)` `iters` times and calls `_exit`. The parent waits for all of them, calls `msync(MS_SYNC)` for the file modes, and prints what it sees in memory and what `pread()` returns from the file.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. This is a shared 8-vCPU guest, so expect different absolute numbers on your machine.

```
$ ./mapcount file-shared  counter.bin ; od -A d -t u8 -N 8 counter.bin
file-shared  children=4 iters=1000000  expected=4000000  parent sees=4000000  file has=4000000
0000000              4000000
0000008
$ ./mapcount file-private counter.bin ; od -A d -t u8 -N 8 counter.bin
file-private children=4 iters=1000000  expected=4000000  parent sees=0  file has=0
0000000                    0
0000008
$ ./mapcount anon-shared ; ./mapcount anon-private
anon-shared  children=4 iters=1000000  expected=4000000  parent sees=4000000
anon-private children=4 iters=1000000  expected=4000000  parent sees=0
$ strace -f -e trace=mmap,msync ./mapcount file-shared counter.bin 2 10 2>&1 | grep ...
mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, 3, 0) = 0x72a7b8e96000
msync(0x72a7b8e96000, 4096, MS_SYNC)    = 0
```

## What to observe

| Mode | Parent sees | File has | Why |
|---|---|---|---|
| `file-shared` | 4 000 000 | 4 000 000 | one page-cache page, mapped RW in all processes; `msync` writes it back |
| `file-private` | 0 | 0 | each child's first write is a COW (`do_cow_fault` / `wp_page_copy`) into its own anon page, which is freed at exit |
| `anon-shared` | 4 000 000 | — | a shmem object shared across `fork` |
| `anon-private` | 0 | — | an ordinary COW anonymous page per child |

- With `__ATOMIC_RELAXED` the total is still exact: atomicity does not depend on ordering. Try a plain `(*ctr)++` (see the extension) to see increments get lost.
- `strace` shows the flags exactly as `do_mmap()` received them (`MAP_SHARED`, `PROT_READ|PROT_WRITE`).

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `file-shared` prints less than expected | you replaced the atomic with `++` | keep `__atomic_fetch_add` |
| `Bus error` | the file is shorter than the mapping (no `ftruncate`) | `mapcount.c` calls `ftruncate(fd, 4096)` |
| `od` shows the old value | you read the file before `msync`/exit on another machine via NFS | local file systems share the page cache, so `od` sees it immediately |

## Extension task

1. Replace the atomic with `(*ctr)++` and run `anon-shared` with 4 children × 10 000 000. Explain the lost updates in terms of Module 03.
2. Make two **unrelated** processes (not parent and child) share a counter without a file on disk (`memfd_create` + passing the fd over a Unix socket, or `shm_open`).

No solution is given.

Solution notes: [`solution/answers.md`](solution/answers.md).
