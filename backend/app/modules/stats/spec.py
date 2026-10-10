"""访问统计模块

包含访问埋点(/stats/track), 概览, 趋势与贡献热力图数据. 依赖文章模块:
统计的主体是文章访问量

首页的贡献热力图是本模块的一个展示面, 不是本模块本身 - 统计能力要开, 但未必想占
首页一整行, 所以单独留一个 show_on_home 配置(它原先叫站点设置里的 show_contributions)
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry
from app.modules.stats.router import router

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
        settings=(
            ModuleSetting(
                key="show_on_home",
                name="首页展示发布记录",
                default="1",
                description="首页底部的文章发布记录(贡献热力图), 关闭只影响首页展示",
                kind="bool",
                public=True,
            ),
        ),
        tags=("insight",),
    )
)
