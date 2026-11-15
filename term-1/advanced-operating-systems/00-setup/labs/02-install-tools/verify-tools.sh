#!/usr/bin/env bash
# verify-tools.sh: print one line per tool (OK / MISSING) plus the kernel features the labs need.
# Exit code = number of problems found.
set -uo pipefail

fail=0
ok()   { printf '  \033[32mOK\033[0m      %-14s %s\n' "$1" "$2"; }
bad()  { printf '  \033[31mMISSING\033[0m %-14s %s\n' "$1" "$2"; fail=$((fail + 1)); }
warn() { printf '  \033[33mWARN\033[0m    %-14s %s\n' "$1" "$2"; }

echo "== tools"
for t in gcc clang gdb strace ltrace perf bpftrace trace-cmd valgrind lsof vmstat iostat \
         pidstat numactl lstopo fio stress-ng cyclictest ctags cscope go rustc python3; do
  if p="$(command -v "$t" 2>/dev/null)"; then ok "$t" "$p"; else bad "$t" "not in PATH"; fi
done
# bcc tools are installed with a -bpfcc suffix on Ubuntu
if command -v execsnoop-bpfcc >/dev/null; then ok "bcc" "execsnoop-bpfcc"; else bad "bcc" "bpfcc-tools"; fi

echo "== perf works against the running kernel"
if perf stat -e task-clock true >/dev/null 2>&1; then ok "perf stat" "$(uname -r)"; else bad "perf stat" "version mismatch or perf_event_paranoid"; fi

echo "== kernel features"
cfg="/boot/config-$(uname -r)"
[ -r "$cfg" ] || cfg=/proc/config.gz
check_cfg() {
  local opt="$1" why="$2" line
  if [ "$cfg" = /proc/config.gz ]; then line="$(zcat "$cfg" 2>/dev/null | grep "^$opt=")"; else line="$(grep "^$opt=" "$cfg" 2>/dev/null)"; fi
  if [ -n "$line" ]; then ok "$opt" "$why"; else warn "$opt" "$why (not set)"; fi
}
check_cfg CONFIG_DEBUG_INFO_BTF  "bpftrace struct access (all modules)"
check_cfg CONFIG_FUNCTION_GRAPH_TRACER "ftrace function_graph (M1, M5)"
check_cfg CONFIG_DEBUG_FS        "/sys/kernel/debug/sched (M2); SCHED_DEBUG no longer exists in v6.18"
check_cfg CONFIG_KVM             "KVM (M6)"
check_cfg CONFIG_PREEMPT_RT      "real-time kernel (M7, VM only)"
[ -r /sys/kernel/btf/vmlinux ] && ok "BTF" "/sys/kernel/btf/vmlinux" || bad "BTF" "/sys/kernel/btf/vmlinux"
[ -f /sys/fs/cgroup/cgroup.controllers ] \
  && ok "cgroup v2" "$(cat /sys/fs/cgroup/cgroup.controllers)" || bad "cgroup v2" "unified hierarchy not mounted"
[ -e /dev/kvm ] && ok "/dev/kvm" "present" || warn "/dev/kvm" "absent (expected inside the VM without nesting)"

echo "== sysctl"
printf '  %-22s %s\n' perf_event_paranoid "$(cat /proc/sys/kernel/perf_event_paranoid)"
printf '  %-22s %s\n' kptr_restrict "$(cat /proc/sys/kernel/kptr_restrict)"

echo "== host"
printf '  %-22s %s\n' kernel "$(uname -r)"
printf '  %-22s %s\n' cpus "$(nproc)"
printf '  %-22s %s\n' "virt" "$(systemd-detect-virt 2>/dev/null || echo unknown)"

echo
[ "$fail" -eq 0 ] && echo "all required tools present" || echo "$fail problem(s)"
exit "$fail"
