/* ctr.c: solution to the Lab 06.3 extension. The same container as minictr.sh,
 * but with clone(2) + pivot_root(2) instead of unshare(1). VM ONLY, run as root.
 *
 *   gcc -Wall -Wextra -O2 -o ctr ctr.c
 *   sudo ./ctr ../rootfs /sys/fs/cgroup/aos-m06-ctr /bin/sh -c 'echo pid=$$; hostname'
 *
 * The cgroup directory must already exist with its limits set (minictr.sh step 1).
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#define STACK_SIZE (1024 * 1024)

struct child_args {
	const char *root;
	char **argv;
	int sync_fd; /* read end: parent writes one byte after the cgroup move */
	int sync_wr; /* write end: the child closes its copy, so a dead parent means EOF */
};

static void die(const char *what)
{
	fprintf(stderr, "ctr: %s: %s\n", what, strerror(errno));
	exit(1);
}

/* glibc has no wrapper for pivot_root(2). */
static int pivot_root(const char *new_root, const char *put_old)
{
	return (int)syscall(SYS_pivot_root, new_root, put_old);
}

static int child_main(void *arg)
{
	struct child_args *a = arg;
	char c;

	close(a->sync_wr);
	if (read(a->sync_fd, &c, 1) != 1) /* wait until we are inside the cgroup */
		die("sync read");
	/* New cgroup namespace only now, so its root is the container's cgroup. */
	if (unshare(CLONE_NEWCGROUP) != 0)
		die("unshare cgroup ns");
	if (sethostname("aos-ctr-c", 9) != 0)
		die("sethostname");
	if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != 0)
		die("make / private");
	if (mount(a->root, a->root, NULL, MS_BIND | MS_REC, NULL) != 0)
		die("bind new root");
	if (chdir(a->root) != 0)
		die("chdir root");
	if (mkdir(".oldroot", 0700) != 0 && errno != EEXIST)
		die("mkdir .oldroot");
	if (pivot_root(".", ".oldroot") != 0)
		die("pivot_root");
	if (chdir("/") != 0)
		die("chdir /");
	if (mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL) != 0)
		die("mount /proc");
	if (umount2("/.oldroot", MNT_DETACH) != 0)
		die("umount old root");
	if (rmdir("/.oldroot") != 0)
		die("rmdir old root");
	execv(a->argv[0], a->argv);
	die("execv");
	return 1;
}

int main(int argc, char **argv)
{
	if (argc < 4) {
		fprintf(stderr, "usage: %s ROOTFS CGROUP_DIR CMD [ARGS...]\n", argv[0]);
		return 2;
	}
	int fds[2];
	if (pipe(fds) != 0)
		die("pipe");
	struct child_args a = { .root = argv[1], .argv = &argv[3], .sync_fd = fds[0], .sync_wr = fds[1] };
	char *stack = malloc(STACK_SIZE);
	if (stack == NULL)
		die("malloc");
	const int flags = CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWNET |
			  CLONE_NEWPID | SIGCHLD;
	pid_t pid = clone(child_main, stack + STACK_SIZE, flags, &a);
	if (pid < 0)
		die("clone");

	/* Move the child into the cgroup before it runs anything. */
	char path[512];
	snprintf(path, sizeof(path), "%s/cgroup.procs", argv[2]);
	FILE *f = fopen(path, "w");
	if (f == NULL || fprintf(f, "%d\n", (int)pid) < 0 || fclose(f) != 0)
		die("write cgroup.procs");
	if (write(fds[1], "x", 1) != 1)
		die("sync write");

	int status = 0;
	if (waitpid(pid, &status, 0) < 0)
		die("waitpid");
	if (WIFSIGNALED(status))
		printf("ctr: child killed by signal %d\n", WTERMSIG(status));
	else
		printf("ctr: child exited with %d\n", WEXITSTATUS(status));
	free(stack);
	return 0;
}
