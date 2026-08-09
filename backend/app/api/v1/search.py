"""站内搜索接口。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.models.post import Post
from app.schemas.common import Page
from app.schemas.post import PostListItem

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("", response_model=dict)
def search(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    start_date: str | None = Query(None, description="发布时间起始 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="发布时间结束 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """全文搜索已发布文章(标题/摘要/正文)。"""
    like = f"%{q}%"
    query = (
        db.query(Post)
        .filter(
            Post.status == 2,
            or_(
                Post.title.like(like),
                Post.summary.like(like),
                Post.content_md.like(like),
            ),
        )
    )
    if start_date:
        query = query.filter(Post.published_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(
            Post.published_at <= datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        )
    total = query.count()
    items = (
        query.order_by(Post.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(Page[PostListItem](
        items=[PostListItem.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    ))
