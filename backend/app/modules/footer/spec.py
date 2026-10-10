"""页脚模块(扩展, 纯前台)

前台页脚: 版权文案与备案信息. 两块各自独立 - 只填备案也会渲染页脚, 版权留空则
不显示那一行; 页脚里什么都没有时整体不渲染, 整块可以下线

原先这些是站点设置里的 footer_text / beian_info(以及后来拆出去的 website_links),
现在归本模块. 备案信息是国内站点的可选项, 与页脚一起开关即可, 不再单独占一个模块
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="footer",
        name="页脚",
        description="前台页脚的版权文案与备案信息",
        category="extension",
        default_enabled=False,
        frontend_only=True,
        settings=(
            ModuleSetting(
                key="footer_text",
                name="版权信息",
                default="© {year} {site_name} · Vue3 + FastAPI",
                description="支持 {year} 与 {site_name} 占位符, 留空则不显示",
                kind="text",
                public=True,
            ),
            ModuleSetting(
                key="beian_info",
                name="备案信息",
                default="[]",
                description="显示在页脚, 图标列选填",
                kind="rows",
                columns=("name", "url", "icon"),
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
