#!/usr/bin/env bash
# Install Ubuntu's mainline build of the course kernel (v6.18.63) inside the VM.
# The .deb files are copied in by create-vm-virtualbox.ps1 (cached on the host in .cache/downloads).
#   bash install-mainline-kernel.sh [DEB_DIR]      # default: ~/mainline
# Then reboot. Check the result with: uname -rv   ->  6.18.63-061863-generic ... PREEMPT_DYNAMIC
set -euo pipefail
DIR="${1:-$HOME/mainline}"
K=6.18.63-061863-generic
cd "$DIR"
ls ./*.deb >/dev/null

# The mainline linux-image postinst calls run-parts with an empty argument on Ubuntu 24.04
# ("run-parts: missing operand") and fails. Install, then finish its work by hand.
sudo apt-get install -y ./*.deb || true
[ -f "/boot/initrd.img-$K" ] || sudo update-initramfs -c -k "$K"
P="/var/lib/dpkg/info/linux-image-unsigned-$K.postinst"
if [ -f "$P" ] && ! head -2 "$P" | grep -qx 'exit 0'; then
  sudo sed -i '2i exit 0' "$P"
fi
sudo dpkg --configure -a
sudo sed -i "s/^GRUB_DEFAULT=.*/GRUB_DEFAULT=\"Advanced options for Ubuntu>Ubuntu, with Linux $K\"/" /etc/default/grub
sudo update-grub
# Ubuntu's perf wrapper refuses unknown kernels; the 6.8 binary works for software events and tracepoints.
p=$(find /usr/lib -maxdepth 2 -path '/usr/lib/linux-tools-*/perf' | sort -V | tail -1)
[ -n "$p" ] && sudo ln -sf "$p" /usr/local/bin/perf
rm -rf "$DIR"
echo "installed $K; reboot to use it"
