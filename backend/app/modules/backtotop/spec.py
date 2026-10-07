"""回到顶部模块(扩展, 纯前台)

文章详情页右下角的胶囊按钮: 滚动超过阈值后出现, 胶囊内的横向填充表示正文阅读进度,
点击或回车平滑回到页面顶部

进度按正文元素的滚动比例计算(正文底部进入视口底部时为 100%), 由后端下发阈值与
"是否显示进度"两个配置; 位置固定右下角, 因此不提供位置配置
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="backtotop",
        name="回到顶部",
        description="文章页右下角的回到顶部按钮, 带正文阅读进度",
        category="extension",
        frontend_only=True,
        depends_on=("posts",),
        settings=(
            ModuleSetting(
                key="threshold_px",
                name="出现阈值(像素)",
                default="600",
                description="页面滚动超过该像素数后按钮才出现(0-2000)",
                kind="int",
                minimum=0,
                maximum=2000,
                public=True,
            ),
            ModuleSetting(
                key="show_progress",
                name="显示阅读进度",
                default="1",
                description="胶囊内是否用横向填充与百分比表示正文阅读进度",
                kind="bool",
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
