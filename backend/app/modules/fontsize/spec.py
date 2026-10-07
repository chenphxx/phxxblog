"""正文字号模块(扩展, 纯前台)

文章详情页的正文可以按档位调整字号, 访客的选择存在浏览器本地(见
frontend/src/utils/readingFont.ts 的 blog_reading_font_size)

档位的像素表固定在前端(5 档, 中间档等于当前默认观感), 后台只配置默认档与允许范围:
这样调整配置不会让老访客已有的偏好落到未定义的像素值上, 越界的偏好在读取时夹取
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="fontsize",
        name="正文字号",
        description="文章正文可按档位调整字号, 偏好记在访客浏览器本地",
        category="extension",
        frontend_only=True,
        depends_on=("posts",),
        settings=(
            ModuleSetting(
                key="default_step",
                name="默认档位",
                default="3",
                description="访客首次进入文章页时使用的档位(1-5, 3 与当前默认观感一致)",
                kind="int",
                minimum=1,
                maximum=5,
                public=True,
            ),
            ModuleSetting(
                key="min_step",
                name="最小档位",
                default="1",
                description="允许访客调到的最小档位(1-5)",
                kind="int",
                minimum=1,
                maximum=5,
                public=True,
            ),
            ModuleSetting(
                key="max_step",
                name="最大档位",
                default="5",
                description="允许访客调到的最大档位(1-5)",
                kind="int",
                minimum=1,
                maximum=5,
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
