"""访问埋点接口"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.models.post import Post
from app.services.stats import record_visit

router = APIRouter(prefix="/tracking", tags=["统计"])


class TrackIn(BaseModel):
    """访问埋点请求"""

    url: str | None = None
    post_id: int | None = None


@router.post("/track", response_model=dict)
def track(data: TrackIn, request: Request, db: Session = Depends(get_db)):
    """前台页面访问埋点: 记录访问明细并累加当日 PV/UV

    对访客无感, 因此本模块保持公开: 配成"仅管理员"时只有管理员的访问会被记录
    """
    post = db.get(Post, data.post_id) if data.post_id else None
    record_visit(db, request=request, post=post, url=data.url)
    return ok(message="ok")
