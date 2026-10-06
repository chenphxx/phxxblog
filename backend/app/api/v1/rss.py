"""RSS 与 Sitemap(挂载在根路径)"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from feedgen.feed import FeedGenerator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.post import Post
from app.models.setting import Setting
from app.modules.registry import registry
from app.modules.state import module_config

router = APIRouter(tags=["RSS/SEO"])

# RSS 最多包含多少篇最新文章: 模块配置(module.rss.post_limit)优先, 没配置时用它
DEFAULT_POST_LIMIT = 50


def _post_limit(db: Session) -> int:
    """取 RSS 的文章条数上限(模块配置)

    @param db: 数据库会话
    @return 条数上限
    """
    spec = registry.get("rss")
    if spec is None:
        return DEFAULT_POST_LIMIT
    value = module_config(db, spec).get("post_limit")
    return int(value) if isinstance(value, int) else DEFAULT_POST_LIMIT


def _aware(value: datetime | None) -> datetime | None:
    """feedgen 要求带时区信息的 datetime"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _site_name(db: Session) -> str:
    row = db.get(Setting, "site_name")
    return row.setting_value if row and row.setting_value else "phxxblog"


def _site_desc(db: Session) -> str:
    row = db.get(Setting, "site_desc")
    return row.setting_value if row and row.setting_value else ""


@router.get("/rss.xml", include_in_schema=False)
def rss_feed(db: Session = Depends(get_db)):
    """RSS 订阅源"""
    feed = FeedGenerator()
    feed.title(_site_name(db))
    feed.description(_site_desc(db))
    feed.link(href=settings.site_url, rel="self")
    feed.language("zh-CN")

    posts = (
        db.query(Post)
        .filter(Post.status == 2)
        .order_by(Post.published_at.desc())
        .limit(_post_limit(db))
        .all()
    )
    for post in posts:
        entry = feed.add_entry()
        entry.title(post.title)
        entry.link(href=f"{settings.site_url}/post/{post.id}")
        entry.published(_aware(post.published_at))
        entry.updated(_aware(post.updated_at))
        entry.summary(post.summary or "")
        entry.content(post.content_html or "", type="html")
    return Response(
        content=feed.rss_str(pretty=True),
        media_type="application/rss+xml; charset=utf-8",
    )


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)):
    """SEO 站点地图"""
    posts = db.query(Post).filter(Post.status == 2).order_by(Post.published_at.desc()).all()
    urls = [f"{settings.site_url}/"]
    urls += [f"{settings.site_url}/archive"]
    urls += [f"{settings.site_url}/post/{post.id}" for post in posts]
    today = datetime.now().date().isoformat()
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        xml.append(f"  <url><loc>{url}</loc><lastmod>{today}</lastmod></url>")
    xml.append("</urlset>")
    return Response(content="\n".join(xml), media_type="application/xml; charset=utf-8")
