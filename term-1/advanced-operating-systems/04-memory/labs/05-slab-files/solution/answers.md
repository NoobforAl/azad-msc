# Lab 04.5 — solution notes

- **Creating a file** (`openat(O_CREAT)`):
  - `d_alloc()` takes one `dentry` from the `dentry` cache (`kmem_cache_alloc(dentry_cache, …)` in `fs/dcache.c`);
  - the filesystem allocates an in-memory inode (`ext4_alloc_inode()` → `alloc_inode_sb(sb, ext4_inode_cachep, …)`);
  - the inode is written to the on-disk inode table, and the directory gets an entry.

  So both caches grow by about N objects.
- **Memory:** 200 000 × (192 + 1128) B ≈ 252 MiB of objects (measured: about 215 MiB of growth in the two caches). All of it is `SReclaimable`, because both caches have shrinkers. None of it is in any process's RSS.
- **After delete:** unlink evicts the inode (`iput` → `evict` → `destroy_inode`) and drops the dentry. In the captured run both `active` and `total` returned close to the starting values (ext4_inode_cache 8433/8671, dentry 34518/35532). Bulk frees emptied whole slabs, and SLUB released them to the buddy allocator. With scattered frees, partial slabs would keep `total` high.
- **The slab-size check:** `objperslab × objsize ≤ pagesperslab × 4096`. The rest is per-slab waste.
