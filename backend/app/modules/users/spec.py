"""用户与角色模块(核心, 不可禁用)

账号, 角色与权限是权限体系的载体: 禁用后没有任何办法把权限授予他人,
因此标记为 locked
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.registry import registry
from app.modules.users.router import router

SPEC = registry.register(
    ModuleSpec(
        id="users",
        name="用户与角色",
        description="账号, 角色与权限的维护",
        category="core",
        locked=True,
        permissions=(Perm.USER_MANAGE, Perm.ROLE_MANAGE),
        routers=(router,),
        api_prefix="/api/v1/users",
        tags=("core",),
    )
)
