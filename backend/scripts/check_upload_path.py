"""验证 resolve_upload_file 的路径校验行为(含旧实现会漏掉的绕过用例)。

跑法: backend/.venv/Scripts/python.exe scripts/check_upload_path.py
只读, 不删任何文件。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.upload import resolve_upload_file, upload_root  # noqa: E402

root = upload_root()
print(f"  上传根目录: {root}")
print()

cases = [
    # (描述, 数据库里可能存的路径, 是否应在允许范围内)
    ("正常相对路径", "uploads/2026/09/abc.png", None),
    ("正常绝对路径", str(root / "2026/09/abc.png"), True),
    ("前缀相似的兄弟目录(旧实现会放行)", str(root.parent / (root.name + "_evil") / "x.png"), False),
    ("用 .. 逃逸", str(root / ".." / ".." / "etc" / "passwd"), False),
    ("上传根目录本身", str(root), True),
    ("空路径", "", False),
]

failed = 0
for desc, stored, expect in cases:
    got = resolve_upload_file(stored)
    inside = got is not None
    if expect is None:
        # 相对路径的存在性取决于当前仓库, 这里只报告结果
        print(f"  {desc:<34} -> {'允许' if inside else '拒绝'}  {got if inside else ''}")
        continue
    ok = inside == expect
    failed += 0 if ok else 1
    print(f"  {'OK  ' if ok else 'FAIL'} {desc:<30} -> {'允许' if inside else '拒绝'}")
    if inside:
        print(f"       解析结果: {got}")

print()
print("  实测数据库里真实媒体的路径解析:")
from app.core.database import SessionLocal  # noqa: E402
from app.models.media import Media  # noqa: E402

with SessionLocal() as db:
    rows = db.query(Media).limit(3).all()
    for m in rows:
        resolved = resolve_upload_file(m.path)
        print(f"    {m.path[:56]:<58} -> {'允许' if resolved else '拒绝'}")

print()
print("结论: " + ("全部符合预期" if failed == 0 else f"{failed} 个用例不符合预期"))
sys.exit(1 if failed else 0)
