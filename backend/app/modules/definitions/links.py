"""外链预览模块(扩展)

为评论/正文里的外链生成预览卡片(标题, 描述, 缩略图), 需要访问外网,
不需要时可以整体关掉
"""

from app.api.v1.links import router
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="links",
        name="外链预览",
        description="抓取外链的标题/描述/缩略图, 生成链接预览卡片",
        category="extension",
        routers=(router,),
        api_prefix="/api/v1/links",
        tags=("extension",),
    )
)
