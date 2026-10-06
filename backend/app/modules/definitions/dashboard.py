"""后台看板模块

聚合文章/评论/统计的概览数据. 依赖的模块被禁用时它仍可用, 只是对应卡片为空,
因此依赖链只标 posts 与 stats(数据来源)
"""

from app.api.v1.dashboard import router
from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="dashboard",
        name="后台看板",
        description="后台首页的数据概览: 文章/访问/评论/用户与最近动态",
        category="insight",
        depends_on=("posts",),
        permissions=(Perm.STATS_VIEW,),
        routers=(router,),
        api_prefix="/api/v1/dashboard",
        tags=("insight",),
    )
)
