# Lab 04.3 — solution notes

| Mode | VMA flags (from `do_mmap`) | First write in a child | Result |
|---|---|---|---|
| `file-shared` | `VM_SHARED \| VM_MAYSHARE`, `vm_file` | `do_shared_fault` → `->page_mkwrite`, the page-cache page becomes RW and dirty | all children and the parent see one page; `msync(MS_SYNC)` writes it to the file, so `pread` returns 4 000 000 |
| `file-private` | `vm_file`, no `VM_SHARED` | `do_cow_fault`: a new anonymous page is filled with a copy of the file data | each child counts in its own copy; the parent's mapping and the file stay 0 |
| `anon-shared` | `vm_file` = shmem object from `shmem_zero_setup()` | `shmem_fault` gives a shmem page, the same one for everyone | 4 000 000 |
| `anon-private` | anonymous, `anon_vma` | before the fork nobody had touched the page; each child's write fault runs `do_anonymous_page()` in its own address space | each child gets its own private page; the parent stays 0 |

`__ATOMIC_RELAXED` is enough for an exact count: every `lock xadd` is atomic, and relaxed ordering only drops ordering constraints against *other* memory locations.
