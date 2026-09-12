"""自定义中间件: 限制 API 文档相关路径仅管理员可访问。"""
from typing import Awaitable, Callable

import jwt
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User

# 文档鉴权 cookie 名称(与前端 utils/docToken.ts 保持一致)
DOC_TOKEN_COOKIE = "phxxblog_doc_token"

# 需要保护的文档路径: Swagger UI / ReDoc 页面、OpenAPI schema 与 OAuth 回调页
DOC_PATHS = {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}


def _extract_doc_token(request: Request) -> str | None:
    """依次从 Authorization 头与文档 cookie 中取出访问令牌。"""
    scheme, _, param = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer" and param.strip():
        return param.strip()
    return request.cookies.get(DOC_TOKEN_COOKIE)


def _error_response(status_code: int, message: str) -> JSONResponse:
    """保持与全局异常处理一致的 { code, message, data } 结构。"""
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None},
    )


async def restrict_docs_to_admin(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """仅允许 admin 角色访问 /docs、/redoc、/openapi.json。

    令牌来源: `Authorization: Bearer <access_token>` 或 cookie `phxxblog_doc_token`。
    未登录返回 401, 已登录但非管理员返回 403。
    """
    # 归一化结尾斜杠(/docs/ 与 /docs 等价)
    path = request.url.path
    if path != "/":
        path = path.rstrip("/")
    if path not in DOC_PATHS:
        return await call_next(request)

    token = _extract_doc_token(request)
    if not token:
        return _error_response(status.HTTP_401_UNAUTHORIZED, "未登录")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("令牌类型错误")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return _error_response(status.HTTP_401_UNAUTHORIZED, "令牌无效或已过期")

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if user is None:
            return _error_response(status.HTTP_401_UNAUTHORIZED, "用户不存在")
        if user.status == 0:
            return _error_response(status.HTTP_403_FORBIDDEN, "账号已被禁用")
        if "admin" not in user.role_codes:
            return _error_response(status.HTTP_403_FORBIDDEN, "仅管理员可访问")
    finally:
        db.close()

    return await call_next(request)
