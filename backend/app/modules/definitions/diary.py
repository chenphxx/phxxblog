"""日记模块(扩展)

与文章分开的私人记录, 只有管理员可见. 属于"可以整体下线"的扩展能力
"""

from app.api.v1.diaries import router
from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="diary",
        name="日记",
        description="私人日记的撰写, 检索与导入导出",
        category="extension",
        permissions=(Perm.DIARY_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/diaries",
        tags=("extension",),
    )
)
