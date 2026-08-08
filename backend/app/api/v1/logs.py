"""操作日志接口。"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.log import OperationLog
from app.models.user import User
from app.schemas.common import Page
from app.services.geo import resolve_location

router = APIRouter(prefix="/logs", tags=["操作日志"])


@router.get("", response_model=dict)
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int | None = None,
    module: str | None = None,
    action: str | None = None,
    _: User = Depends(require_permission(Perm.LOG_VIEW)),
    db: Session = Depends(get_db),
):
    """操作日志列表(可按用户/模块/动作筛选)。"""
    query = db.query(OperationLog)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if module:
        query = query.filter(OperationLog.module == module)
    if action:
        query = query.filter(OperationLog.action == action)
    total = query.count()
    items = (
        query.order_by(OperationLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "module": log.module,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "ip": log.ip,
            "location": resolve_location(log.ip) if log.ip else "",
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in items
    ]
    return ok(Page[dict](items=result, total=total, page=page, page_size=page_size))
