"""模块开关与模块配置的读写

状态与配置都复用现有的 settings 键值表, 不新增表也不需要迁移:

    module.<模块 id>.enabled   模块开关("1" 开 / "0" 关)
    module.<模块 id>.<配置键>   模块自己的配置项

库里没有记录时一律回落到模块元数据里的默认值, 与站点级设置(DEFAULTS 兜底)的
做法保持一致, 因此"新模块"上线不需要写 seed
"""

import json

from sqlalchemy.orm import Session

from app.models.setting import Setting
from app.modules.base import (
    CATEGORIES,
    ModuleSetting,
    ModuleSpec,
    module_enabled_key,
    module_setting_key,
)
from app.modules.registry import registry

# 与 core/settings_schema.py 的 BOOL_KEYS 保持同一套真值写法
TRUE_VALUES = ("1", "true", "yes", "on")


def parse_bool(raw: object) -> bool:
    """把设置值按布尔语义解析

    @param raw: 设置值
    @return 1/true/yes/on 为 True, 其余为 False
    """
    return str(raw if raw is not None else "").strip().lower() in TRUE_VALUES


def _read(db: Session, key: str) -> str | None:
    """读一行设置(不存在返回 None)

    @param db: 数据库会话
    @param key: 设置键
    @return 设置值或 None
    """
    row = db.get(Setting, key)
    return row.setting_value if row else None


def _write(db: Session, key: str, value: str, description: str = "") -> None:
    """写一行设置(存在则更新, 不存在则插入)

    @param db: 数据库会话
    @param key: 设置键
    @param value: 设置值
    @param description: 说明(仅在插入时写入)
    """
    row = db.get(Setting, key)
    if row:
        row.setting_value = value
    else:
        db.add(Setting(setting_key=key, setting_value=value, description=description or None))


def is_enabled(db: Session, module_id: str) -> bool:
    """模块是否启用(库里没有记录时用元数据里的默认值)

    @param db: 数据库会话
    @param module_id: 模块 id
    @return 启用返回 True
    """
    spec = registry.get(module_id)
    if spec is None:
        return False
    raw = _read(db, module_enabled_key(module_id))
    if raw is None:
        return spec.default_enabled
    return parse_bool(raw)


def disabled_dependencies(db: Session, spec: ModuleSpec) -> list[str]:
    """列出该模块当前被禁用的依赖

    @param db: 数据库会话
    @param spec: 模块元数据
    @return 被禁用(或被级联禁用)的依赖 id 列表
    """
    return [dep for dep in spec.depends_on if not effective_enabled(db, dep)]


def effective_enabled(db: Session, module_id: str) -> bool:
    """模块是否真正可用: 自己启用且依赖链上的模块都启用

    @param db: 数据库会话
    @param module_id: 模块 id
    @return 可用返回 True
    """
    spec = registry.get(module_id)
    if spec is None or not is_enabled(db, module_id):
        return False
    return all(effective_enabled(db, dep) for dep in spec.depends_on)


def enabled_ids(db: Session) -> list[str]:
    """当前真正可用的模块 id(注册顺序)

    @param db: 数据库会话
    @return 模块 id 列表
    """
    return [spec.id for spec in registry.all() if effective_enabled(db, spec.id)]


def set_enabled(db: Session, module_id: str, enabled: bool) -> ModuleSpec:
    """开关一个模块

    @param db: 数据库会话
    @param module_id: 模块 id
    @param enabled: 是否启用
    @return 模块元数据
    @throws ValueError 模块不存在, 或试图禁用锁定模块
    """
    spec = registry.get(module_id)
    if spec is None:
        raise ValueError(f"模块不存在: {module_id}")
    if spec.locked and not enabled:
        raise ValueError(f"{spec.name} 是核心模块, 不能禁用")
    _write(db, module_enabled_key(module_id), "1" if enabled else "0", f"模块开关: {spec.name}")
    return spec


def validate_value(item: ModuleSetting, raw: object) -> str:
    """校验并规范化一个配置值

    @param item: 配置项定义
    @param raw: 待写入的值
    @return 可写入 settings 表的字符串
    @throws ValueError 值不符合类型或范围
    """
    # 多行文本(Markdown)原样保存: 前后空行与行首缩进都可能是内容的一部分, 不能 strip
    if item.kind == "long_text":
        return "" if raw is None else str(raw)
    text = "" if raw is None else str(raw).strip()
    if item.kind == "bool":
        return "1" if parse_bool(raw) else "0"
    if item.kind == "int":
        if not text.lstrip("-").isdigit():
            raise ValueError(f"{item.name} 必须是整数")
        value = int(text)
        if item.minimum is not None and value < item.minimum:
            raise ValueError(f"{item.name} 不能小于 {item.minimum}")
        if item.maximum is not None and value > item.maximum:
            raise ValueError(f"{item.name} 不能大于 {item.maximum}")
        return str(value)
    if item.kind == "rows":
        return json.dumps(coerce_rows(item, raw), ensure_ascii=False)
    if item.kind == "json":
        try:
            json.loads(text or "null")
        except json.JSONDecodeError as err:
            raise ValueError(f"{item.name} 不是合法的 JSON") from err
        return text
    return text


def coerce_rows(item: ModuleSetting, raw: object) -> list[dict[str, str]]:
    """把行列表配置的值规范成 [{列名: 值}]

    接受前端直接下发的数组, 也接受库里存的 JSON 字符串(settings 表按字符串存值)

    @param item: 行列表配置项定义
    @param raw: 待规范的值
    @return 每行都按 columns 顺序补齐的行列表
    @throws ValueError 不是数组, 元素不是对象, 或出现了未声明的列
    """
    if isinstance(raw, list):
        parsed: object = raw
    else:
        text = "" if raw is None else str(raw).strip()
        try:
            parsed = json.loads(text or "[]")
        except json.JSONDecodeError as err:
            raise ValueError(f"{item.name} 不是合法的 JSON") from err
    if not isinstance(parsed, list):
        raise ValueError(f"{item.name} 必须是数组")

    columns = set(item.columns)
    rows: list[dict[str, str]] = []
    for index, row in enumerate(parsed, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{item.name} 第 {index} 行必须是对象")
        unknown = set(row) - columns
        if unknown:
            raise ValueError(
                f"{item.name} 第 {index} 行出现未声明的列: {', '.join(sorted(unknown))}"
            )
        rows.append(
            {
                column: "" if row.get(column) is None else str(row.get(column))
                for column in item.columns
            }
        )
    return rows


def typed_value(item: ModuleSetting, raw: str | None) -> bool | int | str | list[dict[str, str]]:
    """把库里存的字符串按配置项类型转成 Python 值(供接口下发)

    读取路径要容错: 库里可能留着历史值或非法 JSON, 此时回落到默认值而不是让
    整个模块状态接口报错

    @param item: 配置项定义
    @param raw: 库里存的字符串(可能为 None)
    @return 按类型转换后的值
    """
    value = raw if raw is not None else item.default
    if item.kind == "bool":
        return parse_bool(value)
    if item.kind == "int":
        text = str(value).strip()
        return int(text) if text.lstrip("-").isdigit() else int(item.default or 0)
    if item.kind == "rows":
        try:
            return coerce_rows(item, value)
        except ValueError:
            return []
    return value


def module_config(db: Session, spec: ModuleSpec, *, typed: bool = True) -> dict:
    """读取模块的全部配置(未设置的用默认值)

    @param db: 数据库会话
    @param spec: 模块元数据
    @param typed: True 返回转换后的 Python 值, False 返回原始字符串
    @return 配置键 -> 值
    """
    result: dict = {}
    for item in spec.settings:
        raw = _read(db, module_setting_key(spec.id, item.key))
        result[item.key] = (
            typed_value(item, raw) if typed else (raw if raw is not None else item.default)
        )
    return result


def set_module_config(db: Session, spec: ModuleSpec, values: dict) -> dict:
    """写入模块配置(只接受模块声明过的键)

    @param db: 数据库会话
    @param spec: 模块元数据
    @param values: 待写入的键值对
    @return 写入后的完整配置(已按类型转换)
    @throws ValueError 出现了未声明的配置键或值非法
    """
    declared = {item.key: item for item in spec.settings}
    for key, raw in values.items():
        item = declared.get(key)
        if item is None:
            raise ValueError(f"模块 {spec.name} 没有配置项: {key}")
        normalized = validate_value(item, raw)
        _write(
            db,
            module_setting_key(spec.id, key),
            normalized,
            f"{spec.name}: {item.description or item.name}",
        )
    return module_config(db, spec)


def public_state(db: Session) -> dict:
    """公开给前台的模块状态: 启用的模块 id 与公开配置

    前台用它决定注册哪些路由/导航项, 因此只暴露"启用集合", 不暴露默认值与依赖细节

    @param db: 数据库会话
    @return {"ids": [...], "config": {模块 id: {公开配置}}}
    """
    ids = set(enabled_ids(db))
    config: dict[str, dict] = {}
    for spec in registry.all():
        if spec.id not in ids:
            continue
        public_items = [item for item in spec.settings if item.public]
        if public_items:
            values = module_config(db, spec, typed=False)
            config[spec.id] = {
                item.key: typed_value(item, values.get(item.key)) for item in public_items
            }
    return {"ids": sorted(ids), "config": config}


def admin_state(db: Session) -> list[dict]:
    """后台"模块管理"需要的全部信息

    @param db: 数据库会话
    @return 每个模块一条记录(含启用状态, 依赖状态与配置项定义)
    """
    records: list[dict] = []
    category_order = {key: index for index, key in enumerate(CATEGORIES)}
    for spec in registry.all():
        values = module_config(db, spec, typed=False)
        records.append(
            {
                "id": spec.id,
                "name": spec.name,
                "description": spec.description,
                "category": spec.category,
                "locked": spec.locked,
                "default_enabled": spec.default_enabled,
                "enabled": is_enabled(db, spec.id),
                "available": effective_enabled(db, spec.id),
                "disabled_dependencies": disabled_dependencies(db, spec),
                "depends_on": list(spec.depends_on),
                "permissions": list(spec.permissions),
                "api_prefix": spec.api_prefix,
                "has_backend": bool(spec.routers),
                "frontend_only": spec.frontend_only,
                "settings": [
                    {
                        "key": item.key,
                        "name": item.name,
                        "description": item.description,
                        "kind": item.kind,
                        "minimum": item.minimum,
                        "maximum": item.maximum,
                        "public": item.public,
                        "columns": list(item.columns),
                        "value": typed_value(item, values.get(item.key)),
                    }
                    for item in spec.settings
                ],
            }
        )
    # 后台按"核心 -> 内容 -> 数据 -> 扩展"分组展示, 组内按 id 稳定排序
    records.sort(
        key=lambda item: (category_order.get(item["category"], len(CATEGORIES)), item["id"])
    )
    return records
