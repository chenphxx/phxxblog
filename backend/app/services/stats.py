"""访问统计服务: 记录访问明细并按日聚合。"""
from datetime import date, datetime

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.deps import get_client_ip
from app.models.analytics import DailyStat, VisitLog
from app.models.post import Post
from app.services.ua import parse_user_agent


def record_visit(
    db: Session,
    *,
    request: Request,
    post: Post | None = None,
    url: str | None = None,
) -> None:
    """记录一次访问: 写明细、累加 PV, 首次访客累加 UV, 文章访问累加阅读量。"""
    ip = get_client_ip(request)
    ua_info = parse_user_agent(request.headers.get("user-agent"))
    today = date.today()

    # 判断今日是否已有该 IP 的访问记录(用于 UV)
    is_new_uv = not db.query(VisitLog.id).filter(
        VisitLog.ip == ip,
        VisitLog.visit_time >= datetime(today.year, today.month, today.day),
    ).first()

    visit = VisitLog(
        post_id=post.id if post else None,
        ip=ip,
        user_agent=request.headers.get("user-agent", "")[:500],
        referer=request.headers.get("referer", "")[:500],
        url=url or (f"/posts/{post.slug}" if post else request.url.path),
        browser=ua_info["browser"],
        os=ua_info["os"],
        device=ua_info["device"],
    )
    db.add(visit)

    if post:
        post.views += 1

    # 聚合到当日统计
    stat = db.query(DailyStat).filter(DailyStat.stat_date == today).first()
    if stat is None:
        stat = DailyStat(stat_date=today)
        db.add(stat)
    stat.pv = (stat.pv or 0) + 1
    if is_new_uv:
        stat.uv = (stat.uv or 0) + 1
    if post:
        stat.post_views = (stat.post_views or 0) + 1

    db.commit()
