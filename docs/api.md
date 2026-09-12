# API 接口设计

> 基础路径: `/api/v1`, 数据格式 JSON, 认证使用 `Authorization: Bearer <access_token>`。
> 在线文档: `/docs`(Swagger UI)、`/redoc`、`/openapi.json` 仅 `admin` 角色可访问,
> 支持 `Authorization: Bearer <access_token>` 或登录后自动写入的 cookie `phxxblog_doc_token`;
> 未登录返回 401, 已登录但非管理员返回 403。

## 通用约定

- 成功响应统一为 `{ "code": 0, "message": "ok", "data": ... }`
- 失败响应统一为 `{ "code": <非0>, "message": "错误说明", "data": null }`
- 列表接口统一分页参数: `page`(默认1)、`page_size`(默认10), 返回 `{ "items": [...], "total": n, "page": p, "page_size": s }`

## 认证 auth

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/v1/auth/register | 注册 |
| POST | /api/v1/auth/login | 登录, 返回 access_token + refresh_token |
| POST | /api/v1/auth/refresh | 刷新令牌 |
| POST | /api/v1/auth/logout | 注销(吊销 refresh token) |
| GET | /api/v1/auth/me | 当前登录用户信息 |
| PUT | /api/v1/auth/password | 修改密码 |
| PUT | /api/v1/auth/email | 修改邮箱 |

## 用户 users

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/users | 用户列表(管理) |
| POST | /api/v1/users | 创建用户 |
| PUT | /api/v1/users/{id} | 编辑用户 |
| DELETE | /api/v1/users/{id} | 删除用户 |
| GET | /api/v1/roles | 角色列表 |
| POST | /api/v1/roles | 创建角色 |
| PUT | /api/v1/roles/{id} | 编辑角色(含权限) |
| DELETE | /api/v1/roles/{id} | 删除角色 |
| GET | /api/v1/permissions | 权限列表 |

## 文章 posts

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/posts | 已发布文章列表(前台, 支持关键词/分类/标签/时间筛选) |
| GET | /api/v1/posts/admin | 文章管理列表(后台, 含草稿/审核中/私密/回收站) |
| GET | /api/v1/posts/{id} | 文章详情(已发布公开; 作者/管理员可见非公开) |
| POST | /api/v1/posts | 新增文章(草稿) |
| PUT | /api/v1/posts/{id} | 编辑文章 |
| DELETE | /api/v1/posts/{id} | 删除(进回收站) |
| DELETE | /api/v1/posts/{id}/force | 彻底删除 |
| POST | /api/v1/posts/{id}/publish | 发布(草稿→审核中/已发布, 依权限) |
| POST | /api/v1/posts/{id}/restore | 从回收站恢复 |
| POST | /api/v1/posts/{id}/like | 点赞(游客按IP) |
| GET | /api/v1/posts/archive | 归档数据(按年/月分组) |

> 文章与评论均记录发布/评论时的 IP, 并在响应中返回 `location`(省市区文案, 基于离线 ip2region 定位)。

> 导入导出: `GET /api/v1/posts/export?ids=1,2&fmt=markdown|html` 导出 zip(markdown 带 frontmatter, 图片一并打包); `POST /api/v1/posts/import` 上传 .md 或 zip 导入(默认草稿), 支持 `mode=check`(只查重不写入)与 `on_duplicate=skip|all`(重复时跳过 / 一并导入)。

## 日记 diaries

仅管理员可访问(其他角色返回 403, 未登录返回 401)。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/diaries | 日记列表(分页, 按日期倒序) |
| POST | /api/v1/diaries | 新增日记 |
| PUT | /api/v1/diaries/{id} | 编辑日记 |
| DELETE | /api/v1/diaries/{id} | 删除日记 |
| GET | /api/v1/diaries/export | 导出 zip(参数 ids 逗号分隔, 不传导出全部; fmt=markdown\|html) |
| POST | /api/v1/diaries/import | 上传 .md 或 zip 导入(可多选); `mode=check` 只查重, `on_duplicate=skip\|all` 决定重复内容的处理 |

> 导出的 Markdown 以 `YYYY-MM-DD.md` 命名并带 `date`/`created_at` frontmatter, 图片一并打包; 导入时日期优先取 frontmatter 再取文件名日期。
> 查重口径: 文章按标题(忽略大小写与首尾空格), 日记按正文(忽略空白差异, 图片地址只比较文件名), 同一批文件内部重复同样会被识别。

## 分类与标签

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/categories | 分类列表 |
| POST / PUT / DELETE | /api/v1/categories[/{id}] | 分类管理 |
| GET | /api/v1/tags | 标签列表 |
| POST / PUT / DELETE | /api/v1/tags[/{id}] | 标签管理 |

## 评论 comments

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/posts/{post_id}/comments | 文章评论列表 |
| POST | /api/v1/posts/{post_id}/comments | 发表评论(游客/用户, 支持回复) |
| GET | /api/v1/comments/admin | 评论管理列表(后台) |
| PUT | /api/v1/comments/{id} | 修改评论状态(隐藏/显示/回收站) |
| DELETE | /api/v1/comments/{id} | 删除评论 |

> 前台评论列表只展示 `location`(省市区), 原始 `ip` 字段仅后台管理接口可见。

## 媒体 media

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/v1/media/upload | 上传图片/视频/附件(multipart), 存储到 `assets/` |
| GET | /api/v1/media | 媒体列表(管理) |
| DELETE | /api/v1/media/{id} | 删除媒体(同时删除文件) |
| GET | /assets/{path} | 静态文件访问(由后端挂载) |

## 统计与看板

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/stats/overview | 统计总览(文章数/总访问量/评论数/用户数) |
| GET | /api/v1/stats/trend | 按日趋势(PV/UV) |
| GET | /api/v1/stats/sources | 访问来源/浏览器/设备占比 |
| GET | /api/v1/dashboard | Dashboard 汇总数据 |

## 日志 logs

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/logs | 操作日志列表(可按用户/模块/时间筛选) |

## 其他

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/v1/search | 全文搜索(标题/摘要/正文) |
| GET | /rss.xml | RSS 订阅 |
| GET | /sitemap.xml | SEO 站点地图 |
| GET | /api/v1/settings/public | 前台公开配置(站点名/标签页标题/简介/社交链接等) |
| GET | /api/v1/settings | 后台设置列表 |
| PUT | /api/v1/settings | 更新设置 |
