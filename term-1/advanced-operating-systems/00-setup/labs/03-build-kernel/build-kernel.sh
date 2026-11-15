#!/usr/bin/env bash
# build-kernel.sh: build and install Linux v6.18.63 (the course pin) INSIDE THE LAB VM.
# Never run this on the real server.
#
#   bash build-kernel.sh            # "lab" flavor: tracing + BTF + debugfs, normal preemption
#   bash build-kernel.sh --rt       # "rt" flavor for Module 7: PREEMPT_RT
#   bash build-kernel.sh --lockdep  # "lockdep" flavor for Module 3: PROVE_LOCKING (slow kernel)
set -euo pipefail

TAG="v6.18.63"
URL="https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"
SRC="${SRC:-$HOME/src/linux-${TAG#v}}"
FLAVOR="lab"
case "${1:-}" in
  --rt) FLAVOR="rt" ;;
  --lockdep) FLAVOR="lockdep" ;;
  "") ;;
  *) echo "usage: $0 [--rt|--lockdep]" >&2; exit 2 ;;
esac

if [ "$(systemd-detect-virt 2>/dev/null || echo none)" = "none" ]; then
  echo "refusing to run on bare metal: this script installs a kernel. Run it in the lab VM." >&2
  exit 1
fi

# 1. Build dependencies --------------------------------------------------------
sudo apt-get update
sudo apt-get install -y build-essential bc bison flex libelf-dev libssl-dev libncurses-dev \
  dwarves zstd cpio rsync kmod debhelper python3 git \
  libdw-dev libunwind-dev libslang2-dev libperl-dev libzstd-dev libcap-dev libtraceevent-dev \
  libbabeltrace-dev systemtap-sdt-dev libpfm4-dev

# 2. Source: full shallow clone of the pinned tag (the repo's sparse checkout lacks scripts/ and drivers/)
if [ ! -d "$SRC/.git" ]; then
  mkdir -p "$(dirname "$SRC")"
  git clone --depth 1 --branch "$TAG" "$URL" "$SRC"
fi
cd "$SRC"
git describe --tags --exact-match HEAD | grep -qx "$TAG" || { echo "tree is not at $TAG" >&2; exit 1; }

# 3. Config: start from the running Ubuntu kernel, keep only loaded modules -----
cp "/boot/config-$(uname -r)" .config
make olddefconfig
# localmodconfig shrinks a 2-hour build to ~20 min by building only modules loaded now.
# Load what later labs need first, so their modules are kept.
for m in kvm kvm_intel kvm_amd loop overlay veth bridge br_netfilter nf_tables tun dm_mod dm_flakey; do
  sudo modprobe "$m" 2>/dev/null || true
done
yes "" | make localmodconfig >/dev/null

# Ubuntu configs point at Canonical's signing certs, which are not in a vanilla tree.
scripts/config --set-str SYSTEM_TRUSTED_KEYS "" --set-str SYSTEM_REVOCATION_KEYS "" \
               --disable MODULE_SIG_ALL --disable MODULE_SIG_FORCE

# Options every module of the course relies on
scripts/config \
  --enable DEBUG_INFO --enable DEBUG_INFO_DWARF5 --enable DEBUG_INFO_BTF \
  --enable KALLSYMS --enable KALLSYMS_ALL \
  --enable DEBUG_FS --enable FTRACE --enable FUNCTION_TRACER --enable FUNCTION_GRAPH_TRACER \
  --enable DYNAMIC_FTRACE --enable KPROBES --enable UPROBES --enable BPF_SYSCALL --enable BPF_JIT \
  --enable IKCONFIG --enable IKCONFIG_PROC \
  --enable KVM --module KVM_INTEL --module KVM_AMD \
  --module DM_FLAKEY \
  --set-str LOCALVERSION "-aos-${FLAVOR}"

case "$FLAVOR" in
  rt)      scripts/config --enable EXPERT --enable PREEMPT_RT ;;
  lockdep) scripts/config --enable PROVE_LOCKING --enable DEBUG_LOCKDEP --enable LOCK_STAT ;;
esac
make olddefconfig

# Fail early if a required option was silently dropped by a dependency
need=(CONFIG_DEBUG_INFO_BTF CONFIG_FUNCTION_GRAPH_TRACER CONFIG_KALLSYMS_ALL CONFIG_IKCONFIG_PROC)
[ "$FLAVOR" = rt ] && need+=(CONFIG_PREEMPT_RT)
[ "$FLAVOR" = lockdep ] && need+=(CONFIG_PROVE_LOCKING)
for o in "${need[@]}"; do
  grep -q "^$o=y" .config || { echo "config check failed: $o is not =y" >&2; exit 1; }
done

# 4. Build .deb packages (image, headers, libc-dev) ---------------------------
time make -j"$(nproc)" bindeb-pkg

# 5. Install and make it the default boot entry -------------------------------
KVER="$(make -s kernelrelease)"
sudo dpkg -i ../linux-image-"${KVER}"_*.deb ../linux-headers-"${KVER}"_*.deb
sudo update-grub

# 6. perf from the same tree (Ubuntu has no linux-tools package for this kernel)
make -C tools/perf -j"$(nproc)" >/dev/null
sudo install -m 0755 tools/perf/perf "/usr/local/bin/perf"

echo
echo "installed $KVER. Reboot, then check:  uname -r   # expect $KVER"
echo "(if GRUB still boots the Ubuntu kernel: sudo grub-reboot 'Advanced options for Ubuntu>Ubuntu, with Linux $KVER')"
