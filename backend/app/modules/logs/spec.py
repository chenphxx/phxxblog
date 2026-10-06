"""操作日志模块

记录后台的关键写操作(谁在什么时候改了什么). 依赖文章与评论是为了拿到可读的资源名,
禁用它不影响业务本身
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.logs.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="logs",
        name="操作日志",
        description="记录并检索后台的写操作(操作人, 模块, 动作, 详情, IP)",
        category="insight",
        permissions=(Perm.LOG_VIEW,),
        routers=(router,),
        api_prefix="/api/v1/logs",
        tags=("insight",),
    )
)
