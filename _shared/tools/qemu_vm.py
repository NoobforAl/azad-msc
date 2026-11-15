"""Create and run the course lab VM ("aos-lab") with plain QEMU. No VirtualBox, no Docker, no WSL needed.

Works on Windows, macOS and Linux with only Python 3 and QEMU (+ the OpenSSH client). It builds the same machine as
create-vm.sh / create-vm-virtualbox.ps1: Ubuntu 24.04, user "fred", the lab tools, optionally the exact course kernel
(Linux v6.18.63), and a clean "fresh" snapshot. The cloud-init data is served over local HTTP, so no seed ISO is built.

  python _shared/tools/qemu_vm.py create        # once: downloads ~0.6 GB, installs tools (~10-40 min)
  python _shared/tools/qemu_vm.py start | stop | status | ssh
  python _shared/tools/qemu_vm.py snapshot [NAME] | restore [NAME]     (VM must be stopped; default NAME: fresh)

Options: --name aos-lab --cpus 4 --ram 8192 --disk 60 --port 2222 --accel auto|kvm|hvf|whpx|tcg --no-kernel --dry-run
--dry-run prints what would run and changes nothing.

Speed: with hardware acceleration (KVM on Linux, HVF on Intel Macs, WHPX on Windows) it is close to native. Without it
QEMU falls back to software emulation ("tcg"), which works but is 10-50x slower; the script warns you when that happens.
"""

import argparse
import hashlib
import http.server
import os
import platform
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE = os.environ.get("CACHE_DIR", os.path.join(ROOT, ".cache"))
DL = os.path.join(CACHE, "downloads")
IS_WIN = os.name == "nt"
IMG = "noble-server-cloudimg-amd64.img"
IMG_BASE = "https://cloud-images.ubuntu.com/noble/current/"
# The same lab tools as create-vm-virtualbox.ps1 (keep the two lists in sync).
PACKAGES = (
    "build-essential, clang, gdb, strace, ltrace, linux-tools-generic, bpftrace, bpfcc-tools, trace-cmd, valgrind, lsof, "
    "sysstat, numactl, golang-go, rustc, liburing-dev, fio, stress-ng, rt-tests, libseccomp-dev, libcap-dev, git, hwloc, "
    "universal-ctags, cscope"
)
KERNEL_BASE = "https://kernel.ubuntu.com/mainline/v6.18.63/amd64"
KERNEL_V = "6.18.63-061863.202611101835"
KERNEL_DEBS = [
    f"linux-headers-6.18.63-061863-generic_{KERNEL_V}_amd64.deb",
    f"linux-headers-6.18.63-061863_{KERNEL_V}_all.deb",
    f"linux-image-unsigned-6.18.63-061863-generic_{KERNEL_V}_amd64.deb",
    f"linux-modules-6.18.63-061863-generic_{KERNEL_V}_amd64.deb",
]
NULL = "NUL" if IS_WIN else "/dev/null"


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, dry, **kw):
    print("  $ " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    return 0 if dry else subprocess.call(cmd, **kw)


# ------------------------------------------------------------------ tools and settings
def find_tool(name):
    p = shutil.which(name)
    if p:
        return p
    if IS_WIN:
        for base in (
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
        ):
            c = os.path.join(base, "qemu", name + ".exe")
            if os.path.exists(c):
                return c
    return None


def need_qemu(dry):
    q, qi = find_tool("qemu-system-x86_64"), find_tool("qemu-img")
    if (q and qi) or dry:
        return q or "qemu-system-x86_64", qi or "qemu-img"
    hint = {
        "nt": "winget install SoftwareFreedomConservancy.QEMU   (or: scoop install qemu)",
        "posix": "Linux: sudo apt install qemu-system-x86 qemu-utils   |   macOS: brew install qemu",
    }["nt" if IS_WIN else "posix"]
    die("QEMU was not found. Install it, open a new terminal, and run this again.\n  " + hint)


def ssh_key():
    for n in ("id_ed25519.pub", "id_rsa.pub", "id_ecdsa.pub"):
        p = os.path.join(os.path.expanduser("~"), ".ssh", n)
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    die("no SSH public key. Create one with: ssh-keygen -t ed25519")


def pick_accel(qemu, want):
    if want != "auto":
        return want
    if sys.platform.startswith("linux"):
        return "kvm" if os.access("/dev/kvm", os.R_OK | os.W_OK) else "tcg"
    if sys.platform == "darwin":
        return "hvf" if platform.machine() in ("x86_64", "AMD64") else "tcg"
    if IS_WIN:
        try:
            out = subprocess.run([qemu, "-accel", "help"], capture_output=True, text=True, timeout=20).stdout
            return "whpx" if "whpx" in out else "tcg"
        except (OSError, subprocess.SubprocessError):
            return "tcg"
    return "tcg"


class Vm:
    def __init__(self, a):
        self.a = a
        self.dir = os.path.join(CACHE, "vm", a.name)
        self.disk = os.path.join(self.dir, "disk.qcow2")
        self.pidf = os.path.join(self.dir, "qemu.pid")
        self.serial = os.path.join(self.dir, "serial.log")
        self.log = os.path.join(self.dir, "qemu.log")

    # --- process helpers
    def pid(self):
        try:
            return int(open(self.pidf).read().strip())
        except (OSError, ValueError):
            return None

    def alive(self):
        pid = self.pid()
        if not pid:
            return False
        if IS_WIN:
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
            return str(pid) in out
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def ssh_args(self, extra=()):
        return [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={NULL}",
            "-o",
            "LogLevel=ERROR",
            "-o",
            "ConnectTimeout=5",
            "-o",
            "BatchMode=yes",
            "-p",
            str(self.a.port),
            *extra,
            "fred@127.0.0.1",
        ]

    def wait_ssh(self, minutes, what):
        end = time.time() + minutes * 60
        while time.time() < end:
            r = subprocess.run(
                self.ssh_args() + ["cloud-init status --wait >/dev/null 2>&1; true"], capture_output=True
            )
            if r.returncode == 0:
                return
            if not self.alive():
                die(f"QEMU stopped while waiting for {what}. See {self.log} and {self.serial}")
            time.sleep(10)
        die(f"the VM did not answer on SSH within {minutes} minutes ({what}). See {self.serial}")

    # --- starting and stopping
    def qemu_cmd(self, accel, seed_port=None):
        a = self.a
        cpu = "host" if accel in ("kvm", "hvf") else "max"
        cmd = [
            self.qemu,
            "-name",
            a.name,
            "-machine",
            f"q35,accel={accel}",
            "-cpu",
            cpu,
            "-smp",
            str(a.cpus),
            "-m",
            str(a.ram),
            "-drive",
            f"file={self.disk},if=virtio,format=qcow2",
            "-netdev",
            f"user,id=n0,hostfwd=tcp:127.0.0.1:{a.port}-:22",
            "-device",
            "virtio-net-pci,netdev=n0",
            "-display",
            "none",
            "-serial",
            f"file:{self.serial}",
        ]  # no QMP/monitor port on purpose: an unauthenticated local control socket would let any local program drive the VM
        if seed_port:  # cloud-init NoCloud over HTTP: the guest reaches the host's loopback as 10.0.2.2
            cmd += ["-smbios", f"type=1,serial=ds=nocloud;s=http://10.0.2.2:{seed_port}/"]
        return cmd

    def launch(self, seed_port=None):
        accel = self.accel
        if accel == "tcg":
            print("warning: no hardware acceleration available. The VM will run, but 10-50x slower than normal.")
        for attempt in (accel, "tcg"):
            if self.a.dry_run:
                print("  $ " + " ".join(f'"{c}"' if " " in c else c for c in self.qemu_cmd(attempt, seed_port)))
                return
            os.makedirs(self.dir, exist_ok=True)
            kw = {"stdin": subprocess.DEVNULL, "stdout": open(self.log, "ab"), "stderr": subprocess.STDOUT}
            if IS_WIN:
                kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_PROCESS_GROUP | NO_WINDOW
            else:
                kw["start_new_session"] = True
            p = subprocess.Popen(self.qemu_cmd(attempt, seed_port), **kw)
            time.sleep(6)
            if p.poll() is None:
                open(self.pidf, "w").write(str(p.pid))
                self.accel = attempt
                return
            if attempt == "tcg":
                die(f"QEMU exited immediately. See {self.log}")
            print(
                f"note: acceleration '{attempt}' is not usable here (see {self.log}); trying software emulation instead."
            )
        die("could not start QEMU")

    def powerdown(self, wait=120):
        # Ask the guest to shut down over SSH (key-only, bound to 127.0.0.1), so QEMU needs no control port at all.
        try:
            subprocess.call(
                self.ssh_args() + ["sudo poweroff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            pass
        end = time.time() + wait
        while time.time() < end and self.alive():
            time.sleep(2)
        if self.alive():
            print("The VM did not shut down in time; forcing power-off.")
            subprocess.call(["taskkill", "/F", "/PID", str(self.pid())] if IS_WIN else ["kill", "-9", str(self.pid())])
            time.sleep(2)


# ------------------------------------------------------------------ commands
def download(url, dest, dry, expected_sha=None):
    if os.path.exists(dest) and not dry:
        return
    print(f"  download {url}")
    if dry:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    h = hashlib.sha256()
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "azad-course-workspace"}), timeout=60
    ) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            h.update(chunk)
            got += len(chunk)
            print(f"\r    {got / 1e6:7.0f} / {total / 1e6:.0f} MB", end="", flush=True)
    print()
    if expected_sha and h.hexdigest() != expected_sha:
        os.remove(tmp)
        die(f"checksum mismatch for {os.path.basename(dest)}: the download is corrupt, run again")
    os.replace(tmp, dest)


def image_sha():
    try:
        with urllib.request.urlopen(IMG_BASE + "SHA256SUMS", timeout=30) as r:
            for line in r.read().decode().splitlines():
                digest, _, name = line.partition(" ")
                if name.strip().lstrip("*") == IMG:
                    return digest
    except OSError:
        pass
    return None


def user_data(name, key):
    return (
        f"#cloud-config\nhostname: {name}\nusers:\n  - name: fred\n    groups: [sudo, adm]\n    shell: /bin/bash\n"
        f'    sudo: "ALL=(ALL) NOPASSWD:ALL"\n    ssh_authorized_keys:\n      - {key}\npackage_update: true\npackages: [{PACKAGES}]\n'
        "runcmd:\n  - [sh, -c, \"printf 'kernel.perf_event_paranoid=1\\nkernel.kptr_restrict=0\\n' > /etc/sysctl.d/90-aos-labs.conf; sysctl --system\"]\n"
    )


def cmd_create(vm):
    a = vm.a
    if os.path.exists(vm.disk):
        die(f"{vm.disk} already exists. Use 'start', or delete the folder {vm.dir} to build again.")
    vm.qemu, vm.qemu_img = need_qemu(a.dry_run)
    key = (
        "ssh-ed25519 AAAA...(your key)"
        if a.dry_run
        and not any(
            os.path.exists(os.path.join(os.path.expanduser("~"), ".ssh", n))
            for n in ("id_ed25519.pub", "id_rsa.pub", "id_ecdsa.pub")
        )
        else ssh_key()
    )
    vm.accel = pick_accel(vm.qemu, a.accel)
    print(
        f"plan: VM '{a.name}', {a.cpus} CPUs, {a.ram} MB RAM, {a.disk} GB disk, SSH on 127.0.0.1:{a.port}, acceleration: {vm.accel}"
    )
    base = os.path.join(DL, IMG)
    download(IMG_BASE + IMG, base, a.dry_run, image_sha())
    if not a.dry_run:
        os.makedirs(vm.dir, exist_ok=True)
    run([vm.qemu_img, "create", "-f", "qcow2", "-F", "qcow2", "-b", base, vm.disk, f"{a.disk}G"], a.dry_run)

    seed = os.path.join(vm.dir, "seed")
    httpd = None
    seed_port = 8888
    if not a.dry_run:
        os.makedirs(seed, exist_ok=True)
        open(os.path.join(seed, "user-data"), "w", encoding="utf-8", newline="\n").write(user_data(a.name, key))
        open(os.path.join(seed, "meta-data"), "w", encoding="utf-8", newline="\n").write(
            f"instance-id: {a.name}-1\nlocal-hostname: {a.name}\n"
        )

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kw):
                super().__init__(*args, directory=seed, **kw)

            def log_message(self, *args):
                pass

        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Quiet)
        seed_port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"first boot: cloud-init installs the lab tools (seed served on http://127.0.0.1:{seed_port}/)")
    vm.launch(seed_port)
    if a.dry_run:
        print("(dry run: stopping here)")
        return
    wait = 25 if vm.accel != "tcg" else 90
    print(f"waiting for first boot + cloud-init (up to {wait} min; serial log: {vm.serial}) ...")
    vm.wait_ssh(wait, "first boot")
    if httpd:
        httpd.shutdown()

    if not a.no_kernel:
        print("installing the course kernel (Linux v6.18.63, Ubuntu mainline build) ...")
        kd = os.path.join(DL, "mainline-6.18.63")
        for deb in KERNEL_DEBS:
            download(f"{KERNEL_BASE}/{deb}", os.path.join(kd, deb), False)
        scp = [
            "scp",
            "-q",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"UserKnownHostsFile={NULL}",
            "-o",
            "LogLevel=ERROR",
            "-P",
            str(a.port),
        ]
        subprocess.call(vm.ssh_args() + ["mkdir -p ~/mainline"])
        subprocess.call(scp + [os.path.join(kd, d) for d in KERNEL_DEBS] + ["fred@127.0.0.1:mainline/"])
        subprocess.call(
            scp
            + [
                os.path.join(
                    ROOT,
                    "term-1",
                    "advanced-operating-systems",
                    "00-setup",
                    "labs",
                    "01-create-vm",
                    "install-mainline-kernel.sh",
                ),
                "fred@127.0.0.1:",
            ]
        )
        subprocess.call(
            vm.ssh_args() + ["bash ~/install-mainline-kernel.sh && rm -f ~/install-mainline-kernel.sh && sudo reboot"],
            stderr=subprocess.DEVNULL,
        )
        time.sleep(20)
        vm.wait_ssh(wait, "reboot into the new kernel")
        subprocess.call(vm.ssh_args() + ["uname -rv"])

    subprocess.call(vm.ssh_args() + ["mkdir -p ~/work; sudo apt-get clean; sudo poweroff"], stderr=subprocess.DEVNULL)
    end = time.time() + 180
    while vm.alive() and time.time() < end:
        time.sleep(2)
    if vm.alive():
        vm.powerdown(30)
    run([vm.qemu_img, "snapshot", "-c", "fresh", vm.disk], False)
    vm.launch(None)
    print("ready: python _shared/tools/qemu_vm.py ssh      (rollback: stop, then restore)")


def cmd_start(vm):
    if not os.path.exists(vm.disk) and not vm.a.dry_run:
        die("the VM does not exist yet. Run: python _shared/tools/qemu_vm.py create")
    if vm.alive():
        return print("already running")
    vm.qemu, _ = need_qemu(vm.a.dry_run)
    vm.accel = pick_accel(vm.qemu, vm.a.accel)
    vm.launch(None)
    if vm.a.dry_run:
        return print("(dry run: nothing started)")
    print(f"started; connect with: python _shared/tools/qemu_vm.py ssh   (SSH on 127.0.0.1:{vm.a.port})")


def cmd_stop(vm):
    if not vm.alive():
        return print("not running")
    vm.powerdown()
    print("stopped")


def cmd_status(vm):
    if not os.path.exists(vm.disk):
        return print(f"{vm.a.name}: not created (run: python _shared/tools/qemu_vm.py create)")
    if not vm.alive():
        return print(f"{vm.a.name}: stopped")
    r = subprocess.run(vm.ssh_args() + ["uname -rv"], capture_output=True, text=True)
    print(
        f"{vm.a.name}: running (pid {vm.pid()}); "
        + (r.stdout.strip() if r.returncode == 0 else "SSH not answering yet")
    )


def cmd_ssh(vm):
    sys.exit(
        subprocess.call(
            [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                f"UserKnownHostsFile={NULL}",
                "-o",
                "LogLevel=ERROR",
                "-p",
                str(vm.a.port),
                "fred@127.0.0.1",
            ]
        )
    )


def cmd_snap(vm, restore):
    if vm.alive():
        die("stop the VM first: python _shared/tools/qemu_vm.py stop")
    qi = need_qemu(vm.a.dry_run)[1]
    run([qi, "snapshot", "-a" if restore else "-c", vm.a.snap, vm.disk], vm.a.dry_run)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("command", choices=["create", "start", "stop", "status", "ssh", "snapshot", "restore"])
    ap.add_argument("snap", nargs="?", default="fresh", help="snapshot name (snapshot / restore), default: fresh")
    ap.add_argument("--name", default=os.environ.get("VM", "aos-lab"))
    ap.add_argument("--cpus", type=int, default=int(os.environ.get("VCPUS", 4)))
    ap.add_argument("--ram", type=int, default=int(os.environ.get("RAM_MB", 8192)), help="MB")
    ap.add_argument("--disk", type=int, default=int(os.environ.get("DISK_GB", 60)), help="GB")
    ap.add_argument("--port", type=int, default=int(os.environ.get("SSH_PORT", 2222)))
    ap.add_argument("--accel", default="auto", choices=["auto", "kvm", "hvf", "whpx", "tcg"])
    ap.add_argument(
        "--no-kernel", action="store_true", help="skip installing the exact course kernel (keep Ubuntu's own)"
    )
    ap.add_argument("--dry-run", action="store_true", help="print what would run, change nothing")
    a = ap.parse_args()
    vm = Vm(a)
    {
        "create": cmd_create,
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "ssh": cmd_ssh,
        "snapshot": lambda v: cmd_snap(v, False),
        "restore": lambda v: cmd_snap(v, True),
    }[a.command](vm)


if __name__ == "__main__":
    main()
