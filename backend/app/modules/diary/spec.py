"""日记模块(扩展)

与文章分开的私人记录, 默认只有管理员可见. 属于"可以整体下线"的扩展能力

可见范围可调, 默认"仅管理员": 配成公开后访客也能读日记(读取接口放行"有权限或模块公开"),
写与导入导出仍然要求 diary:manage 前台的日记入口由模块开关与可见范围共同决定
"""

from app.core.permissions import Perm
from app.modules.base import VISIBILITY_ADMIN, ModuleSpec
from app.modules.diary.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="diary",
        name="日记",
        description="私人日记的撰写, 检索与导入导出",
        category="extension",
        default_visibility=VISIBILITY_ADMIN,
        permissions=(Perm.DIARY_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/diaries",
        tags=("extension",),
    )
)
