"""程序员历史上的今天(扩展)

同样是第三方接口代理, 接口地址可配置
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.history.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="history",
        name="历史上的今天",
        description="首页的“程序员历史上的今天”卡片, 数据来自第三方接口",
        category="extension",
        routers=(router,),
        api_prefix="/api/v1/misc/history/programmer-today",
        settings=(
            ModuleSetting(
                key="api_url",
                name="接口地址",
                default="https://uapis.cn/api/v1/history/programmer/today",
                description="返回 { date, events } 的 JSON 接口, 留空表示不请求上游",
                kind="text",
            ),
        ),
        tags=("extension",),
    )
)
