# 06 — Distributed OS & Virtualization: videos

> Checked on **2026-11-15**. Every YouTube URL was resolved through YouTube's oEmbed endpoint (`https://www.youtube.com/oembed?url=...`), which returns the real title and channel for that exact ID. The FOSDEM entry was checked on its archive page.
> YouTube pages served a login wall to the checker, so **YouTube durations could not be read directly**. Durations are given only when a second source states them, and the source is named. Otherwise the entry says "duration not confirmed".

| # | Video | Channel / host | Notes it serves | Level | Length |
|---|---|---|---|---|---|
| 1 | Distributed Systems lecture series (Cambridge, 8 lectures) | Martin Kleppmann | 01, 02, 03, 04, 05 | Intermediate | ≈ 7 h total (author's blog) |
| 2 | Lecture 2: RPC and Threads (6.824) | MIT 6.824: Distributed Systems | 01 | Intermediate | not confirmed |
| 3 | Lecture 6: Fault Tolerance: Raft (1) (6.824) | MIT 6.824: Distributed Systems | 05 | Advanced | not confirmed |
| 4 | 6.S081 Fall 2020 Lecture 19: Virtual Machines | David Morejon (upload of the MIT lecture, linked from the course schedule) | 06, 07 | Advanced | not confirmed |
| 5 | Containers From Scratch • Liz Rice • GOTO 2018 | GOTO Conferences | 08 | Beginner → Intermediate | 43 min (Class Central listing) |
| 6 | Cgroups, namespaces, and beyond: what are containers made from? | Docker | 08 | Intermediate | 54 min (Class Central listing) |
| 7 | 7 years of cgroup v2: the future of Linux resource control | FOSDEM 2023, Containers devroom | 08 | Intermediate → Advanced | 30 min slot (FOSDEM schedule) |

All talks are in **English**.

---

## 1. Distributed Systems lecture series — Martin Kleppmann (University of Cambridge)

- **URL:** https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB
- **Length:** 8 lectures, "about 7 hours of video and 87 pages of lecture notes", per the author's post https://martin.kleppmann.com/2020/11/18/distributed-systems-and-elliptic-curves.html. The durations of the individual parts are not confirmed.
- **Why it fits:** this is the closest match to notes 01–05. Each part is a short video, so watch the parts instead of using time ranges.

| Part (exact title) | URL | Note |
|---|---|---|
| Distributed Systems 1.3: RPC (Remote Procedure Call) | https://www.youtube.com/watch?v=S2osKiqQG9s | 01 |
| Distributed Systems 2.3: System models | https://www.youtube.com/watch?v=y8f7ZG_UnGI | 05 |
| Distributed Systems 2.4: Fault tolerance | https://www.youtube.com/watch?v=43TDfUNsM3E | 05 |
| Distributed Systems 3.1: Physical time | https://www.youtube.com/watch?v=FQ_2N3AQu0M | 03 |
| Distributed Systems 3.2: Clock synchronisation | https://www.youtube.com/watch?v=mAyW-4LeXZo | 03 (NTP offset/delay) |
| Distributed Systems 3.3: Causality and happens-before | https://www.youtube.com/watch?v=OKHIdpOAxto | 02, 04 |
| Distributed Systems 4.1: Logical time | https://www.youtube.com/watch?v=x-D8iFU1d-o | 02 (Lamport + vector clocks), Lab 06.1 |
| Distributed Systems 4.2: Broadcast ordering | https://www.youtube.com/watch?v=A8oamrHf_cQ | 02 (causal broadcast, Lab 06.1 extension) |
| Distributed Systems 5.2: Quorums | https://www.youtube.com/watch?v=uNxl3BFcKSA | 05 |
| Distributed Systems 5.3: State machine replication | https://www.youtube.com/watch?v=mlWOQuO55PE | 05 |
| Distributed Systems 6.2: Raft | https://www.youtube.com/watch?v=uXEYuDwm7e4 | 05 |

- **Outdated?** No. The theory is timeless, and the course was recorded in 2020.
- **Verified:** the playlist was resolved by oEmbed (title "Distributed Systems lecture series", author Martin Kleppmann). Part IDs were taken from the links inside the official lecture notes PDF (https://www.cl.cam.ac.uk/teaching/2122/ConcDisSys/dist-sys-notes.pdf), and each was resolved by oEmbed to the title shown.

## 2. MIT 6.824 — Lecture 2: RPC and Threads

- **URL:** https://www.youtube.com/watch?v=oZR76REwSyA · channel **MIT 6.824: Distributed Systems** · duration not confirmed
- **Level:** Intermediate. **Why:** Go RPC and threads, which is exactly the toolkit of Lab 06.2. The course notes (https://pdos.csail.mit.edu/6.824/notes/l-rpc.txt) cover RPC failure semantics (at-most-once and the duplicate table) that `rpcbank.go -dedup` implements.
- **Outdated?** This is the Spring 2020 recording. Later years (6.5840) use the same RPC material.
- **Verified:** oEmbed → "Lecture 2: RPC and Threads", MIT 6.824: Distributed Systems.

## 3. MIT 6.824 — Lecture 6: Fault Tolerance: Raft (1)

- **URL:** https://www.youtube.com/watch?v=64Zp3tzNbpE · channel **MIT 6.824: Distributed Systems** · duration not confirmed
- **Level:** Advanced. **Why:** leader election, terms and log replication in Raft. This goes deeper than note 05's "consensus preview". Read the Raft paper (Ongaro & Ousterhout 2014, §5) first. Part (2) is Lecture 7 of the same course.
- **Outdated?** No, this is Spring 2020.
- **Verified:** oEmbed → "Lecture 6: Fault Tolerance: Raft (1)", MIT 6.824: Distributed Systems.

## 4. MIT 6.S081 Fall 2020 — Lecture 19: Virtual Machines (Robert Morris)

- **URL:** https://youtu.be/R8obXHAIPY0 · duration not confirmed
- **Level:** Advanced. **Why:** trap-and-emulate, then hardware support (VT-x, VMCS, EPT), then the Dune paper. This lines up with notes 06 and 07 and explains why `cpuid` costs ~380 ns in Lab 06.5. Lecture notes: https://pdos.csail.mit.edu/6.S081/2020/lec/l-vmm.txt
- **Outdated?** The x86 VT-x/EPT model it teaches is still current. KVM code details are not covered, so use the kernel walkthrough for those.
- **Verified:** the link was taken from the official schedule https://pdos.csail.mit.edu/6.S081/2020/schedule.html ("LEC 19 (rtm): Virtual Machines (video)"), and oEmbed returned "6.S081 Fall 2020 Lecture 19: Virtual Machines" (uploader channel: David Morejon).

## 5. Containers From Scratch — Liz Rice, GOTO 2018

- **URL:** https://www.youtube.com/watch?v=8fi7uSYlOdc · channel **GOTO Conferences** · 43 min (Class Central listing, GOTO Amsterdam 2018)
- **Level:** Beginner → Intermediate. **Why:** live-codes a container in Go with `clone` flags, `chroot` and a cgroup. Watch it before Lab 06.3. The lab goes further, with `pivot_root`, cgroup v2 `memory.max`/`pids.max`/`cpu.max`, and a C `clone()` launcher.
- **Outdated?** Partly. It uses `chroot` (we use `pivot_root`), and its cgroup demo is from the cgroup v1 era. Namespaces are unchanged.
- **Verified:** oEmbed → "Containers From Scratch • Liz Rice • GOTO 2018", GOTO Conferences. The duration comes from Class Central's course page (https://classcentral.com/course/youtube-containers-from-scratch-liz-rice-goto-2018-194167).

## 6. Cgroups, namespaces, and beyond: what are containers made from? — Jérôme Petazzoni

- **URL:** https://www.youtube.com/watch?v=sK5i-N34im8 · channel **Docker** · 54 min (Class Central listing, DockerCon EU 2015)
- **Level:** Intermediate. **Why:** a tour of every namespace type and each cgroup controller, then a demo that assembles a container by hand. It is good background for note 08.
- **Outdated?** **Yes, for cgroups.** It describes cgroup **v1** (one hierarchy per controller). Ubuntu 24.04 and our test VM use the unified v2 hierarchy, so treat its cgroup filesystem paths as historical. The namespace part is still accurate, apart from the time namespace, which was added in Linux 5.6, after this talk.
- **Verified:** oEmbed → "Cgroups, namespaces, and beyond: what are containers made from?", Docker. The duration comes from Class Central (https://classcentral.com/course/youtube-cgroups-namespaces-and-beyond-what-are-containers-made-from-222537).

## 7. 7 years of cgroup v2: the future of Linux resource control — Chris Down, FOSDEM 2023

- **URL:** https://archive.fosdem.org/2023/schedule/event/container_cgroup_v2/ (videos: `https://video.fosdem.org/2023/UB2.252A (Lameere)/container_cgroup_v2.mp4` / `.webm`)
- **Length:** 30-minute slot (16:55–17:25 on the FOSDEM schedule).
- **Level:** Intermediate → Advanced. **Why:** this is the cgroup v2 counterpart to #6. It covers the unified hierarchy, `memory.high` vs `memory.max`, PSI and how Meta uses them. This is the model our `minictr.sh` uses.
- **Outdated?** No (2023).
- **Verified:** the FOSDEM archive page was fetched, and it lists the title, the speaker, the 30-minute slot and both video files.

---

### Not found / not verified

- **KVM internals (vCPU run loop, `KVM_RUN`, VM exits):** searches found no KVM Forum recording on this topic that could be matched to a confirmed YouTube ID. Use instead the written walk-through `../kernel-walkthrough.en.md`, the QEMU blog post "Micro-Optimizing KVM VM-Exits" (https://www.qemu.org/2019/11/15/micro-optimizing-kvm-vmexits/, text, not video), and the KVM Forum archives at https://kvm-forum.qemu.org/.
- **Berkeley CS162 (Kubiatowicz):** the slides for "Distributed Decision Making" and RPC (Spring 2020, lectures 21–22) were found as PDFs, but no video URL could be confirmed, so they are not listed.
