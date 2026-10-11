"""访问统计模块(数据, 仅管理员)

访问概览, 访问趋势, 访问明细与来源分布: 只给管理员看的数据能力

可见范围固定为"仅管理员": 这些数字不该对访客开放, 而它也不需要出现在前台任何位置
采集(访问埋点)与展示(文章发布记录)是另外两件事, 已拆成 tracking 与 contributions 模块
"""

from app.core.permissions import Perm
from app.modules.base import VISIBILITY_ADMIN, ModuleSpec
from app.modules.registry import registry
from app.modules.stats.router import router

SPEC = registry.register(
    ModuleSpec(
        id="stats",
        name="访问统计",
        description="访问概览(PV/UV), 访问趋势, 访问明细与来源分布",
        category="insight",
        default_visibility=VISIBILITY_ADMIN,
        visibility_fixed=True,
        depends_on=("posts",),
        permissions=(Perm.STATS_VIEW,),
        routers=(router,),
        api_prefix="/api/v1/stats",
        tags=("insight",),
    )
)
