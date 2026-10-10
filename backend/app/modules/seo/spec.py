"""SEO 模块(扩展, 纯前台)

启用后向前台页面注入 meta keywords(取本模块配置)与 meta description(读站点设置里的
site_desc). 站点描述留在系统设置是因为 RSS 模块也直接从 settings 表读它当订阅摘要,
属于各模块共享的站点身份信息, 不适合跟着本模块走

关键词原先是站点设置里的 site_keywords, 但前台一直没有输出位置 - 收进模块后
"启用才注入"才说得通
"""

from app.modules.base import ModuleSetting, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="seo",
        name="SEO",
        description="向前台页面注入 meta keywords 与 meta description",
        category="extension",
        default_enabled=False,
        frontend_only=True,
        settings=(
            ModuleSetting(
                key="keywords",
                name="SEO 关键词",
                default="blog, 技术, 分享",
                description="写入页面的 meta keywords, 多个关键词用英文逗号分隔",
                kind="text",
                public=True,
            ),
        ),
        tags=("extension",),
    )
)
