# Create the lab VM on a Windows host with VirtualBox (alternative to create-vm.sh).
# Same recipe as the course's test VM "aos-lab" (2026-11-15). Usually run through: make vm-create
#
#   pwsh -File create-vm-virtualbox.ps1              # defaults below
#   $env:VCPUS=4; $env:RAM_MB=8192; pwsh -File create-vm-virtualbox.ps1
#
# Everything downloaded is cached in <repo>\.cache\downloads and reused on the next run:
#   the Ubuntu cloud image, the cloud-init seed ISO, and the mainline 6.18.63 kernel .debs.
# The VM itself lives in <repo>\.cache\vm\<name> (both folders are git-ignored).
#
# Env: VM=aos-lab VCPUS=8 RAM_MB=12288 DISK_MB=61440 SSH_PORT=2222
#      KERNEL=mainline (install v6.18.63) | stock (keep Ubuntu's 6.8)   CACHE_DIR=<repo>\.cache
# Needs: VirtualBox 7.x, OpenSSH client, and Docker Desktop or WSL (only to build the seed ISO, once).
# Result: headless VM, SSH on 127.0.0.1:2222 (user "fred"), snapshot "fresh".
$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"
$VB     = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$Repo   = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\..")).Path
$Cache  = $env:CACHE_DIR ?? (Join-Path $Repo ".cache")
$DL     = Join-Path $Cache "downloads"
$VMBase = Join-Path $Cache "vm"
$Name   = $env:VM       ?? "aos-lab"
$Cpus   = $env:VCPUS    ?? "8"
$Ram    = $env:RAM_MB   ?? "12288"
$DiskM  = $env:DISK_MB  ?? "61440"
$Port   = $env:SSH_PORT ?? "2222"
$Kernel = $env:KERNEL   ?? "mainline"
$Dir    = Join-Path $VMBase $Name
$KeyPub = @("id_ed25519.pub", "id_rsa.pub") | ForEach-Object { Join-Path "$HOME\.ssh" $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $KeyPub) { throw "no SSH key: run ssh-keygen -t ed25519" }
$Key = (Get-Content $KeyPub -Raw).Trim()
if (& $VB list vms | Select-String "`"$Name`"") { throw "VM '$Name' already exists (make vm-start / vm-restore, or delete it in VirtualBox first)" }
New-Item -ItemType Directory -Force $DL, $Dir | Out-Null

function Get-Cached([string]$Url, [string]$File) {
  $dest = Join-Path $DL $File
  if (Test-Path $dest) { Write-Host "cached: $File" }
  else {
    Write-Host "download: $Url"
    Invoke-WebRequest -UseBasicParsing -OutFile "$dest.part" $Url
    Move-Item -Force "$dest.part" $dest
  }
  return $dest
}

# 1. Ubuntu 24.04 cloud disk (cached VMDK), converted to a resizable VDI for this VM.
$Vmdk = Get-Cached "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.vmdk" "noble-server-cloudimg-amd64.vmdk"
$Vdi  = Join-Path $Dir "$Name.vdi"
& $VB clonemedium disk $Vmdk $Vdi --format VDI
& $VB closemedium disk $Vmdk | Out-Null   # keep the cached image free for the next VM
& $VB modifymedium disk $Vdi --resize $DiskM

# 2. cloud-init NoCloud seed: user, SSH key, sudo, lab tools. Rebuilt only when its content changes.
$UserData = @"
#cloud-config
hostname: $Name
users:
  - name: fred
    groups: [sudo, adm]
    shell: /bin/bash
    sudo: "ALL=(ALL) NOPASSWD:ALL"
    ssh_authorized_keys:
      - $Key
package_update: true
packages: [build-essential, clang, gdb, strace, ltrace, linux-tools-generic, bpftrace, bpfcc-tools, trace-cmd, valgrind, lsof, sysstat, numactl, golang-go, rustc, liburing-dev, fio, stress-ng, rt-tests, libseccomp-dev, libcap-dev, git, hwloc, universal-ctags, cscope]
runcmd:
  - [sh, -c, "printf 'kernel.perf_event_paranoid=1\nkernel.kptr_restrict=0\n' > /etc/sysctl.d/90-aos-labs.conf; sysctl --system"]
"@
$MetaData = "instance-id: $Name-1`nlocal-hostname: $Name`n"
$Hash = [BitConverter]::ToString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($UserData + $MetaData))).Replace("-", "").Substring(0, 12)
$Iso  = Join-Path $DL "seed-$Name-$Hash.iso"
if (Test-Path $Iso) { Write-Host "cached: $(Split-Path $Iso -Leaf)" }
else {
  $Seed = Join-Path $DL "seed-src"; New-Item -ItemType Directory -Force $Seed | Out-Null
  $UserData | Set-Content -NoNewline -Encoding utf8NoBOM (Join-Path $Seed "user-data")
  $MetaData | Set-Content -NoNewline -Encoding utf8NoBOM (Join-Path $Seed "meta-data")
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker run --rm -v "${Seed}:/w" alpine:3.20 sh -c "apk add -q cdrkit && genisoimage -quiet -output /w/seed.iso -volid cidata -joliet -rock /w/user-data /w/meta-data"
  } else {
    $w = wsl wslpath -a ($Seed -replace '\\', '/')
    wsl sh -c "cd '$w' && genisoimage -quiet -output seed.iso -volid cidata -joliet -rock user-data meta-data"
  }
  Move-Item -Force (Join-Path $Seed "seed.iso") $Iso
  Remove-Item -Recurse -Force $Seed
}

# 3. The VM: NAT with SSH port-forward, serial console to a file, KVM paravirt clock.
& $VB createvm --name $Name --ostype Ubuntu_64 --basefolder $VMBase --register
& $VB modifyvm $Name --cpus $Cpus --memory $Ram --nic1 nat --natpf1 "ssh,tcp,127.0.0.1,$Port,,22" `
  --uart1 0x3F8 4 --uartmode1 file (Join-Path $Dir "serial.log") `
  --graphicscontroller vmsvga --ioapic on --paravirtprovider kvm --audio-enabled off
& $VB storagectl $Name --name SATA --add sata --portcount 2
& $VB storageattach $Name --storagectl SATA --port 0 --type hdd --medium $Vdi
& $VB storageattach $Name --storagectl SATA --port 1 --type dvddrive --medium $Iso
& $VB startvm $Name --type headless

$ssh = @("-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-o", "LogLevel=ERROR",
         "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", "-p", $Port, "fred@127.0.0.1")
function Wait-Ssh {
  for ($i = 0; $i -lt 120; $i++) {
    ssh @ssh "cloud-init status --wait >/dev/null 2>&1; true" 2>$null
    if ($LASTEXITCODE -eq 0) { return }
    Start-Sleep 10
  }
  throw "VM did not answer on SSH; see $Dir\serial.log"
}
Write-Host "waiting for first boot + cloud-init (installs the lab tools, ~5-10 min)..."
Wait-Ssh

# 4. Optional: the exact course kernel (Ubuntu mainline build of v6.18.63), .debs cached on the host.
if ($Kernel -eq "mainline") {
  $Base = "https://kernel.ubuntu.com/mainline/v6.18.63/amd64"
  $V = "6.18.63-061863.202611101835"
  $debs = "linux-headers-6.18.63-061863-generic_${V}_amd64.deb", "linux-headers-6.18.63-061863_${V}_all.deb",
          "linux-image-unsigned-6.18.63-061863-generic_${V}_amd64.deb", "linux-modules-6.18.63-061863-generic_${V}_amd64.deb"
  New-Item -ItemType Directory -Force (Join-Path $DL "mainline-6.18.63") | Out-Null
  $files = $debs | ForEach-Object { Get-Cached "$Base/$_" "mainline-6.18.63\$_" }
  ssh @ssh "mkdir -p ~/mainline"
  scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o LogLevel=ERROR -P $Port @files "fred@127.0.0.1:mainline/"
  scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o LogLevel=ERROR -P $Port (Join-Path $PSScriptRoot "install-mainline-kernel.sh") "fred@127.0.0.1:"
  ssh @ssh "bash ~/install-mainline-kernel.sh && rm -f ~/install-mainline-kernel.sh && sudo reboot" 2>$null
  Start-Sleep 20
  Wait-Ssh
  ssh @ssh "uname -rv"
}

# 5. Clean shutdown, detach the seed ISO, snapshot "fresh", start again.
ssh @ssh "mkdir -p ~/work; sudo apt-get clean; sudo poweroff" 2>$null
while ((& $VB showvminfo $Name --machinereadable | Select-String '^VMState=') -notmatch 'poweroff') { Start-Sleep 2 }
& $VB storageattach $Name --storagectl SATA --port 1 --type dvddrive --medium emptydrive
& $VB snapshot $Name take fresh --description "clean install, $(Get-Date -Format yyyy-MM-dd)"
& $VB startvm $Name --type headless
Write-Host "ready: make vm-ssh   (rollback: make vm-stop; make vm-restore SNAP=fresh)"
