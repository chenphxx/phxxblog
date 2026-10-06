"""RSS 与站点地图模块(扩展)

挂在根路径(/rss.xml, /sitemap.xml)而不是 /api/v1 下, 需要 root_routes 标记
"""

from app.api.v1.rss import router
from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="rss",
        name="RSS 与站点地图",
        description="RSS 订阅源与 sitemap.xml, 供阅读器与搜索引擎抓取",
        category="extension",
        routers=(router,),
        root_routes=True,
        api_prefix="/rss.xml, /sitemap.xml",
        settings=(
            ModuleSetting(
                key="post_limit",
                name="RSS 文章条数",
                default="50",
                description="订阅源里最多包含多少篇最新文章",
                kind="int",
                minimum=1,
                maximum=200,
            ),
        ),
        tags=("extension",),
    )
)
