"""模块注册表: 登记全部模块并在启动时做一致性校验

注册表是"系统里到底有哪些能力"的唯一事实来源:
  - 路由装配: api/v1/__init__.py 与 main.py 都按注册表来 include
  - 权限与配置: modules 接口从这里生成元数据, 供后台"模块管理"渲染
  - 校验: 启动即发现 id/权限码/配置键冲突, 依赖缺失或成环

故意不做目录扫描 + 自动导入: 显式登记一次, 出问题时能一眼看出顺序与来源,
也符合项目"避免不必要的动态魔法"的约定
"""

import re

from app.modules.base import CATEGORIES, PERMISSION_CODES, ModuleSpec, module_setting_key

ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class ModuleRegistry:
    """模块登记表"""

    def __init__(self) -> None:
        self._modules: dict[str, ModuleSpec] = {}
        self._permission_owner: dict[str, list[str]] = {}
        self._setting_owner: dict[str, str] = {}

    def register(self, spec: ModuleSpec) -> ModuleSpec:
        """登记一个模块(重复 id 直接报错, 避免后注册的静默覆盖前一个)

        @param spec: 模块元数据
        @return 原样返回 spec, 便于在定义文件里 `SPEC = registry.register(...)`
        @throws ValueError id 非法或重复, 权限码/配置键与他人冲突
        """
        if not ID_RE.match(spec.id):
            raise ValueError(f"模块 id 不合法(只允许小写字母/数字/连字符): {spec.id}")
        if spec.id in self._modules:
            raise ValueError(f"模块 id 重复: {spec.id}")
        if spec.category not in CATEGORIES:
            raise ValueError(f"模块 {spec.id} 的分类不合法: {spec.category}")
        if spec.locked and not spec.default_enabled:
            raise ValueError(f"模块 {spec.id} 是锁定模块, 不能默认禁用")

        for code in spec.permissions:
            if code not in PERMISSION_CODES:
                raise ValueError(f"模块 {spec.id} 声明了不存在的权限码: {code}")
            # 权限码是跨模块的能力: 例如 stats:view 同时被"访问统计"与"后台看板"使用,
            # 这里只登记归属关系供文档/后台展示, 不做"只能属于一个模块"的限制
            owners = self._permission_owner.setdefault(code, [])
            if spec.id not in owners:
                owners.append(spec.id)

        for item in spec.settings:
            if item.key == "enabled":
                raise ValueError(f"模块 {spec.id} 的配置键不能叫 enabled(与开关冲突)")
            # 配置键只在模块内唯一即可: 存进 settings 表时带的是 module.<模块 id>. 前缀,
            # 不同模块可以都叫 api_url, 这是刻意的模块内聚
            seen_in_module = [other.key for other in spec.settings if other.key == item.key]
            if len(seen_in_module) > 1:
                raise ValueError(f"模块 {spec.id} 里配置键 {item.key} 重复声明")
            if item.kind == "int" and (item.minimum is None or item.maximum is None):
                raise ValueError(f"模块 {spec.id} 的整数配置 {item.key} 必须声明取值范围")
            if item.kind == "int" and item.minimum is not None and item.maximum is not None:
                if item.minimum > item.maximum:
                    raise ValueError(f"模块 {spec.id} 的配置 {item.key} 取值范围不合法")
            self._setting_owner[module_setting_key(spec.id, item.key)] = spec.id

        self._modules[spec.id] = spec
        return spec

    def validate(self) -> None:
        """校验依赖关系(存在, 不自依赖, 不成环)

        @throws ValueError 依赖缺失或成环
        """
        for spec in self._modules.values():
            for dep in spec.depends_on:
                if dep == spec.id:
                    raise ValueError(f"模块 {spec.id} 依赖了自己")
                if dep not in self._modules:
                    raise ValueError(f"模块 {spec.id} 依赖了不存在的模块: {dep}")

        # 拓扑排序: 剩下的节点就是环
        pending = {spec.id: set(spec.depends_on) for spec in self._modules.values()}
        while pending:
            ready = [mid for mid, deps in pending.items() if not deps]
            if not ready:
                raise ValueError(f"模块依赖成环: {sorted(pending)}")
            for mid in ready:
                pending.pop(mid)
            for deps in pending.values():
                deps.difference_update(ready)

    def all(self) -> list[ModuleSpec]:
        """全部模块(按注册顺序)

        @return 模块列表
        """
        return list(self._modules.values())

    def ids(self) -> list[str]:
        """全部模块 id

        @return id 列表(注册顺序)
        """
        return list(self._modules)

    def get(self, module_id: str) -> ModuleSpec | None:
        """按 id 取模块

        @param module_id: 模块 id
        @return 找到返回元数据, 否则 None
        """
        return self._modules.get(module_id)

    def permissions(self) -> dict[str, list[str]]:
        """权限码 -> 使用它的模块 id 列表

        @return 映射表
        """
        return {code: list(owners) for code, owners in self._permission_owner.items()}

    def setting_keys(self) -> set[str]:
        """全部模块配置项在 settings 表里的完整键名(用于与站点级设置键查重)

        @return 配置键集合
        """
        return set(self._setting_owner)


"""全局注册表: 定义文件在 import 时把模块登记进来"""
registry = ModuleRegistry()
