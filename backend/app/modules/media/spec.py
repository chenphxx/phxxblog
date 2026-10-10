"""媒体库模块

上传文件的存储与检索. 单文件上传上限仍在"系统设置 - 上传"里(跟随环境变量),
属于站点级配置, 不重复搬进模块

可见范围固定为"仅管理员"(管理后台自身的能力, 后台不提供调整入口): 管理媒体需要
media:manage, 而项目里只有管理员角色持有它(作者只能写文章), 因此访客连媒体接口都调不到,
与一直以来的实际行为一致
"""

from app.core.permissions import Perm
from app.modules.base import VISIBILITY_ADMIN, ModuleSpec
from app.modules.media.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="media",
        name="媒体库",
        description="图片/音视频/附件的上传, 检索与预览",
        category="content",
        default_visibility=VISIBILITY_ADMIN,
        visibility_fixed=True,
        permissions=(Perm.MEDIA_MANAGE,),
        routers=(router,),
        api_prefix="/api/v1/media",
        tags=("content",),
    )
)
