"""模块元数据定义

一个"模块"就是一项可以被整体启用/禁用, 并且可以带自己配置的能力. 模块只描述
元数据与它占用的资源(路由, 权限码, 配置项), 实现放在模块自己的包目录里:

    app/modules/<模块 id>/
      __init__.py   导入即注册(`from .spec import SPEC`)
      spec.py       元数据与它引用的 router
      router.py     接口实现(接口多的模块可以再拆文件, 由 spec 汇总成 routers)

共享的基础设施不跟着搬: models(数据库实体), schemas(接口契约), services(业务逻辑),
core(配置/安全/权限)统一留在 app/ 下, 模块通过 import 使用它们
"""

from dataclasses import dataclass, field
from typing import Literal

from fastapi import APIRouter

from app.core.permissions import Perm

"""配置项类型: bool(开关) / int(整数) / text(单行文本) / long_text(多行文本)
/ json(JSON) / rows(行列表)"""
SettingKind = Literal["bool", "int", "text", "long_text", "json", "rows"]

"""可见范围: public 表示所有访客都可用, admin 表示仅管理员可用

这是"比权限码更粗的一层": 模块自己的权限码照旧生效, 可见范围决定这项能力要不要
对访客开放 - 站内搜索配成 admin 后, 访客连搜索接口都调不到, 管理员照常使用
"""
VISIBILITY_PUBLIC = "public"
VISIBILITY_ADMIN = "admin"

"""可见范围取值 -> 后台展示名"""
VISIBILITIES = {
    VISIBILITY_PUBLIC: "公开",
    VISIBILITY_ADMIN: "仅管理员",
}

"""模块分类, 只影响后台"模块管理"里的分组展示"""
CATEGORIES = {
    "core": "核心",
    "content": "内容",
    "insight": "数据",
    "extension": "扩展",
}

"""权限码全集(用于校验模块声明的权限码是否存在, 防止拼错后静默失效)"""
PERMISSION_CODES = {
    value
    for name, value in vars(Perm).items()
    if not name.startswith("_") and isinstance(value, str)
}

# 模块配置在 settings 表里的键前缀: module.<模块 id>.<配置键>
MODULE_KEY_PREFIX = "module"
ENABLED_KEY = "enabled"


def module_setting_key(module_id: str, key: str) -> str:
    """模块配置项在 settings 表里的完整键名

    @param module_id: 模块 id
    @param key: 模块内的配置键
    @return 形如 module.<模块 id>.<配置键> 的键名
    """
    return f"{MODULE_KEY_PREFIX}.{module_id}.{key}"


def module_enabled_key(module_id: str) -> str:
    """模块开关在 settings 表里的键名

    @param module_id: 模块 id
    @return 形如 module.<模块 id>.enabled 的键名
    """
    return module_setting_key(module_id, ENABLED_KEY)


@dataclass(frozen=True)
class ModuleSetting:
    """模块自己的一项配置

    @param key: 模块内唯一的配置键(不含 module.<id>. 前缀)
    @param name: 后台展示名
    @param default: 默认值(字符串, 与 settings 表的存储形式一致)
    @param description: 说明, 写入 settings.description 并在后台表单里显示
    @param kind: 值类型, 决定后台用什么控件以及怎么校验
    @param minimum: 整数类型的下限(含)
    @param maximum: 整数类型的上限(含)
    @param public: 是否随公开接口下发给前台
    @param columns: 行列表类型的列名(按顺序渲染); 其它类型留空
    """

    key: str
    name: str
    default: str = ""
    description: str = ""
    kind: SettingKind = "text"
    minimum: int | None = None
    maximum: int | None = None
    public: bool = False
    columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModuleSpec:
    """模块元数据

    @param id: 模块标识(小写字母/数字/连字符), 前后端共用, 一旦发布不要改名
    @param name: 中文名, 后台展示
    @param description: 一句话说明这个模块提供什么能力
    @param category: 分组(core/content/insight/extension)
    @param locked: 核心模块(如认证/设置), 不允许在后台禁用
    @param default_enabled: 新装环境下默认是否启用(库里没有记录时用它)
    @param default_visibility: 库里没有可见范围记录时用它(public/admin)
    @param visibility_fixed: 可见范围是否固定(后台不提供调整入口); 管理后台自身的能力用它
    @param depends_on: 依赖的模块 id, 依赖被禁用时本模块也会被视为不可用
    @param permissions: 本模块使用的权限码, 必须存在于 core/permissions.py 的 Perm
    @param settings: 本模块自己的配置项
    @param routers: 本模块的 FastAPI 路由(已带 prefix/tags; 可以多个, 如分类与标签)
    @param root_routes: 是否挂在根路径(非 /api/v1), 如 RSS 与 Sitemap
    @param api_prefix: 对外接口前缀, 仅用于后台展示与文档
    """

    id: str
    name: str
    description: str
    category: str = "extension"
    locked: bool = False
    default_enabled: bool = True
    default_visibility: str = VISIBILITY_PUBLIC
    visibility_fixed: bool = False
    depends_on: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    settings: tuple[ModuleSetting, ...] = ()
    routers: tuple[APIRouter, ...] = ()
    root_routes: bool = False
    api_prefix: str = ""
    # 预留: 后端没有接口, 只影响前台的模块(如看板娘)
    frontend_only: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)
