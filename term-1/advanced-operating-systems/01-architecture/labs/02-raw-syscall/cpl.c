// cpl.c: read the current privilege level from CS, then try two ring-0-only instructions.
// Each attempt runs in a child process so the expected SIGSEGV does not kill the demo.
//
// Build: gcc -Wall -Wextra -O2 -o cpl cpl.c
// Run:   ./cpl
//
// ARCH-SPECIFIC (x86-64).
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static void try_cli(void) { __asm__ volatile("cli"); }

static void try_read_cr3(void) {
    uint64_t cr3;
    __asm__ volatile("mov %%cr3, %0" : "=r"(cr3));
    printf("cr3 = %#lx (should never print)\n", (unsigned long)cr3);
}

static void attempt(const char *what, void (*fn)(void)) {
    fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
        fn();
        _exit(0);
    }
    int status = 0;
    waitpid(pid, &status, 0);
    if (WIFSIGNALED(status))
        printf("%-14s -> killed by signal %d (%s)\n", what, WTERMSIG(status),
               strsignal(WTERMSIG(status)));
    else
        printf("%-14s -> exited %d\n", what, WEXITSTATUS(status));
}

int main(void) {
    uint16_t cs = 0, ss = 0;
    __asm__ volatile("mov %%cs, %0" : "=r"(cs));
    __asm__ volatile("mov %%ss, %0" : "=r"(ss));
    printf("CS = %#06x  -> index %u, RPL/CPL = %u\n", cs, (unsigned)(cs >> 3), (unsigned)(cs & 3));
    printf("SS = %#06x  -> index %u, RPL     = %u\n", ss, (unsigned)(ss >> 3), (unsigned)(ss & 3));
    attempt("cli", try_cli);
    attempt("mov %cr3,reg", try_read_cr3);
    return 0;
}
