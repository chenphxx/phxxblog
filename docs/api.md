# 接口文档

后端为 FastAPI 应用，统一前缀 `/api/v1`。也可用 Swagger 交互式调试：
`http://localhost:8000/docs`（仅具备 `setting:manage` 权限的账号可访问）。

## 统一约定

### 响应结构

所有接口（含错误响应）统一返回同一外壳，HTTP 状态码与 `code` 一致：

```json
{ "code": 0, "message": "ok", "data": { } }
```

失败时 `data` 为 `null`：

```json
{ "code": 403, "message": "缺少权限: post:manage", "data": null }
```

### 鉴权

除标注为「公开」外，均需在请求头携带访问令牌：

```
Authorization: Bearer <access_token>
```

授权判断一律基于**权限码**（由角色聚合而来），不在业务代码里判断角色名 ——
角色 code 可被后台修改，用角色名判断会在改名后静默失效。

| 「鉴权」列取值 | 含义 |
| --- | --- |
| 公开 | 无需令牌 |
| 可选登录 | 匿名可用；带令牌时行为不同（如能看到自己的草稿、点赞按用户去重） |
| 登录 | 任意已登录用户 |
| `<资源>:<动作>` | 需要该权限码，如 `post:manage`、`diary:manage` |

权限码定义在 `backend/app/core/permissions.py`，由 `app/seed.py` 初始化并分配给内置角色。

### 分页

列表接口统一接受 `page`（从 1 开始）与 `page_size`，返回：

```json
{ "items": [], "total": 0, "page": 1, "page_size": 10 }
```

### 状态码

| 状态码 | 含义 |
| --- | --- |
| 400 | 参数或业务校验失败 |
| 401 | 未登录 / 令牌无效或过期 |
| 403 | 已登录但无权限，或账号被禁用 |
| 404 | 资源不存在**或不可见**（私密内容对无权者一律 404） |
| 413 | 上传文件超过大小限制 |
| 429 | 请求过于频繁（目前用于登录失败限流） |

### 请求体与响应字段

字段级细节以 Swagger 为准 —— 本页负责说明**有哪些接口、需要什么权限、有哪些业务约束**。

---

## 路由总览

下表按模块列出全部接口，由 `scripts/dump_routes.py` 从源码提取，与实现保持一致。
改动路由或权限后请重新生成：

```bash
cd backend
python scripts/gen_api_doc.py
```


## 认证（8 个接口）

> `/auth/register` 是否可用由 `PHXXBLOG_ALLOW_REGISTER` 控制，个人博客默认关闭。登录带失败限流（同一 IP+账号 5 分钟内 10 次失败即 429）；刷新令牌一次性，轮换后旧令牌立即失效。`/auth/logout` 只需请求体里的 refresh_token，因此不需要访问令牌。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | 公开 | `register` |
| `POST` | `/auth/login` | 公开 | `login` |
| `POST` | `/auth/refresh` | 公开 | `refresh_token` |
| `POST` | `/auth/logout` | 公开 | `logout` |
| `GET` | `/auth/me` | 登录 | `me` |
| `PUT` | `/auth/password` | 登录 | `change_password` |
| `PUT` | `/auth/email` | 登录 | `change_email` |
| `PUT` | `/auth/profile` | 登录 | `update_profile` |

## 分类（4 个接口）

> 列表公开；写操作需 `post:manage`。列表里的 `post_count` 只统计已发布文章。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/categories` | 公开 | `list_categories` |
| `POST` | `/categories` | post:manage | `create_category` |
| `PUT` | `/categories/{category_id}` | post:manage | `update_category` |
| `DELETE` | `/categories/{category_id}` | post:manage | `delete_category` |

## 评论（6 个接口）

> 游客可评论（按 IP 归属，只能编辑/删除自己的游客评论）；列表与创建为可选登录；管理列表 `GET /comments/admin` 与状态变更需 `comment:manage`；编辑/删除自身评论走 `_can_manage_comment` 判定，故标注为可选登录。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/posts/{post_id}/comments` | 可选登录 | `list_comments` |
| `POST` | `/posts/{post_id}/comments` | 可选登录 | `create_comment` |
| `GET` | `/comments/admin` | comment:manage | `admin_list_comments` |
| `PUT` | `/comments/{comment_id}` | 可选登录 | `update_comment` |
| `PATCH` | `/comments/{comment_id}/status` | comment:manage | `update_comment_status` |
| `DELETE` | `/comments/{comment_id}` | 可选登录 | `delete_comment` |

## 看板（1 个接口）

> 后台首页聚合数据；需 `stats:view`。`trend` 为近 14 天 `{date, pv, uv}`（与 `/stats/trend` 字段名不同）；`overview` 含今日 `today_pv`/`today_uv`。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/dashboard` | stats:view | `dashboard` |

## 日记（6 个接口）

> 整组接口需 `diary:manage`；导入/导出支持 zip 与 markdown，导入的 frontmatter 与文章导入共用同一套解析（`services/archive.py`）。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/diaries` | diary:manage | `list_diaries` |
| `GET` | `/diaries/export` | diary:manage | `export_diaries` |
| `POST` | `/diaries/import` | diary:manage | `import_diaries` |
| `POST` | `/diaries` | diary:manage | `create_diary` |
| `PUT` | `/diaries/{diary_id}` | diary:manage | `update_diary` |
| `DELETE` | `/diaries/{diary_id}` | diary:manage | `delete_diary` |

## 链接预览（1 个接口）

> 公开；用于抓取外链标题与图标。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/links/preview` | 公开 | `link_preview` |

## 操作日志（1 个接口）

> 需 `log:view`。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/logs` | log:view | `list_logs` |

## 媒体（3 个接口）

> 整组接口需 `media:manage`；上传有**扩展名白名单**与图片文件头校验，拒绝 .svg/.html/.js 等可执行文档（上传目录与站点同源，否则等于开放 XSS）；单文件上限见 `PHXXBLOG_MAX_UPLOAD_SIZE`（默认 100MB），超限返回 413 并删除半成品文件。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `POST` | `/media/upload` | 登录 | `upload_file` |
| `GET` | `/media` | media:manage | `list_media` |
| `DELETE` | `/media/{media_id}` | media:manage | `delete_media` |

## 其他（4 个接口）

> 更新日志读写需 `changelog:manage`（注意 `PUT /misc/changelog` 会直接写仓库里的 CHANGELOG.md，要求该目录可写，且会让 git 工作区变 dirty）；一言与历史上的今天是公开代理接口。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/misc/changelog` | changelog:manage | `changelog` |
| `PUT` | `/misc/changelog` | changelog:manage | `update_changelog` |
| `GET` | `/misc/saying` | 公开 | `saying` |
| `GET` | `/misc/history/programmer-today` | 公开 | `programmer_history_today` |

## 文章（14 个接口）

> 列表仅返回已发布文章；状态为 0草稿/1审核中/2已发布/3私密/4回收站。无 `post:publish` 者提交 status=2 会被**静默降级**为审核中（作者提交发布请求不该收到报错），而状态流转接口 `PATCH /posts/{id}/status` 对越权直接返回 403。私密/回收站内容对无权者返回 404 而非 403，不暴露存在性。
>
> `/posts/hot` 按阅读量倒序返回已发布文章（前台首页与文章详情页侧栏的「热门文章」）；详情接口额外返回 `prev_post` / `next_post`，为按发布时间相邻的上一篇/下一篇，首尾文章对应项为 `null`。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/posts` | 公开 | `list_posts` |
| `GET` | `/posts/archive` | 公开 | `archive` |
| `GET` | `/posts/hot` | 公开 | `hot_posts` |
| `GET` | `/posts/admin` | 登录 | `admin_list_posts` |
| `GET` | `/posts/export` | 登录 | `export_posts` |
| `POST` | `/posts/import` | post:create | `import_posts` |
| `GET` | `/posts/{post_id}` | 可选登录 | `get_post` |
| `POST` | `/posts` | post:create | `create_post` |
| `PUT` | `/posts/{post_id}` | post:edit | `update_post` |
| `DELETE` | `/posts/{post_id}` | post:delete | `trash_post` |
| `DELETE` | `/posts/{post_id}/force` | post:manage | `force_delete_post` |
| `POST` | `/posts/{post_id}/restore` | 登录 | `restore_post` |
| `POST` | `/posts/{post_id}/publish` | 登录 | `change_post_status` |
| `POST` | `/posts/{post_id}/like` | 可选登录 | `like_post` |

## RSS/SEO（2 个接口）

> 公开；输出 RSS 与 sitemap。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/rss.xml` | 公开 | `rss_feed` |
| `GET` | `/sitemap.xml` | 公开 | `sitemap` |

## 搜索（1 个接口）

> 公开。关键词长度上限 100 字符。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/search` | 公开 | `search` |

## 设置（3 个接口）

> 公开设置可匿名读取（站点名/简介/模块开关等）；更新需 `setting:manage`。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/settings/public` | 公开 | `public_settings` |
| `GET` | `/settings` | setting:manage | `admin_settings` |
| `PUT` | `/settings` | setting:manage | `update_settings` |

## 统计（6 个接口）

> `/stats/track` 由前台埋点调用（公开）；其余为后台统计，需 `stats:view`。自定义区间的天数上限为 366 天。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `POST` | `/stats/track` | 公开 | `track` |
| `GET` | `/stats/overview` | stats:view | `overview` |
| `GET` | `/stats/trend` | stats:view | `trend` |
| `GET` | `/stats/visits` | stats:view | `visits` |
| `GET` | `/stats/contributions` | 公开 | `contributions` |
| `GET` | `/stats/sources` | stats:view | `sources` |

## 标签（4 个接口）

> 列表公开；写操作需 `post:manage`。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/tags` | 公开 | `list_tags` |
| `POST` | `/tags` | 登录 | `create_tag` |
| `PUT` | `/tags/{tag_id}` | post:manage | `update_tag` |
| `DELETE` | `/tags/{tag_id}` | post:manage | `delete_tag` |

## 用户管理（10 个接口）

> 需 `user:manage`；角色与权限相关接口需 `role:manage`。内置角色的 code 建议不要修改（业务代码已改为按权限码授权，但前端菜单等仍依赖 admin 角色名）。

| 方法 | 路径 | 鉴权 | 处理函数 |
| --- | --- | --- | --- |
| `GET` | `/users` | user:manage | `list_users` |
| `POST` | `/users` | user:manage | `create_user` |
| `PUT` | `/users/{user_id}` | user:manage | `update_user` |
| `PUT` | `/users/{user_id}/password` | user:manage | `reset_password` |
| `DELETE` | `/users/{user_id}` | user:manage | `delete_user` |
| `GET` | `/users/roles` | 登录 | `list_roles` |
| `POST` | `/users/roles` | role:manage | `create_role` |
| `PUT` | `/users/roles/{role_id}` | role:manage | `update_role` |
| `DELETE` | `/users/roles/{role_id}` | role:manage | `delete_role` |
| `GET` | `/users/permissions` | 登录 | `list_permissions` |

---

共 **73** 个接口：17 个公开，56 个需要鉴权。
