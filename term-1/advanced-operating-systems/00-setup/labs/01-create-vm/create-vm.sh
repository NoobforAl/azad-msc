#!/usr/bin/env bash
# create-vm.sh: create the course lab VM ("aos-lab") on the Ubuntu server with libvirt.
# Ubuntu 24.04 cloud image, cloud-init user, nested virtualization, serial console,
# and a clean "fresh" snapshot to roll back to after destructive labs.
#
# Run on the HOST (your Ubuntu server):  bash create-vm.sh
# Override defaults with env vars, e.g.:   VCPUS=8 RAM_MB=16384 bash create-vm.sh
set -euo pipefail

VM="${VM:-aos-lab}"
VCPUS="${VCPUS:-4}"
RAM_MB="${RAM_MB:-8192}"
DISK_GB="${DISK_GB:-60}"          # a v6.18 build tree + debs needs ~25 GB
RELEASE="${RELEASE:-noble}"       # Ubuntu 24.04 LTS
IMG_URL="https://cloud-images.ubuntu.com/${RELEASE}/current/${RELEASE}-server-cloudimg-amd64.img"
POOL="${POOL:-/var/lib/libvirt/images}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519.pub}"
# Downloads are cached in <repo>/.cache/downloads (git-ignored) and reused by later runs.
CACHE_DIR="${CACHE_DIR:-$(cd "$(dirname "$0")/../../../../.." && pwd)/.cache}"

die() { echo "error: $*" >&2; exit 1; }

# 1. Host checks -------------------------------------------------------------
[ "$(uname -m)" = "x86_64" ] || die "course labs assume an x86-64 host"
grep -Eq '(vmx|svm)' /proc/cpuinfo || die "CPU has no VT-x/AMD-V flag: hardware virtualization is off or this is a VPS without nesting"
[ -e /dev/kvm ] || die "/dev/kvm missing: run 'sudo modprobe kvm_intel' (or kvm_amd)"
[ -f "$SSH_KEY" ] || die "no SSH public key at $SSH_KEY (create one with: ssh-keygen -t ed25519)"

nested=""
for p in /sys/module/kvm_intel/parameters/nested /sys/module/kvm_amd/parameters/nested; do
  [ -r "$p" ] && nested="$(cat "$p")"
done
case "$nested" in
  Y|y|1) echo "ok: nested virtualization enabled on host" ;;
  *) echo "warn: nested virtualization is OFF (needed only for Module 6 lab 4)."
     echo "      enable: echo 'options kvm_intel nested=1' | sudo tee /etc/modprobe.d/kvm-nested.conf && reboot" ;;
esac

# 2. Packages ----------------------------------------------------------------
if ! command -v virt-install >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients virtinst cloud-image-utils
fi
sudo systemctl enable --now libvirtd
id -nG | grep -qw libvirt || { sudo usermod -aG libvirt "$USER"; echo "note: added $USER to group libvirt (re-login later)"; }

# 3. Disk from the cloud image ----------------------------------------------
base="$POOL/${RELEASE}-base.img"
disk="$POOL/${VM}.qcow2"
cached="$CACHE_DIR/downloads/${RELEASE}-server-cloudimg-amd64.img"
if [ ! -f "$cached" ]; then
  mkdir -p "$(dirname "$cached")"
  wget -q --show-progress -O "$cached.part" "$IMG_URL" && mv "$cached.part" "$cached"
fi
sudo test -f "$base" || sudo cp "$cached" "$base"
sudo test -f "$disk" && die "$disk already exists (delete the VM first: virsh undefine --remove-all-storage $VM)"
sudo qemu-img create -f qcow2 -F qcow2 -b "$base" "$disk" "${DISK_GB}G"

# 4. cloud-init user-data ------------------------------------------------------
ci="$(mktemp -d)"
trap 'rm -rf "$ci"' EXIT
cat > "$ci/user-data" <<EOF
#cloud-config
hostname: ${VM}
users:
  - name: ${USER}
    groups: [sudo]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - $(cat "$SSH_KEY")
package_update: true
packages: [qemu-guest-agent, build-essential, git]
runcmd:
  - [systemctl, enable, --now, qemu-guest-agent]
  # serial console on ttyS0 so 'virsh console' works and kernel panics are visible
  - [sed, -i, 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200n8"/', /etc/default/grub]
  - [update-grub]
EOF

# 5. Create the VM -------------------------------------------------------------
sudo virt-install \
  --name "$VM" \
  --vcpus "$VCPUS" --memory "$RAM_MB" \
  --cpu host-passthrough \
  --disk "path=$disk,format=qcow2,bus=virtio" \
  --os-variant ubuntu24.04 \
  --network network=default,model=virtio \
  --cloud-init "user-data=$ci/user-data" \
  --graphics none --console pty,target_type=serial \
  --import --noautoconsole

echo "waiting for the VM to get an IP address..."
ip=""
for _ in $(seq 1 60); do
  ip="$(sudo virsh domifaddr "$VM" 2>/dev/null | awk '/ipv4/ {split($4,a,"/"); print a[1]}' | head -1)"
  [ -n "$ip" ] && break
  sleep 5
done
[ -n "$ip" ] || die "no IP after 5 minutes; check 'sudo virsh console $VM'"
echo "VM IP: $ip"

echo "waiting for cloud-init to finish..."
for _ in $(seq 1 60); do
  ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 "$USER@$ip" \
      'cloud-init status --wait >/dev/null 2>&1; cloud-init status' 2>/dev/null | grep -q 'done' && break
  sleep 5
done

# 6. Clean snapshot ----------------------------------------------------------
# Internal qcow2 snapshots need the VM shut off for a consistent state.
sudo virsh shutdown "$VM"
for _ in $(seq 1 30); do sudo virsh domstate "$VM" | grep -q "shut off" && break; sleep 2; done
sudo virsh snapshot-create-as "$VM" fresh "clean Ubuntu + cloud-init, before any lab"
sudo virsh start "$VM"

cat <<EOF

Done.
  ssh $USER@$ip
  sudo virsh console $VM                       # serial console (exit: Ctrl+])
  sudo virsh snapshot-revert $VM fresh         # roll back after a destructive lab
EOF
