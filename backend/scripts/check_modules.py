"""校验模块体系的一致性(不需要数据库, 只读源码与注册表)

跑法: backend/.venv/Scripts/python.exe scripts/check_modules.py

为什么需要这个脚本:
    一个模块要在三处出现 - 后端定义(app/modules/definitions/<id>.py), 前端注册表
    (frontend/src/modules/registry.ts) 与权限表(seed 里的 PERMISSIONS). 任何一处漏改
    都不会报错, 只会表现为"后端启用了但前台没有入口"或者"模块声明的权限码从未被授予
    任何角色". 这里把三者的关系固定下来, 并挂了 verify_all.py

    模块配置的类型同样横跨两侧: 后端 app/modules/base.py 的 SettingKind 与前端
    types/index.ts 的 ModuleSettingKind. 加一种类型时只改一侧, 后台会把控件渲染成
    兜底的单行输入框, 界面上不会有任何报错, 因此也在这里对齐
"""

import re
import sys
from pathlib import Path
from typing import get_args

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent

sys.path.insert(0, str(BACKEND))

from app.core.settings_schema import ADMIN_ONLY_KEYS, DEFAULTS  # noqa: E402
from app.modules import build_registry  # noqa: E402
from app.modules.base import SettingKind  # noqa: E402
from app.seed import PERMISSIONS  # noqa: E402

# Windows 下 stdout 被重定向到管道时默认按本地编码(GBK)输出, 而 verify_all.py 按 UTF-8
# 读取子进程输出, 不统一编码就会在汇总表里显示成乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FRONT_REGISTRY = ROOT / "frontend" / "src" / "modules" / "registry.ts"
FRONT_TYPES = ROOT / "frontend" / "src" / "types" / "index.ts"

problems: list[str] = []


def check(condition: bool, message: str) -> None:
    """记录一条不满足的约束; 全部收集完再退出, 便于一次看到所有问题"""
    print(f"  {'OK  ' if condition else 'FAIL'} {message}")
    if not condition:
        problems.append(message)


registry = build_registry()
backend_ids = registry.ids()

print("后端: 模块注册表")
check(len(backend_ids) >= 10, f"已注册 {len(backend_ids)} 个模块")
check(len(backend_ids) == len(set(backend_ids)), "模块 id 不重复")

# 模块声明的权限码必须已经写进 seed 的权限表, 否则角色里永远拿不到这个权限
# (权限码是否存在于 Perm 由注册表的 register() 直接抛错拦住, 这里不必重复校验)
seeded_codes = {code for code, _name, _desc in PERMISSIONS}
declared_codes = set(registry.permissions())
missing_in_seed = declared_codes - seeded_codes
check(not missing_in_seed, f"模块声明的 {len(declared_codes)} 个权限码都已写入 seed 权限表")
if missing_in_seed:
    print(f"       未在 seed 中定义: {sorted(missing_in_seed)}")

undeclared = sorted(seeded_codes - declared_codes)
print(f"       未被模块声明的权限码 {len(undeclared)} 个: {', '.join(undeclared) or '无'}")

print()
print("后端: 模块配置键")
# 模块配置的键带 module.<id>. 前缀, 与站点级设置键天然不冲突, 这里做一次显式确认
site_keys = set(DEFAULTS) | set(ADMIN_ONLY_KEYS)
collisions = registry.setting_keys() & site_keys
check(not collisions, f"模块配置键({len(registry.setting_keys())} 个)不与站点级设置键冲突")
if collisions:
    print(f"       冲突: {sorted(collisions)}")

print()
print("前后端: 模块 id 集合")
front_ids = re.findall(
    r"^\s{4}id: '([a-z0-9-]+)',$", FRONT_REGISTRY.read_text(encoding="utf-8"), re.M
)
check(len(front_ids) >= 10, f"从前端注册表解析出 {len(front_ids)} 个模块")
check(set(front_ids) == set(backend_ids), "前端注册表与后端注册表的模块 id 完全一致")
missing_in_front = sorted(set(backend_ids) - set(front_ids))
stale_in_front = sorted(set(front_ids) - set(backend_ids))
if missing_in_front or stale_in_front:
    print(f"       前端缺少: {missing_in_front}")
    print(f"       前端多余: {stale_in_front}")

print()
print("前后端: 模块配置类型")
types_src = FRONT_TYPES.read_text(encoding="utf-8")
kind_match = re.search(r"export type ModuleSettingKind =([^\n]+)", types_src)
if kind_match is None:
    raise SystemExit(f"  FAIL 在 {FRONT_TYPES.name} 里找不到 ModuleSettingKind")
front_kinds = set(re.findall(r"'([a-z_]+)'", kind_match.group(1)))
backend_kinds = set(get_args(SettingKind))
check(
    front_kinds == backend_kinds,
    f"ModuleSettingKind 与后端 SettingKind 完全一致({len(backend_kinds)} 种)",
)
if front_kinds != backend_kinds:
    print(f"       前端缺少: {sorted(backend_kinds - front_kinds)}")
    print(f"       前端多余: {sorted(front_kinds - backend_kinds)}")

print()
print("模块清单")
for spec in registry.all():
    flags = []
    if spec.locked:
        flags.append("核心")
    if spec.frontend_only:
        flags.append("纯前台")
    if spec.depends_on:
        flags.append("依赖 " + ",".join(spec.depends_on))
    if spec.settings:
        flags.append(f"配置 {len(spec.settings)} 项")
    print(f"  {spec.id.ljust(14)} {spec.name.ljust(14)} {' '.join(flags) or '-'}")

print()
print("结论: " + ("全部一致" if not problems else f"{len(problems)} 项不一致"))
sys.exit(1 if problems else 0)
