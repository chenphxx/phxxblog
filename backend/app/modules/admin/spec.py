"""管理后台模块(核心, 不可禁用, 仅管理员可见)

后台外壳本身: 侧栏菜单, 页面框架与"个人资料"页. 它没有自己的接口 - 各个管理接口
归属各自的模块(文章管理属 posts, 评论属 comments …), 因此这里 frontend_only=True

之所以仍然登记成模块: 后台是"启用了哪些能力"的展示与操作入口, 关掉它等于失去了
所有管理能力, 所以它必须是核心模块并出现在模块清单里, 而不是游离在注册表之外
"""

from app.modules.base import VISIBILITY_ADMIN, ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="admin",
        name="管理后台",
        description="后台的页面框架, 侧栏菜单与个人资料页",
        category="core",
        locked=True,
        default_visibility=VISIBILITY_ADMIN,
        visibility_fixed=True,
        frontend_only=True,
        tags=("core",),
    )
)
