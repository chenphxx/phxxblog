"""操作日志模块

记录后台的关键写操作(谁在什么时候改了什么). 依赖文章与评论是为了拿到可读的资源名,
禁用它不影响业务本身

可见范围固定为"仅管理员"(管理后台自身的能力, 后台不提供调整入口): 看日志需要 log:view,
项目里只有管理员角色持有它
"""

from app.core.permissions import Perm
from app.modules.base import VISIBILITY_ADMIN, ModuleSpec
from app.modules.logs.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="logs",
        name="操作日志",
        description="记录并检索后台的写操作(操作人, 模块, 动作, 详情, IP)",
        category="insight",
        default_visibility=VISIBILITY_ADMIN,
        visibility_fixed=True,
        permissions=(Perm.LOG_VIEW,),
        routers=(router,),
        api_prefix="/api/v1/logs",
        tags=("insight",),
    )
)
