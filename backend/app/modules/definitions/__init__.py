"""模块定义清单

新增一个模块只需要两步:
  1. 在本目录新建 <模块 id>.py, 导出 `SPEC = registry.register(ModuleSpec(...))`
  2. 在下面的 import 列表里加一行

这里显式列出而不是扫描目录: 注册顺序可控(核心在前, 扩展在后), 出错时也能一眼看出
是哪个文件贡献了这份元数据
"""

from app.modules.definitions import (  # noqa: F401  仅为触发注册
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
    modules,
    posts,
    rss,
    saying,
    search,
    settings,
    stats,
    taxonomy,
    users,
)

__all__ = [
    "auth",
    "users",
    "settings",
    "modules",
    "taxonomy",
    "posts",
    "comments",
    "media",
    "search",
    "stats",
    "dashboard",
    "logs",
    "diary",
    "changelog",
    "saying",
    "history",
    "links",
    "rss",
    "kanbanniang",
]
