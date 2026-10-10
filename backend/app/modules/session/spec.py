"""终端卡片模块(扩展, 纯前台)

首页的 session 终端卡片: whoami / 文章总数与最新一篇 / 一句一言. 整块可以下线,
原先由站点设置里的 show_session 控制

刻意不声明依赖 saying: 一言只是卡片里的一段输出, 关掉一言后卡片仍保留另外两段.
原先两者是"一言关了整张卡片一起消失", 那样把两个独立能力的生命周期绑在了一起
"""

from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="session",
        name="终端卡片",
        description="首页顶部的 session 终端卡片, 含个人简介, 文章统计与一言",
        category="extension",
        default_enabled=False,
        frontend_only=True,
        tags=("extension",),
    )
)
