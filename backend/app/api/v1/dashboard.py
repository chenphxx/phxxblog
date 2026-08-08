"""后台 Dashboard 汇总接口。"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.analytics import DailyStat
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentOut
from app.schemas.post import PostListItem

router = APIRouter(prefix="/dashboard", tags=["看板"])


@router.get("", response_model=dict)
def dashboard(
    _: User = Depends(require_permission(Perm.STATS_VIEW)),
    db: Session = Depends(get_db),
):
    """Dashboard 数据: 总览 + 14 天趋势 + 最新文章/评论。"""
    start = date.today() - timedelta(days=13)
    trend_rows = (
        db.query(DailyStat)
        .filter(DailyStat.stat_date >= start)
        .order_by(DailyStat.stat_date)
        .all()
    )
    stat_map = {row.stat_date: row for row in trend_rows}
    trend = [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "pv": stat_map.get(start + timedelta(days=i)).pv if stat_map.get(start + timedelta(days=i)) else 0,
            "uv": stat_map.get(start + timedelta(days=i)).uv if stat_map.get(start + timedelta(days=i)) else 0,
        }
        for i in range(14)
    ]
    recent_posts = db.query(Post).order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = db.query(Comment).order_by(Comment.created_at.desc()).limit(5).all()
    return ok({
        "overview": {
            "posts": db.query(func.count(Post.id)).scalar(),
            "views": int(db.query(func.sum(Post.views)).scalar() or 0),
            "comments": db.query(func.count(Comment.id)).scalar(),
            "users": db.query(func.count(User.id)).scalar(),
        },
        "trend": trend,
        "recent_posts": [PostListItem.model_validate(p) for p in recent_posts],
        "recent_comments": [CommentOut.model_validate(c) for c in recent_comments],
    })
