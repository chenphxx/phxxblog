"""本次 review 优化的全量验证脚本

把散落在各处的检查串起来跑一遍, 输出一张汇总表
用法: backend/.venv/Scripts/python.exe scripts/verify_all.py
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
FRONTEND = ROOT / "frontend"

results: list[tuple[str, bool, str]] = []


def run(label: str, cmd: list[str], cwd: Path, ok_hint: str = "") -> None:
    # 统一让 Python 子进程输出 UTF-8, 与这里的解码方式一致: Windows 控制台默认
    # cp936, 子进程按管道输出时会用 GBK 编码, 不强制的话中文与部分符号会解码成乱码
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or "").strip().split("\n")
    msg = tail[-1].strip() if tail else (proc.stderr or "").strip().split("\n")[-1][:80]
    if ok and ok_hint and ok_hint in (proc.stdout or ""):
        msg = ok_hint
    elif ok and not msg:
        msg = "通过"
    results.append((label, ok, msg[:90]))


py = str(BACKEND / ".venv" / "Scripts" / "python.exe")

run("后端: 可导入", [py, "-c", "import app.main"], BACKEND)
run(
    "后端: 启动即校验表结构",
    [
        py,
        "-c",
        "from app.core.database import missing_columns; assert not missing_columns(), missing_columns()",
    ],
    BACKEND,
)
run("后端: 设置项定义一致", [py, "scripts/check_settings_keys.py"], BACKEND, ok_hint="全部一致")
run("后端: 静态检查(ruff)", [py, "-m", "ruff", "check", "."], BACKEND, ok_hint="All checks passed")
run(
    "后端: 格式一致(ruff)",
    [py, "-m", "ruff", "format", "--check", "."],
    BACKEND,
    ok_hint="already formatted",
)

if sys.platform == "win32":
    npx = "npx.cmd"
    npm = "npm.cmd"
else:
    npx = "npx"
    npm = "npm"
run("前端: 类型检查", [npx, "vue-tsc", "-b", "--force"], FRONTEND)
run("前端: 主题与生成物一致", [npm, "run", "themes:audit"], FRONTEND, ok_hint="ALL OK")
run("前端: 图标路径", [npm, "run", "check:icons"], FRONTEND, ok_hint="ALL OK")
run("前端: 程序式组件样式", [npm, "run", "check:element-styles"], FRONTEND, ok_hint="ALL OK")
run("前端: 静态检查(eslint)", [npx, "eslint", "."], FRONTEND)
run(
    "前端: 格式一致(prettier)",
    [npm, "run", "check:format"],
    FRONTEND,
    ok_hint="All matched files use Prettier code style",
)

# 个别检查的输出可能含当前代码页无法表示的字符,
# 打印时用替换而不是抛 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

print("=" * 78)
print("验证汇总")
print("=" * 78)
width = max(len(r[0]) for r in results)
failed = 0
for label, ok, msg in results:
    if not ok:
        failed += 1
    print(f"  {'OK  ' if ok else 'FAIL'} {label.ljust(width)}  {msg}")
print("=" * 78)
print(f"  {len(results) - failed}/{len(results)} 通过")
sys.exit(1 if failed else 0)
