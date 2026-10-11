"""文章发布记录模块(扩展, 前台展示)

首页底部的发布记录(贡献热力图): 按周或年份聚合每天的发布数量; 日记页的同类热力图也用它

它原先挂在访问统计模块下(首页要不要展示由 stats 的 show_on_home 配置决定), 但这两件事
性质不同: 访问统计是只给管理员看的数据能力, 发布记录是前台展示 - 拆开之后各自有自己的
开关与可见范围, "统计"也不再是一个会出现在页面上的东西

展示位置是它自己的配置(系统设置里维护): 首页与日记页各一个开关, 模块开关只决定这项能力
在不在 - 两处都想关掉时应当直接禁用模块, 而不是把两个开关都关掉
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.contributions.router import router
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="contributions",
        name="文章发布记录",
        description="首页底部的发布记录(贡献热力图), 按周或年份聚合每天的发布数量",
        category="extension",
        default_enabled=False,
        depends_on=("posts",),
        routers=(router,),
        api_prefix="/api/v1/contributions",
        settings=(
            ModuleSetting(
                key="show_on_home",
                name="首页展示",
                default="1",
                description="首页底部的发布记录(贡献热力图)",
                kind="bool",
                public=True,
            ),
            ModuleSetting(
                key="show_on_diary",
                name="日记页展示",
                default="1",
                description="日记页顶部的发布记录热力图",
                kind="bool",
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
