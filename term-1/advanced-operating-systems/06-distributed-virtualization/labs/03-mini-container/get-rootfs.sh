#!/usr/bin/env bash
# get-rootfs.sh: download and unpack an Alpine minirootfs (~3 MB) into ./rootfs.
set -euo pipefail
cd "$(dirname "$0")"
VER="${ALPINE_VER:-3.20.3}"
ARCH="x86_64"
TAR="alpine-minirootfs-${VER}-${ARCH}.tar.gz"
URL="https://dl-cdn.alpinelinux.org/alpine/v${VER%.*}/releases/${ARCH}/${TAR}"
[ -f "$TAR" ] || curl -fsSLO "$URL"
curl -fsSL "${URL}.sha256" | sha256sum -c -
sudo rm -rf rootfs && mkdir rootfs
sudo tar -xzf "$TAR" -C rootfs
sudo du -sh rootfs
