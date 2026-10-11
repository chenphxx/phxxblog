"""访问埋点模块(数据)

记录访客的访问明细并累加当日 PV/UV: 前台每次进入页面时上报一次, 对访客无感

为什么从"访问统计"里拆出来: 埋点必须对所有访客可调用(否则访客的访问根本不会被记录),
而访问统计的数据只给管理员看 - 两者的"可见范围"天然相反, 合成一个模块时怎么配都是错的
拆开之后本模块保持公开(想停止记录访问时直接关掉它), 访问统计则固定为仅管理员
"""

from app.modules.base import ModuleSpec
from app.modules.registry import registry
from app.modules.tracking.router import router

SPEC = registry.register(
    ModuleSpec(
        id="tracking",
        name="访问埋点",
        description="记录访客的访问明细与按日 PV/UV, 供访问统计使用",
        category="insight",
        routers=(router,),
        api_prefix="/api/v1/tracking",
        tags=("insight",),
    )
)
