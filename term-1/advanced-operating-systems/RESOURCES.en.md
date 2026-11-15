# Further reading

Picked from GitHub “awesome-os” lists. Every link was opened and checked on 2026-11-15 (`python _shared/tools/add_references.py --check` re-checks them). The same picks are the last slide of each lesson deck.

## 00-setup

- **[The Linux Kernel documentation](https://www.kernel.org/doc/html/latest/)** (Docs): The official kernel docs: admin guide, core APIs, subsystem notes.
- **[virtme-ng](https://github.com/arighi/virtme-ng)** (Tool): Build and run a kernel inside a virtualized snapshot of your live system (needs a Linux host).
- **[A Beginner's Guide to Linux Kernel Development (LFD103)](https://training.linuxfoundation.org/training/a-beginners-guide-to-linux-kernel-development-lfd103/)** (Course): Linux Foundation course on getting started with kernel development.
- **[Bug hunting (kernel docs)](https://www.kernel.org/doc/html/latest/admin-guide/bug-hunting.html)** (Docs): The kernel admin guide on how to hunt a bug.
- **[Bisecting a regression (kernel docs)](https://www.kernel.org/doc/html/latest/admin-guide/bug-bisect.html)** (Docs): Find the exact commit that broke something.
- **[kworkflow (kw)](https://github.com/kworkflow/kworkflow)** (Tool): A workflow tool that cuts the setup cost of kernel development.

## 01-architecture

- **[linux-insides](https://0xax.gitbooks.io/linux-insides/content/)** (Book): A book-style walk through Linux internals: booting, interrupts, system calls, memory.
- **[Interactive map of Linux kernel](https://makelinux.github.io/kernel/map/)** (Docs): One clickable diagram of the kernel's subsystems and how they connect.
- **[Linux system calls table](https://gpages.juszkiewicz.com.pl/syscalls-table/syscalls.html)** (Docs): System-call numbers side by side for every architecture.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (Book): Chapters “Operating system organization” and “Traps and device drivers”.
- **[Exokernel: An Operating System Architecture for Application-Level Resource Management](https://pdos.csail.mit.edu/6.828/2008/readings/engler95exokernel.pdf)** (Paper): 1995: export the hardware and let libraries be the OS, the opposite of a big kernel.
- **[seL4: Formal Verification of an OS Kernel](https://www.sigops.org/s/conferences/sosp/2009/papers/klein-sosp09.pdf)** (Paper): SOSP '09: a small kernel whose correctness is proven, microkernel taken to its limit.

## 02-processes-threads

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (Book): Part I, virtualization: processes, scheduling, address spaces.
- **[Think OS (Allen B. Downey)](https://greenteapress.com/wp/think-os/)** (Book): A brief introduction to operating systems, written for programmers.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (Book): Chapter “Scheduling”.
- **[Linux Kernel Teaching](https://linux-kernel-labs.github.io/refs/heads/master/)** (Course): University-style lectures and labs on the Linux kernel.
- **[linux-insides](https://0xax.gitbooks.io/linux-insides/content/)** (Book): A book-style walk through Linux internals: booting, interrupts, system calls, memory.
- **[Tracing Linux kernel with retsnoop](https://nakryiko.com/posts/retsnoop-intro/)** (Post): Blog post on tracing kernel function calls and returns with a BPF tool.

## 03-concurrency

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (Book): Part II, concurrency: locks, condition variables, semaphores, bugs.
- **[Think OS (Allen B. Downey)](https://greenteapress.com/wp/think-os/)** (Book): A brief introduction to operating systems, written for programmers.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (Book): Chapters “Locking” and “Concurrency revisited”.
- **[Corey: An Operating System for Many Cores](https://www.usenix.org/legacy/events/osdi08/tech/full_papers/boyd-wickizer/boyd_wickizer.pdf)** (Paper): OSDI '08: OS design for many cores, where applications control sharing.
- **[The Multikernel: A new OS architecture for scalable multicore systems](https://www.sigops.org/s/conferences/sosp/2009/papers/baumann-sosp09.pdf)** (Paper): SOSP '09: treat a multicore machine as a network of cores that pass messages.
- **[Linux Kernel Teaching](https://linux-kernel-labs.github.io/refs/heads/master/)** (Course): University-style lectures and labs on the Linux kernel.

## 04-memory

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (Book): Part I, virtualization: address spaces, paging, TLBs, swapping.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (Book): Chapter “Page tables”.
- **[linux-insides](https://0xax.gitbooks.io/linux-insides/content/)** (Book): A book-style walk through Linux internals: booting, interrupts, system calls, memory.
- **[Linux Kernel Teaching](https://linux-kernel-labs.github.io/refs/heads/master/)** (Course): University-style lectures and labs on the Linux kernel.
- **[Dune: Safe User-level Access to Privileged CPU Features](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-117.pdf)** (Paper): OSDI '12: give a process safe access to privileged CPU features using virtualization hardware.
- **[The Linux Kernel documentation](https://www.kernel.org/doc/html/latest/)** (Docs): The official kernel docs: admin guide, core APIs, subsystem notes.

## 05-filesystems-io

- **[Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)** (Book): Part III, persistence: I/O devices, file systems, journaling.
- **[xv6: a simple, Unix-like teaching operating system](https://pdos.csail.mit.edu/6.828/2019/xv6/book-riscv-rev0.pdf)** (Book): Chapters “File system” and “Traps and device drivers”.
- **[The Linux Kernel Module Programming Guide](https://sysprog21.github.io/lkmpg/)** (Book): Hands-on guide to writing kernel modules, where drivers start.
- **[The Linux Kernel documentation](https://www.kernel.org/doc/html/latest/)** (Docs): The official kernel docs: admin guide, core APIs, subsystem notes.
- **[Arrakis: The Operating System is the Control Plane](https://www.usenix.org/conference/osdi14/technical-sessions/presentation/peter)** (Paper): OSDI '14: the kernel steps out of the I/O data path and only controls it.
- **[The Demikernel Datapath OS Architecture for Microsecond-scale Datacenter Systems](https://irenezhang.net/papers/demikernel-sosp21.pdf)** (Paper): SOSP '21: an OS architecture for microsecond-scale datacenter I/O.

## 06-distributed-virtualization

- **[Unikernels: Library Operating Systems for the Cloud](https://anil.recoil.org/papers/2013-asplos-mirage.pdf)** (Paper): ASPLOS '13: one application plus a library OS, built as a single cloud image.
- **[Unikraft](https://github.com/unikraft/unikraft)** (Tool): A project for building specialized, fast unikernels.
- **[LegoOS: A Disseminated, Distributed OS for Hardware Resource Disaggregation](https://www.usenix.org/system/files/osdi18-shan.pdf)** (Paper): OSDI '18: one OS split across machines by hardware resource.
- **[Dune: Safe User-level Access to Privileged CPU Features](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-117.pdf)** (Paper): OSDI '12: give a process safe access to privileged CPU features using virtualization hardware.
- **[The Multikernel: A new OS architecture for scalable multicore systems](https://www.sigops.org/s/conferences/sosp/2009/papers/baumann-sosp09.pdf)** (Paper): SOSP '09: treat a multicore machine as a network of cores that pass messages.

## 07-realtime-research

- **[SOSP: Symposium on Operating Systems Principles](https://sosp.org/)** (Talks): The flagship OS-research conference.
- **[USENIX conferences (OSDI, ATC)](https://www.usenix.org/conferences)** (Talks): Home of OSDI and ATC, two other main OS-research venues.
- **[ASPLOS](https://www.asplos-conference.org/)** (Talks): Where OS research meets architecture and programming languages.
- **[HotOS: Workshop on Hot Topics in Operating Systems](https://sigops.org/s/conferences/hotos/)** (Talks): Short, forward-looking position papers on where OS research is heading.
- **[The benefits and costs of writing a POSIX kernel in a high-level language](https://www.usenix.org/conference/osdi18/presentation/cutler)** (Paper): OSDI '18: what a kernel gains and loses when it is not written in C.
- **[Multiprogramming a 64 kB Computer Safely and Efficiently](https://www.tockos.org/assets/papers/tock-sosp2017.pdf)** (Paper): SOSP '17 (Tock): several apps running safely on a tiny microcontroller.
- **[Linux Plumbers Conference](https://lpc.events/)** (Talks): Where kernel developers present and discuss their work.

## Lists that were reviewed

| List | Used | Why |
|---|---|---|
| [jubalh/awesome-os](https://github.com/jubalh/awesome-os) | yes | Used most: books, Linux-specific guides, kernel debugging, tools, conferences. |
| [penberg/awesome-os](https://github.com/penberg/awesome-os) | yes | Used for research: classic OS papers and the main OS-research conferences. |
| [Francesco601/AWESOME-Operating-System-Resources](https://github.com/Francesco601/AWESOME-Operating-System-Resources) | no | Skipped: mostly a directory of hobby operating systems and from-scratch tutorials. The course reads real kernels (Linux, OpenBSD) instead. |
| [leap0x7b/awesome-osdev](https://github.com/leap0x7b/awesome-osdev) | no | Skipped: about writing a new hobby OS (bootloaders, toy kernels), which is outside this course. |
| [ishandutta2007/Awesome-Operating-Systems](https://github.com/ishandutta2007/Awesome-Operating-Systems) | no | Skipped: a directory of operating systems with market-style overview sections, with few learning resources. |

Note: the link to “The UNIX Time-Sharing System” in penberg/awesome-os (dsf.berkeley.edu) no longer resolves, so it is not included.
