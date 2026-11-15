#!/usr/bin/env bash
# Initialize the Linux and OpenBSD reference submodules: shallow (depth 1) + sparse.
# Fetches exactly the commit pinned in the parent repo, and only the listed directories.
# Run from the repository root: bash _shared/sources/setup-sources.sh
set -euo pipefail

LINUX_DIRS=(
  kernel mm fs ipc init include block io_uring net security virt lib
  arch/x86/entry arch/x86/kernel arch/x86/mm arch/x86/include arch/x86/kvm
  Documentation/process Documentation/scheduler Documentation/locking
  Documentation/RCU Documentation/mm Documentation/filesystems
  Documentation/admin-guide/cgroup-v1 Documentation/dev-tools drivers/net/wireguard
  drivers/block drivers/char   # added by OS modules 05 (block layer, char devices)
)

OPENBSD_DIRS=(
  sys/kern sys/sys sys/uvm sys/net sys/netinet sys/netinet6 sys/crypto
  sys/arch/amd64/amd64 sys/arch/amd64/include
  sbin/pfctl usr.bin/ssh lib/libc/sys lib/libssl lib/libcrypto/evp
  usr.sbin/httpd usr.sbin/relayd regress/sys/kern
  share/man/man2 share/man/man4 share/man/man9
  sys/dev/vmm sys/ufs           # added by OS modules 06 (vmm) and 05 (ufs)
)

init_sparse() {
  local path="$1"; shift
  local url sha
  url="$(git config -f .gitmodules "submodule.${path}.url")"
  sha="$(git ls-tree HEAD "$path" | awk '{print $3}')"
  if [ -e "$path/.git" ]; then
    echo "skip: $path already initialized"; return
  fi
  mkdir -p "$path"
  git -C "$path" init -q
  git -C "$path" remote add origin "$url"
  git -C "$path" sparse-checkout set "$@"
  git -C "$path" fetch --depth 1 --filter=blob:none origin "$sha"
  git -C "$path" checkout -q FETCH_HEAD
  git submodule init "$path"
  git submodule absorbgitdirs "$path"
}

init_sparse _shared/sources/linux   "${LINUX_DIRS[@]}"
init_sparse _shared/sources/openbsd "${OPENBSD_DIRS[@]}"

git submodule status
