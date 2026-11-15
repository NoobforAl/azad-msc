# Solution — clone the lab VM

```bash
sudo virsh shutdown aos-lab
# virt-clone copies the disk and gives the clone a new MAC address and UUID
sudo virt-clone --original aos-lab --name aos-scratch --auto-clone
sudo virsh start aos-lab
sudo virsh start aos-scratch

# the clone keeps the same hostname and machine-id: reset them
ip=$(sudo virsh domifaddr aos-scratch | awk '/ipv4/ {split($4,a,"/"); print a[1]}')
ssh "$USER@$ip" 'sudo hostnamectl set-hostname aos-scratch && sudo rm /etc/machine-id && sudo systemd-machine-id-setup'

# independence test
ssh "$USER@$ip" 'sudo rm /etc/hostname'
ssh "$USER@<aos-lab-ip>" 'cat /etc/hostname'     # still prints: aos-lab

# clean up
sudo virsh destroy aos-scratch && sudo virsh undefine aos-scratch --remove-all-storage
```

Why it's fast: `--auto-clone` copies the qcow2 *overlay* (a few GB) rather than the full 60 GB. A faster alternative is a new overlay on the same base: `qemu-img create -f qcow2 -F qcow2 -b <base> new.qcow2`, then `virt-install --import`.
