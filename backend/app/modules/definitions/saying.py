"""一言模块(扩展)

代理第三方语录接口, 避免前端跨域. 上游接口地址与"每天只刷一次"都可以在
后台"模块管理"里改, 因此换数据源不需要改代码
"""

from app.api.v1.saying import router
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="saying",
        name="一言",
        description="首页终端卡片里的随机语录, 每天只向上游请求一次",
        category="extension",
        routers=(router,),
        api_prefix="/api/v1/misc/saying",
        tags=("extension",),
    )
)
