"""互联网纪事模块

记录作者在互联网世界遇见的人物与事件, 作为可整体启停的独立内容模块.
访客读取默认公开, 新增与编辑复用文章管理权限(post:manage).
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.chronicles.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="chronicles",
        name="互联网纪事",
        description="以杂志网格记录令人印象深刻的人物与事件",
        category="content",
        permissions=(Perm.POST_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/chronicles",
        tags=("content",),
    )
)
