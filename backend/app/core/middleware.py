"""自定义中间件: 限制 API 文档与静态资源仅管理员可访问。"""
from pathlib import PurePosixPath
from typing import Awaitable, Callable

import jwt
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.core.database import SessionLocal
from app.core.permissions import Perm
from app.core.security import decode_token
from app.models.user import User
from app.services.upload import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS

# 鉴权 cookie 名称(与前端 utils/docToken.ts 保持一致)。
# 名字里的 doc 来自它最初的用途(/docs), 现在静态资源也复用它: 改名字会让已登录
# 用户的 cookie 立即失效, 且必须前后端同时发布, 收益却只是名字更贴切。
DOC_TOKEN_COOKIE = "phxxblog_doc_token"

# 需要保护的文档路径: Swagger UI / ReDoc 页面、OpenAPI schema 与 OAuth 回调页
DOC_PATHS = {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}

# 静态资源里匿名可访问的扩展名: 前台正文、站点图标与头像引用的都是这类文件。
# 直接复用上传白名单的图片/音视频子集, 避免两处白名单各写一份后逐渐漂移。
PUBLIC_ASSET_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS

# 静态资源里无论扩展名都只给管理员看的路径前缀。
# WordPress 迁移的原始导出(WXR/XML、媒体库导出 zip、个人信息导出)只是导入来源,
# 前台从不引用, 没有匿名下载的必要。
PROTECTED_ASSET_PREFIXES = ("/assets/wordpress/",)


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


def _authorize_admin(request: Request, forbidden_message: str) -> JSONResponse | None:
    """校验请求携带的令牌是否属于有站点管理权限的账号。

    令牌来源: `Authorization: Bearer <access_token>` 或 cookie `phxxblog_doc_token`
    (浏览器直接打开页面/加载图片时带不上请求头, 只能靠 cookie)。

    @param request: 当前请求。
    @param forbidden_message: 已登录但无权限时返回的提示文案。
    @return 通过校验返回 None, 否则返回可直接下发的 401/403 响应。
    """
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
        if Perm.SETTING_MANAGE not in user.permission_codes:
            return _error_response(status.HTTP_403_FORBIDDEN, forbidden_message)
    finally:
        db.close()

    return None


def asset_requires_admin(path: str) -> bool:
    """判断 `/assets` 下的某个资源是否需要管理员身份。

    放行范围只有"浏览器会直接渲染的媒体"(图片/音视频), 因为:
      - 前台文章正文、站点图标与头像都指向 `/assets/uploads/**`, 必须匿名可访问;
      - 文档/压缩包/表格等附件不参与渲染, 匿名下载没有必要性;
      - `PROTECTED_ASSET_PREFIXES` 下的迁移导出整体不放行。
    注意 `/assets/uploads/wordpress/**` 里的图片是文章正文在用的, 不能整目录锁掉。

    @param path: 请求路径(URL path, 不含 query)。
    @return 需要管理员身份返回 True。
    """
    if path.startswith(PROTECTED_ASSET_PREFIXES):
        return True
    return PurePosixPath(path).suffix.lower() not in PUBLIC_ASSET_EXTS


async def restrict_assets_to_admin(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """仅允许管理员访问 `/assets` 下的非公开文件。

    公开的媒体(图片/音视频)照旧匿名可访问, 其余一律走与 /docs 相同的鉴权:
    未登录 401, 已登录但无 `setting:manage` 权限 403。
    """
    path = request.url.path
    if not path.startswith("/assets/") or not asset_requires_admin(path):
        return await call_next(request)

    error = _authorize_admin(request, "无访问该静态资源的权限")
    if error is not None:
        return error
    return await call_next(request)


async def restrict_docs_to_admin(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """仅允许拥有 SETTING_MANAGE 权限的用户访问 /docs、/redoc、/openapi.json。

    令牌来源: `Authorization: Bearer <access_token>` 或 cookie `phxxblog_doc_token`。
    未登录返回 401, 已登录但无权限返回 403。

    权限判断用权限码而非角色名: 角色 code 可被后台修改, 用 `"admin" in role_codes`
    会在改名后静默放行或误拦。
    """
    # 归一化结尾斜杠(/docs/ 与 /docs 等价)
    path = request.url.path
    if path != "/":
        path = path.rstrip("/")
    if path not in DOC_PATHS:
        return await call_next(request)

    error = _authorize_admin(request, "无访问 API 文档的权限")
    if error is not None:
        return error
    return await call_next(request)
