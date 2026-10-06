"""评论模块

评论接口的路径挂在文章下(/api/v1/posts/{id}/comments), 但模块归属由 router 决定,
因此禁用评论只影响评论接口, 文章本身照常工作
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.comments.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="comments",
        name="评论",
        description="文章评论与回复, 含审核, 批量管理与回收站",
        category="content",
        depends_on=("posts",),
        permissions=(Perm.COMMENT_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/posts/{id}/comments",
        tags=("content",),
    )
)
