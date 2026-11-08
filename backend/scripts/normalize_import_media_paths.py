"""将历史导入图片迁移为短路径并同步数据库引用

旧版导出会把 assets 下的完整相对路径写进 ZIP, 再次导入后又保留整段目录,
导致 uploads/import 内出现不断叠加的长路径. 本脚本把 import 目录内层级超过
年/月/文件名的图片移动到 年/月/<uuid>.<ext>, 并替换数据库中的旧 URL

默认只预览迁移计划, 加 --apply 才会移动文件和提交数据库更新
"""

# ruff: noqa: E402

import argparse
import os
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.chronicle import ChronicleEntry
from app.models.comment import Comment
from app.models.diary import DiaryEntry
from app.models.media import Media
from app.models.post import Post
from app.models.setting import Setting
from app.models.user import User
from app.services.archive import IMPORT_IMAGE_EXTS


@dataclass(frozen=True)
class MovePlan:
    """一张待迁移图片的移动计划"""

    source: Path
    target: Path
    old_url: str
    new_url: str


def _upload_import_root() -> Path:
    """上传目录中的 import 根目录"""
    return (Path(settings.upload_dir) / "import").resolve()


def _target_month(parts: tuple[str, ...]) -> tuple[str, str]:
    """优先沿用原路径中的年/月, 非标准路径回退到当前月"""
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return parts[0], parts[1]
    today = date.today()
    return str(today.year), f"{today.month:02d}"


def build_plan(db: Session) -> list[MovePlan]:
    """扫描 import 目录中的长路径图片并生成移动计划"""
    import_root = _upload_import_root()
    if not import_root.is_dir():
        return []

    existing_filenames = {filename for (filename,) in db.query(Media.filename).all() if filename}
    plans: list[MovePlan] = []
    for source in sorted(path for path in import_root.rglob("*") if path.is_file()):
        suffix = source.suffix.lower()
        if suffix not in IMPORT_IMAGE_EXTS:
            continue
        relative = source.relative_to(import_root)
        if len(relative.parts) <= 3:
            continue

        year, month = _target_month(relative.parts)
        target_dir = import_root / year / month
        while True:
            filename = f"{uuid.uuid4().hex}{suffix}"
            target = target_dir / filename
            if filename not in existing_filenames and not target.exists():
                existing_filenames.add(filename)
                break
        plans.append(
            MovePlan(
                source=source,
                target=target,
                old_url=f"/assets/uploads/import/{relative.as_posix()}",
                new_url=f"/assets/uploads/import/{year}/{month}/{filename}",
            )
        )
    return plans


def _replace_urls(value: str | None, url_map: dict[str, str]) -> str | None:
    """替换单个字段中的全部旧 URL"""
    if not value:
        return value
    for old_url, new_url in url_map.items():
        if old_url in value:
            value = value.replace(old_url, new_url)
    return value


def update_references(db: Session, plans: list[MovePlan]) -> int:
    """更新媒体记录与所有已知内容表中的旧 URL, 返回更新字段数"""
    if not plans:
        return 0

    url_plan_map = {plan.old_url: plan for plan in plans}
    url_map = {plan.old_url: plan.new_url for plan in plans}
    path_map = {plan.source.resolve(): plan for plan in plans}
    changed = 0

    assigned_filenames = {media.filename for media in db.query(Media).all() if media.filename}
    for media in db.query(Media).all():
        plan = url_plan_map.get(media.url) or path_map.get(Path(media.path).resolve())
        if plan is None:
            continue
        media.path = str(plan.target).replace("\\", "/")
        media.url = plan.new_url
        filename = plan.target.name
        if filename in assigned_filenames:
            filename = f"{plan.target.stem}-{media.id}{plan.target.suffix}"
        assigned_filenames.add(filename)
        media.filename = filename
        changed += 1

    targets: list[tuple[type, tuple[str, ...]]] = [
        (Post, ("content_md", "content_html", "cover_image")),
        (DiaryEntry, ("content_md", "content_html")),
        (ChronicleEntry, ("content_md", "content_html", "cover_image")),
        (Comment, ("content",)),
        (User, ("avatar",)),
        (Setting, ("setting_value",)),
    ]
    for model, fields in targets:
        for row in db.query(model).all():
            old_updated_at = getattr(row, "updated_at", None)
            for field in fields:
                current = getattr(row, field)
                updated = _replace_urls(current, url_map)
                if updated != current:
                    setattr(row, field, updated)
                    changed += 1
                    if old_updated_at is not None:
                        # 显式写回原更新时间并标记为已修改, 防止模型的 onupdate
                        # 把维护性 URL 替换误记为一次正式内容更新
                        row.updated_at = old_updated_at
                        flag_modified(row, "updated_at")
    return changed


def remove_empty_legacy_dirs() -> None:
    """迁移完成后清理 import 目录下已经变空的旧层级目录"""
    import_root = _upload_import_root()
    if not import_root.is_dir():
        return
    for root, _dirs, _files in os.walk(import_root, topdown=False):
        path = Path(root)
        if path == import_root:
            continue
        try:
            path.rmdir()
        except OSError:
            pass


def main() -> None:
    """执行预览或正式迁移"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="移动文件并提交数据库更新")
    args = parser.parse_args()

    db = SessionLocal()
    moved: list[MovePlan] = []
    committed = False
    try:
        plans = build_plan(db)
        print(f"待迁移图片: {len(plans)}")
        for plan in plans[:20]:
            print(f"  {plan.old_url} -> {plan.new_url}")
        if len(plans) > 20:
            print(f"  ... 另有 {len(plans) - 20} 张")
        if not args.apply or not plans:
            print("预览完成; 加 --apply 执行迁移")
            return

        for plan in plans:
            plan.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(plan.source), str(plan.target))
            moved.append(plan)

        changed = update_references(db, plans)
        db.flush()
        db.commit()
        committed = True
        try:
            remove_empty_legacy_dirs()
        except OSError:
            pass
        print(f"迁移完成: 文件 {len(moved)} 个, 数据库字段 {changed} 处")
    except Exception:
        db.rollback()
        if not committed:
            for plan in reversed(moved):
                if plan.target.exists() and not plan.source.exists():
                    plan.source.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(plan.target), str(plan.source))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
