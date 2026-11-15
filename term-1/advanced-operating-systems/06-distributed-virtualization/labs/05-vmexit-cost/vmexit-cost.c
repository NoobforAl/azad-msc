/* vmexit-cost.c: what a VM exit costs, measured from INSIDE a guest.
 * CPUID always causes a VM exit under VT-x/AMD-V (the hypervisor must emulate it),
 * a system call does not (it stays inside the guest kernel), and a plain ALU
 * instruction never leaves the CPU. ARCH-SPECIFIC (x86-64).
 *
 *   gcc -Wall -Wextra -O2 -o vmexit-cost vmexit-cost.c
 *   ./vmexit-cost [iterations]
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

static inline void do_cpuid(uint32_t leaf)
{
	uint32_t a, b, c, d;
	__asm__ volatile("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(leaf), "c"(0));
}

static inline void do_alu(void)
{
	uint32_t x = 1;
	__asm__ volatile("add $1, %0" : "+r"(x));
}

static inline void do_syscall(void)
{
	(void)syscall(SYS_getppid); /* syscall() avoids any libc caching */
}

static double ns_now(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

#define MEASURE(label, stmt, n)                                              \
	do {                                                                 \
		double t0 = ns_now();                                        \
		for (long i = 0; i < (n); i++) {                             \
			stmt;                                                \
		}                                                            \
		double per = (ns_now() - t0) / (double)(n);                  \
		printf("%-26s %10.1f ns/op   (%ld ops)\n", label, per, (long)(n)); \
	} while (0)

int main(int argc, char **argv)
{
	long n = argc > 1 ? strtol(argv[1], NULL, 10) : 200000;
	uint32_t a, b, c, d;

	__asm__ volatile("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(1), "c"(0));
	printf("CPUID.1:ECX bit 31 (hypervisor present) = %u\n", (c >> 31) & 1);
	__asm__ volatile("cpuid" : "=a"(a), "=b"(b), "=c"(c), "=d"(d) : "a"(0x40000000), "c"(0));
	char sig[13] = { 0 };
	memcpy(&sig[0], &b, 4);
	memcpy(&sig[4], &c, 4);
	memcpy(&sig[8], &d, 4);
	printf("CPUID.0x40000000 hypervisor signature = \"%s\"\n", sig);

	MEASURE("add (stays on the CPU)", do_alu(), n * 100);
	MEASURE("getppid syscall (guest)", do_syscall(), n);
	MEASURE("cpuid leaf 0 (VM exit)", do_cpuid(0), n);
	MEASURE("cpuid leaf 1 (VM exit)", do_cpuid(1), n);
	return 0;
}
