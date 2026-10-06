"""分类与标签模块(核心, 不可禁用)

文章必须归属至少一个分类, 分类/标签接口也被前台列表与搜索复用,
禁用会让文章能力残缺, 因此标记为 locked
"""

from app.api.v1 import categories, tags
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="taxonomy",
        name="分类与标签",
        description="分类与标签的维护, 供文章归类与前台筛选使用",
        category="core",
        locked=True,
        routers=(categories.router, tags.router),
        api_prefix="/api/v1/categories, /api/v1/tags",
        tags=("core",),
    )
)
