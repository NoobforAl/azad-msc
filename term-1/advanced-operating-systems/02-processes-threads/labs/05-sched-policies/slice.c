// slice.c: ask EEVDF for a custom time slice with sched_setattr().
//
// For a SCHED_OTHER task, sched_attr.sched_runtime is the requested slice r_i.
// The kernel clamps it to [0.1 ms, 100 ms] in __setparam_fair()
// (kernel/sched/fair.c). 0 means "use sysctl_sched_base_slice" again.
// We read the value back two ways: sched_getattr() and /proc/self/sched (se.slice).
//
// glibc in Ubuntu 24.04 has no sched_setattr() wrapper, so we use syscall().
// Build: gcc -Wall -Wextra -O2 -o slice slice.c
// Run:   ./slice 50000 3000000 0          (requested slices in ns)
#define _GNU_SOURCE
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

// struct sched_attr from include/uapi/linux/sched/types.h (SCHED_ATTR_SIZE_VER1 = 56 bytes).
// Declared here because <linux/sched/types.h> clashes with glibc's <sched.h>.
struct sched_attr {
    uint32_t size;
    uint32_t sched_policy;
    uint64_t sched_flags;
    int32_t sched_nice;
    uint32_t sched_priority;
    uint64_t sched_runtime;
    uint64_t sched_deadline;
    uint64_t sched_period;
    uint32_t sched_util_min;
    uint32_t sched_util_max;
};

static long proc_slice(void) {
    char line[256];
    long v = -1;
    FILE *f = fopen("/proc/self/sched", "r");
    if (f == NULL) return -1;
    while (fgets(line, sizeof line, f) != NULL) {
        if (strncmp(line, "se.slice", 8) == 0) {
            char *colon = strchr(line, ':');
            if (colon != NULL) v = strtol(colon + 1, NULL, 10);
        }
    }
    fclose(f);
    return v;
}

static void show(const char *label) {
    struct sched_attr a;
    memset(&a, 0, sizeof a);
    if (syscall(SYS_sched_getattr, 0, &a, sizeof a, 0) != 0) { perror("sched_getattr"); exit(1); }
    printf("%-22s policy=%u nice=%d sched_runtime=%llu ns  /proc se.slice=%ld ns\n",
           label, a.sched_policy, a.sched_nice, (unsigned long long)a.sched_runtime, proc_slice());
}

int main(int argc, char **argv) {
    show("default");
    for (int i = 1; i < argc; i++) {
        struct sched_attr a;
        memset(&a, 0, sizeof a);
        a.size = sizeof a;
        a.sched_policy = SCHED_OTHER;
        a.sched_nice = 0;
        a.sched_runtime = strtoull(argv[i], NULL, 10);
        if (syscall(SYS_sched_setattr, 0, &a, 0) != 0) { perror("sched_setattr"); return 1; }
        char label[64];
        snprintf(label, sizeof label, "request %s ns", argv[i]);
        show(label);
    }
    return 0;
}
