"""从后端源码提取完整的路由清单, 用于生成 docs/api.md 里的接口表。

只扫描「装饰器 + 函数签名」这一段, 不跨越到下一个接口 ——
按固定行数窗口扫描会把下一个接口的权限依赖误算进来(已踩过这个坑)。

用法:
  python scripts/dump_routes.py            # 写到 stdout
  python scripts/dump_routes.py --json     # 输出 JSON(便于脚本消费)
"""

import json
import re
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1] / "app" / "api" / "v1"

DECORATOR = re.compile(r'@router\.(get|post|put|patch|delete)\(\s*"([^"]*)"', re.I)
PREFIX = re.compile(r'APIRouter\([^)]*prefix="([^"]*)"', re.S)
TAG = re.compile(r'APIRouter\([^)]*tags=\["([^"]+)"\]', re.S)
FUNC = re.compile(r"^def (\w+)\(", re.M)

# 顺序敏感: 越具体的越靠前
AUTH_LABELS = [
    ("require_permission(Perm.", None),  # 动态解析权限码
    ("get_optional_user", "可选"),
    ("get_current_user", "登录"),
]


def route_block(lines: list[str], deco_index: int) -> tuple[str, str]:
    """从装饰器行扫到函数签名结束, 返回 (整段文本, 函数名)。

    不能只扫签名: 权限依赖有时写在函数名之后换行的参数里(例如
    `data: CategoryIn,\\n user: User = Depends(require_permission(...))`),
    也不能扫固定行数窗口 —— 那会把下一个接口的依赖算进来。
    """
    end = None
    for j in range(deco_index, min(deco_index + 40, len(lines))):
        if lines[j].rstrip().endswith("):"):
            end = j
            break
    if end is None:
        end = min(deco_index + 40, len(lines) - 1)
    block = "\n".join(lines[deco_index : end + 1])
    m = FUNC.search(block)
    return block, (m.group(1) if m else "?")


def detect_auth(block: str) -> str:
    m = re.search(r"require_permission\(Perm\.(\w+)\)", block)
    if m:
        # Perm.POST_MANAGE -> post:manage
        return m.group(1).lower().replace("_", ":")
    if "get_optional_user" in block:
        return "可选登录"
    if "get_current_user" in block:
        return "登录"
    return "公开"


def main() -> None:
    # Windows 控制台/重定向默认不是 UTF-8, 中文标签会变乱码; 显式固定编码
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    rows = []
    for path in sorted(API_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        prefix = (PREFIX.search(src) or [None, ""])[1]
        tag = (TAG.search(src) or [None, path.stem])[1]
        lines = src.split("\n")
        for i, line in enumerate(lines):
            m = DECORATOR.search(line)
            if not m:
                continue
            block, func = route_block(lines, i)
            rows.append(
                {
                    "tag": tag,
                    "method": m.group(1).upper(),
                    "path": (prefix + m.group(2)) or "/",
                    "auth": detect_auth(block),
                    "func": func,
                    "file": path.name,
                }
            )

    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        by_tag.setdefault(r["tag"], []).append(r)

    print(f"共 {len(rows)} 条路由, {len(by_tag)} 个模块\n")
    for tag, group in by_tag.items():
        print(f"### {tag}\n")
        print("| 方法 | 路径 | 鉴权 | 处理函数 |")
        print("| --- | --- | --- | --- |")
        for r in group:
            print(f"| `{r['method']}` | `{r['path']}` | {r['auth']} | `{r['func']}` |")
        print()

    from collections import Counter

    print("鉴权分布:", dict(Counter(r["auth"] for r in rows)))


if __name__ == "__main__":
    main()
