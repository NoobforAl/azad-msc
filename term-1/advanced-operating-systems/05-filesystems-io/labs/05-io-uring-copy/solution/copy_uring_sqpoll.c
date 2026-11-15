// copy_uring_sqpoll.c: extension solution. Same linked READ->WRITE copy as copy_uring.c, plus
//   - IORING_SETUP_SQPOLL: a kernel thread (iou-sqp-<pid>) polls the SQ, so submitting needs
//     no syscall while that thread is awake;
//   - registered buffers: io_uring_register_buffers() pins the pages once,
//     READ_FIXED/WRITE_FIXED skip per-request page pinning.
//   copy_uring_sqpoll SRC DST [block_bytes=131072] [qd=8]
// Build: gcc -Wall -Wextra -O2 -o copy_uring_sqpoll copy_uring_sqpoll.c -luring
#define _GNU_SOURCE
#include <fcntl.h>
#include <liburing.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/uio.h>
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

    struct io_uring_params p;
    memset(&p, 0, sizeof(p));
    p.flags = IORING_SETUP_SQPOLL;
    p.sq_thread_idle = 2000;                       // ms before the poller sleeps
    struct io_uring ring;
    int rc = io_uring_queue_init_params(2 * qd, &ring, &p);
    if (rc < 0) {
        fprintf(stderr, "io_uring_queue_init_params: %s\n", strerror(-rc));
        return 1;
    }
    struct iovec *iov = calloc(qd, sizeof(*iov));
    if (iov == NULL)
        return 1;
    for (unsigned i = 0; i < qd; i++) {
        if (posix_memalign(&iov[i].iov_base, 4096, bs) != 0)
            return 1;
        iov[i].iov_len = bs;
    }
    rc = io_uring_register_buffers(&ring, iov, qd);
    if (rc < 0) {
        fprintf(stderr, "io_uring_register_buffers: %s\n", strerror(-rc));
        return 1;
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t off = 0, waits = 0;
    while (off < size) {
        unsigned k = 0;
        for (; k < qd && off < size; k++) {
            unsigned len = (unsigned)((size - off < bs) ? size - off : bs);
            struct io_uring_sqe *r = io_uring_get_sqe(&ring);
            io_uring_prep_read_fixed(r, in, iov[k].iov_base, len, off, (int)k);
            r->flags |= IOSQE_IO_LINK;
            io_uring_sqe_set_data64(r, ((uint64_t)len << 1) | 0);
            struct io_uring_sqe *w = io_uring_get_sqe(&ring);
            io_uring_prep_write_fixed(w, out, iov[k].iov_base, len, off, (int)k);
            io_uring_sqe_set_data64(w, ((uint64_t)len << 1) | 1);
            off += len;
        }
        // With SQPOLL, io_uring_submit() only enters the kernel if the poller went to sleep.
        rc = io_uring_submit(&ring);
        if (rc < 0) {
            fprintf(stderr, "io_uring_submit: %s\n", strerror(-rc));
            return 1;
        }
        for (unsigned done = 0; done < 2 * k; done++) {
            struct io_uring_cqe *cqe;
            if (io_uring_peek_cqe(&ring, &cqe) != 0) {
                waits++;                                  // must sleep: one enter
                rc = io_uring_wait_cqe(&ring, &cqe);
                if (rc < 0) {
                    fprintf(stderr, "wait_cqe: %s\n", strerror(-rc));
                    return 1;
                }
            }
            uint64_t ud = io_uring_cqe_get_data64(cqe);
            if (cqe->res != (int)(ud >> 1)) {
                fprintf(stderr, "%s failed: res=%d\n", (ud & 1) ? "write" : "read", cqe->res);
                return 1;
            }
            io_uring_cqe_seen(&ring, cqe);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double dt = (double)(t1.tv_sec - t0.tv_sec) + (double)(t1.tv_nsec - t0.tv_nsec) / 1e9;
    printf("copy_uring_sqpoll: %llu MiB, %.3f s, %.0f MiB/s, %llu blocking waits\n",
           (unsigned long long)(size >> 20), dt, (double)size / 1048576.0 / dt,
           (unsigned long long)waits);
    io_uring_queue_exit(&ring);
    for (unsigned i = 0; i < qd; i++)
        free(iov[i].iov_base);
    free(iov);
    close(in);
    close(out);
    return 0;
}
