"""网站链接模块(扩展, 纯前台)

首页右侧的"常用网站"卡片: 站长自己的快捷入口, 只有管理员看得到

原先它是页脚模块的一项配置(website_links), 现在拆成独立模块: "页脚上显示什么"与
"首页放哪些快捷入口"是两件事, 生命周期也不一样 - 只想改其中一个时才不必动另一个

可见范围可调, 默认"仅管理员": 配成公开后这张卡片对所有访客展示, 配成仅管理员时它的配置
也不会随公开接口下发给访客
"""

from app.modules.base import VISIBILITY_ADMIN, ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="sitelinks",
        name="网站链接",
        description="首页右侧的常用网站卡片(仅管理员可见)",
        category="extension",
        default_enabled=False,
        default_visibility=VISIBILITY_ADMIN,
        frontend_only=True,
        settings=(
            ModuleSetting(
                key="links",
                name="网站链接",
                default="[]",
                description="名称留空时自动取网站名",
                kind="rows",
                columns=("name", "url"),
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
