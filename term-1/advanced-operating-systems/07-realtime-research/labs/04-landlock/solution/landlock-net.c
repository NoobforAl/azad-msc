// landlock-net.c: extension solution. Restrict outgoing TCP connections to one port.
// handled_access_net = CONNECT_TCP  -> every TCP connect() is denied ...
// ... except to the port granted by a LANDLOCK_RULE_NET_PORT rule.
//
// Build: gcc -Wall -Wextra -O2 -o landlock-net landlock-net.c
// Run:   ./landlock-net 443 python3 -c "import socket; socket.create_connection(('127.0.0.1', 22), 1)"
//        -> PermissionError (EACCES from Landlock)
//        ./landlock-net 443 python3 -c "import socket; socket.create_connection(('127.0.0.1', 443), 1)"
//        -> ConnectionRefusedError if nothing listens: Landlock allowed it, TCP refused it.
#define _GNU_SOURCE
#include <errno.h>
#include <linux/landlock.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <allowed-port> cmd [args...]\n", argv[0]);
        return 2;
    }
    int abi = (int)syscall(SYS_landlock_create_ruleset, NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 4) {
        fprintf(stderr, "Landlock ABI %d: no TCP rules (need >= 4)\n", abi);
        return 1;
    }
    struct landlock_ruleset_attr attr = {.handled_access_net = LANDLOCK_ACCESS_NET_CONNECT_TCP};
    int rs = (int)syscall(SYS_landlock_create_ruleset, &attr, sizeof(attr), 0);
    if (rs < 0) {
        perror("landlock_create_ruleset");
        return 1;
    }
    struct landlock_net_port_attr port = {
        .allowed_access = LANDLOCK_ACCESS_NET_CONNECT_TCP,
        .port = strtoull(argv[1], NULL, 10),
    };
    if (syscall(SYS_landlock_add_rule, rs, LANDLOCK_RULE_NET_PORT, &port, 0) != 0) {
        perror("landlock_add_rule(net port)");
        return 1;
    }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 ||
        syscall(SYS_landlock_restrict_self, rs, 0) != 0) {
        perror("restrict");
        return 1;
    }
    close(rs);
    fprintf(stderr, "landlock ABI %d: TCP connect allowed only to port %s\n", abi, argv[1]);
    execvp(argv[2], &argv[2]);
    perror("execvp");
    return 127;
}
