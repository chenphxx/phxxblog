"""站内搜索模块

依赖文章模块: 没有文章就没有可搜索的内容
"""

from app.api.v1.search import router
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="search",
        name="站内搜索",
        description="按关键词检索文章标题与正文",
        category="content",
        depends_on=("posts",),
        routers=(router,),
        api_prefix="/api/v1/search",
        tags=("content",),
    )
)
