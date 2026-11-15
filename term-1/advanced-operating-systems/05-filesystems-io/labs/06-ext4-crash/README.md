# Lab 05.6 — ext4 crash consistency with `dm-flakey`

> **VM ONLY.** Uses device-mapper and a loop device as root. It only touches its own 256 MiB image, but a mistake with `dmsetup` on the wrong device can destroy data. Never run it on a machine you care about.

**Goal:** simulate a power cut under a mounted ext4 filesystem and see exactly which writes survive: a file that was `fsync()`ed, a file that was only `write()`n, and a "replace by rename" without `fsync()`.

Runs on: the lab VM, `~/work/05-filesystems-io/labs/06-ext4-crash`. Needs the `dm-flakey` target (`sudo modprobe dm-flakey`; on aos-lab: `flakey v1.5.0`). Time: ~30 min.

## Steps

```bash
cd ~/work/05-filesystems-io/labs/06-ext4-crash
sudo modprobe dm-flakey && sudo dmsetup targets | grep flakey
bash crash-demo.sh                    # data=ordered (ext4 default)
MODE=writeback bash crash-demo.sh
MODE=journal   bash crash-demo.sh
```

What `crash-demo.sh` does:

1. `truncate` a 256 MiB image, attach it to a loop device, `mkfs.ext4`.
2. Create a dm-flakey device on top with an **"always up"** table (`<up 180 s> <down 0 s>`): it behaves like a normal disk. Mount it with `data=$MODE`.
3. Write three things:
   - `config` = "old contents", then `sync` (an existing, durable file);
   - `A`, then `sync A` (= `fsync(2)`);
   - `B` with no sync;
   - `config.tmp` = "new contents", then `mv config.tmp config` (replace by rename, no `fsync`).
4. **Power cut:** load the **"always down, drop_writes"** table and switch to it with `dmsetup suspend --nolockfs` + `resume`. From now on every write is acknowledged and thrown away; reads still work. Then `sync` and `umount`: the kernel believes everything was written, but nothing reached the "disk".
5. Switch back to the "up" table, run `e2fsck -fn` (read-only), mount again (journal replay), and print what survived.
6. A `trap` unmounts, removes the dm device and the loop device, and deletes the image.

## Code

[`crash-demo.sh`](crash-demo.sh). The dm-flakey table format is `<start> <len> flakey <dev> <offset> <up_interval> <down_interval> [<num_features> <features>]`, see `Documentation/admin-guide/device-mapper/dm-flakey.rst`.

## Expected output

Real run, `aos-lab` (VirtualBox, Ubuntu 24.04, Linux 6.18.63, dm-flakey v1.5.0), 2026-11-15:

```text
$ bash crash-demo.sh
== mounted: rw,relatime,data=ordered
== before the crash:
  A        19 bytes: A: written + fsync
  B        21 bytes: B: written, no fsync
  config   13 bytes: new contents
== fsck -n right after the crash (read-only check):
  e2fsck 1.47.0 (5-Feb-2023)
  Warning: skipping journal recovery because doing a read-only filesystem check.
  Pass 1: Checking inodes, blocks, and sizes
  Pass 2: Checking directory structure
  Pass 3: Checking directory connectivity
  Pass 4: Checking reference counts
  Pass 5: Checking group summary information
  Free blocks count wrong (57268, counted=57267).
== kernel log at remount (journal replay):
  EXT4-fs (dm-0): recovery complete
  EXT4-fs (dm-0): mounted filesystem 0ecc1a3b-c5e3-4bc5-b364-c6f2bc7a0278 r/w with ordered data mode. Quota mode: none.
== after the crash:
  A        19 bytes: A: written + fsync
  B       MISSING
  config   13 bytes: old contents
```

`MODE=writeback` and `MODE=journal` gave the same "after" result on this run (`A` intact, `B` missing, `config` old); only the mount line changes (`writeback data mode`, `journalled data mode`, and `nodelalloc` is forced for `data=journal`).

## What to observe

- **`A` survived** because `fsync()` waited for its data and for the jbd2 commit of its metadata (note 07 §2.3). This is the only durable state you can rely on.
- **`B` is gone entirely**, not even an empty file: its inode, directory entry and data were all still in the *running* transaction / page cache when the power was cut. A consistent filesystem is not the same as "my data is there".
- **`config` is the old version.** The rename was atomic, but neither the new data nor the rename was ever committed. You got "old", which is fine; the danger is the variant where the rename commits before the data (see the extension).
- **`e2fsck -n` complains** (`Free blocks count wrong`) only because it skipped the journal (`-n` = read-only). The real mount **replays** the journal (`recovery complete`) and the filesystem is consistent with no `fsck` at all.
- **`--nolockfs` matters.** A plain `dmsetup suspend` freezes the filesystem first (`freeze_super`), which syncs it, and then every file survives. The first attempt of this lab on 2026-11-15 did exactly that and "proved" that unsynced data is safe. Always check that your crash test can actually lose data.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `device-mapper: reload ioctl ... failed: Invalid argument` | `dm-flakey` not loaded, or a wrong table length | `sudo modprobe dm-flakey`; length = `blockdev --getsz $LOOP` |
| every file survives | `dmsetup suspend` without `--nolockfs` (fs freeze = sync), or a `sync` before the cut | use `--nolockfs`; no `sync` between the writes and the cut |
| `Device or resource busy` on `dmsetup remove` | still mounted | `umount` first; the script's `trap` does it |
| leftover `/dev/mapper/aos05flakey` after Ctrl-C | the trap was interrupted | `sudo umount mnt; sudo dmsetup remove aos05flakey; sudo losetup -d /dev/loopN` |

## Extension task

Make `config` survive the crash **with the new contents**: write `config.tmp`, `fsync()` it, `rename()` it over `config`, `fsync()` the directory. Run the same crash. What happens to `B` now, and why?

Solution: [`solution/durable_save.c`](solution/durable_save.c), [`solution/crash-fixed.sh`](solution/crash-fixed.sh), [`solution/README.md`](solution/README.md).
