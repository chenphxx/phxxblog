"""看板娘模块(扩展, 纯前台)

后端没有接口: 运行时与模型都由前端自托管并按需加载, 因此只登记元数据;
禁用后前台的看板娘浮层与形象切换入口一起消失, 也不会再去下载模型资源

注意: 站点设置里的 show_kanbanniang 决定"默认要不要展示", 与这里的"能力是否启用"
是两个层级 - 模块被禁用时该设置不再生效
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
