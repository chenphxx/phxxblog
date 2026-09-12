# phxxblog 技术架构与实现说明

> 本文档说明项目的技术栈、整体架构、目录职责与关键功能的实现方式。
> 相关文档: [接口设计](./api.md) · [数据库表结构](./mysql.md) · [更新日志](../CHANGELOG.md)

## 1. 项目概览

phxxblog 是一个前后端分离的个人博客系统, 前台与管理后台共用同一套 REST API。

- **前台**: 首页(个人主页 + 终端卡片 + 贡献热力图 + 程序员历史上的今天 + 一言)、文章列表与详情、归档时间轴、全部文章、日记(仅管理员)、更新日志(仅管理员)。
- **后台**: 数据看板、文章管理(含导入/导出)、分类标签、评论管理、媒体库、用户与角色权限、系统设置、操作日志、个人资料。
- **通用能力**: 账号体系(注册/登录/刷新令牌)、JWT + RBAC 权限、访问统计、深色/浅色主题、SEO(RSS 与 sitemap)。

## 2. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3(组合式 API + `script setup`)、TypeScript、Vite、Vue Router(hash 模式)、Pinia、Axios、Element Plus、Vditor(Markdown 编辑与渲染) |
| 后端 | Python 3.10+、FastAPI、SQLAlchemy 2.x(声明式 ORM)、Pydantic v2 / pydantic-settings、PyMySQL、PyJWT、bcrypt、feedgen、Markdown、requests |
| 数据库 | MySQL 9(utf8mb4 / utf8mb4_unicode_ci, `posts` 表带 ngram 中文全文索引) |
| 其他 | ip2region 离线 IP 库(可选)、start.bat 一键启动脚本 |

主要依赖版本(节选, 完整清单见 `backend/requirements.txt` 与 `frontend/package.json`):

| 依赖 | 版本 | 依赖 | 版本 |
| --- | --- | --- | --- |
| fastapi | 0.141 | vue | 3.5 |
| uvicorn | 0.52 | vue-router | 5.2 |
| sqlalchemy | 2.0 | pinia | 4.0 |
| pydantic | 2.13 | element-plus | 2.14 |
| PyMySQL | 1.2 | vditor | 3.11 |
| PyJWT / bcrypt | 2.13 / 5.0 | vite | 8.2 |
| feedgen / Markdown | 1.0 / 3.10 | typescript / vue-tsc | 6.0 / 3.3 |

## 3. 系统架构

```text
浏览器 (Vue3 SPA: 博客前台 + 管理后台, Pinia 状态 / Axios 请求 / Element Plus 组件)
   │
   │  Axios → /api/v1/**          上传与静态资源 → /assets/**
   ▼
Vite 开发代理(frontend/vite.config.ts, 仅开发环境)
   │  /api  /assets  /docs  /redoc  /openapi.json  →  http://localhost:8000
   ▼
FastAPI(backend/app/main.py)
   ├─ api/v1    路由层(依赖注入: 当前用户 / 权限校验 / 数据库会话)
   ├─ core      配置 · 安全(JWT/bcrypt) · 权限码 · 中间件(文档鉴权) · 统一响应
   ├─ services  业务服务(markdown / upload / stats / geo / ua / log / text / link_preview)
   ├─ models    SQLAlchemy 模型        ├─ schemas  Pydantic 请求与响应模型
   ▼
MySQL 9(SQLAlchemy + PyMySQL; 上传文件落盘在 assets/, 由 /assets 静态目录对外提供)
```

### 3.1 请求链路

1. 前端统一通过 Axios 实例请求 `/api/v1/**`; 开发环境由 Vite 代理到 `http://localhost:8000`, 同时代理 `/assets` 与文档路径 `/docs`、`/redoc`、`/openapi.json`(见 `frontend/vite.config.ts`)。
2. 请求拦截器自动附带 `Authorization: Bearer <access_token>`(令牌存于 localStorage)。
3. 后端通过 FastAPI 依赖注入完成"取当前用户 → 校验权限 → 提供数据库会话"。
4. 所有接口返回统一结构 `{ code, message, data }`, 前端响应拦截器解出 `data` 供业务代码直接使用。
5. 上传文件落盘到仓库根目录的 `assets/uploads/<年>/<月>/`, 再由后端的 `/assets` 静态目录对外提供访问。

### 3.2 运行形态

- **开发**: 后端 uvicorn(--reload, 8000) + 前端 Vite(5173), 直接运行根目录 `start.bat` 即可。
- **生产**: `npm run build` 产出 `frontend/dist`, 交给任意静态服务器(Nginx 等); 后端独立部署(uvicorn / gunicorn + systemd 或容器), 反向代理 `/api`、`/assets` 与文档路径到后端。

## 4. 目录结构

```text
phxxblog/
├── start.bat                     # 一键启动前后端(检查环境 -> 启动 -> 打印访问地址)
├── CHANGELOG.md                  # 更新日志(前台可直接展示与编辑)
├── docs/                         # 开发文档
│   ├── api.md                    # 接口清单
│   ├── mysql.md                  # 数据库表结构设计
│   └── architecture.md           # 本文档: 技术架构与实现说明
├── assets/                       # 上传文件与素材(uploads/<年>/<月>/ 由后端写入)
├── frontend/                     # 前端工程(Vue3 + TS + Vite)
│   ├── scripts/copy-vditor-assets.mjs   # 把 vditor 静态资源复制到 public/vditor
│   ├── vite.config.ts            # 别名 @ -> src, 开发代理(/api /assets /docs ...)
│   └── src/
│       ├── api/                  # http.ts(Axios 实例与拦截器) + index.ts(按模块的接口封装)
│       ├── components/           # 通用组件(MarkdownView / PostCard / 图表 / 评论等)
│       ├── layouts/              # 前台布局(顶栏 + 页脚)
│       ├── router/               # 路由表与登录守卫
│       ├── stores/               # Pinia: auth(登录态) / theme(深浅色)
│       ├── styles/theme.css      # 全局样式与深浅色 CSS 变量
│       ├── types/index.ts        # 与后端对齐的 TypeScript 类型
│       ├── utils/                # 文档 cookie、标签配色、文本统计等工具
│       └── views/                # 页面(前台 views/ + 后台 views/admin/)
└── backend/                      # 后端工程(FastAPI)
    ├── app/
    │   ├── main.py               # 应用入口: 中间件、异常处理、路由与静态目录挂载
    │   ├── seed.py               # 初始化: 权限/角色/管理员/默认设置/默认分类标签
    │   ├── api/v1/               # 路由层(按业务模块拆分)
    │   ├── core/                 # config / database / security / deps / permissions / middleware / response
    │   ├── models/               # ORM 模型
    │   ├── schemas/              # Pydantic 请求与响应模型
    │   └── services/             # 业务服务(markdown / upload / stats / geo / ua / log / text / link_preview)
    ├── scripts/                  # init_db.sql、migration_*.sql、WordPress 导入、IP 库下载等
    └── requirements.txt
```

## 5. 后端实现

### 5.1 应用入口 `backend/app/main.py`

- 创建 `FastAPI` 实例(标题/描述/版本即 `/docs` 上展示的内容)并注册 CORS 中间件(来源取 `PHXXBLOG_CORS_ORIGINS`, 默认 5173)。
- 注册自定义 HTTP 中间件 `restrict_docs_to_admin` 保护文档路径(见 7.21)。
- `startup` 钩子执行 `Base.metadata.create_all()` 自动建表(幂等), 并调用 `ensure_columns()` 为老库补齐新增列; 失败时只打印警告, 提示手工执行迁移 SQL。
- 统一异常处理: 业务异常 `HTTPException` → `{code, message, data}`; 参数校验失败 `RequestValidationError` → 422 + 第一条错误信息; 兜底 `Exception` 在调试模式下直接抛出便于排查。
- 挂载 `/api/v1` 汇总路由与 RSS/sitemap 路由, 并把 `assets/` 目录挂载为 `/assets` 静态资源。

### 5.2 配置管理 `backend/app/core/config.py`

基于 pydantic-settings, 从环境变量或 `backend/.env` 读取, 统一前缀 `PHXXBLOG_`, 通过 `get_settings()` 提供单例。

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `PHXXBLOG_DEBUG` | true | 调试模式(同时决定 SQLAlchemy 是否打印 SQL) |
| `PHXXBLOG_DATABASE_URL` | mysql+pymysql://root:password@localhost:3306/phxxblog | 数据库连接串 |
| `PHXXBLOG_SECRET_KEY` | change-me-to-a-random-secret-key | JWT 签名密钥 |
| `PHXXBLOG_ALGORITHM` | HS256 | JWT 算法 |
| `PHXXBLOG_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | 访问令牌有效期 |
| `PHXXBLOG_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | 刷新令牌有效期 |
| `PHXXBLOG_CORS_ORIGINS` | http://localhost:5173,http://127.0.0.1:5173 | 允许的跨域来源(逗号分隔) |
| `PHXXBLOG_UPLOAD_DIR` | `<仓库根目录>/assets/uploads` | 上传目录(相对路径按启动目录解析) |
| `PHXXBLOG_GEO_DB_PATH` | backend/data/ip2region_v4.xdb | 离线 IP 库路径 |
| `PHXXBLOG_MAX_UPLOAD_SIZE` | 100MB | 单文件大小上限 |
| `PHXXBLOG_SITE_URL` | http://localhost:5173 | 站点地址(RSS/sitemap 生成绝对链接) |

### 5.3 数据层

- `core/database.py`: 以 `DeclarativeBase` 定义 `Base`; `engine` 开启 `pool_pre_ping` 与 `pool_recycle=3600`; `SessionLocal` 使用 `autoflush=False, expire_on_commit=False`; `get_db()` 作为请求级会话依赖。
- `ensure_columns()`: 用 SQLAlchemy 反射检查表结构, 对缺失的新增列执行幂等 `ALTER TABLE`(当前为 `categories.color`、`tags.color`)。
- 模型层 `models/*.py`: 使用 SQLAlchemy 2.0 的 `Mapped / mapped_column` 声明; `posts` 建有 `(status, published_at)`、`category_id`、`author_id` 索引与 ngram 全文索引; 关联对象用 `lazy="selectin"` 预加载避免 N+1。
- `seed.py`: 初始化权限码、三种角色(admin/editor/author)、管理员账号(仅当库中无用户时创建)、默认系统设置与默认分类/标签。

### 5.4 认证与授权

- **密码**: bcrypt 散列存储(`core/security.py` 的 `hash_password / verify_password`)。
- **访问令牌**: JWT(HS256), 默认 30 分钟失效, 载荷为 `{sub, iat, exp, type: access, username}`。
- **刷新令牌**: `secrets.token_urlsafe(48)` 随机串, 数据库只保存 SHA-256 散列与 `ip/user_agent/expires_at/revoked`, 默认 7 天, 支持吊销(登出)。
- **依赖注入**(`core/deps.py`): `get_current_user` 必须登录; `get_optional_user` 允许游客(点赞、文章详情用); `require_permission(code)` 做权限码校验; `get_client_ip` 兼容 `X-Forwarded-For`。
- **权限模型**: 用户-角色、角色-权限均为多对多; 权限码定义在 `core/permissions.py`(post:create / post:edit / post:publish / post:delete / post:manage / comment:manage / user:manage / role:manage / media:manage / setting:manage / log:view / stats:view / data:export)。除权限码外, 文章还会做资源级判断(`_can_manage`: 作者本人或管理员)。

### 5.5 统一响应与异常

成功响应直接由 `core/response.py` 的 `ok(data, message)` 生成; 失败响应由全局异常处理器生成; 两者结构一致, 前端只需处理一个分支。

```json
{ "code": 0, "message": "ok", "data": {} }
```

列表接口统一返回分页结构: `{ items, total, page, page_size }`(`schemas/common.py` 的 `Page`)。

### 5.6 业务服务层 `backend/app/services/`

| 文件 | 职责 |
| --- | --- |
| `markdown.py` | Markdown → HTML(fenced_code / tables / nl2br / attr_list / toc 等扩展), 代码高亮交给前端 |
| `upload.py` | 上传校验与落盘: 按扩展名判定 image/video/file, 按 `年/月` 分目录, UUID 文件名, 分块写入 |
| `text.py` | 字数统计(中日韩按字、英文按词)与预计阅读时间(300 字/分钟, 不足 1 分钟按 1 分钟) |
| `geo.py` | ip2region 离线库查询 IP 归属地, 懒加载 + 缺失时优雅降级为空 |
| `ua.py` | 轻量正则解析 User-Agent(浏览器/系统/设备) |
| `stats.py` | 记录访问明细: 写 `visit_logs`、累加 PV、当日首次 IP 累加 UV、文章访问累加阅读量 |
| `log.py` | 写操作日志(谁、何时、哪个模块、什么动作、目标对象、IP) |
| `link_preview.py` | 抓取目标网页的 og:title / description / image 生成链接卡片 |

### 5.7 路由模块一览 `backend/app/api/v1/`

| 模块 | 前缀 | 说明 |
| --- | --- | --- |
| auth | /api/v1/auth | 注册、登录、刷新、登出、当前用户、改密码/邮箱/资料 |
| users | /api/v1/users | 用户与角色权限管理(含重置密码) |
| posts | /api/v1/posts | 文章: 前台列表、归档、后台列表、详情、增删改、回收站、发布状态、点赞、导入/导出 |
| categories / tags | /api/v1/categories, /api/v1/tags | 分类与标签(含颜色) |
| comments | /api/v1/comments, /api/v1/posts/{id}/comments | 评论的读取、发布与后台管理 |
| media | /api/v1/media | 媒体上传、列表、删除 |
| diaries | /api/v1/diaries | 日记(仅管理员) |
| misc | /api/v1/misc | 更新日志读写、一言、程序员历史上的今天 |
| stats | /api/v1/stats | 埋点、概览、趋势、来源、访问记录、贡献数据 |
| dashboard | /api/v1/dashboard | 后台看板聚合数据 |
| logs | /api/v1/logs | 操作日志查询 |
| settings | /api/v1/settings | 公开配置与后台全部配置的读写 |
| search | /api/v1/search | 站内搜索 |
| links | /api/v1/links | 链接预览 |
| rss | /rss.xml, /sitemap.xml | 订阅与站点地图(不在 /api/v1 下) |

## 6. 前端实现

### 6.1 入口与主题 `frontend/src/main.ts`

- 创建应用并注册 Pinia、Vue Router、Element Plus(中文语言包 `zh-cn`, 全局 Message 可手动关闭)。
- 引入样式: `element-plus/dist/index.css`、`element-plus/theme-chalk/dark/css-vars.css`、`vditor/dist/index.css` 与项目自己的 `styles/theme.css`。
- 应用挂载前先读取 localStorage 中的主题并给 `html` 加上 `dark` 类, 避免首屏闪白。
- `frontend/scripts/copy-vditor-assets.mjs` 在 `predev / prebuild` 阶段把 `node_modules/vditor/dist` 复制到 `public/vditor/dist`, 使 Vditor 的 Lute、图标、高亮资源全部走本地, 不依赖 CDN。

### 6.2 路由与布局

- 使用 hash 模式(`createWebHashHistory`), 便于静态托管: 前台 `/`、`/post/:id`、`/archive`、`/posts`、`/search`、`/write(/:id)`、`/changelog`、`/diary`; 后台 `/admin/**`(仪表盘/文章/分类标签/评论/媒体/用户/设置/日志/资料)。
- 全局前置守卫: 路由标记 `meta.requiresAuth` 且本地无令牌时跳转登录页并带上 `redirect`。
- 前台布局 `layouts/SiteLayout.vue`: 顶栏(站点名 + 终端风格提示符 + 导航 + 主题开关) + 内容区 + 页脚; 布局层负责加载公开配置(站点名/标签页标题/图标)与访问埋点。
- 后台布局 `views/admin/AdminLayout.vue`: 侧边菜单 + 顶栏(API 文档入口、主题开关、退出登录)。
- 前台部分页面使用 `keep-alive` 缓存(首页、全部文章、归档、搜索), 并用 `onActivated` 在返回时刷新数据。

### 6.3 状态管理 `stores/`

- `auth.ts`: `accessToken / refreshToken / user` 三份状态与 localStorage 同步; 登录成功后写入会话, 同时把 access token 同步到 API 文档鉴权 cookie; 登出时清理令牌、cookie 并跳转登录页。
- `theme.ts`: 深浅色开关, 通过 `html.dark` 与 `data-theme` 属性切换 CSS 变量并持久化。

### 6.4 请求层 `api/`

- `http.ts`: `axios.create({ baseURL: '/api/v1' })`; 请求拦截器附加 Bearer 令牌; 响应拦截器解包 `data` 字段(blob 下载除外), 统一弹出错误提示, 401 时清理本地会话与文档 cookie 并跳转登录页。
- `index.ts`: 按业务域封装接口(authApi、postApi、categoryApi、tagApi、commentApi、mediaApi、statsApi、diaryApi、miscApi、logApi、settingsApi、searchApi、linkApi、userApi), 并导出与后端对齐的请求/响应类型。
- 刷新令牌接口已封装(`authApi.refresh`), 当前拦截器策略为 401 直接清理会话(未做自动续期), 需要时可在此处扩展静默刷新。

### 6.5 组件 `components/`

| 组件 | 职责 |
| --- | --- |
| `MarkdownView.vue` | 文章正文渲染: Vditor 预览 + 代码高亮/折叠 + 图片点击预览 |
| `VditorEditor.vue` | 写作页编辑器(即时渲染模式、工具栏、图片上传、深浅色联动) |
| `PostCard.vue` | 文章卡片: 标题、摘要、分类/标签彩色标签、字数与阅读时间、views/likes、状态标签 |
| `ContributionsChart.vue` | GitHub 风格贡献热力图(纯 SVG/CSS 实现, 支持按年切换) |
| `TrendChart.vue` | 访问趋势折线/柱状图(纯 SVG 实现, 无第三方图表库) |
| `CommentSection.vue / CommentNode.vue` | 评论区与递归渲染的多层回复 |
| `LinkCard.vue` | 链接预览卡片 |
| `ThemeToggle.vue` | 深浅色切换按钮 |

### 6.6 样式与主题

- `styles/theme.css` 用 CSS 变量定义配色(`:root` 浅色、`html.dark` 深色), 页面与组件只引用变量, 因此切换主题无需改动组件样式。
- 代码块背景与高亮风格对齐 VSCode 默认主题: 浅色用 `vs`、深色用 `vs2015`, 并统一注释为斜体、字号与正文字号联动。
- 分类/标签与 views/likes 的彩色标签由 `utils/chipColor.ts` 计算: 后台配置了颜色则使用该颜色, 否则按名称哈希生成稳定色相, 再用 `color-mix` 生成背景、边框与文字色, 深浅色下均自动适配。

## 7. 关键功能实现

### 7.1 文章状态与可见性

状态取值: 0 草稿 / 1 审核中 / 2 已发布 / 3 私密 / 4 回收站。前台列表只返回已发布文章; 详情接口对非公开文章要求"作者本人或管理员"; 删除默认进回收站(可恢复), `/force` 为彻底删除。每次创建/更新/发布/删除都会写操作日志。

### 7.2 Markdown 渲染与代码高亮

前端 `MarkdownView.vue` 调用 `Vditor.preview()` 渲染正文(资源走本地 `/vditor`), 随后:

1. `Vditor.codeRender / mediaRender` 生成代码复制按钮与视频/音频/iframe 结构。
2. 未标注语言的代码块用 highlight.js 自动识别语言: 先用特征规则匹配常见语言(C/C++/Rust/PowerShell 等), 再按候选语言集合打分选取相关度最高者, 相关度为 0 则保持纯文本, 避免误上色。
3. `Vditor.highlightRender` 统一重渲染以套用行号与主题(vs / vs2015)。
4. 超过 20 行的代码块包一层 `code-block` 容器, 折叠时用 `max-height` 裁剪并隐藏纵向溢出, 点击按钮展开/收起(主题切换后保持展开状态)。

后端只把 Markdown 转成带 class 的 HTML(`services/markdown.py`), 高亮完全在前端完成。

### 7.3 图片点击预览

正文图片点击后使用 Element Plus 的图片查看器(`el-image-viewer`): 图片按窗口等比缩放并居中显示(不再按原始分辨率铺满页面), 支持鼠标滚轮缩放、拖拽平移、旋转与恢复原始尺寸, 关闭方式支持 ✕、Esc 与点击遮罩。

### 7.4 字数与预计阅读时间

`backend/app/services/text.py` 统计中日韩字符数 + 英文单词数, 按 300 字/分钟估算阅读时间; `Post` 模型以 `word_count / reading_minutes` 属性暴露给接口, 文章列表与详情页在 meta 区展示 "约 N 字 · 大约 M 分钟"。前端 `utils/textStats.ts` 保留同算法的实现, 便于前端本地统计。

### 7.5 文章摘要

`posts.summary` 字段由作者在写作页手动填写, 不自动生成; 列表页在标题下方展示摘要, 详情页在正文上方以引用块样式展示, 未填写则不渲染该区域。

### 7.6 分类与标签配色

`categories``tags` 表新增 `color` 列(后台可填色值, 留空则由前端按名称生成兜底色)。前端所有展示分类/标签的位置(文章卡片、详情页 meta、首页分类胶囊)统一调用 `chipStyle(name, color)` 生成内联样式, 保证同一分类/标签在全站颜色一致。

### 7.7 首页模块开关与分页

后台`系统设置 → 前台展示`提供四个开关(主页 README、文章发布记录、程序员历史上的今天、session 终端卡片), 以 `1/0` 存入 `settings` 表, 由 `/settings/public` 输出为布尔值。首页按开关决定是否渲染对应模块, 并跳过对应的接口请求(不浪费请求); 首页文章列表默认展示最近 10 篇, 底部分页可查看更早文章, 翻页后自动回到列表顶部。

### 7.8 一言(每天仅刷新一次)

后端 `/api/v1/misc/saying` 代理第三方接口, 并把结果按天缓存到 `settings` 表的 `saying_cache` 键(JSON: `{date, text}`): 同一天内所有访客共用同一条, 不再每次进入首页都请求外部接口; 前端点击"换一句"时传 `force=true` 强制刷新; 外部接口异常时回退到旧缓存, 避免页面空白。

### 7.9 程序员历史上的今天

`/api/v1/misc/history/programmer-today` 代理第三方接口并按接口返回的结构透出 `{date, events}`, 前端在首页以时间线卡片展示, 可手动刷新。

### 7.10 页脚与浏览器标签页

- 页脚包含备案信息(数组配置, 可选)与版权信息(`footer_text` 配置, 支持 `{year}`/`{site_name}` 占位符, 留空则不显示该行); 页脚高度由内容决定, 两者都为空时整个页脚不渲染。
- 浏览器标签页名称取 `site_title`, 留空回退站点名称; 前台布局与后台布局在加载公开配置后都会设置 `document.title`, 站点图标同理动态替换 `link[rel=icon]`。

### 7.11 评论

游客即可评论(记录 IP 与归属地); 评论支持多级回复(`parent_id` 自关联), 前端用递归组件渲染; 可附带图片/附件; 后台可编辑、审核(状态)与删除。

### 7.12 点赞

`/posts/{id}/like` 为"切换式"接口: 登录用户按账号去重, 游客按 IP 去重, 已点赞再次调用即取消; 点赞同时累加当天的 `likes` 统计。

### 7.13 媒体上传

`/media/upload` 接收 `multipart/form-data`, 按扩展名判定类型, 文件名使用 UUID、按 `年/月` 分目录落盘, 返回可直接访问的 `/assets/...` URL; 前端写作页与媒体库共用该接口, Vditor 的上传也指向它(请求头带 Bearer 令牌)。媒体表记录原始名、路径、MIME、大小、类型与关联对象。

### 7.14 访问统计与贡献热力图

- 前台布局挂载时调用 `/stats/track` 埋点; 文章详情接口在成功返回已发布文章时也会记录一次访问。
- `services/stats.py` 写 `visit_logs` 明细(IP、UA、Referer、URL、浏览器/系统/设备), 累加当日 PV、当日新 IP 计 UV, 并累加文章阅读量。
- `/stats/trend` 按日/月/年聚合, 前端 `TrendChart` 渲染折线或柱状图; `/stats/sources` 输出来源/浏览器/设备 TOP 榜; `/stats/visits` 分页返回访问明细(含归属地)。
- `/stats/contributions` 返回近 N 周或指定年份每天的发布数量(文章或日记), 前端 `ContributionsChart` 渲染 GitHub 风格热力图。

### 7.15 操作日志

`services/log.py` 在关键写操作(登录/注册、文章增删改与导入导出、评论、媒体、用户、设置等)后写入 `operation_logs`; 后台日志页支持按用户/模块/动作筛选, 并展示 IP 归属地。

### 7.16 站内搜索

`/search` 对已发布文章的标题、摘要、正文做模糊匹配(`LIKE`), 支持发布时间区间与分页; `posts` 表同时保留了 ngram 全文索引, 数据量大时可切换为 `MATCH ... AGAINST` 以提升性能。

### 7.17 归档

`/posts/archive` 一次性取回所有已发布文章并在服务端按 `年-月` 分组(含每组数量), 前端 `ArchiveView` 渲染时间轴, 支持跳转到指定时间段。

### 7.18 RSS 与 Sitemap

`api/v1/rss.py` 用 feedgen 生成 `/rss.xml`, 站点名称与描述取自 `settings` 表; `/sitemap.xml` 输出已发布文章的 URL 列表, 两者都使用 `PHXXBLOG_SITE_URL` 拼接绝对地址。

### 7.19 文章导入导出

- 导出: `/posts/export?ids=...&fmt=markdown|zip` 把选中文章导出为 Markdown(带 frontmatter: 标题、slug、摘要、分类、标签、发布时间、状态等)或打包为 zip, 一并附带正文引用到的本地图片。
- 导入: 上传一个或多个 Markdown/zip 文件, 解析 frontmatter、自动生成不冲突的 slug、按名称匹配或创建分类与标签, 并把压缩包内的图片保存到上传目录同时改写正文中的图片地址。

### 7.20 WordPress 数据迁移

`backend/scripts/import_wordpress.py` 解析 WXR XML: 正文由 Gutenberg/HTML 转为 Markdown, 自动创建作者账号、导入分类/标签/评论, 下载附件到 `assets/uploads/wordpress/` 并登记媒体库, 同时把正文中的旧站图片链接改写为本地地址。

### 7.21 API 文档鉴权

`core/middleware.py` 的 `restrict_docs_to_admin` 拦截 `/docs`、`/redoc`、`/openapi.json` 与 OAuth 回调页:

1. 从 `Authorization: Bearer <token>` 或 cookie `phxxblog_doc_token` 取访问令牌, 两者都没有返回 401。
2. 校验 JWT(必须是 access 类型)并查询用户; 令牌非法/过期或用户不存在返回 401。
3. 用户被禁用或角色中不含 `admin` 返回 403。
4. 通过后放行到 FastAPI 自带的文档页面。

令牌来源的配合: 前端登录或恢复会话时把 access token 写入 `phxxblog_doc_token` cookie(SameSite=Lax, https 下附带 Secure), 登出或令牌失效时清除; 因此后台顶栏的"API 文档"按钮可以直接新窗口打开 `/docs`, 无需在 URL 上携带令牌。

## 8. 数据模型概览

| 表 | 说明 |
| --- | --- |
| users / roles / permissions | 用户、角色、权限及两张多对多关联表; refresh_tokens 存刷新令牌散列 |
| posts / categories / tags | 文章(状态、摘要、封面、阅读量、点赞数、IP/归属地)、分类与标签(含颜色), 文章-标签多对多 |
| comments / post_likes | 评论(自关联多级回复)与点赞去重记录 |
| media | 上传文件元数据与实际路径 |
| diaries | 日记(仅管理员, 支持附件) |
| visit_logs / daily_stats | 访问明细与按日聚合统计(PV/UV/点赞数) |
| operation_logs | 操作日志 |
| settings | 键值对配置(站点信息、前台展示开关、页脚、一言缓存等) |

字段级说明见 [mysql.md](./mysql.md)。

## 9. 部署与运行

### 9.1 本地开发

```bash
# 后端
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
copy .env.example .env                                        # 修改数据库密码
.venv/Scripts/python.exe -m app.seed                          # 初始化权限/角色/管理员/默认设置
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

也可直接双击根目录 `start.bat`: 脚本会检查虚拟环境与依赖、缺少 `.env` 时自动从示例复制, 然后分别开两个窗口启动前后端并打印访问地址。

### 9.2 生产部署要点

1. 前端执行 `npm run build`(内部先跑 `vue-tsc` 类型检查), 产物在 `frontend/dist`, 交给静态服务器托管。
2. 后端以 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 或 gunicorn + uvicorn worker 运行, 建议关闭 `PHXXBLOG_DEBUG`。
3. 反向代理需要转发 `/api`、`/assets`, 如需在线文档再转发 `/docs`、`/redoc`、`/openapi.json`; 若前端与后端不同域, 还要把前端域名加入 `PHXXBLOG_CORS_ORIGINS`。
4. 生产环境务必替换 `PHXXBLOG_SECRET_KEY`, 并保证 `backend/data/ip2region_v4.xdb` 已下载(否则评论归属地显示为空)。

## 10. 开发约定

- 代码注释与文档统一使用中文, 注释说明"为什么"而非重复代码本身。
- 所有接口统一返回 `{code, message, data}`, 列表统一分页结构; 前端只解包一次。
- 权限校验放在路由层(依赖 `require_permission` 或资源级判断), 业务服务层不感知 HTTP 上下文。
- 新增数据库列时, 除修改模型外要同步 `backend/scripts/migration_*.sql`, 并在 `ensure_columns()` 中登记, 保证老库能自动补齐。
- 前端提交前建议执行类型检查与构建: `cd frontend && npm run build`。
- 功能变更同步更新根目录 `CHANGELOG.md`(前台可展示给访客)。
