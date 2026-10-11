"""发布记录(贡献热力图)数据接口"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.models.diary import DiaryEntry
from app.models.post import Post

router = APIRouter(prefix="/contributions", tags=["发布记录"])


@router.get("", response_model=dict)
def contributions(
    source: str = Query("post", pattern="^(post|diary)$"),
    weeks: int = Query(52, ge=4, le=104),
    year: int | None = Query(None, ge=2000, le=2100, description="指定年份(返回整年数据)"),
    db: Session = Depends(get_db),
):
    """GitHub 风格贡献数据: 近 N 周或指定年份每天的发布数量"""
    if year:
        start = date(year, 1, 1)
        days = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
    else:
        start = date.today() - timedelta(weeks=weeks)
        days = (date.today() - start).days + 1
    count_map: dict[str, int] = {}
    if source == "post":
        rows = (
            db.query(func.date(Post.published_at), func.count(Post.id))
            .filter(
                Post.status == 2,
                Post.published_at >= datetime(start.year, start.month, start.day),
            )
            .group_by(func.date(Post.published_at))
            .all()
        )
    else:
        rows = (
            db.query(DiaryEntry.entry_date, func.count(DiaryEntry.id))
            .filter(DiaryEntry.entry_date >= start)
            .group_by(DiaryEntry.entry_date)
            .all()
        )
    for day, count in rows:
        count_map[str(day)] = int(count)
    items = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        items.append({"date": day.isoformat(), "count": count_map.get(day.isoformat(), 0)})
    return ok(items)
