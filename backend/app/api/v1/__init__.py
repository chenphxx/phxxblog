"""v1 路由汇总: 按模块注册表装配

这里不再逐个 include 路由, 而是遍历注册表:
  - 锁定模块(认证/用户/设置/模块/分类标签/文章)一定可用, 不加模块依赖, 少一次查询
  - 其余模块统一挂 require_module 依赖, 被禁用时该模块的全部接口返回 404
  - 挂在根路径的模块(如 RSS/Sitemap)由 main.py 装配, 这里跳过
"""

from fastapi import APIRouter, Depends

from app.modules import build_registry
from app.modules.base import ModuleSpec
from app.modules.deps import require_module

# 导入定义清单并校验(幂等): 下面的装配与接口文档都依赖它
registry = build_registry()

api_router = APIRouter(prefix="/api/v1")

for spec in registry.all():
    if spec.root_routes or not spec.routers:
        continue
    dependencies = [] if spec.locked else [Depends(require_module(spec.id))]
    for module_router in spec.routers:
        api_router.include_router(module_router, dependencies=dependencies)


def root_module_routers() -> list[tuple[ModuleSpec, list]]:
    """挂在根路径(非 /api/v1)的模块路由

    @return [(模块元数据, 依赖列表)] 供 main.py 逐个 include, 依赖由调用方按 locked 组装
    """
    return [
        (spec, list(spec.routers)) for spec in registry.all() if spec.root_routes and spec.routers
    ]
