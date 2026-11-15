// threads.c: the C counterpart of `gvt sleep N`: N pthreads that just sleep.
// Every pthread is a kernel task (clone with CLONE_THREAD), so /proc/self/task grows by N.
//
// Build: gcc -Wall -Wextra -O2 -pthread -o threads threads.c
// Run:   ./threads 10000
#define _GNU_SOURCE
#include <dirent.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int count_tasks(void) {
    DIR *d = opendir("/proc/self/task");
    int n = 0;
    if (d == NULL) return -1;
    for (struct dirent *e = readdir(d); e != NULL; e = readdir(d)) {
        if (e->d_name[0] != '.') n++;
    }
    closedir(d);
    return n;
}

static void vmrss(char *out, size_t len) {
    char line[256];
    FILE *f = fopen("/proc/self/status", "r");
    snprintf(out, len, "?");
    if (f == NULL) return;
    while (fgets(line, sizeof line, f) != NULL) {
        if (strncmp(line, "VmRSS:", 6) == 0) {
            char *p = line + 6;
            while (*p == ' ' || *p == '\t') p++;
            p[strcspn(p, "\n")] = '\0';
            snprintf(out, len, "%.40s", p);
        }
    }
    fclose(f);
}

static void *sleeper(void *arg) {
    (void)arg;
    sleep(3600);
    return NULL;
}

int main(int argc, char **argv) {
    int n = argc > 1 ? atoi(argv[1]) : 1000;
    char rss[64];
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setstacksize(&attr, 64 * 1024);   // small stacks, like a goroutine runtime would want

    vmrss(rss, sizeof rss);
    printf("start:   os_threads=%-6d VmRSS=%s\n", count_tasks(), rss);
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < n; i++) {
        pthread_t t;
        int err = pthread_create(&t, &attr, sleeper, NULL);
        if (err != 0) {
            fprintf(stderr, "pthread_create #%d: %s\n", i, strerror(err));
            break;
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms = (double)(t1.tv_sec - t0.tv_sec) * 1e3 + (double)(t1.tv_nsec - t0.tv_nsec) / 1e6;
    vmrss(rss, sizeof rss);
    printf("created: os_threads=%-6d VmRSS=%s  in %.1f ms (%.1f us/thread)\n",
           count_tasks(), rss, ms, ms * 1000.0 / n);
    return 0;
}
