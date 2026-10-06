"""模块管理模块(核心, 不可禁用)

这是"模块的模块": 提供模块清单, 启停与配置接口. 它自己必须始终可用, 否则关掉
某个模块后就再也打不开了

模块管理复用 setting:manage 权限: 它属于系统配置类操作, 单独再开一个权限码只会让
角色配置更碎
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.modules.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="modules",
        name="模块管理",
        description="查看系统中已注册的能力, 启用/禁用模块并维护模块自己的配置",
        category="core",
        locked=True,
        permissions=(Perm.SETTING_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/modules",
        tags=("core",),
    )
)
