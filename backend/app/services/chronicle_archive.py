"""互联网纪事导入导出: Markdown 序列化, 解析, 查重与落库"""

import io
import re
import zipfile
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.chronicle import ChronicleEntry
from app.models.user import User
from app.services.archive import (
    frontmatter_lines,
    lookup_image,
    pack_images,
    parse_frontmatter,
    rewrite_import_images,
    title_key,
)
from app.services.markdown import render_markdown
from app.services.post_archive import import_title

STATUS_DRAFT = 0
STATUS_REVIEW = 1
STATUS_PUBLISHED = 2
STATUS_PRIVATE = 3
STATUS_TRASH = 4


def to_markdown(entry: ChronicleEntry) -> str:
    """将纪事序列化为带 YAML frontmatter 的 Markdown 文本"""
    pairs: list[tuple[str, object]] = [
        ("title", entry.title),
        ("status", entry.status),
    ]
    if entry.published_at:
        pairs.append(("date", entry.published_at.strftime("%Y-%m-%d %H:%M:%S")))
    pairs.append(("summary", entry.summary))
    if entry.cover_image:
        pairs.append(("cover_image", entry.cover_image))
    lines = frontmatter_lines(pairs)
    lines.append("")
    lines.append(entry.content_md)
    return "\n".join(lines)


def build_zip(entries: list[ChronicleEntry], fmt: str) -> bytes:
    """把纪事打包成 Markdown 或 HTML 压缩包, 正文与封面图片一并放入"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            stem = f"chronicle-{entry.id}"
            if fmt == "html":
                content = entry.content_html or render_markdown(entry.content_md)
                body = (
                    "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='utf-8'>\n"
                    f"<title>{entry.title}</title>\n</head>\n<body>\n{content}\n</body>\n</html>"
                )
                filename = f"{stem}.html"
                text_for_images = f"{content} {entry.cover_image or ''}"
            else:
                body = to_markdown(entry)
                filename = f"{stem}.md"
                text_for_images = body
            body = pack_images(zf, body, text_for_images, f"images/{stem}")
            zf.writestr(filename, body)
    return buf.getvalue()


def parse_import(filename: str, content: str) -> dict | None:
    """解析导入内容, 返回 {content, title}; 识别不出标题返回 None"""
    meta, body = parse_frontmatter(content)
    title = import_title(meta, body, filename)
    if not title:
        return None
    return {"content": content, "title": title}


def existing_title_keys(db: Session) -> set[str]:
    """已有纪事标题的查重键(回收站中的纪事不算重复)"""
    rows = db.query(ChronicleEntry.title).filter(ChronicleEntry.status != STATUS_TRASH).all()
    return {title_key(str(title)) for (title,) in rows if str(title).strip()}


def _parse_status(meta: dict) -> int:
    """解析 frontmatter 状态, 非法值回退为草稿"""
    try:
        value = int(str(meta.get("status") or STATUS_DRAFT))
    except (TypeError, ValueError):
        return STATUS_DRAFT
    if value not in (STATUS_DRAFT, STATUS_REVIEW, STATUS_PUBLISHED, STATUS_PRIVATE):
        return STATUS_DRAFT
    return value


def _parse_published_at(meta: dict) -> datetime:
    """解析 frontmatter 发布日期, 失败时使用当前时间"""
    value = str(meta.get("date") or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except (TypeError, ValueError):
            continue
    return datetime.now()


def _import_summary(meta: dict, body: str, title: str) -> str:
    """优先使用 frontmatter 概览, 缺失时从正文提取一段纯文本"""
    summary = str(meta.get("summary") or "").strip()
    if summary:
        return summary[:500]
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", body)
    text = re.sub(r"[#>*_`~\[\]()\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return (text or title)[:500]


def create_from_plan(
    db: Session,
    user: User,
    plan: dict,
    image_map: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """按导入计划创建纪事, 返回 (是否导入, 错误信息)"""
    filename = plan["filename"]
    meta, body = parse_frontmatter(plan["content"])
    image_map = image_map or {}
    title = import_title(meta, body, filename)
    if not title:
        return False, f"{filename}: 无法识别标题"

    status = _parse_status(meta)
    body = rewrite_import_images(body, image_map).strip()
    cover = str(meta.get("cover_image") or "").strip() or None
    cover = lookup_image(image_map, cover) or cover
    entry = ChronicleEntry(
        author_id=user.id,
        title=title[:200],
        summary=_import_summary(meta, body, title),
        cover_image=cover[:255] if cover else None,
        status=status,
        content_md=body,
        content_html=render_markdown(body),
    )
    if status == STATUS_PUBLISHED:
        entry.published_at = _parse_published_at(meta)
    db.add(entry)
    db.flush()
    return True, None
