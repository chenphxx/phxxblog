"""从 WordPress WXR 导出文件迁移数据到本项目。

支持导入: 作者、分类、文章(含正文/Gutenberg 块转 Markdown)、评论、附件(可下载到 assets/uploads/wordpress)。
跳过: 页面、导航、主题模板等站点结构数据。

用法:
    python scripts/import_wordpress.py
    python scripts/import_wordpress.py --xml assets/wordpress/所有内容.xml --no-download
"""
import argparse
import glob
import mimetypes
import re
import secrets
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import html2text
import requests

# 让脚本可直接运行: 将项目根目录与 backend 目录加入模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.comment import Comment  # noqa: E402
from app.models.media import Media  # noqa: E402
from app.models.post import Category, Post, Tag  # noqa: E402
from app.models.user import Role, User  # noqa: E402
from app.services.geo import resolve_location  # noqa: E402

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}

# WordPress 文章状态 -> 本项目状态
STATUS_MAP = {
    "publish": 2,
    "draft": 0,
    "pending": 1,
    "private": 3,
    "trash": 4,
    "future": 0,
    "inherit": 2,
}


def text(elem: ET.Element | None, tag: str) -> str:
    """读取带命名空间的子标签文本。"""
    if elem is None:
        return ""
    node = elem.find(tag, NS)
    return (node.text or "").strip() if node is not None and node.text else ""


def parse_datetime(value: str) -> datetime | None:
    """解析 WXR 日期(如 2025-09-22 14:40:57)。"""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=None)
        except ValueError:
            continue
    return None


def content_to_markdown(html: str) -> str:
    """把 WordPress 正文(Gutenberg 块 + HTML)转换为 Markdown。"""
    if not html:
        return ""
    # 去掉 Gutenberg 块注释 <!-- wp:xxx --> 与普通 HTML 注释
    cleaned = re.sub(r"<!--[\s\S]*?-->", "", html)
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.unicode_snob = True
    converter.ignore_links = False
    converter.ignore_images = False
    converter.single_line_break = True
    return converter.handle(cleaned).strip()


def unique_slug(db, base: str, model, column) -> str:
    """确保 slug 唯一, 冲突时追加 -2/-3。"""
    slug = base or f"post-{secrets.token_hex(4)}"
    candidate, index = slug, 2
    while db.query(model).filter(column == candidate).first():
        candidate = f"{slug}-{index}"
        index += 1
    return candidate


def download_attachment(url: str) -> bytes | None:
    """下载附件, 返回 (目标路径, 内容)。"""
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        print(f"  [跳过] 附件下载失败: {url} ({exc})")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="迁移 WordPress WXR 数据到本项目")
    parser.add_argument("--xml", default="", help="WXR XML 文件路径(默认自动找 assets/wordpress 下最大的 xml)")
    parser.add_argument("--no-download", action="store_true", help="跳过附件下载(仅导入元数据)")
    args = parser.parse_args()

    if args.xml:
        xml_path = Path(args.xml)
    else:
        candidates = sorted(
            glob.glob(str(PROJECT_ROOT / "assets" / "wordpress" / "*.xml")),
            key=lambda p: Path(p).stat().st_size,
        )
        if not candidates:
            print("未找到 WXR XML 文件, 请通过 --xml 指定")
            return
        xml_path = Path(candidates[-1])
    print(f"数据源: {xml_path}")

    # 静默 SQL 日志
    engine.echo = False
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        channel = ET.parse(str(xml_path)).getroot().find("channel")
        items = channel.findall("item")

        # ---------- 1. 作者 ----------
        author_map: dict[str, User] = {}
        author_role = db.query(Role).filter(Role.code == "author").first()
        for author in channel.findall("wp:author", NS):
            login = text(author, "wp:author_login")
            email = text(author, "wp:author_email")
            display = text(author, "wp:author_display_name")
            user = db.query(User).filter(User.username == login).first()
            if user is None:
                # 邮箱已被占用(如管理员账号)时使用占位邮箱, 避免唯一约束冲突
                if email and db.query(User).filter(User.email == email).first():
                    email = f"{login}@imported.local"
                user = User(
                    username=login,
                    email=email or f"{login}@imported.local",
                    password_hash=hash_password(secrets.token_urlsafe(12)),
                    nickname=display or login,
                    bio="从 WordPress 迁移的作者",
                )
                if author_role:
                    user.roles = [author_role]
                db.add(user)
                db.flush()
                print(f"创建作者: {login} ({display})")
            author_map[login] = user
        db.commit()

        # ---------- 2. 分类 ----------
        category_map: dict[str, Category] = {}
        for cat in channel.findall("wp:category", NS):
            name = text(cat, "wp:cat_name") or text(cat, "wp:category_nicename")
            slug = text(cat, "wp:category_nicename") or name
            existing = db.query(Category).filter(Category.slug == slug).first()
            if existing is None:
                existing = Category(name=name, slug=slug)
                db.add(existing)
                db.flush()
            category_map[slug] = existing
        db.commit()

        # ---------- 3. 附件 ----------
        upload_root = PROJECT_ROOT / "assets" / "uploads" / "wordpress"
        url_map: dict[str, str] = {}  # 原 URL -> 本地 URL
        media_count = 0
        for item in items:
            if text(item, "wp:post_type") != "attachment":
                continue
            remote = text(item, "wp:attachment_url")
            if not remote or remote in url_map:
                continue
            # 仅处理本项目可访问的旧站点附件
            match = re.search(r"/wp-content/uploads/(.+)$", remote)
            if not match:
                continue
            rel = match.group(1).replace("\\", "/")
            target = upload_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                if args.no_download:
                    continue
                result = download_attachment(remote)
                if result is None:
                    continue
                content = result
                target.write_bytes(content)
            local_url = f"/assets/uploads/wordpress/{rel}"
            url_map[remote] = local_url
            filename = target.name
            if db.query(Media).filter(Media.filename == filename).first():
                filename = f"{target.parent.name}_{filename}"
            if not db.query(Media).filter(Media.filename == filename).first():
                suffix = target.suffix.lower()
                file_type = (
                    "image" if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}
                    else "video" if suffix in {".mp4", ".webm", ".mov", ".avi", ".mkv"}
                    else "file"
                )
                db.add(Media(
                    uploader_id=next(iter(author_map.values())).id if author_map else None,
                    original_name=target.name,
                    filename=filename,
                    path=str(target).replace("\\", "/"),
                    url=local_url,
                    mime_type=mimetypes.guess_type(target.name)[0],
                    size=target.stat().st_size,
                    type=file_type,
                ))
                media_count += 1
        db.commit()
        print(f"附件: 下载/登记 {media_count} 个")

        # ---------- 4. 文章 ----------
        post_count = 0
        comment_map: dict[int, dict] = {}  # wp 评论 id -> 数据(两遍导入处理父子关系)
        for item in items:
            if text(item, "wp:post_type") != "post":
                continue
            title = text(item, "title")
            slug = unique_slug(
                db, unquote(text(item, "wp:post_name")) or "", Post, Post.slug
            )
            # 幂等: 同名 slug 已存在则跳过
            if db.query(Post).filter(Post.slug == slug).first():
                print(f"  [跳过] 已存在: {title}")
                continue

            content_html = text(item, "content:encoded")
            # 将旧站附件 URL 替换为本地 URL
            for remote, local in url_map.items():
                content_html = content_html.replace(remote, local)
            content_md = content_to_markdown(content_html)
            excerpt = text(item, "excerpt:encoded")
            if not excerpt:
                excerpt = re.sub(r"\s+", " ", content_to_markdown(content_html))[:200]

            creator = text(item, "dc:creator")
            author = author_map.get(creator) or next(iter(author_map.values()), None)
            if author is None:
                print(f"  [跳过] 无作者可归属: {title}")
                continue

            post = Post(
                author_id=author.id,
                title=title,
                slug=slug,
                summary=excerpt[:500] or None,
                content_md=content_md,
                content_html=content_html,
                status=STATUS_MAP.get(text(item, "wp:status"), 0),
                published_at=parse_datetime(text(item, "wp:post_date")),
                created_at=parse_datetime(text(item, "wp:post_date")) or datetime.now(),
                updated_at=parse_datetime(text(item, "wp:post_modified")) or datetime.now(),
            )
            # 分类
            for cat in item.findall("category"):
                if cat.get("domain") == "category":
                    category = category_map.get(cat.get("nicename", ""))
                    if category:
                        post.category = category
                        break
            # 标签
            tag_slugs = [c.get("nicename", "") for c in item.findall("category") if c.get("domain") == "post_tag"]
            for slug_name in tag_slugs:
                tag = db.query(Tag).filter(Tag.slug == slug_name).first()
                if tag is None:
                    tag = Tag(name=slug_name, slug=slug_name)
                    db.add(tag)
                post.tags.append(tag)
            db.add(post)
            db.flush()
            post_count += 1
            print(f"导入文章: {title} [{post.status}]")

            # 收集评论
            for comment in item.findall("wp:comment", NS):
                comment_map[int(text(comment, "wp:comment_id"))] = {
                    "post": post,
                    "parent_wp_id": int(text(comment, "wp:comment_parent") or 0),
                    "author_name": text(comment, "wp:comment_author"),
                    "author_email": text(comment, "wp:comment_author_email"),
                    "content": text(comment, "wp:comment_content"),
                    "ip": text(comment, "wp:comment_author_IP"),
                    "approved": text(comment, "wp:comment_approved"),
                    "date": parse_datetime(text(comment, "wp:comment_date")) or datetime.now(),
                }
        db.commit()
        print(f"文章: 共导入 {post_count} 篇")

        # ---------- 5. 评论(两遍: 先建后挂父子) ----------
        new_comment_ids: dict[int, int] = {}
        comment_count = 0
        for wp_id, data in comment_map.items():
            # 幂等: 同内容/同 IP/同时间的评论已存在则跳过
            existing = (
                db.query(Comment)
                .filter(
                    Comment.content == data["content"],
                    Comment.ip == data["ip"],
                    Comment.created_at == data["date"],
                )
                .first()
            )
            if existing:
                new_comment_ids[wp_id] = existing.id
                continue
            comment = Comment(
                post_id=data["post"].id,
                author_name=data["author_name"] or None,
                author_email=data["author_email"] or None,
                content=data["content"],
                ip=data["ip"] or None,
                location=resolve_location(data["ip"]) if data["ip"] else "",
                status=1 if data["approved"] == "1" else 0,
                created_at=data["date"],
            )
            db.add(comment)
            db.flush()
            new_comment_ids[wp_id] = comment.id
            comment_count += 1
        db.commit()
        # 父子关系
        for wp_id, data in comment_map.items():
            if data["parent_wp_id"] and data["parent_wp_id"] in new_comment_ids:
                comment = db.get(Comment, new_comment_ids[wp_id])
                comment.parent_id = new_comment_ids[data["parent_wp_id"]]
        db.commit()
        print(f"评论: 共导入 {comment_count} 条")

        print("\n迁移完成! 统计数据:")
        print(f"  分类: {db.query(Category).count()} | 文章: {db.query(Post).count()} | 评论: {db.query(Comment).count()} | 媒体: {db.query(Media).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
