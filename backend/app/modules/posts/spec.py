"""文章模块(核心, 不可禁用)

博客的主体内容. 虽然它可以被"禁用", 但禁用它之后整个站点没有任何内容可读,
因此按核心模块处理(locked)
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.posts.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="posts",
        name="文章",
        description="文章的创建, 编辑, 发布, 归档与导入导出",
        category="content",
        locked=True,
        permissions=(
            Perm.POST_CREATE,
            Perm.POST_EDIT,
            Perm.POST_PUBLISH,
            Perm.POST_DELETE,
            Perm.POST_MANAGE,
            Perm.DATA_EXPORT,
        ),
        routers=(router,),
        api_prefix="/api/v1/posts",
        tags=("core",),
    )
)
