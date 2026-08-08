"""访问统计接口: 埋点、总览、趋势、来源分析。"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.analytics import DailyStat, VisitLog
from app.models.comment import Comment
from app.models.diary import DiaryEntry
from app.models.post import Post, PostLike
from app.models.user import User
from app.schemas.common import Page
from app.services.geo import resolve_location
from app.services.stats import record_visit

router = APIRouter(prefix="/stats", tags=["统计"])


class TrackIn(BaseModel):
    """访问埋点请求。"""

    url: str | None = None
    post_id: int | None = None


@router.post("/track", response_model=dict)
def track(data: TrackIn, request: Request, db: Session = Depends(get_db)):
    """前台页面访问埋点(公开)。"""
    post = db.get(Post, data.post_id) if data.post_id else None
    record_visit(db, request=request, post=post, url=data.url)
    return ok(message="ok")


@router.get("/overview", response_model=dict)
def overview(
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """统计总览: 文章/访问量/评论/用户/点赞。"""
    total_views = db.query(func.sum(Post.views)).scalar() or 0
    return ok({
        "posts": db.query(func.count(Post.id)).scalar(),
        "published_posts": db.query(func.count(Post.id)).filter(Post.status == 2).scalar(),
        "views": int(total_views),
        "comments": db.query(func.count(Comment.id)).scalar(),
        "users": db.query(func.count(User.id)).scalar(),
        "likes": db.query(func.count(PostLike.id)).scalar(),
        "today_pv": (
            db.query(DailyStat.pv).filter(DailyStat.stat_date == date.today()).scalar() or 0
        ),
        "today_uv": (
            db.query(DailyStat.uv).filter(DailyStat.stat_date == date.today()).scalar() or 0
        ),
    })


@router.get("/trend", response_model=dict)
def trend(
    granularity: str = Query("day", pattern="^(day|month|year)$"),
    days: int = Query(14, ge=1, le=365),
    start_date: str | None = Query(None, description="自定义起始日期 YYYY-MM-DD(仅日粒度)"),
    end_date: str | None = Query(None, description="自定义结束日期 YYYY-MM-DD(仅日粒度)"),
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """访问趋势: 日(默认近两周, 可自定义区间)/月(近12月)/年(近6年) 聚合。"""
    rows = db.query(DailyStat).order_by(DailyStat.stat_date).all()
    stat_map = {row.stat_date: row for row in rows}
    result = []

    def point(label: str, stat: DailyStat | None) -> dict:
        return {
            "label": label,
            "pv": stat.pv if stat else 0,
            "uv": stat.uv if stat else 0,
            "post_views": stat.post_views if stat else 0,
        }

    if granularity == "day":
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        else:
            start = date.today() - timedelta(days=days - 1)
            end = date.today()
        total_days = (end - start).days + 1
        if total_days <= 0 or total_days > 366:
            raise HTTPException(status_code=400, detail="时间区间无效(1-366天)")
        for offset in range(total_days):
            day = start + timedelta(days=offset)
            result.append(point(day.isoformat(), stat_map.get(day)))
    elif granularity == "month":
        today = date.today()
        for i in range(11, -1, -1):
            year, month = today.year, today.month - i
            while month <= 0:
                month += 12
                year -= 1
            month_rows = [
                s for s in rows
                if s.stat_date.year == year and s.stat_date.month == month
            ]
            merged = DailyStat(stat_date=date(year, month, 1))
            merged.pv = sum(s.pv for s in month_rows)
            merged.uv = sum(s.uv for s in month_rows)
            merged.post_views = sum(s.post_views for s in month_rows)
            result.append(point(f"{year}-{month:02d}", merged))
    else:
        years = sorted({s.stat_date.year for s in rows})
        for year in years[-6:]:
            year_rows = [s for s in rows if s.stat_date.year == year]
            merged = DailyStat(stat_date=date(year, 1, 1))
            merged.pv = sum(s.pv for s in year_rows)
            merged.uv = sum(s.uv for s in year_rows)
            merged.post_views = sum(s.post_views for s in year_rows)
            result.append(point(str(year), merged))
    return ok(result)


@router.get("/visits", response_model=dict)
def visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    days: int | None = Query(None, ge=1, le=365, description="只看最近 N 天"),
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """访问明细(IP/省市区/设备/浏览器/系统/来源/时间)。"""
    query = db.query(VisitLog)
    if days:
        query = query.filter(VisitLog.visit_time >= datetime.now() - timedelta(days=days))
    total = query.count()
    items = (
        query.order_by(VisitLog.visit_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok(Page[dict](
        items=[{
            "id": v.id,
            "post_id": v.post_id,
            "post_title": v.post.title if v.post else None,
            "ip": v.ip,
            "location": resolve_location(v.ip) if v.ip else "",
            "browser": v.browser,
            "os": v.os,
            "device": v.device,
            "referer": v.referer,
            "url": v.url,
            "visit_time": v.visit_time.isoformat() if v.visit_time else None,
        } for v in items],
        total=total, page=page, page_size=page_size,
    ))


@router.get("/contributions", response_model=dict)
def contributions(
    source: str = Query("post", pattern="^(post|diary)$"),
    weeks: int = Query(52, ge=4, le=104),
    year: int | None = Query(None, ge=2000, le=2100, description="指定年份(返回整年数据)"),
    db: Session = Depends(get_db),
):
    """GitHub 风格贡献数据: 近 N 周或指定年份每天的发布数量。"""
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


@router.get("/sources", response_model=dict)
def sources(
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """访问来源/浏览器/设备/操作系统分析。"""

    def top(column, limit=10):
        return [
            {"name": name, "count": count}
            for name, count in db.query(column, func.count(VisitLog.id))
            .filter(column.isnot(None), column != "")
            .group_by(column)
            .order_by(func.count(VisitLog.id).desc())
            .limit(limit)
            .all()
        ]

    return ok({
        "browsers": top(VisitLog.browser),
        "os": top(VisitLog.os),
        "devices": top(VisitLog.device),
        "referers": [
            {"name": name, "count": count}
            for name, count in db.query(VisitLog.referer, func.count(VisitLog.id))
            .filter(VisitLog.referer.isnot(None), VisitLog.referer != "")
            .group_by(VisitLog.referer)
            .order_by(func.count(VisitLog.id).desc())
            .limit(10)
            .all()
        ],
    })
