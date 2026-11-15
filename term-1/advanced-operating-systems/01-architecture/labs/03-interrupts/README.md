# Lab 01.3 — Count interrupts: `/proc/interrupts` deltas and `irq:*` tracepoints

**Goal:** measure which interrupt sources fire on an idle and on a loaded machine, check the count against the kernel's own tracepoints, and see that page faults (exceptions) are counted somewhere else.

Runs on: the `aos-lab` VM. `perf stat -a` needs root. Time: 40 min.

## Steps

```bash
scp -r term-1/advanced-operating-systems/01-architecture/labs/03-interrupts aos-lab:~/work/01-architecture/lab03
ssh aos-lab
cd ~/work/01-architecture/lab03
bash irq-delta.sh 5 8                                   # idle: top 8 sources in 5 s
bash irq-delta.sh 5 8 -- dd if=/dev/zero of=big.bin bs=1M count=512 oflag=direct   # disk load
rm -f big.bin
sudo perf stat -e 'irq:irq_handler_entry,irq:softirq_entry,irq_vectors:local_timer_entry,irq_vectors:reschedule_entry,exceptions:page_fault_user' -a sleep 5
perf stat -e page-faults,context-switches ls / > /dev/null
```

## Code

- [`irq-delta.sh`](irq-delta.sh): reads `/proc/interrupts` twice, sums each row over all CPU columns, and prints the rows that grew, sorted by delta. The optional `-- <command>` runs a load in between.

## Expected output

Captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15, about one minute after a VM restart. Six other users were working on the same 8-vCPU guest, so "idle" here means "nothing of ours was running". Numbers are unedited.

```text
$ bash irq-delta.sh 5 8
interrupts during 5s on 8 CPUs (sum over CPUs):
   delta  irq    source
   46186  CAL    Function call interrupts
    9223  21     IO-APIC 21-fasteoi ahci[0000:00:0d.0]
    8746  LOC    Local timer interrupts
     193  RES    Rescheduling interrupts
     100  19     IO-APIC 19-fasteoi enp0s3
      38  TLB    TLB shootdowns
      10  IWI    IRQ work interrupts

$ bash irq-delta.sh 5 8 -- dd if=/dev/zero of=big.bin bs=1M count=512 oflag=direct
interrupts during 5s on 8 CPUs (sum over CPUs):
   delta  irq    source
   16201  LOC    Local timer interrupts
   12139  CAL    Function call interrupts
    2625  21     IO-APIC 21-fasteoi ahci[0000:00:0d.0]
      48  RES    Rescheduling interrupts
      35  IWI    IRQ work interrupts
      28  19     IO-APIC 19-fasteoi enp0s3
      24  TLB    TLB shootdowns

$ sudo perf stat -e 'irq:irq_handler_entry,irq:softirq_entry,irq_vectors:local_timer_entry,irq_vectors:reschedule_entry,exceptions:page_fault_user' -a sleep 5
 Performance counter stats for 'system wide':
              3650      irq:irq_handler_entry
             18126      irq:softirq_entry
             22222      irq_vectors:local_timer_entry
               668      irq_vectors:reschedule_entry
            134260      exceptions:page_fault_user
       5.023989062 seconds time elapsed

$ perf stat -e page-faults,context-switches ls / > /dev/null
               101      page-faults
                 3      context-switches
```

## What to observe

- **Device IRQs vs architecture vectors.** Numbered rows (`21` = the AHCI disk controller, `19` = the `enp0s3` NIC) go through `common_interrupt()` → `handle_irq_event()`. Each of them fires `irq:irq_handler_entry` (walkthrough §6). Named rows (`LOC`, `CAL`, `RES`, `TLB`, `IWI`) have their own IDT entries and never reach `irq_handler_entry`. That's why the tracepoint counted only 3,650 events while `LOC` + `CAL` alone were in the tens of thousands.
- **`LOC` is the scheduler tick.** `CONFIG_HZ=1000` on this kernel. Eight CPUs ticking at full rate for 5 s would be 40,000. The idle sample shows 8,746, about 220/s per CPU, because the kernel is built with `NO_HZ` (`CONFIG_NO_HZ_FULL=y`, which includes idle tick suppression) and idle CPUs skip ticks. The `perf` window saw 22,222 timer interrupts: busier CPUs tick more.
- **IPIs dominate a busy shared VM.** `CAL` (function-call IPIs) was the largest row: other tenants were starting processes and changing memory mappings, and every such change triggers TLB and function-call work on other CPUs (Module 04). `RES` counts "please reschedule" wake-ups across CPUs.
- **`dd oflag=direct` and the disk row.** The `ahci` row counts completions. In this run the "idle" sample had *more* disk interrupts than the `dd` sample, because someone else's I/O dominated. On a quiet machine you'll see row `21` climb with `dd`. Always say what else was running.
- **Exceptions are not interrupts.** 134,260 user page faults in 5 s, system-wide, and none of them appear in `/proc/interrupts`. A single `ls /` takes 101 page faults: demand paging of the binary and its libraries (Module 04).
- **Softirqs outnumber hard IRQs.** 18,126 `softirq_entry` events: timer, RCU and block completions deferred out of the top halves.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `irq_vectors:*` events "not found" | the `perf` binary is older than the kernel, or the tracepoint doesn't exist on this arch | `ls /sys/kernel/tracing/events/irq_vectors/`; use the names listed there |
| `perf stat -a`: permission denied | system-wide counting needs root or `perf_event_paranoid ≤ 0` | `sudo` |
| a device row never moves under load | the device uses MSI-X with per-queue rows, or polling (NAPI) | look for `virtio*-req.*` / `*-input.*` rows |
| huge `LOC` numbers | the counters run since boot | always diff two snapshots |

## Extension task

Write a bpftrace script that prints, per handler **name**, a histogram of how long the top half (`action->handler`) runs, using `irq:irq_handler_entry` and `irq:irq_handler_exit`. Run it during the `dd` load. Explain why pairing entry and exit per CPU is safe here (hint: `kernel/irq/handle.c` and interrupt state during the handler).

Solution: [`solution/irq-latency.bt`](solution/irq-latency.bt).
