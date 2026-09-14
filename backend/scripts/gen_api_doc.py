"""生成 docs/api.md。

路由清单从后端源码提取(复用 dump_routes.py 的解析逻辑), 因此不会与实现漂移;
各模块的业务约束写在本文件的 MODULE_NOTES 里。

用法: backend/.venv/Scripts/python.exe scripts/gen_api_doc.py
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "api.md"

# 各模块的补充说明(字段级细节以 Swagger 为准, 这里写业务约束)
MODULE_NOTES: dict[str, str] = {
    "认证": "`/auth/register` 是否可用由 `PHXXBLOG_ALLOW_REGISTER` 控制, 个人博客默认关闭 "
    "登录带失败限流(同一 IP+账号 5 分钟内 10 次失败即 429); 刷新令牌一次性, 轮换后旧令牌立即失效 "
    "`/auth/logout` 只需请求体里的 refresh_token, 因此不需要访问令牌 ",
    "文章": "列表仅返回已发布文章; 状态为 0草稿/1审核中/2已发布/3私密/4回收站 "
    "无 `post:publish` 者提交 status=2 会被**静默降级**为审核中(作者提交发布请求不该收到报错), "
    "而状态流转接口 `PATCH /posts/{id}/status` 对越权直接返回 403 "
    "私密/回收站内容对无权者返回 404 而非 403, 不暴露存在性 "
    "\n>"
    "\n> `/posts/hot` 按阅读量倒序返回已发布文章(前台首页与文章详情页侧栏的\"热门文章\"); 详情接口额外返回 `prev_post` / `next_post`, 为按发布时间相邻的上一篇/下一篇, 首尾文章对应项为 `null` ",
    "分类": "列表公开; 写操作需 `post:manage` 列表里的 `post_count` 只统计已发布文章 ",
    "标签": "列表公开; 写操作需 `post:manage` ",
    "评论": "游客可评论(按 IP 归属, 只能编辑/删除自己的游客评论); "
    "列表与创建为可选登录; 管理列表 `GET /comments/admin` 与状态变更需 `comment:manage`; "
    "编辑/删除自身评论走 `_can_manage_comment` 判定, 故标注为可选登录 ",
    "日记": "整组接口需 `diary:manage`; 导入/导出支持 zip 与 markdown, "
    "导入的 frontmatter 与文章导入共用同一套解析(`services/archive.py`) ",
    "媒体": "整组接口需 `media:manage`; 上传有**扩展名白名单**与图片文件头校验, "
    "拒绝 .svg/.html/.js 等可执行文档(上传目录与站点同源, 否则等于开放 XSS); "
    "单文件上限见 `PHXXBLOG_MAX_UPLOAD_SIZE`(默认 100MB), 超限返回 413 并删除半成品文件 ",
    "看板": "后台首页聚合数据; 需 `stats:view` `trend` 为近 14 天 `{date, pv, uv}`(与 `/stats/trend` 字段名不同) `overview` 含今日 `today_pv`/`today_uv` ",
    "统计": "`/stats/track` 由前台埋点调用(公开); "
    "其余为后台统计, 需 `stats:view` 自定义区间的天数上限为 366 天 ",
    "设置": "公开设置可匿名读取(站点名/简介/模块开关等); 更新需 `setting:manage` ",
    "用户管理": "需 `user:manage`; 角色与权限相关接口需 `role:manage` 内置角色的 code 建议不要修改"
    "(业务代码已改为按权限码授权, 但前端菜单等仍依赖 admin 角色名) ",
    "操作日志": "需 `log:view` ",
    "其他": "更新日志读写需 `changelog:manage`(注意 `PUT /misc/changelog` 会直接写仓库里的 CHANGELOG.md, "
    "要求该目录可写, 且会让 git 工作区变 dirty); 一言与历史上的今天是公开代理接口 ",
    "搜索": "公开 关键词长度上限 100 字符 ",
    "链接预览": "公开; 用于抓取外链标题与图标 ",
    "RSS/SEO": "公开; 输出 RSS 与 sitemap ",
}

HEADER = """# 接口文档

后端为 FastAPI 应用, 统一前缀 `/api/v1` 也可用 Swagger 交互式调试: 
`http://localhost:8000/docs`(需要 `setting:manage` 权限, 内置角色中只有管理员具备) 
`/docs`, `/redoc`, `/openapi.json` 与 `/docs/oauth2-redirect` 走同一道鉴权: 令牌取自 
`Authorization: Bearer <access_token>` 或 cookie `phxxblog_doc_token`, 未登录返回 401, 
已登录但没有该权限返回 403 

## 统一约定

### 响应结构

所有接口(含错误响应)统一返回同一外壳, HTTP 状态码与 `code` 一致: 

```json
{ "code": 0, "message": "ok", "data": { } }
```

失败时 `data` 为 `null`: 

```json
{ "code": 403, "message": "缺少权限: post:manage", "data": null }
```

### 鉴权

除标注为"公开"外, 均需在请求头携带访问令牌: 

```
Authorization: Bearer <access_token>
```

授权判断一律基于**权限码**(由角色聚合而来), 不在业务代码里判断角色名 - 
角色 code 可被后台修改, 用角色名判断会在改名后静默失效 

| "鉴权"列取值 | 含义 |
| --- | --- |
| 公开 | 无需令牌 |
| 可选登录 | 匿名可用; 带令牌时行为不同(如能看到自己的草稿, 点赞按用户去重) |
| 登录 | 任意已登录用户 |
| `<资源>:<动作>` | 需要该权限码, 如 `post:manage`, `diary:manage` |

权限码定义在 `backend/app/core/permissions.py`, 由 `app/seed.py` 初始化并分配给内置角色 

### 分页

列表接口统一接受 `page`(从 1 开始)与 `page_size`, 返回: 

```json
{ "items": [], "total": 0, "page": 1, "page_size": 10 }
```

### 状态码

| 状态码 | 含义 |
| --- | --- |
| 400 | 参数或业务校验失败 |
| 401 | 未登录 / 令牌无效或过期 |
| 403 | 已登录但无权限, 或账号被禁用 |
| 404 | 资源不存在**或不可见**(私密内容对无权者一律 404) |
| 413 | 上传文件超过大小限制 |
| 429 | 请求过于频繁(目前用于登录失败限流) |

### 请求体与响应字段

字段级细节以 Swagger 为准 - 本页负责说明**有哪些接口, 需要什么权限, 有哪些业务约束** 

---

## 路由总览

下表按模块列出全部接口, 由 `scripts/dump_routes.py` 从源码提取, 与实现保持一致 
改动路由或权限后请重新生成: 

```bash
cd backend
python scripts/gen_api_doc.py
```

"""


def load_dump_routes():
    spec = importlib.util.spec_from_file_location(
        "dump_routes", BACKEND / "scripts" / "dump_routes.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_rows(dump_routes) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(dump_routes.API_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        prefix = (dump_routes.PREFIX.search(src) or [None, ""])[1]
        tag = (dump_routes.TAG.search(src) or [None, path.stem])[1]
        lines = src.split("\n")
        for i, line in enumerate(lines):
            m = dump_routes.DECORATOR.search(line)
            if not m:
                continue
            block, func = dump_routes.route_block(lines, i)
            rows.append(
                {
                    "tag": tag,
                    "method": m.group(1).upper(),
                    "path": (prefix + m.group(2)) or "/",
                    "auth": dump_routes.detect_auth(block),
                    "func": func,
                }
            )
    return rows


def build() -> str:
    rows = collect_rows(load_dump_routes())

    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        by_tag.setdefault(r["tag"], []).append(r)

    out = [HEADER]
    for tag, group in by_tag.items():
        out.append(f"## {tag}({len(group)} 个接口)\n")
        note = MODULE_NOTES.get(tag)
        if note:
            out.append(f"> {note}\n")
        out.append("| 方法 | 路径 | 鉴权 | 处理函数 |")
        out.append("| --- | --- | --- | --- |")
        for r in group:
            out.append(f"| `{r['method']}` | `{r['path']}` | {r['auth']} | `{r['func']}` |")
        out.append("")

    total = len(rows)
    public = sum(1 for r in rows if r["auth"] == "公开")
    out.append("---\n")
    out.append(f"共 **{total}** 个接口: {public} 个公开, {total - public} 个需要鉴权 \n")
    return "\n".join(out)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    content = build()
    DOC.write_text(content, encoding="utf-8")
    print(f"已写入 {DOC.name}  ({len(content)} 字符)")


if __name__ == "__main__":
    main()
