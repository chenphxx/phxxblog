"""媒体库模块

上传文件的存储与检索. 单文件上传上限仍在"系统设置 - 上传"里(跟随环境变量),
属于站点级配置, 不重复搬进模块
"""

from app.core.permissions import Perm
from app.modules.base import ModuleSpec
from app.modules.media.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="media",
        name="媒体库",
        description="图片/音视频/附件的上传, 检索与预览",
        category="content",
        permissions=(Perm.MEDIA_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/media",
        tags=("content",),
    )
)
