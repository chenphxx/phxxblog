"""程序员历史上的今天(扩展)

同样是第三方接口代理, 接口地址可配置
"""

from app.api.v1.history import router
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="history",
        name="历史上的今天",
        description="首页的“程序员历史上的今天”卡片, 数据来自第三方接口",
        category="extension",
        routers=(router,),
        api_prefix="/api/v1/misc/history/programmer-today",
        tags=("extension",),
    )
)
