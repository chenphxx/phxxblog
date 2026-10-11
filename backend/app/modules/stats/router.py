"""访问统计接口: 总览, 趋势, 访问明细与来源分析(只给管理员看的数据能力)

访问埋点与发布记录已拆成独立模块(见 app/modules/tracking 与 app/modules/contributions):
它们要出现在前台或必须对访客开放, 与本模块的"仅管理员"可见范围正好相反
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.analytics import DailyStat, VisitLog
from app.models.comment import Comment
from app.models.post import Post, PostLike
from app.models.user import User
from app.schemas.common import Page
from app.services.geo import resolve_location

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/overview", response_model=dict)
def overview(
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """统计总览: 文章/访问量/评论/用户/点赞"""
    total_views = db.query(func.sum(Post.views)).scalar() or 0
    return ok(
        {
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
        }
    )


@router.get("/trend", response_model=dict)
def trend(
    granularity: str = Query("day", pattern="^(day|month|year)$"),
    days: int = Query(14, ge=1, le=365),
    start_date: str | None = Query(None, description="自定义起始日期 YYYY-MM-DD(仅日粒度)"),
    end_date: str | None = Query(None, description="自定义结束日期 YYYY-MM-DD(仅日粒度)"),
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """访问趋势: 日(默认近两周, 可自定义区间)/月(近12月)/年(近6年) 聚合"""
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
                s for s in rows if s.stat_date.year == year and s.stat_date.month == month
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
    """访问明细(IP/省市区/设备/浏览器/系统/来源/时间)"""
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
    return ok(
        Page[dict](
            items=[
                {
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
                }
                for v in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/sources", response_model=dict)
def sources(
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """访问来源/浏览器/设备/操作系统分析"""

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

    return ok(
        {
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
        }
    )
