/* kvm-hello.c: a complete VMM in ~100 lines. One VM, one vCPU, 4 KiB of guest
 * RAM, real-mode guest code that computes 2+2 and prints it on I/O port 0x3f8.
 * ARCH-SPECIFIC (x86-64). Needs /dev/kvm (bare metal, or a VM with nested virt).
 *
 *   gcc -Wall -Wextra -O2 -o kvm-hello kvm-hello.c
 *   ./kvm-hello
 */
#include <err.h>
#include <fcntl.h>
#include <linux/kvm.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#define GUEST_ADDR 0x1000

/* 16-bit real-mode guest. Bytes checked with: as --32 guest.S && objdump -d -mi8086 */
static const uint8_t guest_code[] = {
	0xba, 0xf8, 0x03, /* mov  $0x3f8, %dx   serial port            */
	0x00, 0xd8,       /* add  %bl, %al      al = 2 + 2             */
	0x04, '0',        /* add  $'0', %al     to ASCII               */
	0xee,             /* out  %al, (%dx)    -> KVM_EXIT_IO         */
	0xb0, '\n',       /* mov  $'\n', %al                           */
	0xee,             /* out  %al, (%dx)    -> KVM_EXIT_IO         */
	0xf4,             /* hlt                -> KVM_EXIT_HLT        */
};

static double now_us(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (double)ts.tv_sec * 1e6 + (double)ts.tv_nsec / 1e3;
}

int main(void)
{
	int kvm = open("/dev/kvm", O_RDWR | O_CLOEXEC);
	if (kvm < 0)
		err(1, "open /dev/kvm");
	int api = ioctl(kvm, KVM_GET_API_VERSION, 0);
	if (api != KVM_API_VERSION)
		errx(1, "KVM_GET_API_VERSION %d, expected %d", api, KVM_API_VERSION);

	int vmfd = ioctl(kvm, KVM_CREATE_VM, 0UL); /* fd #2: the VM */
	if (vmfd < 0)
		err(1, "KVM_CREATE_VM");

	/* Guest "physical" RAM is ordinary anonymous memory of this process. */
	uint8_t *mem = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
	if (mem == MAP_FAILED)
		err(1, "mmap guest memory");
	memcpy(mem, guest_code, sizeof(guest_code));
	struct kvm_userspace_memory_region region = {
		.slot = 0, .guest_phys_addr = GUEST_ADDR, .memory_size = 0x1000,
		.userspace_addr = (uint64_t)(uintptr_t)mem,
	};
	if (ioctl(vmfd, KVM_SET_USER_MEMORY_REGION, &region) < 0)
		err(1, "KVM_SET_USER_MEMORY_REGION");

	int vcpufd = ioctl(vmfd, KVM_CREATE_VCPU, 0UL); /* fd #3: the vCPU */
	if (vcpufd < 0)
		err(1, "KVM_CREATE_VCPU");
	int run_size = ioctl(kvm, KVM_GET_VCPU_MMAP_SIZE, 0);
	if (run_size < (int)sizeof(struct kvm_run))
		errx(1, "KVM_GET_VCPU_MMAP_SIZE %d", run_size);
	struct kvm_run *run = mmap(NULL, (size_t)run_size, PROT_READ | PROT_WRITE, MAP_SHARED, vcpufd, 0);
	if (run == MAP_FAILED)
		err(1, "mmap kvm_run");

	/* Real mode: CS base 0, so CS:IP = 0:0x1000. */
	struct kvm_sregs sregs;
	if (ioctl(vcpufd, KVM_GET_SREGS, &sregs) < 0)
		err(1, "KVM_GET_SREGS");
	sregs.cs.base = 0;
	sregs.cs.selector = 0;
	if (ioctl(vcpufd, KVM_SET_SREGS, &sregs) < 0)
		err(1, "KVM_SET_SREGS");
	struct kvm_regs regs = { .rip = GUEST_ADDR, .rax = 2, .rbx = 2, .rflags = 0x2 };
	if (ioctl(vcpufd, KVM_SET_REGS, &regs) < 0)
		err(1, "KVM_SET_REGS");

	for (int exits = 1;; exits++) {
		double t0 = now_us();
		if (ioctl(vcpufd, KVM_RUN, 0) < 0) /* enter the guest until the next exit */
			err(1, "KVM_RUN");
		double dt = now_us() - t0;
		switch (run->exit_reason) {
		case KVM_EXIT_IO:
			if (run->io.direction == KVM_EXIT_IO_OUT && run->io.size == 1 &&
			    run->io.port == 0x3f8 && run->io.count == 1) {
				char ch = *((char *)run + run->io.data_offset);
				fprintf(stderr, "exit %d: KVM_EXIT_IO port=0x%x byte=0x%02x (%.1f us)\n",
					exits, run->io.port, (unsigned)(uint8_t)ch, dt);
				putchar(ch);
				fflush(stdout);
			} else {
				errx(1, "unexpected KVM_EXIT_IO");
			}
			break;
		case KVM_EXIT_HLT:
			fprintf(stderr, "exit %d: KVM_EXIT_HLT (%.1f us)\n", exits, dt);
			return 0;
		case KVM_EXIT_FAIL_ENTRY:
			errx(1, "KVM_EXIT_FAIL_ENTRY: hardware_entry_failure_reason = 0x%llx",
			     (unsigned long long)run->fail_entry.hardware_entry_failure_reason);
		case KVM_EXIT_INTERNAL_ERROR:
			errx(1, "KVM_EXIT_INTERNAL_ERROR: suberror = 0x%x", run->internal.suberror);
		default:
			errx(1, "exit_reason = 0x%x", run->exit_reason);
		}
	}
}
