"""模块相关的 FastAPI 依赖"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.permissions import Perm
from app.models.user import User
from app.modules.base import VISIBILITY_PUBLIC
from app.modules.state import effective_enabled, module_visibility


def require_module(module_id: str) -> Callable:
    """模块依赖工厂: 模块未启用时接口按"不存在"处理

    为什么用依赖而不是"启动时只装配启用的模块":
      - 后台把模块关掉后要立刻生效, 不能要求重启服务;
      - 挂在 include_router 上, 一条依赖覆盖该模块的全部路由, 不必逐个接口加判断;
      - 返回 404 而不是 403: 能力整体不存在, 语义上就是"没有这个接口"

    get_db 与路由自身的 Depends(get_db) 由 FastAPI 缓存为同一个会话, 不会多开连接

    @param module_id: 模块 id
    @return 可直接传给 include_router 的依赖函数
    """

    def checker(db: Session = Depends(get_db)) -> None:
        if not effective_enabled(db, module_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"模块未启用: {module_id}"
            )

    return checker


def require_module_visible(module_id: str) -> Callable:
    """模块可见范围依赖工厂: 配成"仅管理员"时, 访客调不到该模块的接口

    与 require_module 的分工: 那个回答"这个能力在不在"(不在返回 404), 这个回答
    "你能不能用它"(未登录 401, 已登录但无权限 403)

    管理员按站点管理权限(setting:manage)判定, 与 /docs 和受控静态资源同一套做法:
    项目约定不判断角色名, 因为角色 code 可以被后台改名

    @param module_id: 模块 id
    @return 可直接传给 include_router 的依赖函数
    """

    def checker(
        user: User | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ) -> None:
        if module_visibility(db, module_id) == VISIBILITY_PUBLIC:
            return
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="该功能仅管理员可用"
            )
        if Perm.SETTING_MANAGE not in user.permission_codes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该功能仅管理员可用")

    return checker


def permission_or_module_public(code: str, module_id: str) -> Callable:
    """宽松版权限依赖: 有权限码, 或者该模块可见范围是公开, 就放行(给读取接口用)

    日记与更新日志默认只给管理员用, 配成公开后访客也该能读 - 这类能力用这个依赖:
    写操作仍然走严格的 require_permission, 这里只放宽"看"

    模块可见范围为 public 时允许匿名(返回 None); 否则未登录 401, 已登录但无权限 403

    @param code: 权限码
    @param module_id: 模块 id(可见范围从它读)
    @return 可直接用于 Depends 的依赖函数, 返回当前用户(游客为 None)
    """

    def checker(
        user: User | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ) -> User | None:
        if module_visibility(db, module_id) == VISIBILITY_PUBLIC:
            return user
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
        if code not in user.permission_codes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"缺少权限: {code}")
        return user

    return checker
