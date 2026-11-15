// SPDX-License-Identifier: GPL-2.0
// lockdep_abba.c: take two kernel mutexes in A->B order, then in B->A order,
// one after the other in the same thread. It never actually deadlocks, but on
// a kernel with CONFIG_PROVE_LOCKING=y lockdep reports the inverted order:
// "WARNING: possible circular locking dependency detected".
// VM ONLY. Build: make   Load: sudo insmod lockdep_abba.ko   Check: sudo dmesg | tail -40
#include <linux/module.h>
#include <linux/mutex.h>

static DEFINE_MUTEX(lock_a);
static DEFINE_MUTEX(lock_b);

static int __init abba_init(void)
{
	mutex_lock(&lock_a);          /* records dependency A -> B */
	mutex_lock(&lock_b);
	mutex_unlock(&lock_b);
	mutex_unlock(&lock_a);

	mutex_lock(&lock_b);          /* B -> A closes the cycle: lockdep fires here */
	mutex_lock(&lock_a);
	mutex_unlock(&lock_a);
	mutex_unlock(&lock_b);

	pr_info("lockdep_abba: done (A->B then B->A)\n");
	return 0;
}

static void __exit abba_exit(void)
{
	pr_info("lockdep_abba: unloaded\n");
}

module_init(abba_init);
module_exit(abba_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("AB-BA lock order inversion for lockdep (Module 03, lab 6)");
