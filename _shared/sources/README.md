# Reference Sources (git submodules, depth 1, sparse)

| Submodule | Upstream | Pinned | Elixir / web browse |
|---|---|---|---|
| `linux/` | `git.kernel.org/.../stable/linux.git` | tag **v6.18.63** (longterm), commit `1cdda838e` | https://elixir.bootlin.com/linux/v6.18.63/source |
| `openbsd/` | `github.com/openbsd/src` (official mirror, -current) | commit **`8cada8c`** (master, 2026-11) | https://cvsweb.openbsd.org/src/ · https://github.com/openbsd/src/tree/8cada8c |

Both are **shallow (`--depth 1`)** and **sparse**: only the directories the courses use are checked out. That keeps the size small (~490 MB + ~60 MB) and avoids Linux paths Windows can't create (e.g. `drivers/.../aux.c`).

## Setup after cloning this repo

```bash
bash _shared/sources/setup-sources.sh
```

## Rules for quoting (all courses)

- Cite every excerpt as `<repo>/<path> · <function> · <pin>`, e.g. `linux/kernel/sched/core.c · __schedule() · v6.18.63` or `openbsd/sys/kern/kern_pledge.c · sys_pledge() · 8cada8c`.
- Copy excerpts **from these local files** (`grep -n`, then copy). Never quote from memory. ≤ 25 lines per excerpt.
- Need a directory that isn't checked out? `git -C _shared/sources/linux sparse-checkout add <dir>`.
- Need history (e.g. repository mining, `git blame`)? **Don't deepen these submodules.** Make a separate clone outside the repo (`git clone --filter=blob:none --shallow-since=2024-01-01 ...`).
- Windows note: Linux has a few case-only filename pairs (e.g. `xt_DSCP.h` / `xt_dscp.h`), so `git status` may show the submodule as modified. Read those files on Elixir or on the Linux server.
