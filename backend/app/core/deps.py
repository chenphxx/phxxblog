"""FastAPI 依赖: 当前用户、权限校验、通用工具。"""

from typing import Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """获取客户端 IP。

    X-Forwarded-For 是**客户端可伪造**的请求头, 只有在请求确实经过我们自己配置的
    反向代理时才可信。以前无条件采信它, 导致:
      - 点赞去重(按 IP)可绕过 -> 刷 likes_count
      - 游客评论归属(按 IP)可伪造 -> 改别人的游客评论
      - UV 去重与操作日志里的 IP 全部失真
    现在只有 TCP 直连地址出现在 PHXXBLOG_TRUSTED_PROXIES 里时才采信 XFF,
    否则一律使用直连地址。反代部署时把它设为反代的内网地址即可。
    """
    peer = request.client.host if request.client else "unknown"
    trusted = settings.trusted_proxy_list
    if not trusted or peer not in trusted:
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return peer
    # XFF 形如 "client, proxy1, proxy2" —— 取最左边第一个非空值
    for candidate in forwarded.split(","):
        candidate = candidate.strip()
        if candidate:
            return candidate
    return peer


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization 头解析当前登录用户。"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="令牌类型错误")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效或已过期"
        ) from err
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.status == 0:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """可选登录: 有有效令牌则返回用户, 否则返回 None(游客)。"""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None
    if user is None or user.status == 0:
        return None
    return user


def require_permission(code: str) -> Callable:
    """权限依赖工厂: 要求当前用户拥有指定权限码。"""

    def checker(user: User = Depends(get_current_user)) -> User:
        if code not in user.permission_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {code}",
            )
        return user

    return checker
