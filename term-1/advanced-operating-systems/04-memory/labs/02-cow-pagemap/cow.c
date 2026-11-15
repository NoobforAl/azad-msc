// cow.c: watch copy-on-write after fork() through /proc/self/pagemap and
// /proc/self/smaps. Run as root to see real PFNs (non-root reads PFN = 0).
//
// Build: gcc -Wall -Wextra -O2 -o cow cow.c
// Run:   sudo ./cow 64        # 64 MiB region; the child writes the first half
#define _GNU_SOURCE
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>

#define PAGE ((size_t)4096)

// One 64-bit pagemap entry per virtual page (Documentation/admin-guide/mm/pagemap.rst):
// bit 63 present, bit 62 swapped, bit 56 exclusively mapped, bits 0-54 PFN.
static uint64_t pagemap_entry(const void *addr)
{
    uint64_t e = 0;
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0)
        return 0;
    off_t off = (off_t)((uintptr_t)addr / PAGE * sizeof(uint64_t));
    if (pread(fd, &e, sizeof(e), off) != (ssize_t)sizeof(e))
        e = 0;
    close(fd);
    return e;
}

static void show_page(const char *who, const char *tag, const void *addr)
{
    uint64_t e = pagemap_entry(addr);
    printf("%-6s %-12s va=%p present=%d excl=%d pfn=0x%" PRIx64 "\n", who, tag, addr,
           (int)((e >> 63) & 1), (int)((e >> 56) & 1), e & ((UINT64_C(1) << 55) - 1));
}

// Print Rss / Shared_Dirty / Private_Dirty of the VMA that contains addr.
static void show_smaps(const char *who, const char *tag, const void *addr)
{
    FILE *f = fopen("/proc/self/smaps", "r");
    char line[512];
    int in = 0;
    long rss = -1, shd = -1, pvd = -1;
    if (f == NULL)
        return;
    while (fgets(line, sizeof(line), f) != NULL) {
        unsigned long lo, hi;
        if (sscanf(line, "%lx-%lx ", &lo, &hi) == 2 && strchr(line, '-') < strchr(line, ' ')) {
            if (in)
                break;
            in = (uintptr_t)addr >= lo && (uintptr_t)addr < hi;
            continue;
        }
        if (!in)
            continue;
        sscanf(line, "Rss: %ld", &rss);
        sscanf(line, "Shared_Dirty: %ld", &shd);
        sscanf(line, "Private_Dirty: %ld", &pvd);
    }
    fclose(f);
    printf("%-6s %-12s Rss=%ld kB  Shared_Dirty=%ld kB  Private_Dirty=%ld kB\n",
           who, tag, rss, shd, pvd);
}

static long minflt(void)
{
    struct rusage r;
    getrusage(RUSAGE_SELF, &r);
    return r.ru_minflt;
}

int main(int argc, char **argv)
{
    size_t mib = argc > 1 ? (size_t)strtoul(argv[1], NULL, 10) : 64;
    size_t len = mib << 20;
    uint8_t *p = mmap(NULL, len, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    madvise(p, len, MADV_NOHUGEPAGE);   // keep 4 KiB pages: one COW per page
    memset(p, 0xAA, len);               // populate every page in the parent

    show_page("parent", "before fork", p);
    show_smaps("parent", "before fork", p);

    int go[2];
    if (pipe(go) != 0) { perror("pipe"); return 1; }
    fflush(stdout);

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }
    if (pid == 0) {
        show_page("child", "after fork", p);
        show_smaps("child", "after fork", p);
        long f0 = minflt();
        for (size_t off = 0; off < len / 2; off += PAGE)
            p[off] = 0x55;              // each first write = one COW fault
        long f1 = minflt();
        show_page("child", "after write", p);
        show_smaps("child", "after write", p);
        printf("child  wrote %zu pages -> %ld minor faults (COW)\n", len / 2 / PAGE, f1 - f0);
        fflush(stdout);
        if (write(go[1], "x", 1) != 1)
            return 1;
        _exit(0);
    }

    char c;
    if (read(go[0], &c, 1) != 1)
        return 1;
    show_page("parent", "child wrote", p);
    printf("parent byte[0]=0x%02x (child wrote 0x55 into its own copy)\n", p[0]);
    waitpid(pid, NULL, 0);
    show_page("parent", "child exited", p);
    return 0;
}
