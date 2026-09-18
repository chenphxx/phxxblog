"""修复 media 表里失效的 path 字段。

背景: 项目搬迁过(或数据库从别处导入), 记录里的 path 指向旧机器的绝对路径
      (D:/Files/chenphxx/...), 而 url 是相对路径因此仍然有效。后果是删除媒体时
      找不到磁盘文件, 只删了数据库记录, 留下孤儿文件。

做法: path 可以完全由 url 推导 —— url 形如 /assets/uploads/<相对路径>,
      磁盘位置 = <PHXXBLOG_UPLOAD_DIR>/<相对路径>。

用法:
  python scripts/repair_media_paths.py            # 只预览(dry-run), 默认
  python scripts/repair_media_paths.py --apply    # 实际写入
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.services.upload import upload_root  # noqa: E402

APPLY = "--apply" in sys.argv
root = upload_root()

print(f"  上传根目录: {root}")
print(f"  模式: {'实际写入' if APPLY else '预览(dry-run, 加 --apply 才写入)'}")
print()

with SessionLocal() as db:
    rows = db.query(Media).all()
    fixed = skipped_no_url = skipped_missing_file = already_ok = 0

    for m in rows:
        url = m.url or ""
        if "/assets/uploads/" not in url:
            skipped_no_url += 1
            continue
        rel = url.split("/assets/uploads/", 1)[1]
        target = (root / rel).resolve()

        # 已经被修过(或本来就正确)的跳过
        if m.path and Path(m.path).resolve() == target:
            already_ok += 1
            continue

        if not target.exists():
            skipped_missing_file += 1
            print(f"  [跳过] 磁盘上找不到: {url}")
            continue

        old = m.path
        if APPLY:
            m.path = str(target).replace("\\", "/")
        fixed += 1
        if fixed <= 5:
            print(f"  [修正] {url}")
            print(f"         {old}")
            print(f"      -> {str(target).replace(chr(92), '/')}")

    if APPLY:
        db.commit()

    print()
    print(f"  待修正: {fixed}")
    print(f"  已正确(跳过): {already_ok}")
    print(f"  url 不含 /assets/uploads/(跳过): {skipped_no_url}")
    print(f"  磁盘文件缺失(跳过): {skipped_missing_file}")

if not APPLY and fixed:
    print()
    print("  确认无误后执行: python scripts/repair_media_paths.py --apply")
