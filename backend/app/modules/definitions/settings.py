"""系统设置模块(核心, 不可禁用)

站点级配置(站点名/页脚/首页模块开关等)的读写入口, 也是后台"模块管理"权限所在,
关掉它等于失去所有配置能力
"""

from app.api.v1.settings import router
from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="settings",
        name="系统设置",
        description="站点名称, SEO, 首页展示开关, 页脚与链接等站点级配置",
        category="core",
        locked=True,
        permissions=(Perm.SETTING_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/settings",
        tags=("core",),
    )
)
