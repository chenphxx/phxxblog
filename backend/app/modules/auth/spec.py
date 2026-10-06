"""认证与会话模块(核心, 不可禁用)

登录/注册/令牌刷新/当前用户是其余一切能力的前置条件: 关掉它后台也进不去,
因此标记为 locked
"""

from app.modules.auth.router import router
from app.modules.base import ModuleSpec
from app.modules.registry import registry

SPEC = registry.register(
    ModuleSpec(
        id="auth",
        name="认证与会话",
        description="登录, 注册, 令牌刷新与当前用户信息",
        category="core",
        locked=True,
        routers=(router,),
        api_prefix="/api/v1/auth",
        tags=("core",),
    )
)
