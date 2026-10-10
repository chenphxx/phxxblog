"""看板娘模块(扩展, 纯前台)

后端没有接口: 运行时与模型都由前端自托管并按需加载, 因此只登记元数据;
禁用后前台的看板娘浮层与形象切换入口一起消失, 也不会再去下载模型资源

原先站点设置里有一个 show_kanbanniang 展示开关, 现在由模块开关直接承担: 关了模块,
浮层与形象切换入口一起消失; 访客自己存在浏览器里的开关与形象偏好不受影响
"""

from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="kanbanniang",
        name="看板娘",
        description="前台左下角的 Live2D 看板娘浮层与形象切换",
        category="extension",
        frontend_only=True,
        tags=("extension",),
    )
)
