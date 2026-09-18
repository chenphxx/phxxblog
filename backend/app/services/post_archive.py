"""文章导入导出: Markdown 序列化, 解析, 查重与落库。

为什么单独抽一个模块:
    导入导出原先占 api/v1/posts.py 近 200 行, 与文章 CRUD, 状态流转, 点赞混在一起,
    而它们只在"导入/导出"两个接口里被用到; 导入的解析规则(标题推断, 分类兼容旧格式,
    状态降级)还需要被测试单独覆盖。这里只放文章自己的规则, 上传文件的拆分与查重流程
    走 services/import_pipeline.py, 与日记共用。
"""

import io
import zipfile
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.post import Category, Post, Tag
from app.models.user import User
from app.services.archive import (
    frontmatter_lines,
    lookup_image,
    pack_images,
    parse_frontmatter,
    rewrite_import_images,
    title_key,
    unique_slug,
)
from app.services.markdown import render_markdown
from app.services.post_write import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_REVIEW,
    auto_slug,
    resolve_categories_by_name,
    resolve_submitted_status,
)


def to_markdown(post: Post) -> str:
    """将文章序列化为带 YAML frontmatter 的 Markdown 文本。"""
    pairs: list[tuple[str, object]] = [
        ("title", post.title),
        ("slug", post.slug),
        ("status", post.status),
    ]
    if post.published_at:
        pairs.append(("date", post.published_at.strftime("%Y-%m-%d %H:%M:%S")))
    if post.summary:
        pairs.append(("summary", post.summary))
    if post.cover_image:
        pairs.append(("cover_image", post.cover_image))
    if post.categories:
        pairs.append(("categories", [category.name for category in post.categories]))
    if post.tags:
        pairs.append(("tags", [t.name for t in post.tags]))
    lines = frontmatter_lines(pairs)
    lines.append("")
    lines.append(post.content_md)
    return "\n".join(lines)


def build_zip(posts: list[Post], fmt: str) -> bytes:
    """把文章打包成 zip 字节流(markdown 或 html), 正文引用的本地图片一并放入。

    @param posts 待导出的文章
    @param fmt markdown 或 html
    @return zip 文件内容
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for post in posts:
            slug = post.slug or str(post.id)
            if fmt == "html":
                content = post.content_html or render_markdown(post.content_md)
                body = (
                    "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='utf-8'>\n"
                    f"<title>{post.title}</title>\n</head>\n<body>\n{content}\n</body>\n</html>"
                )
                filename = f"{slug}.html"
                # 封面可能写在 frontmatter 外, html 导出时要单独把封面也算进图片来源
                text_for_images = f"{content} {post.cover_image or ''}"
            else:
                body = to_markdown(post)
                filename = f"{slug}.md"
                text_for_images = body
            body = pack_images(zf, body, text_for_images, f"images/{slug}")
            zf.writestr(filename, body)
    return buf.getvalue()


def rewrite_cover_image(cover: str | None, image_map: dict[str, str]) -> str | None:
    """改写 frontmatter 中的封面图片路径。"""
    if not cover:
        return cover
    return lookup_image(image_map, cover) or cover


def import_title(meta: dict, body: str, filename: str) -> str:
    """推断文章标题: frontmatter -> 首个一级标题 -> 文件名。"""
    title = str(meta.get("title") or "").strip()
    if not title:
        for line in body.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
    if not title:
        stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        title = stem[:-3] if stem.lower().endswith(".md") else stem
    return title


def existing_title_keys(db: Session) -> set[str]:
    """已有文章标题的查重键(回收站中的文章不算重复)。"""
    rows = db.query(Post.title).filter(Post.status != 4).all()
    return {title_key(str(title)) for (title,) in rows if str(title).strip()}


def parse_import(filename: str, content: str) -> dict | None:
    """解析导入内容, 返回 {content, title}; 识别不出标题返回 None。"""
    meta, body = parse_frontmatter(content)
    title = import_title(meta, body, filename)
    if not title:
        return None
    return {"content": content, "title": title}


def _resolve_import_status(meta: dict, user: User) -> int:
    """按 frontmatter 的 status 与提交人权限推出实际落库状态。"""
    try:
        raw_status = int(str(meta.get("status") or str(STATUS_DRAFT)))
    except (TypeError, ValueError):
        raw_status = STATUS_DRAFT
    # 与新增/修改共用同一条状态规则(见 services/post_write), 差别只在
    # 越权时的降级目标: 批量导入落"草稿"而不是"审核中"(不宜把导入内容塞进审核队列)。
    resolved = resolve_submitted_status(raw_status, user)
    if raw_status in (STATUS_DRAFT, STATUS_REVIEW):
        # 草稿/审核中不需要任何权限, 原样保留
        return raw_status
    if resolved != raw_status:
        return STATUS_DRAFT
    return resolved


def _resolve_import_categories(db: Session, meta: dict) -> list[Category]:
    """解析 frontmatter 里的分类名(兼容旧格式的单值 category)并按需新建。"""
    raw_categories = meta.get("categories")
    if raw_categories is None:
        raw_categories = meta.get("category")
    if isinstance(raw_categories, str):
        # 手写的 [后端, 运维] 不带引号时 json 解析不出列表, 这里按逗号兜底拆分;
        # 其余情况整体当作一个分类名(避免把名字里带逗号的分类拆开)
        text = raw_categories.strip()
        if text.startswith("[") and text.endswith("]"):
            raw_categories = [name.strip() for name in text[1:-1].split(",") if name.strip()]
        else:
            raw_categories = [text]
    elif not isinstance(raw_categories, list):
        raw_categories = []
    return resolve_categories_by_name(
        db,
        [str(name) for name in raw_categories],
        lambda value: unique_slug(db, Category, value),
    )


def _resolve_import_tags(db: Session, meta: dict) -> list[Tag]:
    """解析 frontmatter 里的标签名并按需新建。"""
    raw_tags = meta.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.strip("[]").split(",") if t.strip()]
    tags: list[Tag] = []
    for tag_name in raw_tags:
        tag_name = str(tag_name).strip()
        if not tag_name:
            continue
        tag = db.query(Tag).filter(func.lower(Tag.name) == tag_name.lower()).first()
        if tag is None:
            tag = Tag(name=tag_name[:50], slug=unique_slug(db, Tag, tag_name[:80]))
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def _parse_published_at(meta: dict) -> datetime:
    """解析 frontmatter 的发布日期, 解析失败退回当前时间。"""
    date_str = str(meta.get("date") or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.now()


def create_from_plan(
    db: Session,
    user: User,
    plan: dict,
    image_map: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """按导入计划创建一篇文章(默认草稿), 返回 (是否导入, 错误信息)。

    @param db 数据库会话
    @param user 导入人(作者)
    @param plan parse_import 产出的计划项, 含 filename 与 content
    @param image_map 压缩包内图片的相对路径 -> 服务器 URL 映射
    @return (是否导入, 错误信息); 失败时不计入导入数
    """
    filename = plan["filename"]
    meta, body = parse_frontmatter(plan["content"])
    image_map = image_map or {}
    title = import_title(meta, body, filename)
    if not title:
        return False, f"{filename}: 无法识别标题"

    slug = unique_slug(db, Post, auto_slug(str(meta.get("slug") or "").strip()))

    status = _resolve_import_status(meta, user)
    body = rewrite_import_images(body, image_map)
    summary = str(meta.get("summary") or "").strip() or None
    cover_image = rewrite_cover_image(str(meta.get("cover_image") or "").strip() or None, image_map)
    post = Post(
        author_id=user.id,
        title=title[:200],
        slug=slug,
        summary=summary[:500] if summary else None,
        content_md=body,
        cover_image=cover_image[:255] if cover_image else None,
        status=status,
    )
    if status == STATUS_PUBLISHED:
        post.published_at = _parse_published_at(meta)
    post.categories = _resolve_import_categories(db, meta)
    post.tags = _resolve_import_tags(db, meta)
    db.add(post)
    db.flush()
    return True, None
