<div dir="rtl">

# ماژول ۰۵ — فهرست یادداشت‌ها

> به ترتیب بخوانید؛ هر یادداشت این بخش‌ها را دارد: خلاصه ← توضیح کامل ← نمودار ← مثال عملی ← دام‌ها ← نکته‌های امتحانی ← پیوندها. نسخهٔ انگلیسی: [`INDEX.en.md`](INDEX.en.md)

| # | یادداشت | پرسش اصلی | منبع اصلی | آزمایش |
|---|---|---|---|---|
| ۰۱ | [اشیای VFS: superblock، inode، dentry، file](01-vfs-objects.fa.md) | یک `read()` چطور روی همهٔ فایل‌سیستم‌ها کار می‌کند؟ | `include/linux/fs.h`، `include/linux/dcache.h` | ۰۵.۱ |
| ۰۲ | [Path lookup: namei، RCU-walk، ref-walk](02-path-lookup.fa.md) | یک رشته چطور، سریع و روی ۶۴ CPU، به یک dentry تبدیل می‌شود؟ | `fs/namei.c`، `fs/dcache.c` | ۰۵.۱ |
| ۰۳ | [جدول‌های file descriptor و `struct file`](03-fd-tables.fa.md) | fd چیست، و چرا processهای fork‌شده offset مشترک دارند؟ | `include/linux/fdtable.h`، `fs/file.c`، `fs/open.c` | ۰۵.۱ |
| ۰۴ | [Page cache و writeback](04-page-cache-writeback.fa.md) | چرا خواندن دوم ۵ تا ۱۰ برابر سریع‌تر است، و یک write کی به دیسک می‌رسد؟ | `mm/filemap.c`، `mm/page-writeback.c`، `fs/sync.c` | ۰۵.۲، ۰۵.۳ |
| ۰۵ | [Block layer و blk-mq](05-block-layer-blk-mq.fa.md) | یک bio چطور بدون lock سراسری به فرمان سخت‌افزاری تبدیل می‌شود؟ | `block/blk-mq.c`، `drivers/block/loop.c` | ۰۵.۴ |
| ۰۶ | [I/O schedulerها](06-io-schedulers.fa.md) | none، mq-deadline، bfq، kyber: کدام، کی، با چه هزینه‌ای؟ | `block/mq-deadline.c`، `block/elevator.c` | ۰۵.۴ |
| ۰۷ | [Journaling و سازگاری پس از crash](07-journaling-crash-consistency.fa.md) | بعد از قطع برق چه چیزی باقی می‌ماند، و چرا `fsync` مهم است؟ | `fs/jbd2/commit.c`، `fs/ext4/fsync.c` | ۰۵.۶ |
| ۰۸ | [io_uring](08-io-uring.fa.md) | ringهای مشترک چطور syscallها را از مسیر I/O حذف می‌کنند؟ | `io_uring/io_uring.c`، `io_uring/rw.c` | ۰۵.۵ |
| ۰۹ | [درایورهای دستگاه و character deviceها](09-device-drivers-char-devices.fa.md) | `open("/dev/null")` چطور به کد درایور می‌رسد؟ | `fs/char_dev.c`، `drivers/char/mem.c` | ۰۵.۱ (تکمیلی) |

مرتبط: [درس](../lesson.fa.md) · [مرور کد کرنل](../kernel-walkthrough.fa.md) · [آزمایش‌ها](../labs/) · [آزمونک](../quiz.fa.md) · [ویدیوها](../videos.md)

</div>
