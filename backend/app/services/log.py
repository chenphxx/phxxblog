"""操作日志服务。"""
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.deps import get_client_ip
from app.models.log import OperationLog
from app.models.user import User


def write_operation_log(
    db: Session,
    *,
    request: Request,
    user: User | None,
    module: str,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: dict | None = None,
) -> OperationLog:
    """写入一条操作日志。"""
    log = OperationLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        module=module,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip=get_client_ip(request),
    )
    db.add(log)
    db.commit()
    return log
