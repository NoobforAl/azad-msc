// raw_mmap.c: mmap(2) with inline asm. Six arguments: the 4th must go in r10, not rcx.
// Shows the wrong version (flags in rcx) next to the right one.
//
// Build: gcc -Wall -Wextra -O2 -o raw_mmap raw_mmap.c
// Run:   ./raw_mmap
//
// ARCH-SPECIFIC (x86-64). Kernel side: SC_X86_64_REGS_TO_ARGS in
// arch/x86/include/asm/syscall_wrapper.h (regs->di, si, dx, r10, r8, r9).
//
// Real run on aos-lab (Linux 6.18.63), 2026-11-15:
//   flags in rcx: ret=-9 (Bad file descriptor)
//   flags in r10: ret=0x7a4dbe632000 -> "written through a raw mmap"
//   munmap: 0
// With flags in rcx the kernel read flags = r10 = 0: no MAP_ANONYMOUS, so fd -1 is used as a
// real file descriptor and do_mmap() fails with -EBADF (other garbage values give -EINVAL).
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>

static inline long raw_syscall6(long nr, long a0, long a1, long a2, long a3, long a4, long a5) {
    long ret;
    register long r10 __asm__("r10") = a3;
    register long r8 __asm__("r8") = a4;
    register long r9 __asm__("r9") = a5;
    __asm__ volatile("syscall"
                     : "=a"(ret)
                     : "a"(nr), "D"(a0), "S"(a1), "d"(a2), "r"(r10), "r"(r8), "r"(r9)
                     : "rcx", "r11", "memory");
    return ret;
}

// WRONG on purpose: passes arg3 in rcx like a normal C call. syscall overwrites rcx
// with the return address, and the kernel reads r10, which holds whatever was left there.
static inline long wrong_syscall6(long nr, long a0, long a1, long a2, long a3, long a4, long a5) {
    long ret;
    register long r8 __asm__("r8") = a4;
    register long r9 __asm__("r9") = a5;
    register long r10 __asm__("r10") = 0;  // make the garbage deterministic: flags = 0
    __asm__ volatile("syscall"
                     : "=a"(ret), "+c"(a3), "+r"(r10)
                     : "a"(nr), "D"(a0), "S"(a1), "d"(a2), "r"(r8), "r"(r9)
                     : "r11", "memory");
    return ret;
}

int main(void) {
    const long len = 4096;
    const long prot = PROT_READ | PROT_WRITE;
    const long flags = MAP_PRIVATE | MAP_ANONYMOUS;

    long bad = wrong_syscall6(SYS_mmap, 0, len, prot, flags, -1, 0);
    printf("flags in rcx: ret=%ld (%s)\n", bad,
           (bad < 0 && bad > -4096) ? strerror((int)-bad) : "mapped?!");

    long good = raw_syscall6(SYS_mmap, 0, len, prot, flags, -1, 0);
    if (good < 0 && good > -4096) {
        printf("flags in r10: error %s\n", strerror((int)-good));
        return 1;
    }
    char *p = (char *)good;
    strcpy(p, "written through a raw mmap");
    printf("flags in r10: ret=%#lx -> \"%s\"\n", (unsigned long)good, p);
    long rc = raw_syscall6(SYS_munmap, good, len, 0, 0, 0, 0);
    printf("munmap: %ld\n", rc);
    return 0;
}
