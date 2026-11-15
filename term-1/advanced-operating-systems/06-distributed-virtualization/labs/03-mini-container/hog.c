/* hog.c: allocate and touch memory 4 MiB at a time until killed.
 * Build (static, so it runs inside the Alpine rootfs):
 *   gcc -Wall -Wextra -O2 -static -o hog hog.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
	const size_t chunk = (size_t)4 << 20;
	long limit_mib = argc > 1 ? strtol(argv[1], NULL, 10) : 1024;
	long total_mib = 0;

	while (total_mib < limit_mib) {
		char *p = malloc(chunk);
		if (p == NULL) {
			printf("malloc failed at %ld MiB\n", total_mib);
			return 1;
		}
		memset(p, 0xA5, chunk); /* touching the pages is what charges the memcg */
		total_mib += (long)(chunk >> 20);
		if (total_mib % 16 == 0) {
			printf("hog: %ld MiB touched\n", total_mib);
			fflush(stdout);
		}
	}
	printf("hog: done, %ld MiB\n", total_mib);
	return 0;
}
