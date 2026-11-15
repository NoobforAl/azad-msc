// copy_uring.c: file copy with io_uring (liburing). Each block is a linked pair
// READ -> WRITE (IOSQE_IO_LINK), QD pairs are submitted with ONE io_uring_enter().
//   copy_uring SRC DST [block_bytes=131072] [qd=8]
// Build: gcc -Wall -Wextra -O2 -o copy_uring copy_uring.c -luring
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <liburing.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s SRC DST [block_bytes] [qd]\n", argv[0]);
        return 2;
    }
    size_t bs = (argc > 3) ? strtoul(argv[3], NULL, 0) : 131072;
    unsigned qd = (argc > 4) ? (unsigned)strtoul(argv[4], NULL, 0) : 8;
    int in = open(argv[1], O_RDONLY);
    int out = open(argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (in < 0 || out < 0) {
        perror("open");
        return 1;
    }
    struct stat st;
    if (fstat(in, &st) != 0) {
        perror("fstat");
        return 1;
    }
    uint64_t size = (uint64_t)st.st_size;

    struct io_uring ring;
    int rc = io_uring_queue_init(2 * qd, &ring, 0);   // SQ holds qd read+write pairs
    if (rc < 0) {
        fprintf(stderr, "io_uring_queue_init: %s\n", strerror(-rc));
        return 1;
    }
    char **bufs = calloc(qd, sizeof(*bufs));
    if (bufs == NULL)
        return 1;
    for (unsigned i = 0; i < qd; i++)
        if ((bufs[i] = malloc(bs)) == NULL)
            return 1;

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t off = 0, enters = 0;
    while (off < size) {
        unsigned k = 0;
        for (; k < qd && off < size; k++) {
            unsigned len = (unsigned)((size - off < bs) ? size - off : bs);
            struct io_uring_sqe *r = io_uring_get_sqe(&ring);
            io_uring_prep_read(r, in, bufs[k], len, off);
            r->flags |= IOSQE_IO_LINK;               // the write starts only after this read
            io_uring_sqe_set_data64(r, ((uint64_t)len << 1) | 0);
            struct io_uring_sqe *w = io_uring_get_sqe(&ring);
            io_uring_prep_write(w, out, bufs[k], len, off);
            io_uring_sqe_set_data64(w, ((uint64_t)len << 1) | 1);
            off += len;
        }
        // One syscall: submit 2k SQEs and wait until all 2k CQEs are posted.
        rc = io_uring_submit_and_wait(&ring, 2 * k);
        enters++;
        if (rc < 0) {
            fprintf(stderr, "io_uring_submit_and_wait: %s\n", strerror(-rc));
            return 1;
        }
        for (unsigned done = 0; done < 2 * k; done++) {
            struct io_uring_cqe *cqe;
            rc = io_uring_peek_cqe(&ring, &cqe);
            if (rc < 0) {                            // not posted yet: wait (extra enter)
                rc = io_uring_wait_cqe(&ring, &cqe);
                enters++;
                if (rc < 0) {
                    fprintf(stderr, "wait_cqe: %s\n", strerror(-rc));
                    return 1;
                }
            }
            uint64_t ud = io_uring_cqe_get_data64(cqe);
            int expect = (int)(ud >> 1);
            if (cqe->res != expect) {                // short read breaks the link: -ECANCELED
                fprintf(stderr, "%s failed: res=%d (%s), expected %d\n",
                        (ud & 1) ? "write" : "read", cqe->res,
                        cqe->res < 0 ? strerror(-cqe->res) : "short", expect);
                return 1;
            }
            io_uring_cqe_seen(&ring, cqe);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double dt = (double)(t1.tv_sec - t0.tv_sec) + (double)(t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("copy_uring: %llu MiB, block %zu KiB, qd %u, %llu io_uring_enter calls, %.3f s, %.0f MiB/s\n",
           (unsigned long long)(size >> 20), bs / 1024, qd, (unsigned long long)enters, dt,
           (double)size / 1048576.0 / dt);
    io_uring_queue_exit(&ring);
    for (unsigned i = 0; i < qd; i++)
        free(bufs[i]);
    free(bufs);
    close(in);
    close(out);
    return 0;
}
