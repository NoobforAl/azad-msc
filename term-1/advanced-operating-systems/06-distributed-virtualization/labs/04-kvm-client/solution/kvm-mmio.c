/* kvm-mmio.c: solution to the Lab 06.4 extension.
 * Guest prints "Hello\n" with a lodsb/out loop (one KVM_EXIT_IO per byte), then
 * writes 0x42 to guest-physical 0x8000, where no memory slot exists:
 * KVM cannot handle it, so it returns KVM_EXIT_MMIO with the address and data.
 * The VMM prints an exit histogram at the end. ARCH-SPECIFIC (x86-64).
 *
 *   gcc -Wall -Wextra -O2 -o kvm-mmio kvm-mmio.c && ./kvm-mmio
 */
#include <err.h>
#include <fcntl.h>
#include <linux/kvm.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

#define GUEST_ADDR 0x1000

/* Flat binary of guest-mmio.S linked at 0x1000 (as --32; ld -Ttext=0x1000 --oformat binary). */
static const uint8_t guest_code[] = {
	0xba, 0xf8, 0x03, 0xbe, 0x14, 0x10, 0xac, 0x84, 0xc0, 0x74, 0x03, 0xee,
	0xeb, 0xf8, 0xc6, 0x06, 0x00, 0x80, 0x42, 0xf4, 0x48, 0x65, 0x6c, 0x6c,
	0x6f, 0x0a, 0x00,
};

int main(void)
{
	int kvm = open("/dev/kvm", O_RDWR | O_CLOEXEC);
	if (kvm < 0)
		err(1, "open /dev/kvm");
	int vmfd = ioctl(kvm, KVM_CREATE_VM, 0UL);
	if (vmfd < 0)
		err(1, "KVM_CREATE_VM");
	uint8_t *mem = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
	if (mem == MAP_FAILED)
		err(1, "mmap");
	memcpy(mem, guest_code, sizeof(guest_code));
	struct kvm_userspace_memory_region region = {
		.slot = 0, .guest_phys_addr = GUEST_ADDR, .memory_size = 0x1000,
		.userspace_addr = (uint64_t)(uintptr_t)mem,
	};
	if (ioctl(vmfd, KVM_SET_USER_MEMORY_REGION, &region) < 0)
		err(1, "KVM_SET_USER_MEMORY_REGION");
	int vcpufd = ioctl(vmfd, KVM_CREATE_VCPU, 0UL);
	if (vcpufd < 0)
		err(1, "KVM_CREATE_VCPU");
	int run_size = ioctl(kvm, KVM_GET_VCPU_MMAP_SIZE, 0);
	struct kvm_run *run = mmap(NULL, (size_t)run_size, PROT_READ | PROT_WRITE, MAP_SHARED, vcpufd, 0);
	if (run == MAP_FAILED)
		err(1, "mmap kvm_run");

	struct kvm_sregs sregs;
	if (ioctl(vcpufd, KVM_GET_SREGS, &sregs) < 0)
		err(1, "KVM_GET_SREGS");
	sregs.cs.base = 0;
	sregs.cs.selector = 0;
	sregs.ds.base = 0; /* lodsb reads ds:si */
	sregs.ds.selector = 0;
	if (ioctl(vcpufd, KVM_SET_SREGS, &sregs) < 0)
		err(1, "KVM_SET_SREGS");
	struct kvm_regs regs = { .rip = GUEST_ADDR, .rflags = 0x2 };
	if (ioctl(vcpufd, KVM_SET_REGS, &regs) < 0)
		err(1, "KVM_SET_REGS");

	unsigned long n_io = 0, n_mmio = 0;
	for (;;) {
		if (ioctl(vcpufd, KVM_RUN, 0) < 0)
			err(1, "KVM_RUN");
		switch (run->exit_reason) {
		case KVM_EXIT_IO:
			n_io++;
			putchar(*((char *)run + run->io.data_offset));
			break;
		case KVM_EXIT_MMIO:
			n_mmio++;
			printf("KVM_EXIT_MMIO: %s gpa=0x%llx len=%u data=0x%02x\n",
			       run->mmio.is_write ? "write" : "read",
			       (unsigned long long)run->mmio.phys_addr, run->mmio.len,
			       (unsigned)run->mmio.data[0]);
			break; /* KVM completes the write on the next KVM_RUN */
		case KVM_EXIT_HLT:
			printf("KVM_EXIT_HLT. exits to user space: io=%lu mmio=%lu hlt=1\n", n_io, n_mmio);
			return 0;
		default:
			errx(1, "exit_reason = 0x%x", run->exit_reason);
		}
	}
}
