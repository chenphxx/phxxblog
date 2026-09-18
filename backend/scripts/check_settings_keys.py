"""校验设置项的三处定义是否一致(不需要数据库, 只读源码与默认值)。

跑法: backend/.venv/Scripts/python.exe scripts/check_settings_keys.py

为什么需要这个脚本:
    一个设置项要在四个地方出现 —— 后端的默认值(core/settings_schema.py), 后端
    "对前台公开"的键列表, 前端的类型(frontend/src/types/index.ts 的 PublicSettings)
    与后台表单(frontend/src/views/admin/SettingsView.vue)。漏改任何一处都不会报错,
    只会表现为"后台存了但前台读不到"或者"类型里没有这个字段", 靠人眼极难发现。
    这个脚本把四者的键集合对齐, 挂了 verify_all.py 里一起跑。
"""
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent

sys.path.insert(0, str(BACKEND))

from app.core.settings_schema import BOOL_KEYS, DEFAULTS, DEFAULT_SETTINGS, PUBLIC_KEYS  # noqa: E402

# Windows 下 stdout 被重定向到管道时默认按本地编码(GBK)输出, 而 verify_all.py 按 UTF-8
# 读取子进程输出, 不统一编码就会在汇总表里显示成乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TYPES_TS = ROOT / "frontend" / "src" / "types" / "index.ts"
SETTINGS_VIEW = ROOT / "frontend" / "src" / "views" / "admin" / "SettingsView.vue"

problems: list[str] = []


def check(condition: bool, message: str) -> None:
    """记录一条不满足的约束; 全部收集完再退出, 便于一次看到所有问题。"""
    print(f"  {'OK  ' if condition else 'FAIL'} {message}")
    if not condition:
        problems.append(message)


def interface_keys(source: str, name: str) -> set[str]:
    """从 TS 源码里取出某个 interface 的顶层字段名(只处理扁平接口)。"""
    match = re.search(rf"export interface {name} \{{(.*?)\n\}}", source, re.S)
    if match is None:
        raise SystemExit(f"  FAIL 在 {TYPES_TS.name} 里找不到 interface {name}")
    return set(re.findall(r"^\s{2}(\w+)\??:", match.group(1), re.M))


print("后端: 键与默认值")
check(
    set(DEFAULTS) == set(DEFAULT_SETTINGS),
    f"DEFAULTS 与 DEFAULT_SETTINGS 的键一致({len(DEFAULTS)} 个)",
)
check(
    set(PUBLIC_KEYS) <= set(DEFAULTS),
    "PUBLIC_KEYS 里的每个键都有默认值",
)
check(len(PUBLIC_KEYS) == len(set(PUBLIC_KEYS)), "PUBLIC_KEYS 没有重复项")
check(
    set(BOOL_KEYS) <= set(PUBLIC_KEYS),
    "BOOL_KEYS 只包含对外公开的键",
)

print()
print("前端: 类型与后台表单")
types_src = TYPES_TS.read_text(encoding="utf-8")
view_src = SETTINGS_VIEW.read_text(encoding="utf-8")
public_settings = interface_keys(types_src, "PublicSettings")
check(public_settings == set(PUBLIC_KEYS), f"PublicSettings 与 PUBLIC_KEYS 完全一致({len(public_settings)} 个)")

# 类型里有、后端没公开的键 -> 前端会拿到 undefined; 后端公开、类型里没有 -> 类型检查看不到
missing_in_types = set(PUBLIC_KEYS) - public_settings
stale_in_types = public_settings - set(PUBLIC_KEYS)
if missing_in_types or stale_in_types:
    print(f"       类型里缺少: {sorted(missing_in_types)}")
    print(f"       类型里多余: {sorted(stale_in_types)}")

# 后台表单可以编辑的键 = 公开键 - 这里明确排除的那些
NOT_IN_FORM = {
    # 头像不在系统设置里改: 首页直接点头像即可上传(见 HomeView), 但键仍对外公开
    "site_avatar",
}
form_match = re.search(r"const form = ref\(\{(.*?)\n\}\)", view_src, re.S)
if form_match is None:
    raise SystemExit("  FAIL 在 SettingsView.vue 里找不到 form 定义")
form_keys = set(re.findall(r"^\s{2}(\w+):", form_match.group(1), re.M))
expected_form = set(PUBLIC_KEYS) - NOT_IN_FORM
check(form_keys == expected_form, f"后台表单的字段与公开键一致(除 {sorted(NOT_IN_FORM)})")
if form_keys != expected_form:
    print(f"       表单里缺少: {sorted(expected_form - form_keys)}")
    print(f"       表单里多余: {sorted(form_keys - expected_form)}")

print()
print("结论: " + ("全部一致" if not problems else f"{len(problems)} 项不一致"))
sys.exit(1 if problems else 0)
