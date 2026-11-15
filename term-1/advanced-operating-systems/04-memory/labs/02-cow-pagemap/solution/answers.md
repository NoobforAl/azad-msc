# Lab 04.2 — solution notes

1. **Before `fork`:**
   - `excl=1`, and `Private_Dirty` ≈ the whole region: the parent wrote every page and is the only mapper.
2. **After `fork` (child):**
   - The PFN is the same as the parent's: `copy_page_range()` copied the PTE, not the page, and write-protected both PTEs.
   - `excl=0`: pagemap bit 56 means "mapped by exactly one process", and the page now has a map count of 2.
   - `Shared_Dirty` ≈ the whole region.
3. **Child writes half the pages:**
   - Each first write is a write fault on a read-only PTE in a writable VMA. The path is `handle_pte_fault()` → `do_wp_page()`. The page is not `PageAnonExclusive` and the refcount is > 1, so it ends in `wp_page_copy()`.
   - One minor fault and one new frame per page. That is why the minor-fault count equals the number of pages written.
   - The child's page 0 has a new PFN and `excl=1`.
   - `Shared_Dirty` and `Private_Dirty` split about 50/50.
4. **Parent after the child wrote:**
   - Same PFN as before, and still reads `0xaa`.
   - `excl` is 1 again for page 0, because the child no longer maps it.
   - If the parent now wrote page 0, `wp_can_reuse_anon_folio()` would find refcount 1 and reuse the page without copying.
5. **Without root:** `pagemap_read()` hides PFNs from readers without `CAP_SYS_ADMIN` (since 4.2, Rowhammer mitigation), so every PFN reads as 0.
