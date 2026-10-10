"""个人资料卡模块(扩展, 纯前台)

首页个人资料卡上的社交链接与技术标签. 个人简介仍留在站点设置里(侧栏品牌区与终端
卡片也在读它), 这里只管"链接"与"标签"这两个纯展示项

原先这两项是站点设置里的 social_links 与 tech_tags, 现在归本模块
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="profile",
        name="个人资料卡",
        description="首页个人资料卡上的社交链接与技术标签",
        category="extension",
        default_enabled=False,
        frontend_only=True,
        settings=(
            ModuleSetting(
                key="social_links",
                name="社交链接",
                default="[]",
                description="显示在首页个人资料卡, 如 GitHub",
                kind="rows",
                columns=("name", "url"),
                public=True,
            ),
            ModuleSetting(
                key="tech_tags",
                name="技术标签",
                default="[]",
                description="显示在首页个人资料卡, 每行一个标签",
                kind="rows",
                columns=("name",),
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
