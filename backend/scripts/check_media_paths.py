"""检查 media 表: url 与磁盘文件是否都对得上, 以及 path 字段是否失效。

只读。用法: python scripts/check_media_paths.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.services.upload import upload_root  # noqa: E402

root = upload_root()
print(f"  上传根目录: {root}")
print()

with SessionLocal() as db:
    rows = db.query(Media).all()

url_ok = url_missing = 0
path_ok = path_bad = 0
samples = []

for m in rows:
    # url 形如 /assets/uploads/<相对路径>
    rel = m.url.split("/assets/uploads/", 1)[1] if "/assets/uploads/" in (m.url or "") else None
    file_exists = bool(rel) and (root / rel).exists()
    if file_exists:
        url_ok += 1
    else:
        url_missing += 1
        if len(samples) < 5:
            samples.append(("url 指向的文件不存在", m.url))

    stored = Path(m.path or "")
    stored_ok = stored.exists()
    if stored_ok:
        path_ok += 1
    else:
        path_bad += 1

print(f"  记录数: {len(rows)}")
print()
print(f"  url 对应的磁盘文件存在: {url_ok}")
print(f"  url 对应的磁盘文件不存在: {url_missing}")
print()
print(f"  path 字段指向的文件存在: {path_ok}")
print(f"  path 字段指向的文件不存在: {path_bad}")
if path_bad:
    print(f"    -> path 字段已失效(项目搬迁/数据库导入导致), 删除媒体时无法清理磁盘文件")

for kind, val in samples:
    print(f"  [{kind}] {val}")

print()
if url_missing == 0 and path_bad == 0:
    verdict = "url 与 path 都有效, 磁盘文件齐全 —— 无需处理"
elif url_missing == 0 and path_bad:
    verdict = "url 有效但 path 字段失效(项目搬迁/数据库导入导致) → 用 repair_media_paths.py 按 url 重算"
elif url_missing and path_bad == 0:
    verdict = "path 有效但 url 指向的文件缺失 —— 需要人工确认 url 是否正确"
else:
    verdict = "url 与 path 都失效 —— 需要人工确认数据来源"
print("  结论: " + verdict)
