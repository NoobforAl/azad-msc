// landlock-sandbox.c: unprivileged filesystem sandbox with Landlock.
// The whole filesystem becomes read+execute only; ONE directory stays writable.
// Rules are inherited across execve(), like seccomp filters.
//
// Build: gcc -Wall -Wextra -O2 -o landlock-sandbox landlock-sandbox.c
// Run:   mkdir -p /tmp/ll-rw
//        ./landlock-sandbox /tmp/ll-rw sh -c 'echo ok > /tmp/ll-rw/a; echo no > /tmp/b'
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/landlock.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

/* glibc 2.39 has no Landlock wrappers. */
static int ll_create_ruleset(const struct landlock_ruleset_attr *a, size_t sz, uint32_t flags) {
    return (int)syscall(SYS_landlock_create_ruleset, a, sz, flags);
}
static int ll_add_rule(int fd, enum landlock_rule_type t, const void *attr, uint32_t flags) {
    return (int)syscall(SYS_landlock_add_rule, fd, t, attr, flags);
}
static int ll_restrict_self(int fd, uint32_t flags) {
    return (int)syscall(SYS_landlock_restrict_self, fd, flags);
}

#define FS_READ (LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE | \
                 LANDLOCK_ACCESS_FS_READ_DIR)
#define FS_WRITE (LANDLOCK_ACCESS_FS_WRITE_FILE | LANDLOCK_ACCESS_FS_REMOVE_DIR | \
                  LANDLOCK_ACCESS_FS_REMOVE_FILE | LANDLOCK_ACCESS_FS_MAKE_DIR | \
                  LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SYM | \
                  LANDLOCK_ACCESS_FS_TRUNCATE)

static void allow(int ruleset, const char *path, uint64_t access) {
    struct landlock_path_beneath_attr pb = {.allowed_access = access};
    pb.parent_fd = open(path, O_PATH | O_CLOEXEC);
    if (pb.parent_fd < 0) {
        fprintf(stderr, "open(%s): %s\n", path, strerror(errno));
        exit(1);
    }
    if (ll_add_rule(ruleset, LANDLOCK_RULE_PATH_BENEATH, &pb, 0) != 0) {
        fprintf(stderr, "landlock_add_rule(%s): %s\n", path, strerror(errno));
        exit(1);
    }
    close(pb.parent_fd);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <writable-dir> cmd [args...]\n", argv[0]);
        return 2;
    }
    int abi = ll_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 0) {
        fprintf(stderr, "Landlock unavailable: %s (is 'landlock' in /sys/kernel/security/lsm?)\n",
                strerror(errno));
        return 1;
    }
    fprintf(stderr, "landlock ABI version: %d\n", abi);

    /* "Handled" rights are denied everywhere unless a rule grants them below. */
    struct landlock_ruleset_attr attr = {.handled_access_fs = FS_READ | FS_WRITE};
    int rs = ll_create_ruleset(&attr, sizeof(attr), 0);
    if (rs < 0) {
        perror("landlock_create_ruleset");
        return 1;
    }
    allow(rs, "/", FS_READ);                 /* read + exec everywhere */
    allow(rs, argv[1], FS_READ | FS_WRITE);  /* write only beneath argv[1] */

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return 1;
    }
    if (ll_restrict_self(rs, 0) != 0) {
        perror("landlock_restrict_self");
        return 1;
    }
    close(rs);
    execvp(argv[2], &argv[2]);
    perror("execvp");
    return 127;
}
