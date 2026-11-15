#!/usr/bin/env bash
# install-tools.sh: install every tool used in the Advanced OS labs (Ubuntu 24.04).
# Run on BOTH the server and the VM:  bash install-tools.sh
set -euo pipefail

KREL="$(uname -r)"

PKGS=(
  # build
  build-essential clang llvm gdb make pkg-config git
  # tracing & profiling
  strace ltrace bpftrace bpfcc-tools trace-cmd linux-tools-common
  # inspection
  lsof sysstat numactl hwloc procps psmisc util-linux iproute2 msr-tools cpuid
  # debugging & memory
  valgrind
  # libraries used by labs
  libbpf-dev liburing-dev libseccomp-dev libnuma-dev libcap-dev
  # benchmarks / load
  fio stress-ng rt-tests
  # code navigation
  universal-ctags cscope
  # languages for M2/M3 labs
  golang-go rustc cargo python3 python3-pip jq
)

sudo apt-get update
sudo apt-get install -y "${PKGS[@]}"

# perf + kernel headers must match the RUNNING kernel. A self-built kernel (lab 03)
# has no Ubuntu linux-tools package, so lab 03 builds perf from the same tree.
if apt-cache show "linux-tools-$KREL" >/dev/null 2>&1; then
  sudo apt-get install -y "linux-tools-$KREL" "linux-headers-$KREL"
else
  echo "note: no Ubuntu perf package for kernel $KREL (self-built kernel?). See lab 03, step 6."
fi

# Allow perf / tracing for your user without sudo (lab machine only, not production)
sudo tee /etc/sysctl.d/90-aos-labs.conf >/dev/null <<'EOF'
kernel.perf_event_paranoid = 1
kernel.kptr_restrict = 0
EOF
sudo sysctl --system >/dev/null

echo "done. now run: bash verify-tools.sh"
