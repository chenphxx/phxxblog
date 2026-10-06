"""模块体系

目录约定: 一个模块 = 一个包 app/modules/<模块 id>/
  __init__.py   导入即注册(只做 `from .spec import SPEC`)
  spec.py       模块元数据: id, 名称, 分类, 依赖, 权限码, 配置项, router
  router.py     模块的接口实现(接口多的模块可以再拆文件, 由 spec 汇总成 routers)

对外只暴露两件事:
  - registry  模块注册表(登记与查询)
  - build_registry()  把全部模块装载进注册表并做一致性校验(幂等)

应用启动路径(app/main.py 与 app/modules/router.py)都会调用 build_registry(),
其余代码只管用 registry / state / deps, 不需要关心装载顺序

这里显式列出模块而不是扫描目录: 注册顺序可控, 出错时也能一眼看出是哪个包贡献了元数据
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
    # 导入模块包会触发各自 spec 里的 register(); 必须在校验之前完成
    # 核心 -> 内容 -> 数据 -> 扩展, 与后台"模块管理"的分组顺序一致
    from app.modules import (  # noqa: F401
        auth,
        changelog,
        comments,
        dashboard,
        diary,
        history,
        kanbanniang,
        links,
        logs,
        media,
        modules as module_admin,
        posts,
        rss,
        saying,
        search,
        settings,
        stats,
        taxonomy,
        users,
    )

    registry.validate()
    _built = True
    return registry
