"""代码块字体模块(扩展, 纯前台)

文章详情页的代码块(行内代码与围栏代码块)使用自托管的 Cascadia Code

为什么需要一个额外的外层类: Vditor 自带的 `.vditor-reset pre > code`(特异性 0,1,2)
与 `.vditor-reset code:not(.hljs):not(.highlight-chroma)`(0,3,1) 都高于项目里的字体
覆盖规则(0,1,1), 只加一条同特异性的规则压不住它, 文章代码块会退回 Vditor 的
mononoki/Consolas 字体栈. 因此启用本模块时由 MarkdownView 的外层容器多带一层
`.reading-code-font` 类, 由 frontend/src/styles/theme.css 里的对应规则真正生效

禁用后代码块回到 Vditor 的默认字体栈, 其余排版不受影响
"""

from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="codefont",
        name="代码块字体",
        description="文章代码块使用自托管的 Cascadia Code, 与写作时的观感一致",
        category="extension",
        frontend_only=True,
        depends_on=("posts",),
        tags=("extension",),
    )
)
