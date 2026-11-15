# Module 01 notes — index

Read them in order. Each note has: summary, explanation, diagram, worked example, pitfalls, exam key points, links. Persian: [`INDEX.fa.md`](INDEX.fa.md).

| # | Note | Core question | Lab | Quiz |
|---|---|---|---|---|
| 01 | [Kernel types](01-kernel-types.en.md) | What runs in ring 0, and how do the parts talk? | 05 | 1, 2, 13, O1 |
| 02 | [Privilege rings and `CPL`](02-privilege-rings-cpl.en.md) | What exactly does the CPU check, and how does code change level? | 02 (`cpl.c`) | 3, 4, 10 |
| 03 | [Interrupts vs exceptions vs traps](03-interrupts-exceptions-traps.en.md) | How do unrequested events enter the kernel through the IDT? | 03 | 5, 6, 11 |
| 04 | [The `syscall` instruction path](04-syscall-path.en.md) | What happens, instruction by instruction, on `read()`? | 01, 02, 04 | 7, 8, 9, 12 |
| 05 | [Context switch](05-context-switch.en.md) | What is saved and swapped when the CPU changes task? | 05 ext., M02 lab 3 | 10, 14, O2 |
| 06 | [Linux source tree map](06-linux-source-tree-map.en.md) | Where is everything, and how do I find a symbol fast? | 01 | 15 |

Back to the [lesson](../lesson.en.md) · [walkthrough](../kernel-walkthrough.en.md).
