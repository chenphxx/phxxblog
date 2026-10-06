"""访问统计模块

包含访问埋点(/stats/track), 概览, 趋势与贡献热力图数据. 依赖文章模块:
统计的主体是文章访问量
"""

from app.api.v1.stats import router
from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="stats",
        name="访问统计",
        description="访问埋点, PV/UV 概览, 访问趋势与文章发布记录",
        category="insight",
        depends_on=("posts",),
        permissions=(Perm.STATS_VIEW,),
        routers=(router,),
        api_prefix="/api/v1/stats",
        tags=("insight",),
    )
)
