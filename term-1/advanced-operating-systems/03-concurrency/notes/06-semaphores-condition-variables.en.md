# 06 — Semaphores and condition variables

> Module 03 · Concurrency & Synchronization · Linux v6.18.63 · OpenBSD 8cada8c · Farsi: [06-semaphores-condition-variables.fa.md](06-semaphores-condition-variables.fa.md)

## 1. Summary

- A **semaphore** is a counter plus a wait queue. `P` (down/wait) takes a unit or sleeps, and `V` (up/post) returns one and wakes a sleeper. It counts **resources**.
- A **condition variable** has no memory. It is a wait queue tied to a mutex and a **predicate** that you re-check in a `while` loop after every wake-up.
- In Linux both kinds of sleep follow one rule: put yourself on the queue and set your task state **before** the last check of the condition, so that a wake-up can never fall into the gap.

## 2. Explanation

### 2.1 Dijkstra's semaphore

In 1965 Dijkstra defined two operations on a non-negative integer `S`:

| Op | Name | Effect |
|---|---|---|
| `P(S)` | proberen / down / `sem_wait` | if `S > 0` then `S--`, else sleep until it is |
| `V(S)` | verhogen / up / `sem_post` | `S++`, and wake one sleeper if there is one |

The check and the decrement are **one atomic step**. That is the whole value of the abstraction.

| Kind | Initial value | Meaning | Example |
|---|---|---|---|
| Binary | 1 | mutual exclusion (but no owner!) | old kernel code before `struct mutex` |
| Counting | N | N identical resources | free slots in a bounded buffer |
| Signalling | 0 | "event happened" between two threads | `full` in Producer-Consumer |

A semaphore has **no owner**. Any thread may `V` it. That makes it right for signalling, and wrong as a lock: nobody can tell who holds it, so there is no priority inheritance, no optimistic spin on the owner, and no debugging of the "unlocked by the wrong task" kind. This is why the kernel replaced most binary semaphores with `struct mutex` ([note 05](05-mutex-optimistic-spinning.en.md)).

### 2.2 The kernel's `struct semaphore`

```text
linux/include/linux/semaphore.h · struct semaphore · v6.18.63 · L15-23
   15  struct semaphore {
   16  	raw_spinlock_t		lock;
   17  	unsigned int		count;
   18  	struct list_head	wait_list;
   19
   20  #ifdef CONFIG_DETECT_HUNG_TASK_BLOCKER
   21  	unsigned long		last_holder;
   22  #endif
   23  };
```

The struct is just three fields: a spinlock that protects them, the count, and a FIFO list of sleeping waiters. There is no atomic fast path. Every `down()` takes the spinlock.

```text
linux/kernel/locking/semaphore.c · down() · v6.18.63 · L91-103
   91  void __sched down(struct semaphore *sem)
   92  {
   93  	unsigned long flags;
   94
   95  	might_sleep();
   96  	raw_spin_lock_irqsave(&sem->lock, flags);
   97  	if (likely(sem->count > 0))
   98  		__sem_acquire(sem);
   99  	else
  100  		__down(sem);
  101  	raw_spin_unlock_irqrestore(&sem->lock, flags);
  102  }
  103  EXPORT_SYMBOL(down);
```

<https://elixir.bootlin.com/linux/v6.18.63/source/kernel/locking/semaphore.c#L91>

- **L95** `might_sleep()`: with debugging on, this warns if `down()` is called from atomic context (IRQ, or while holding a spinlock).
- **L96**: the check and decrement happen under `sem->lock`, with interrupts off. `up()` may be called from an interrupt handler, so the lock must be IRQ-safe.
- **L97–98**: the fast case. `__sem_acquire()` decrements the count (and records the holder for hung-task detection).
- **L100** `__down()`: this path ends in `___down_common()` (L252). It appends a waiter to `wait_list`, sets the task state, **drops the spinlock**, calls `schedule_timeout()`, retakes the lock, and checks `waiter.up`. The waker sets `waiter.up` under the same lock. A wake-up therefore cannot be lost between "decide to sleep" and "sleep".

```text
linux/kernel/locking/semaphore.c · up() · v6.18.63 · L220-233
  220  void __sched up(struct semaphore *sem)
  221  {
  222  	unsigned long flags;
  223  	DEFINE_WAKE_Q(wake_q);
  224
  225  	raw_spin_lock_irqsave(&sem->lock, flags);
  226
  227  	hung_task_sem_clear_if_holder(sem);
  228
  229  	if (likely(list_empty(&sem->wait_list)))
  230  		sem->count++;
  231  	else
  232  		__up(sem, &wake_q);
  233  	raw_spin_unlock_irqrestore(&sem->lock, flags);
```

<https://elixir.bootlin.com/linux/v6.18.63/source/kernel/locking/semaphore.c#L220>

- **L223** `DEFINE_WAKE_Q`: wake-ups are collected here and carried out **after** the spinlock is dropped (the lines after L233), so the woken task does not immediately spin on `sem->lock`.
- **L229–230**: if no one is waiting, just increment the count.
- **L232** `__up()`: if someone is waiting, the count is **not** incremented. The unit is handed straight to the first waiter (`waiter->up = true`). That is FIFO handoff: a late arrival cannot steal the unit.

In user space, glibc's `sem_wait`/`sem_post` keep the count in a user-memory word and call `futex()` only to sleep or wake. That is a glibc implementation detail and glibc is not in our checkout (UNVERIFIED here; you can observe it with `strace -f -e futex ./pc_sem` in [lab 03.2](../labs/02-producer-consumer/README.md)). See [note 07](07-futex-user-kernel-split.en.md).

### 2.3 Condition variables

A semaphore counts. A condition variable lets a thread wait for **any predicate over shared state** (`count > 0`, `queue not full`, `no writer active`). It works with three parts:

1. a **mutex** protecting the state,
2. the **predicate**, written as normal code,
3. the condvar, which is just a queue of sleepers.

`pthread_cond_wait(&cv, &m)` atomically **unlocks `m` and sleeps**. When it returns, `m` is held again. Two things follow:

- **Why pass the mutex?** Without the atomic "unlock + sleep", the lost wake-up comes back: you check the predicate (false), the producer changes the state and signals (nobody is on the queue yet), and then you sleep forever.
- **Why `while`, not `if`?** POSIX uses **Mesa semantics**: `signal` only makes a waiter runnable. By the time it reacquires the mutex, another thread may have consumed the item (a *stolen wake-up*, common with more than one consumer). On top of that, POSIX explicitly allows **spurious wake-ups**. The predicate must be re-checked.

| Semantics | After `signal()` | Waiter's check | Used by |
|---|---|---|---|
| Hoare (1974) | signaller hands the monitor directly to the waiter, which runs **now** | `if` is enough | textbooks, some RTOS monitors |
| Mesa (1980) | waiter becomes runnable and **competes** for the mutex later | **`while`** required | POSIX threads, Java, Go `sync.Cond`, Linux `wait_event` |

| Call | Wakes | Use when |
|---|---|---|
| `pthread_cond_signal` | at least one waiter | every waiter waits for the same thing and any one can proceed |
| `pthread_cond_broadcast` | all waiters | waiters wait for different predicates on one condvar, or a state change frees many (shutdown) |

### 2.4 The kernel version: `wait_event()`

The kernel has no "condvar" type. It has wait queues and the `wait_event(wq, condition)` macro, which builds the loop for you:

```text
linux/include/linux/wait.h · wait_event · v6.18.63 · L345-351
  345  #define wait_event(wq_head, condition)						\
  346  do {										\
  347  	might_sleep();								\
  348  	if (condition)								\
  349  		break;								\
  350  	__wait_event(wq_head, condition);					\
  351  } while (0)
```

<https://elixir.bootlin.com/linux/v6.18.63/source/include/linux/wait.h#L345>

- **L348**: fast check. If the condition is already true, don't touch the queue.
- **L350** `__wait_event` expands to `___wait_event()` (L302). Its loop is: `prepare_to_wait_event()` (enqueue and set the task state), then `if (condition) break;`, then `schedule()`, then check again. The enqueue + state change come **before** the check, which is the same ordering rule as `futex_wait_setup()` ([note 07](07-futex-user-kernel-split.en.md)). `wake_up()` sets the task back to RUNNING, so a wake-up that arrives between the check and `schedule()` makes `schedule()` return immediately.
- The `condition` is re-evaluated after every wake-up. That is Mesa semantics, written as a macro.

## 3. Diagram

```mermaid
sequenceDiagram
  participant C as Consumer
  participant M as mutex m
  participant Q as condvar not_empty
  participant P as Producer
  C->>M: lock(m)
  C->>C: while (count == 0)
  C->>Q: cond_wait: enqueue + unlock(m) atomically
  P->>M: lock(m)
  P->>P: buf[head]=v; count++
  P->>Q: cond_signal(not_empty)
  Q-->>C: runnable (not running yet)
  P->>M: unlock(m)
  C->>M: re-lock(m) inside cond_wait
  C->>C: re-check count == 0 ? (Mesa)
  C->>C: take item; count--
  C->>M: unlock(m)
```

## 4. Worked example

The two C versions of the bounded buffer in [lab 03.2](../labs/02-producer-consumer/README.md):

```c
// labs/02-producer-consumer/pc_sem.c · producer() · L22-29
    for (long i = 1; i <= g_items; i++) {
        sem_wait(&g_empty);                 // P(empty): wait for a free slot
        pthread_mutex_lock(&g_lock);
        g_buf[g_head] = i;
        g_head = (g_head + 1) % g_cap;
        pthread_mutex_unlock(&g_lock);
        sem_post(&g_full);                  // V(full): one more item
    }
```

- `g_empty` starts at `cap` and `g_full` starts at 0. Together they enforce `0 ≤ items ≤ cap` with no `if` at all: the counters *are* the predicate.
- The mutex protects only the index update. With one producer and one consumer it could be dropped. With several of each it is needed.
- **Order matters:** `sem_wait(&g_empty)` **before** `mutex_lock`. If you swap them, a producer that holds the mutex sleeps on a full buffer, and the consumer can never take the mutex to free a slot. That is a deadlock ([note 09](09-deadlock-coffman-lockdep.en.md)).

```c
// labs/02-producer-consumer/pc_cond.c · consumer() · L41-50
        pthread_mutex_lock(&g_lock);
        while (g_count == 0) {
            g_waits_empty++;
            pthread_cond_wait(&g_not_empty, &g_lock);
        }
        long v = g_buf[g_tail];
        g_tail = (g_tail + 1) % g_cap;
        g_count--;
        pthread_cond_signal(&g_not_full);
        pthread_mutex_unlock(&g_lock);
```

- The predicate `g_count == 0` is ordinary code, read under the mutex.
- `g_waits_empty` counts how often the consumer actually slept. The lab prints it, and it shows how buffer size changes the number of sleeps.
- `signal(not_full)` is sent while holding the mutex. That is legal and simple. Signalling after unlock saves the woken producer one immediate block on the mutex, but then the predicate must still be updated under the lock.
- The Go version (`pc_chan.go`) is the same buffer, with the runtime doing the counting, locking and parking: `ch <- i` blocks while the buffer is full, and `range ch` blocks while it is empty.

Run them and compare `ns/item` and `waits(...)` for `cap=1` vs `cap=1024`. Captured output is in the lab README.

## 5. Edge cases & pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| `if` instead of `while` around `cond_wait` | rare wrong item / underflow with ≥ 2 consumers or a spurious wake-up | always `while (!predicate)` |
| Changing the predicate without the mutex | lost wake-up: waiter sleeps forever | modify state under the same mutex the waiter uses |
| `signal` when waiters wait for different predicates on one condvar | the woken thread's predicate is false, the right one sleeps (deadlock-like stall) | `broadcast`, or one condvar per predicate (`not_full` / `not_empty`) |
| Taking the mutex, then `sem_wait` | deadlock in Producer-Consumer | wait on the semaphore first, then lock |
| Using a binary semaphore as a lock | no owner, so no PI, no lockdep owner checks, wrong-thread release allowed | `pthread_mutex` / kernel `struct mutex` |
| Kernel `down()` in IRQ context | sleeping in atomic context → BUG | `down_trylock()`, or move work to process context |
| Shutdown with blocked consumers | consumers wait forever | poison pills or a `done` flag + `broadcast` (lab extension) |

## 6. Exam key points

- Semaphore = counter + wait queue, with an atomic check-and-decrement. Binary, counting and signalling uses.
- A semaphore has **no owner**; a mutex does. That is why the kernel prefers `struct mutex` for locking.
- Kernel `down()`/`up()` take `sem->lock` with irqsave. `up()` with waiters **hands the unit to the first waiter** (FIFO) without incrementing the count.
- Condvar = mutex + predicate + queue. `cond_wait` atomically unlocks and sleeps, and returns with the mutex held.
- **Mesa semantics → `while`**. Hoare semantics would allow `if`. POSIX also allows spurious wake-ups.
- `signal` wakes ≥ 1 waiter, `broadcast` wakes all. Use one condvar per predicate.
- Lost-wake-up rule (kernel `___wait_event`, futex, semaphore): **enqueue + set state before the final check**.
- Producer-Consumer: `empty = N`, `full = 0`, mutex for indices. Order: `P(empty)` then `lock`.

## 7. Links

- Lesson: [§4.5 How do threads wait for a condition?](../lesson.en.md#45-how-do-threads-wait-for-a-condition)
- Walkthrough: [kernel-walkthrough.en.md](../kernel-walkthrough.en.md)
- Labs: [03.2 Producer-Consumer (semaphores → condvars → Go channels)](../labs/02-producer-consumer/README.md), [03.3 Readers-Writers and writer starvation](../labs/03-readers-writers/README.md)
- Quiz: [Q14 (condvar `if` vs `while`)](../quiz.en.md), Q13 (readers-writers starvation)
- Related notes: [07 futex](07-futex-user-kernel-split.en.md), [05 mutex](05-mutex-optimistic-spinning.en.md), [09 deadlock](09-deadlock-coffman-lockdep.en.md), [10 classic problems](10-classic-problems.en.md)

### OpenBSD comparison

OpenBSD has no kernel counting-semaphore type in the style of `struct semaphore`. Kernel code sleeps on a **wait channel**, which is any address. `sleep_setup(ident, prio, wmesg)` comes before the final check of the condition and `sleep_finish(timeout, do_sleep)` after it (`sys/kern/kern_synch.c` L284 / L320). `wakeup(ident)` / `wakeup_n()` wake sleepers on that address. You can see the pattern in `rw_do_enter_write()`:

```text
openbsd/sys/kern/kern_rwlock.c · rw_do_enter_write() · 8cada8c · L292-298
  292  	rw_inc(&rwl->rwl_waiters);
  293  	membar_producer();
  294  	do {
  295  		sleep_setup(&rwl->rwl_waiters, prio, rwl->rwl_name);
  296  		membar_consumer();
  297  		owner = atomic_load_long(&rwl->rwl_owner);
  298  		error = sleep_finish(RW_SLEEP_TMO, owner != 0);
```

<https://github.com/openbsd/src/blob/8cada8c/sys/kern/kern_rwlock.c#L292>

- **L292–293**: announce yourself as a waiter, and publish that with a store barrier.
- **L295**: register on the channel `&rwl->rwl_waiters` **before** reading the owner. This is the same "enqueue before the final check" rule.
- **L298** `sleep_finish(..., owner != 0)`: sleep only if the condition still says so. The `do { } while` around it is the Mesa re-check.

| Design choice | Linux | OpenBSD | Trade-off |
|---|---|---|---|
| Wait object | typed `wait_queue_head_t`, `struct semaphore` | any address as a wait channel | Linux: type-safe, per-object lists. OpenBSD: simpler API, a shared hashed sleep queue |
| Condition loop | `wait_event()` macro | hand-written `sleep_setup` / check / `sleep_finish` | the macro hides the ordering rule. The manual form makes it visible but easy to get wrong |
| Counting semaphore in kernel | yes (`down`/`up`, FIFO handoff) | no dedicated type | Linux keeps it for legacy and counting cases |
| Wake | `wake_up()` (exclusive waiters: one) | `wakeup()` all / `wakeup_n()` | wake-all is simpler but causes a thundering herd |
