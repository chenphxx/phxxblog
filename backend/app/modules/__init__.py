"""模块体系

对外只暴露两件事:
  - registry  模块注册表(登记与查询)
  - build_registry()  把全部模块定义装载进注册表并做一致性校验(幂等)

应用启动路径(app/main.py 与 app/api/v1/__init__.py)都会调用 build_registry(),
其余代码只管用 registry / state / deps, 不需要关心装载顺序
"""

from app.modules.registry import ModuleRegistry, registry

__all__ = ["ModuleRegistry", "registry", "build_registry"]

_built = False


def build_registry() -> ModuleRegistry:
    """装载全部模块定义并校验(重复调用是安全的)

    @return 已装载完成的注册表
    @throws ValueError 模块定义存在冲突(见 ModuleRegistry.register / validate)
    """
    global _built
    if _built:
        return registry
    # 导入定义清单会触发各模块的 register(); 必须在校验之前完成
    from app.modules import definitions  # noqa: F401

    registry.validate()
    _built = True
    return registry
