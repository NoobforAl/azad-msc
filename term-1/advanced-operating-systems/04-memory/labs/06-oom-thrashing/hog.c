// hog.c: allocate and touch memory in steps until a limit (or until killed).
//
// Build: gcc -Wall -Wextra -O2 -o hog hog.c
// Usage: ./hog <max MiB> [step MiB=16]
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    size_t max = argc > 1 ? (size_t)strtoul(argv[1], NULL, 10) : 256;
    size_t step = argc > 2 ? (size_t)strtoul(argv[2], NULL, 10) : 16;
    size_t total = 0;

    while (total + step <= max) {
        char *p = mmap(NULL, step << 20, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (p == MAP_FAILED) {
            perror("mmap");
            return 1;
        }
        memset(p, 0x5A, step << 20);   // touching is what really allocates
        total += step;
        printf("hog pid=%d touched %zu MiB\n", (int)getpid(), total);
        fflush(stdout);
        usleep(50 * 1000);
    }
    printf("hog reached %zu MiB without being killed\n", total);
    return 0;
}
