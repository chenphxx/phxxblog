"""主页 README 模块(扩展, 纯前台)

首页的"关于"区块: 一段 GitHub 风格的 Markdown 自我介绍, 整块可以下线

内容与开关原先分别是站点设置里的 site_readme 与 show_readme, 都迁到这里: 系统设置
只保留"站点身份"(站点名/图标/简介), 某个区块的内容与开关归它自己的模块
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="about",
        name="主页简介",
        description="首页的关于区块, 用 Markdown 写一段自我介绍",
        category="extension",
        default_enabled=False,
        frontend_only=True,
        settings=(
            ModuleSetting(
                key="content",
                name="README 内容",
                default="",
                description="GitHub 风格的 Markdown, 留空则首页不渲染关于区块",
                kind="long_text",
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
