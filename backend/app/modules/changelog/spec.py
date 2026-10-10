"""更新日志模块(扩展)

把仓库根目录的 CHANGELOG.md 读出来给前台展示, 并允许后台直接编辑

可见范围可调, 默认"仅管理员": 配成公开后访客也能读更新日志, 编辑仍然要求 changelog:manage
"""

from app.core.permissions import Perm
from app.modules.base import VISIBILITY_ADMIN, ModuleSpec
from app.modules.changelog.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="changelog",
        name="更新日志",
        description="站点更新日志的展示与在线编辑(读写仓库根目录的 CHANGELOG.md)",
        category="extension",
        default_visibility=VISIBILITY_ADMIN,
        permissions=(Perm.CHANGELOG_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/misc/changelog",
        tags=("extension",),
    )
)
