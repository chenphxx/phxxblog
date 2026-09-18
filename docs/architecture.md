# phxxblog 技术架构与实现说明

> 本文档说明项目的技术栈, 整体架构, 目录职责与关键功能的实现方式 
> 相关文档: [接口设计](./api.md), [数据库表结构](./mysql.md), [测试与检查说明](./testing.md), [更新日志](../CHANGELOG.md) 

## 1. 项目概览

phxxblog 是一个前后端分离的个人博客系统, 前台与管理后台共用同一套 REST API 

- **前台**: 首页(个人主页 + 终端卡片 + 贡献热力图 + 程序员历史上的今天 + 一言), 文章列表与详情, 归档时间轴, 全部文章, 日记(仅管理员), 更新日志(仅管理员) 
- **后台**: 数据看板, 文章管理(含导入/导出), 分类标签, 评论管理, 媒体库, 用户与角色权限, 系统设置, 操作日志, 个人资料 
- **通用能力**: 账号体系(注册/登录/刷新令牌), JWT + RBAC 权限, 访问统计, 深色/浅色主题, SEO(RSS 与 sitemap) 

## 2. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3(组合式 API + `script setup`), TypeScript, Vite, Vue Router(hash 模式), Pinia, Axios, Element Plus, Vditor(Markdown 编辑与渲染) |
| 后端 | Python 3.10+, FastAPI, SQLAlchemy 2.x(声明式 ORM), Pydantic v2 / pydantic-settings, PyMySQL, PyJWT, bcrypt, feedgen, Markdown, requests |
| 数据库 | MySQL 9(utf8mb4 / utf8mb4_unicode_ci, `posts` 表带 ngram 中文全文索引) |
| 字体 | Cascadia Code(自托管 latin 子集, `frontend/public/fonts/`) |
| 测试 | pytest + httpx(内存 SQLite, 见 `backend/tests/`) |
| 其他 | ip2region 离线 IP 库(vendored, 可选), start.bat 一键启动脚本 |

> **没有引入数据库迁移工具**(Alembic) 新表由 `create_all` 自动创建, 已有表加列需手工写迁移 SQL; 
> 应用启动时会校验模型与库结构是否一致, 缺列则拒绝启动 约定见 `docs/mysql.md` 的"表结构演进" 

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

1. 前端统一通过 Axios 实例请求 `/api/v1/**`; 开发环境由 Vite 代理到 `http://localhost:8000`, 同时代理 `/assets` 与文档路径 `/docs`, `/redoc`, `/openapi.json`(见 `frontend/vite.config.ts`) 
2. 请求拦截器自动附带 `Authorization: Bearer <access_token>`(令牌存于 localStorage) 
3. 后端通过 FastAPI 依赖注入完成"取当前用户 → 校验权限 → 提供数据库会话" 
4. 所有接口返回统一结构 `{ code, message, data }`, 前端响应拦截器解出 `data` 供业务代码直接使用 
5. 上传文件落盘到仓库根目录的 `assets/uploads/<年>/<月>/`, 再由后端的 `/assets` 静态目录对外提供访问 

### 3.2 运行形态

- **开发**: 后端 uvicorn(--reload, 8000) + 前端 Vite(5173), 直接运行根目录 `start.bat` 即可 
- **生产**: `npm run build` 产出 `frontend/dist`, 交给任意静态服务器(Nginx 等); 后端独立部署(uvicorn / gunicorn + systemd 或容器), 反向代理 `/api`, `/assets` 与文档路径到后端 

## 4. 目录结构

```text
phxxblog/
├── start.bat                     # 一键启动前后端(检查环境 -> 启动 -> 打印访问地址)
├── CHANGELOG.md                  # 更新日志(前台可直接展示与编辑)
├── docs/                         # 开发文档
│   ├── api.md                    # 接口清单(由 backend/scripts/gen_api_doc.py 生成)
│   ├── mysql.md                  # 数据库表结构设计
│   └── architecture.md           # 本文档: 技术架构与实现说明
├── assets/                       # 上传文件与素材(uploads/<年>/<月>/ 由后端写入)
├── .github/workflows/            # CI: 前端构建发布 / 后端测试 + 主题与图标校验
├── frontend/                     # 前端工程(Vue3 + TS + Vite)
│   ├── public/fonts/             # 自托管 Cascadia Code(latin 子集)与 OFL 许可
│   ├── public/kanbanniang/       # 看板娘: 自托管 Live2D 运行时与模型(见该目录 README)
│   ├── scripts/
│   │   ├── copy-vditor-assets.mjs  # 把 vditor 静态资源复制到 public/vditor
│   │   ├── check-icons.mjs         # 校验 MetaIcon 的 SVG path(npm run check:icons)
│   │   └── measure-first-paint.mjs # 量首屏/整包体积(npm run check:size)
│   ├── vitest.config.ts          # 单测配置(与 vite.config.ts 分开, 见 frontend/README.md)
│   └── src/
│       ├── api/                  # http.ts(Axios 实例、拦截器与 401 静默刷新) + index.ts(按模块的接口封装)
│       ├── components/           # 通用组件(MarkdownView / PostCard / MetaIcon / 图表 / 评论等)
│       ├── composables/          # 跨视图复用逻辑(usePostEditor / useImportExport)
│       ├── kanbanniang/          # 看板娘形象清单(registry.ts)与运行时加载(loader.ts)
│       ├── layouts/              # 前台布局(顶栏 + 页脚)
│       ├── router/               # 路由表与登录守卫
│       ├── stores/               # Pinia: auth(登录态) / theme(深浅色 + 9 套配色主题) / kanbanniang(看板娘)
│       ├── styles/
│       │   ├── theme.css         # 结构样式与基础令牌
│       │   ├── theme-green.css   # 主题入口(汇总各主题 CSS)
│       │   ├── admin.css         # 后台主题层(Element Plus 主色与语义色 -> 主题令牌)
│       │   ├── fonts.css         # 自托管 Cascadia Code 的 @font-face
│       │   └── themes/           # 9 套主题令牌(生成物) + registry.ts + _source/(源与脚本)
│       ├── types/index.ts        # 与后端对齐的 TypeScript 类型
│       ├── utils/                # 令牌存储、文档 cookie、标签配色、文本统计等工具
│       └── views/                # 页面(前台 views/ + 后台 views/admin/)
└── backend/                      # 后端工程(FastAPI)
    ├── app/
    │   ├── main.py               # 应用入口: 中间件、异常处理、路由与静态目录挂载
    │   ├── seed.py               # 初始化: 权限/角色/管理员/默认设置/默认分类标签
    │   ├── api/v1/               # 路由层(按业务模块拆分)
    │   ├── core/                 # config / database / security / deps / permissions / pagination / ratelimit / middleware / response
    │   ├── models/               # ORM 模型
    │   ├── schemas/              # Pydantic 请求与响应模型
    │   └── services/             # 业务服务(markdown / upload / stats / geo / ua / log / text / link_preview / archive / post_write / ip2region)
    ├── tests/                    # pytest 用例(内存 SQLite, 不碰开发库)
    ├── scripts/                  # init_db.sql、migration_*.sql、WordPress 导入、IP 库下载、接口文档生成等
    ├── requirements.txt          # 运行依赖
    └── requirements-dev.txt       # 测试依赖(pytest / httpx)
```

## 5. 后端实现

### 5.1 应用入口 `backend/app/main.py`

- 创建 `FastAPI` 实例(标题/描述/版本即 `/docs` 上展示的内容)并注册 CORS 中间件(来源取 `PHXXBLOG_CORS_ORIGINS`, 默认 5173) 
- 注册自定义 HTTP 中间件 `restrict_docs_to_admin` 保护文档路径(见 7.21) 
- `startup` 钩子执行 `Base.metadata.create_all()` 自动建表(幂等), 再建 `schema_version` 表, 
  最后调用 `check_schema()` **校验模型与库结构是否一致**: 缺列时 `debug=true` 只告警并打印 `ALTER` 语句, 
  否则拒绝启动 取代了旧的 `ensure_columns()` 静默补列(只认两列, 其余加列不报错, 直到查询才炸) 
- 统一异常处理: 业务异常 `HTTPException` → `{code, message, data}`; 参数校验失败 `RequestValidationError` → 422 + 第一条错误信息; 兜底 `Exception` 在调试模式下直接抛出便于排查 
- 挂载 `/api/v1` 汇总路由与 RSS/sitemap 路由, 并把 `assets/` 目录挂载为 `/assets` 静态资源 

### 5.2 配置管理 `backend/app/core/config.py`

基于 pydantic-settings, 从环境变量或 `backend/.env` 读取, 统一前缀 `PHXXBLOG_`, 通过 `get_settings()` 提供单例 

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `PHXXBLOG_DEBUG` | false | 调试模式(同时决定 SQLAlchemy 是否打印 SQL); 本地按需在 `.env` 里打开 |
| `PHXXBLOG_DATABASE_URL` | mysql+pymysql://root:password@localhost:3306/phxxblog | 数据库连接串 |
| `PHXXBLOG_SECRET_KEY` | change-me-to-a-random-secret-key | JWT 签名密钥; 用仓库里的占位值或长度不足 32 会拒绝启动 |
| `PHXXBLOG_ALGORITHM` | HS256 | JWT 算法 |
| `PHXXBLOG_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | 访问令牌有效期 |
| `PHXXBLOG_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | 刷新令牌有效期 |
| `PHXXBLOG_ALLOW_REGISTER` | false | 是否开放注册; 个人博客建议保持 false, 否则任意访客都能注册成 author 并上传文件 |
| `PHXXBLOG_TRUSTED_PROXIES` | 空 | 可信反向代理 IP(逗号分隔), 只有来自这些地址的请求才采信 X-Forwarded-For |
| `PHXXBLOG_CORS_ORIGINS` | http://localhost:5173,http://127.0.0.1:5173 | 允许的跨域来源(逗号分隔) |
| `PHXXBLOG_UPLOAD_DIR` | `<仓库根目录>/assets/uploads` | 上传目录(相对路径按启动目录解析) |
| `PHXXBLOG_GEO_DB_PATH` | backend/data/ip2region_v4.xdb | 离线 IP 库路径 |
| `PHXXBLOG_MAX_UPLOAD_SIZE` | 100MB | 单文件大小上限 |
| `PHXXBLOG_SITE_URL` | http://localhost:5173 | 站点地址(RSS/sitemap 生成绝对链接) |
| `PHXXBLOG_DATA_RETENTION_DAYS` | 180 | 访问明细 `visit_logs` 的保留天数, 由 `scripts/cleanup_old_data.py` 清理 |
| `PHXXBLOG_AUDIT_LOG_RETENTION_DAYS` | 365 | 操作日志 `operation_logs` 的保留天数(审计用途) |

另外 `PHXXBLOG_ADMIN_PASSWORD` 由 `seed.py` 直接读环境变量, 不是 `config.py` 的配置项: 留空时随机生成初始密码, 并在 seed 的输出里打印一次 

### 5.3 数据层

- `core/database.py`: 以 `DeclarativeBase` 定义 `Base`; `engine` 开启 `pool_pre_ping` 与 `pool_recycle=3600`; `SessionLocal` 使用 `autoflush=False, expire_on_commit=False`; `get_db()` 作为请求级会话依赖 
- 表结构校验: `check_schema()` 反射实际表结构并与模型比对, 缺列时报错(或按 `debug` 只告警)并打印 `ALTER` 语句; 
  `ensure_schema_version_table()` / `record_version()` 维护 `schema_version` 表记录已应用的迁移 
  详见 `docs/mysql.md` 的"表结构演进" 
- 模型层 `models/*.py`: 使用 SQLAlchemy 2.0 的 `Mapped / mapped_column` 声明; `posts` 建有 `(status, published_at)`, `author_id` 索引 
  **关联加载策略按"是否真的要用"逐个指定**(改动前请先读模型里的注释): 
  `Post.author` 用 `joined`, `Post.categories/tags` 用 `selectin`(列表要序列化分类与标签; 
  两者都是多对多, 用 `joined` 会让分页的 `LIMIT` 作用在放大后的行数上, 分页结果会变少), 
  `Post.comments/likes` 用 `raise`(列表与详情都不使用这两个关系, 误用会立刻报错而不是退化成 N+1), 
  `User.roles` 用 `selectin`(每次请求都要权限码), `User.posts` 与 `Role.users` 用 `select` 
  (以前是 `selectin`, 导致每个需要登录的接口都顺带全量拉取该用户的文章) 
- `core/pagination.py`: `paginate(query, page, page_size, schema)` 统一分页取数与返回结构 
- `core/ratelimit.py`: 进程内滑动窗口限流器, 目前用于登录失败(同 IP+账号 5 分钟 10 次即 429) 
  局限已写在文件里: 多 worker/多实例部署时各自计数, 需要跨实例限流请换 Redis 或交给反代 
- `seed.py`: 初始化权限码, 三种角色(admin/editor/author), 管理员账号(仅当库中无用户时创建, 初始密码取 
  `PHXXBLOG_ADMIN_PASSWORD` 或随机生成并打印一次, 不再硬编码默认口令), 默认系统设置与默认分类/标签 

### 5.4 认证与授权

- **密码**: bcrypt 散列存储(`core/security.py` 的 `hash_password / verify_password`) 
- **访问令牌**: JWT(HS256), 默认 30 分钟失效, 载荷为 `{sub, iat, exp, type: access, username}` 
- **刷新令牌**: `secrets.token_urlsafe(48)` 随机串, 数据库只保存 SHA-256 散列与 `ip/user_agent/expires_at/revoked`, 默认 7 天, 支持吊销(登出) 
- **依赖注入**(`core/deps.py`): `get_current_user` 必须登录; `get_optional_user` 允许游客(点赞, 文章详情用); `require_permission(code)` 做权限码校验; `get_client_ip` 兼容 `X-Forwarded-For` 
- **权限模型**: 用户-角色, 角色-权限均为多对多; 权限码定义在 `core/permissions.py`(post:create / post:edit / post:publish / post:delete / post:manage / comment:manage / user:manage / role:manage / media:manage / setting:manage / log:view / stats:view / data:export) 除权限码外, 文章还会做资源级判断(`_can_manage`: 作者本人或管理员) 

### 5.5 统一响应与异常

成功响应直接由 `core/response.py` 的 `ok(data, message)` 生成; 失败响应由全局异常处理器生成; 两者结构一致, 前端只需处理一个分支 

```json
{ "code": 0, "message": "ok", "data": {} }
```

列表接口统一返回分页结构: `{ items, total, page, page_size }`(`schemas/common.py` 的 `Page`) 

### 5.6 业务服务层 `backend/app/services/`

| 文件 | 职责 |
| --- | --- |
| `markdown.py` | Markdown → HTML(fenced_code / tables / nl2br / attr_list / toc 等扩展), 代码高亮交给前端 |
| `upload.py` | 上传校验与落盘: 按扩展名判定 image/video/file, 按 `年/月` 分目录, UUID 文件名, 分块写入 |
| `text.py` | 字数统计(中日韩按字, 英文按词)与预计阅读时间(300 字/分钟, 不足 1 分钟按 1 分钟) |
| `geo.py` | ip2region 离线库查询 IP 归属地, 懒加载 + 缺失时优雅降级为空 |
| `ua.py` | 轻量正则解析 User-Agent(浏览器/系统/设备) |
| `stats.py` | 记录访问明细: 写 `visit_logs`, 累加 PV, 当日首次 IP 累加 UV, 文章访问累加阅读量 |
| `log.py` | 写操作日志(谁, 何时, 哪个模块, 什么动作, 目标对象, IP) |
| `link_preview.py` | 抓取目标网页的 og:title / description / image 生成链接卡片 |
| `archive.py` | 导入导出公共工具: frontmatter 解析/生成, zip 内图片落盘与正文图片路径改写(文章与日记共用) |

### 5.7 路由模块一览 `backend/app/api/v1/`

| 模块 | 前缀 | 说明 |
| --- | --- | --- |
| auth | /api/v1/auth | 注册, 登录, 刷新, 登出, 当前用户, 改密码/邮箱/资料 |
| users | /api/v1/users | 用户与角色权限管理(含重置密码) |
| posts | /api/v1/posts | 文章: 前台列表, 归档, 热门榜单, 后台列表, 详情(含上一篇/下一篇), 增删改, 回收站, 发布状态, 点赞, 导入/导出 |
| categories / tags | /api/v1/categories, /api/v1/tags | 分类与标签(含颜色) |
| comments | /api/v1/comments, /api/v1/posts/{id}/comments | 评论的读取, 发布与后台管理 |
| media | /api/v1/media | 媒体上传, 列表, 删除 |
| diaries | /api/v1/diaries | 日记(仅管理员) |
| misc | /api/v1/misc | 更新日志读写, 一言, 程序员历史上的今天 |
| stats | /api/v1/stats | 埋点, 概览, 趋势, 来源, 访问记录, 贡献数据 |
| dashboard | /api/v1/dashboard | 后台看板聚合数据 |
| logs | /api/v1/logs | 操作日志查询 |
| settings | /api/v1/settings | 公开配置与后台全部配置的读写 |
| search | /api/v1/search | 站内搜索 |
| links | /api/v1/links | 链接预览 |
| rss | /rss.xml, /sitemap.xml | 订阅与站点地图(不在 /api/v1 下) |

## 6. 前端实现

### 6.1 入口与主题 `frontend/src/main.ts`

- 创建应用并注册 Pinia, Vue Router, Element Plus(中文语言包 `zh-cn`, 全局 Message 可手动关闭) 
- 引入样式顺序: `element-plus/dist/index.css` → `element-plus/theme-chalk/dark/css-vars.css` → 
  `vditor/dist/index.css` → `styles/fonts.css`(自托管字体) → `styles/theme-green.css`(主题入口) 
  **顺序有意义**: 主题令牌必须晚于 Element Plus 与 Vditor 才能覆盖它们(见 6.6) 
- 应用挂载前读取 localStorage 中的深浅色与配色主题, 给 `html` 打上 `.dark` 类与 `data-theme` 属性, 避免首屏闪白 
- `frontend/scripts/copy-vditor-assets.mjs` 在 `predev / prebuild` 阶段把 `node_modules/vditor/dist` 复制到 `public/vditor/dist`, 使 Vditor 的 Lute, 图标, 高亮资源全部走本地, 不依赖 CDN(代价是 dist 里多约 21 MB 静态资源) 

### 6.2 路由与布局

- 使用 hash 模式(`createWebHashHistory`), 便于静态托管: 前台 `/`, `/post/:id`, `/archive`, `/posts`, `/search`, `/write(/:id)`, `/changelog`, `/diary`; 后台 `/admin/**`(仪表盘/文章/分类标签/评论/媒体/用户/设置/日志/资料) 
- 全局前置守卫: 路由标记 `meta.requiresAuth` 且本地无令牌时跳转登录页并带上 `redirect` 
- 前台布局 `layouts/SiteLayout.vue`: 顶栏(站点名 + 终端风格提示符 + 导航 + 看板娘开关组 + 主题按钮) + 内容区 + 页脚; 布局层负责加载公开配置(站点名/标签页标题/图标)与访问埋点 
  看板娘浮层 `<Kanbanniang />` 也挂在这个布局里, 因此只在后台之外的前台出现(见 7.26) 
  高度链: `.site-layout` 是 `min-height: 100vh` 的纵向 flex, `.site-body` 用 `flex: 1` 加 `grid-auto-rows: minmax(0, 1fr)` 
  撑满页头与页脚之间的空间(页脚另有 `margin-top: auto`), 内容少的页面也不会在页脚上方留出空白 
- 后台布局 `views/admin/AdminLayout.vue`: 侧边菜单 + 顶栏(API 文档入口, 主题按钮, 退出登录) 
- 前台部分页面使用 `keep-alive` 缓存(首页, 全部文章, 归档, 搜索) 
  **注意**: 被缓存的组件不会重新走 setup / onMounted, 因此 URL 查询参数变化必须用 `watch(route)` 自行响应 
  (见 `SearchView.vue` 的 `syncFromQuery`), 返回时的数据刷新用 `onActivated`(见 `HomeView.vue`) 

### 6.3 状态管理 `stores/`

- `auth.ts`: `accessToken / refreshToken / user` 三份状态与 localStorage 同步; 登录成功后写入会话, 同时把 access token 同步到 API 文档鉴权 cookie; 登出时清理令牌与 cookie 并回到前台首页 
  `accessToken / refreshToken` 是 **computed**(读 `utils/tokenStorage.ts`)而不是 ref - 静默刷新会直接改写 localStorage(见 6.4), 
  只有每次都从存储读, UI 才能看到最新令牌 
- `theme.ts`: 外观设置分两个独立维度 - `isDark`(深浅色)与 `themeId`(9 套配色主题, 见 `styles/themes/registry.ts`), 
  共同决定 `html` 上的 `.dark` 类与 `data-theme` 属性并持久化; 切换时临时加 `theme-transition` 类做颜色过渡 
- `kanbanniang.ts`: 看板娘的开关、当前形象与浮层位置(`enabled` / `modelId` / `position`, 见 7.26) 与主题一样属于访客自己的外观偏好, 
  只存 localStorage, 不下发到后端; 另有一个不落盘的 `allowed` 承载后台的总开关(见 7.26) 

### 6.4 请求层 `api/`

- `http.ts`: `axios.create({ baseURL: '/api/v1' })`; 请求拦截器附加 Bearer 令牌; 响应拦截器解包 `data` 字段(blob 下载除外), 统一打一条 `[api] METHOD url -> status message` 的 `console.warn`(便于定位是哪个请求失败), 统一弹出错误提示 
- **401 静默刷新**: access token 过期(默认 30 分钟)时不再直接把用户踢到登录页, 而是用 refresh token 换一对新令牌并**重放原请求** 
  三个必须遵守的约束(都有单测覆盖): 
  1. **单飞**: 页面同时发出的多个请求几乎必然同时 401, 而 refresh token 是一次性轮换的 - 并发刷新会让后到的那次拿到已失效的令牌, 
     于是整页掉线 因此所有并发 401 共用同一个刷新 Promise(`refreshOnce()`) 
  2. **不循环**: 重放过的请求打上 `_retried` 标记, 再 401 就走正常的未登录处理; 登录/刷新接口自身的 401 也一律不触发刷新 
  3. **刷新失败才算掉线**: 只有"换令牌失败"才清理会话并跳登录页; 重放失败按普通错误处理 
  刷新请求走独立的 `refreshClient` 实例(不带拦截器), 否则刷新失败的响应会再次进入本拦截器形成递归 
  受保护前缀见 `PROTECTED_PREFIXES`(含 `/write`, `/diary`, `/changelog`, 不只是 `/admin`) 
- `utils/tokenStorage.ts`: 令牌与用户信息的唯一读写入口(`ACCESS_TOKEN_KEY` 等) 此前 key 字面量散落在 store, `http.ts`, 
  下载导出, 路由守卫, 编辑器上传共 6 处, 改一处名字就会让其它几处静默失效(症状是"登录成功但立刻 401") 
- `utils/trendRange.ts`: 访问趋势看板的区间计算与区间汇总(快捷区间起止日期, 上一个等长区间, KPI 汇总, 环比) 
  看板要同时取本期与上期两份数据, 这部分是纯函数且有单测, 视图只负责展示 
- `utils/mediaGrid.ts`: 媒体库栅格的一屏容量与行高计算(列 × 行) 媒体库是铺满一屏的固定高度栅格, 
  每页数量必须等于一屏容量(否则"还有空位却已翻页"), 行高必须由容器高度均分而不能用 `1fr`(否则末页只剩一行时会被拉伸占满整屏); 取整边界有单测 
- `utils/mediaPreview.ts`: 媒体在线预览方式判定(图片/视频/音频/PDF/文本/不支持), 文档类按扩展名细分 
- `utils/format.ts`: 文件大小格式化(B / KB / MB), 媒体库列表与预览浮层共用 
- `index.ts`: 按业务域封装接口(authApi, postApi, categoryApi, tagApi, commentApi, mediaApi, statsApi, diaryApi, miscApi, logApi, settingsApi, searchApi, linkApi, userApi), 并导出与后端对齐的请求/响应类型 

### 6.5 组件 `components/` 与组合式函数 `composables/`

| 组件 | 职责 |
| --- | --- |
| `MarkdownView.vue` | 文章正文渲染(设置页的主页 README 预览也复用它): Vditor 预览 + 代码高亮/折叠 + 图片点击预览 |
| `VditorEditor.vue` | 写作页编辑器(即时渲染模式, 工具栏, 图片上传, 深浅色联动) |
| `PostFormFields.vue` | 文章表单字段(标题/别名/摘要/分类/标签/可见性/封面/正文), 写作页与后台编辑器共用 |
| `ImportExportDialogs.vue` | 导入 / 查重 / 导出三个弹窗, 文章管理与日记页共用 |
| `PostCard.vue` | 文章卡片: 标题, 摘要, 分类/标签彩色标签, 字数与阅读时间, views/likes, 状态标签(均带图标) |
| `HotPostsCard.vue` | 热门文章榜单(名次 + 标题 + 彩色阅读量): 首页左侧栏与文章详情页右侧栏共用, 顺序由后端 `/posts/hot` 决定 |
| `MetaIcon.vue` | 元信息小图标(日历/眼睛/标签/hash 等): 内联 SVG + `currentColor`, 自动跟随主题; 路径由 `npm run check:icons` 校验 |
| `ContributionsChart.vue` | GitHub 风格贡献热力图(纯 SVG/CSS 实现, 支持按年切换) |
| `TrendChart.vue` | 访问趋势折线/柱状图(纯 SVG 实现, 无第三方图表库): 宽度实测容器, PV 面积填充 + UV 虚线, 悬停/方向键十字准线取值, 数值浮层默认浮在数据点上方, 上方放不下时翻到数据点下方, 避免贴顶被图表裁切 |
| `MediaPreview.vue` | 媒体预览浮层(图片/视频/音频/PDF/文本), 覆盖在当前页面上: 点遮罩或 Esc 关闭, ← → 在当页媒体间切换 |
| `CommentSection.vue / CommentNode.vue` | 评论区与递归渲染的多层回复 |
| `LinkCard.vue` | 链接预览卡片 |
| `ThemeSwitcher.vue` | 主题下拉(色点 + 主题名)与深浅色切换按钮, 前台后台共用 |
| `Kanbanniang.vue` | 看板娘浮层(默认在左下角的 canvas, 按住模型本体可拖动): 运行时与模型按需加载, 后台总开关关掉、窄屏、无 WebGL 或加载失败时不展示 |
| `KanbanniangSwitcher.vue` | 顶栏的看板娘开关, 打开后其左侧出现形象下拉(名字 + 系列); 后台总开关关掉时整组隐藏 |
| `ThemeToggle.vue` | 仅浅色/深色切换的圆形按钮(登录页使用) |

| 组合式函数 | 职责 |
| --- | --- |
| `usePostEditor.ts` | 文章编辑的全部状态与流程(加载选项/详情, 分类标签就地新建, 封面上传, 保存, 删除) |
| `useImportExport.ts` | 导入(查重 -> 选择策略 -> 写入), 导出下载与三个弹窗的状态 |

两个 composable 都返回 `reactive` 对象(内部不使用 ref), 调用方直接写 `editor.form.title` / `io.importDialog`, 无需 `.value` 
视图之间的差异(取消的去向, 数量单位, 文案)通过 options 注入 - 这是把原先 4 个视图里约 400 行重复逻辑收敛成两份的原因 

### 6.6 样式与主题

- 配色采用**令牌 + 生成**的方式: 源数据在 `styles/themes/_source/tokens.mjs`, 由 
  `npm run themes:generate` 生成 9 套 `theme-<id>.css`(各含深浅两套令牌)与 `registry.ts` 
  改配色只改数据源, 不要手改生成物 
- 每个主题文件里的令牌选择器是 `html[data-theme='<id>']` 与 `html[data-theme='<id>'].dark`; 
  只有 `theme-default.css` 写裸 `:root`(承载"新访客未选主题"时的默认配色), 否则多套主题会互相覆盖 
- **跟随主题的 Element Plus 令牌**集中在 `styles/admin.css`: `--el-color-primary` 指向主题主色, 
  `--el-color-success` / `warning` / `danger` / `info` 指向主题的 `--ok` / `--warn` / `--danger` / `--muted`(`error` 复用 `danger` 的整套色阶), 
  各自的 `light-3/5/7/8/9` 与 `dark-2` 色阶用 `color-mix` 与 `--card-bg` / `--text` 推导(与 `chipColor.ts` 同一套算法) 
  语义色不接管的话, "删除 / 警告 / 提示"这类按钮在 9 套主题下都是同一套固定的绿红黄, 换主题时不跟着变 
- **按钮类型约定**: 主操作(写文章页的"发布", 后台的"保存")用 `type="primary"`, 由各主题文件里的 
  `.el-button--primary` 规则绑到 `--primary`(主题身份色), 因此预设主题这种"静蓝主色"的主题下也是蓝色, 
  不会出现绿色按钮配蓝色主题; 9 套主题的主按钮对比度由 `themes:audit` 校验 
  语义操作(删除 / 警告 / 提示)才用 `success` / `warning` / `danger` / `info`, 它们取主题的语义色 
- 该文件必须排在所有主题之后(`theme-green.css` 的 `@import` 顺序) 主色以同特异性后写入即可覆盖, 
  语义色与色阶写在 `html:root` 里: 它比 Element Plus 浅色的 `:root` 高一级, 与深色的 `html.dark` 同档, 
  否则运行期按需注入的组件样式会把它盖回去 
- **纯色语义按钮的文字色**改用页面底色 `--bg`: 主题的语义色浅色下是深色, 深色下是亮色, 本身就是正文前景色, 
  配页面底色对比度才够; Element Plus 固定用白字, 深色主题下亮色按钮上的白字看不清 文字色是按钮自己的变量, 
  因此覆盖的是 `--el-button-text-color` 一族(hover / active / disabled) 
- **按需引入的边界**: `vite.config.ts` 的 `ElementPlusResolver({ importStyle: 'css' })` 只能识别**模板里的标签** 
  `ElMessageBox.confirm()` / `ElMessage.success()` 这类 JS 调用不在模板里, 样式不会自动进来, 必须在 `main.ts` 手动 
  `import 'element-plus/es/components/<name>/style/css'` 漏了不会报错, 只会让确认框变成页面左上角一堆裸按钮, 
  提示条完全不可见(曾因此吞掉"内容为空"的提示, 表现为"点保存没反应") `npm run check:element-styles` 会把漏掉的拦下来 
- 代码块背景与高亮风格对齐 VSCode 默认主题: 浅色用 `vs`, 深色用 `vs2015`, 并统一注释为斜体, 字号与正文字号联动 
  注意 Vditor 自带的 `.vditor-reset` 写死了字体栈且不引用 `var(--font-sans)`, 正文的字体由 `theme.css` 里 
  同特异性的 `.markdown-body, .vditor-reset` 规则覆盖, **那条规则不要删** 
- 编辑器(Vditor IR 模式)里的代码块与正文用同一套外观: 预览用的 `.vditor-ir__preview code` 复用 
  `--code-block-bg` / `--border` / `--radius` 变成一张卡片, 字号与正文的代码块取平(`--font-mono`, 15px) 
  光标进入代码块时 Vditor 会把原文展开, 并在下面重复渲染一份预览, 因此 `theme.css` 里 
  `.vditor-ir__node--expand[data-type='code-block'] .vditor-ir__preview` 把它收掉, 同时给外层节点套同一张卡片, 
  卡片内的原文再去掉 Vditor 的行内代码底色 两个坑: 不要覆盖 `.vditor-linenumber` 的 `padding-left`(4em, 带 
  `!important`, 那是行号槽), 也不要改 `.vditor-ir__marker--pre` 的 display - 展开/收起与光标定位都依赖它, 
  改成 block 会让编辑态的排版散开 
- 编辑区的左右留白来自 Vditor: 它的"居中"不是 CSS, 而是 JS 按 `(容器宽 - preview.maxWidth) / 2` 写行内左右 
  padding(下限 35px) 默认 `maxWidth` 只有 800, 在后台这张约 1300px 宽的卡片里会左右各留 250px 空白, 
  所以 `VditorEditor` 把 `maxWidth` 设为 1100 
- 编辑区高度: `VditorEditor` 的 `height` 默认 `'auto'` 且不设最小高度 - 内容变长时 `pre.vditor-reset` 跟着变高, 滚动交给页面, 
  编辑器内部不会出现滚动条; 确需固定高度(内部滚动, 如后台的版本日志编辑器)时给 `height` 传数字 
  写作页在这个基础上还要求"内容少时也要铺满可用高度": `WriteView` 的页面容器与卡片, `PostFormFields` 的正文表单项, 
  `VditorEditor` 逐层 `flex: 1`, 把 `.site-main` 撑出来的高度一直传到编辑器, 因此空文档下卡片也会铺到页脚上方, 
  不会在下方露出一块页面底色 后台的文章编辑页(`PostEditView`)照这套补了页面容器与卡片, 因此点"新建文章"时正文编辑框默认也是铺满的 
  日记的编辑对话框是 `el-dialog`, 高度由内容决定, 这套 `flex` 在里面不生效: 对话框宽 860px, 编辑器用 `height` 传 360 固定高度, 
  这样上方工具栏能排在同一行 
- 编辑区外观由 `theme.css` 统一: 去掉 Vditor 自带的 1px 边框与工具栏的 `border-bottom`, 编辑区, 预览区与工具栏的背景一律改为 
  `transparent`, 文字色用 `var(--text)` Vditor 自带的底色变量(`--panel-background-color` / `--textarea-background-color` / 
  `--toolbar-background-color`, 深色下是 `#24292e` / `#2f363d` / `#1d2125`)与本站卡片底色不一致: 深色下编辑区会明显比周围亮一块, 
  浅色下则在编辑区上方压出一条灰带与一条分割线 编辑区透明后全屏还需要给 `.vditor--fullscreen` 补一层实底(`--card-bg`), 
  否则整屏编辑器会透出下层页面 
- 编辑器全屏的层级用 `fullscreen.index` 提到 1000: 站点头部 `.site-header` 的 `z-index` 是 100, 用 Vditor 默认的 90 
  时全屏后工具栏会被头部盖住, 既看不见也点不到(无法退出全屏) 
- 深浅色切换要同步给编辑器: Vditor 的深色是 `vditor--dark` 类加一组 CSS 变量, 代码高亮主题(vs / vs2015)也是按主题名 
  另载的样式表, 所以 `VditorEditor` 除了初始化读 `theme.isDark`, 还 watch 它并调用 `setTheme`; 只在初始化时读一次的话, 
  运行中切到深色时编辑区会一直是白底 
- 字体: 字母/数字/符号统一 Cascadia Code(自托管 latin 子集, `public/fonts/`); 该字体不含中文字形, 
  中文自动回退到 PingFang SC / 微软雅黑 
- 分类/标签与 views/likes 的彩色标签由 `utils/chipColor.ts` 计算: 后台配置了颜色则使用该颜色, 否则按名称哈希生成稳定色相, 再用 `color-mix` 生成背景, 边框与文字色, 深浅色下均自动适配 
- **后台页内工具条**统一走 `styles/admin.css` 的 `.admin-toolbar` 一族类, 视图里不要再各写一份 scoped `.toolbar`: 
  标题 `h2` 独占一行(间距由 `.admin-main > div > h2:first-child` 提供), 下面是一个工具条行 - 
  左侧 `.admin-toolbar-filters` 放筛选/范围控件, 右侧 `.admin-toolbar-actions` 放操作控件并靠 `margin-left: auto` 靠右, 
  组内顺序为"搜索框 + 搜索按钮 → 普通操作 → 主操作(primary) → 危险操作(danger)" 
  `.admin-toolbar .el-input` 固定 220px 宽: `el-input` 自身是 `width: 100%`, 在 flex 行里会撑满剩余空间并把"搜索"按钮推远 
  (曾表现为文章管理页"搜索"按钮被顶到下一行按钮的正下方, 像是错位) 
  卡片内若有批量操作(如文章管理的"设为私密/移入回收站"), 仍留在卡片内的 `.batch-bar`, 不并入页级工具条 
- **系统设置页**是全后台最长的表单, 因此按配置域拆成 4 张卡片(基础信息 / SEO / 首页内容 / 页脚与链接), 
  卡片内统一用 `el-row :gutter="16"` + `el-col :span="12|24"` 的栅格, 与个人资料页的 `.card` + `<h3>` 写法一致 
  保存按钮放在页级 `.admin-toolbar` 里并随页面滚动**吸附在顶部**, 表单与"最近一次载入/保存"的 JSON 快照做深比较, 
  有未保存修改时在工具条左侧提示 吸附用的是 `top: -20px` 而不是 `0`: sticky 的吸附边界是滚动容器(`.admin-main`)的**内容盒**, 
  而它自带 20px 上内边距, 写 `top: 0` 会在工具条上方留出一条缝, 让卡片文字从缝里露出来 
  每张卡片标题还带一个"公开可见 / 仅管理员可见"徽标, 依据是这些配置在前台的**实际渲染位置** - 例如"网站链接"在 
  `HomeView.vue` 里是 `v-if="isAdmin && ..."`, 前台只有管理员能看到, 所以标成仅管理员可见, 不能凭字段名想当然 
  主页 README 的文本域高度始终交给 `autosize` 跟随内容(内容少时不留大片空白), 只有"逻辑行数超过 20 且未展开"时才用 
  `maxRows: 20` 封顶: 多出来的部分靠 scoped 的 `overflow-y: hidden !important` 裁掉, 并叠一层底部渐隐 这里必须带 
  `!important` - el-input 在用 `maxRows` 封顶时会把 overflow 写成行内样式 上限只按**逻辑行数**启用: 行数没超就干脆不封顶, 
  免得长段落自动换行撑过 20 行, 在折叠态被悄悄裁掉却又没有展开按钮可点 
  注意展开那一刻 `el-input` 的 `modelValue` 没有变化, 不会触发它内部的高度重算, 所以文本域上挂了随折叠状态变化的 `:key`, 
  靠重建触发挂载时的 `resizeTextarea` 
  页脚与链接里的三处行列表(社交链接 / 网站链接 / 备案信息)结构同构, 由 `linkLists` 列定义驱动, 模板里只写一份: 
  行首序号, 名称列 `flex: 0 0 200px` 定宽(内联 `width` 会被同一行 `.el-input` 的 flex 覆盖, 必须用 flex-basis 表达), 
  备案多一列图标, 删除按钮改成默认灰, 悬停变红的图标按钮, 避免整屏红色文字; 
  "添加"按钮按"序号列宽 + 行间距"缩进(两者抽成 `.link-list` 上的 `--link-index-width` / `--link-row-gap`), 与上方名称输入框左对齐 
- **入场动画**统一由各主题文件里的 `@keyframes rise-in / snap-in / fade-up / fade-in` + `.site-main > *` 提供(源在 `_source/enhance.base.css`), 
  填充模式必须写 `backwards` 而不是 `both`: `both` 会让动画结束后仍把 transform 留在效果栈里(计算值是一单位矩阵而非 `none`), 
  于是 `.site-main` 的直接子元素(`.page-container`)就成了 `position: fixed` 的定位基准 - 容器里的弹窗会相对"整页高"的容器居中, 
  曾表现为"点开首页头像后弹窗跑到页面下方" 改这里后 9 套主题都要 `npm run themes:generate` 重新生成 

## 7. 关键功能实现

### 7.1 文章状态与可见性

状态取值: 0 草稿 / 1 审核中 / 2 已发布 / 3 私密 / 4 回收站 前台列表只返回已发布文章; 详情接口对非公开文章要求"作者本人或管理员"; 删除默认进回收站(可恢复), `/force` 为彻底删除 每次创建/更新/发布/删除都会写操作日志 

### 7.2 Markdown 渲染与代码高亮

前端 `MarkdownView.vue` 调用 `Vditor.preview()` 渲染正文(资源走本地 `/vditor`), 随后: 

1. `Vditor.codeRender / mediaRender` 生成代码复制按钮与视频/音频/iframe 结构 
2. 未标注语言的代码块用 highlight.js 自动识别语言: 先用特征规则匹配常见语言(C/C++/Rust/PowerShell 等), 再按候选语言集合打分选取相关度最高者, 相关度为 0 则保持纯文本, 避免误上色 
3. `Vditor.highlightRender` 统一重渲染以套用行号与主题(vs / vs2015) 
4. 超过 20 行的代码块包一层 `code-block` 容器, 折叠时用 `max-height` 裁剪并隐藏纵向溢出, 点击按钮展开/收起(主题切换后保持展开状态) 

后端只把 Markdown 转成带 class 的 HTML(`services/markdown.py`), 高亮完全在前端完成 

### 7.3 图片点击预览

正文图片点击后使用 Element Plus 的图片查看器(`el-image-viewer`): 图片按窗口等比缩放并居中显示(不再按原始分辨率铺满页面), 支持鼠标滚轮缩放, 拖拽平移, 旋转与恢复原始尺寸, 关闭方式支持 ✕, Esc 与点击遮罩 

### 7.4 字数与预计阅读时间

`backend/app/services/text.py` 统计中日韩字符数 + 英文单词数, 按 300 字/分钟估算阅读时间; `Post` 模型以 `word_count / reading_minutes` 属性暴露给接口, 文章列表与详情页在 meta 区展示 "约 N 字, 大约 M 分钟" 前端 `utils/textStats.ts` 保留同算法的实现, 便于前端本地统计 

### 7.5 文章摘要

`posts.summary` 字段由作者在写作页手动填写, 不自动生成; 列表页在标题下方展示摘要, 详情页在正文上方以引用块样式展示, 未填写则不渲染该区域 

### 7.6 分类与标签配色

`categories``tags` 表新增 `color` 列(后台可填色值, 留空则由前端按名称生成兜底色) 前端所有展示分类/标签的位置(文章卡片, 详情页 meta, 首页分类胶囊)统一调用 `chipStyle(name, color)` 生成内联样式, 保证同一分类/标签在全站颜色一致 

### 7.7 首页模块开关与分页

后台`系统设置 → 前台展示`提供五个开关(主页 README, 文章发布记录, 程序员历史上的今天, session 终端卡片, 看板娘), 以 `1/0` 存入 `settings` 表, 由 `/settings/public` 输出为布尔值 首页按开关决定是否渲染对应模块, 并跳过对应的接口请求(不浪费请求); 看板娘开关由前台布局读取, 关掉后不加载也不展示(见 7.26); 首页文章列表默认展示最近 10 篇, 底部分页可查看更早文章, 翻页后自动回到列表顶部 

### 7.8 一言(每天仅刷新一次)

后端 `/api/v1/misc/saying` 代理第三方接口, 并把结果按天缓存到 `settings` 表的 `saying_cache` 键(JSON: `{date, text}`): 同一天内所有访客共用同一条, 不再每次进入首页都请求外部接口; 前端点击"换一句"时传 `force=true` 强制刷新; 外部接口异常时回退到旧缓存, 避免页面空白 

### 7.9 程序员历史上的今天

`/api/v1/misc/history/programmer-today` 代理第三方接口并按接口返回的结构透出 `{date, events}`, 前端在首页以时间线卡片展示, 可手动刷新 

### 7.10 页脚与浏览器标签页

- 页脚包含备案信息(数组配置, 可选)与版权信息(`footer_text` 配置, 支持 `{year}`/`{site_name}` 占位符, 留空则不显示该行); 页脚高度由内容决定, 两者都为空时整个页脚不渲染 
- 浏览器标签页名称取 `site_title`, 留空回退站点名称; 前台布局与后台布局在加载公开配置后都会设置 `document.title`, 站点图标同理动态替换 `link[rel=icon]` 

### 7.11 评论

游客即可评论(记录 IP 与归属地); 评论支持多级回复(`parent_id` 自关联), 前端用递归组件渲染; 可附带图片/附件; 后台可编辑, 审核(状态)与删除 

### 7.12 点赞

`/posts/{id}/like` 为"切换式"接口: 登录用户按账号去重, 游客按 IP 去重, 已点赞再次调用即取消; 点赞同时累加当天的 `likes` 统计 

### 7.13 媒体上传

`/media/upload` 接收 `multipart/form-data`, 按扩展名判定类型, 文件名使用 UUID, 按 `年/月` 分目录落盘, 返回可直接访问的 `/assets/...` URL; 前端写作页与媒体库共用该接口, Vditor 的上传也指向它(请求头带 Bearer 令牌) 媒体表记录原始名, 路径, MIME, 大小, 类型与关联对象 

媒体库页点击卡片会在当前页面弹出预览浮层(`components/MediaPreview.vue`), 渲染方式由 `utils/mediaPreview.ts` 的 `previewKind()` 判定(有单测): 图片 / 视频 / 音频直接按媒体类型渲染; pdf 交给浏览器内置阅读器(iframe 指向文件本身); `.txt/.md/.csv/.json` 读取内容后用 `<pre>` 展示(内容经模板插值转义, 不会当 HTML 执行, 上限 256 KB); office, 压缩包等浏览器无法渲染的只提供下载 浮层支持点遮罩或 Esc 关闭, ← → 在当页媒体之间切换 

### 7.14 访问统计与贡献热力图

- 前台布局挂载时调用 `/stats/track` 埋点; 文章详情接口在成功返回已发布文章时也会记录一次访问 
- `services/stats.py` 写 `visit_logs` 明细(IP, UA, Referer, URL, 浏览器/系统/设备), 累加当日 PV, 当日新 IP 计 UV, 并累加文章阅读量 
- `/stats/trend` 按日/月/年聚合, 前端 `TrendChart` 渲染折线或柱状图; `/stats/sources` 输出来源/浏览器/设备 TOP 榜; `/stats/visits` 分页返回访问明细(含归属地) 
- `/stats/contributions` 返回近 N 周或指定年份每天的发布数量(文章或日记), 前端 `ContributionsChart` 渲染 GitHub 风格热力图 

### 7.15 操作日志

`services/log.py` 在关键写操作(登录/注册, 文章增删改与导入导出, 评论, 媒体, 用户, 设置等)后写入 `operation_logs`; 后台日志页支持按用户/模块/动作筛选, 并展示 IP 归属地 

### 7.16 站内搜索

`/search` 对已发布文章的标题, 摘要, 正文做模糊匹配(`LIKE`), 支持发布时间区间与分页; `posts` 表同时保留了 ngram 全文索引, 数据量大时可切换为 `MATCH ... AGAINST` 以提升性能 

### 7.17 归档

`/posts/archive` 一次性取回所有已发布文章并在服务端按 `年-月` 分组(含每组数量), 前端 `ArchiveView` 渲染时间轴, 支持跳转到指定时间段 

### 7.18 RSS 与 Sitemap

`api/v1/rss.py` 用 feedgen 生成 `/rss.xml`, 站点名称与描述取自 `settings` 表; `/sitemap.xml` 输出已发布文章的 URL 列表, 两者都使用 `PHXXBLOG_SITE_URL` 拼接绝对地址 

### 7.19 文章导入导出

- 导出: `/posts/export?ids=...&fmt=markdown|html` 把选中文章导出为 Markdown(带 frontmatter: 标题, slug, 摘要, 分类, 标签, 发布时间, 状态等)或打包为 zip, 一并附带正文引用到的本地图片 
- 导入: 上传一个或多个 Markdown/zip 文件, 解析 frontmatter, 自动生成不冲突的 slug, 按名称匹配或创建分类与标签(都可以有多个, 分类兼容旧格式的单值 `category`), 并把压缩包内的图片保存到上传目录同时改写正文中的图片地址 
- 查重: 导入前先按标题(忽略大小写与首尾空格)与库中已有文章, 本批已出现的标题比对, 接口返回 `mode=check` 的查重结果; 前端据此提示重复, 由用户选择"仅导入不重复"(`on_duplicate=skip`)或"导入全部"(`on_duplicate=all`) 
- 文章与日记的导入导出共用 `services/archive.py`: frontmatter 解析, zip 内图片落盘, 正文图片地址改写只有一份实现 

### 7.20 WordPress 数据迁移

`backend/scripts/import_wordpress.py` 解析 WXR XML: 正文由 Gutenberg/HTML 转为 Markdown, 自动创建作者账号, 导入分类/标签/评论, 下载附件到 `assets/uploads/wordpress/` 并登记媒体库, 同时把正文中的旧站图片链接改写为本地地址 

### 7.21 API 文档鉴权

`core/middleware.py` 的 `restrict_docs_to_admin` 拦截 `/docs`, `/redoc`, `/openapi.json` 与 OAuth 回调页: 

1. 从 `Authorization: Bearer <token>` 或 cookie `phxxblog_doc_token` 取访问令牌, 两者都没有返回 401 
2. 校验 JWT(必须是 access 类型)并查询用户; 令牌非法/过期或用户不存在返回 401 
3. 用户被禁用或没有 `setting:manage` 权限码返回 403(判断权限码而不是角色名 - 角色 code 可被后台修改, 
   用 `"admin" in role_codes` 判断会在角色改名后静默放行或误拦) 
4. 通过后放行到 FastAPI 自带的文档页面 

令牌校验这段逻辑抽在 `_authorize_admin()` 里, 与 7.25 的静态资源鉴权共用: 两处的令牌来源, 
失败状态码与权限码判断必须一致, 各写一份迟早会漂移 

令牌来源的配合: 前端登录或恢复会话时把 access token 写入 `phxxblog_doc_token` cookie(SameSite=Lax, https 下附带 Secure), 登出或令牌失效时清除; 因此后台顶栏的"API 文档"按钮可以直接新窗口打开 `/docs`, 无需在 URL 上携带令牌 

### 7.22 日记导入导出

日记(/diary, 仅管理员)与文章使用同一套导入导出机制: 

- 导出: `GET /api/v1/diaries/export?ids=...&fmt=markdown|html` 打包为 zip Markdown 文件按 `YYYY-MM-DD.md` 命名(同一天多条追加 `-2`, `-3` 序号), frontmatter 记录 `date` 与 `created_at`; html 格式输出完整 HTML 文档 正文引用到的本地图片一并放入 `images/<日期>/` 并改写为包内相对路径 
- 导入: `POST /api/v1/diaries/import` 支持 .md 或 zip(可多选) 日期优先取 frontmatter 的 `date`, 其次取文件名开头的 `YYYY-MM-DD`, 都取不到则记为今天; `created_at` 有效时一并还原, 用于同一天多条日记的排序 zip 内的图片保存到上传目录并自动改写正文地址, 内容为空的文件会被跳过并在结果中给出提示 
- 查重: 导入前按正文比对(`normalize_content` 忽略空白差异, 图片地址只比较文件名, 因此"相对路径"与导入后改写出的 `/assets/uploads/...` 地址视为同一张图), 与库中已有日记及本批内容比对; 前端可选择仅导入不重复或全部导入 
- 前端入口: 日记页右上角的"导入日记 / 导出日记"按钮(导出可选 Markdown 或 HTML 格式) 

### 7.23 文章目录与相邻文章

文章详情页是"正文 + 右侧栏"两栏布局(窄屏 ≤1100px 收成单栏并隐藏右侧栏): 

- 目录: `MarkdownView` 渲染完正文后收集 `h1~h6`, 给每个标题补上锚点 id(同名标题追加 `-2`, `-3` 保证唯一), 再通过 `headings` 
  事件交给详情页; 详情页在右侧栏上方的卡片里按层级缩进列出目录, 滚动时高亮"最后一个已滚过顶栏的标题", 
  点击调 `scrollIntoView` 定位 - 本站是 hash 路由, 不能靠改 `location.hash` 跳锚点 顶栏是 sticky 的, 
  标题的 `scroll-margin-top` 已按顶栏高度留出余量 
- 相邻文章: 详情接口在 `PostDetail` 上附带 `prev_post` / `next_post`(按 `published_at` 相邻查询, 只在已发布文章之间取, 缺失为 `null`), 
  正文末尾右下角展示"最后更新于"与上一篇/下一篇卡片; 没有相邻文章的一侧不渲染卡片(用 `grid-column` 让"下一篇"始终落在右列) 
- 注意: 阅读量由访问埋点累加, 为此 `record_visit` 改用显式 `UPDATE` 并带上 `updated_at` 原值, 避免触发 `onupdate` 
  把"最后更新时间"顶成"最后一次访问时间"(详情页的"最后更新于"会因此永远显示当前时间) 

### 7.24 热门文章榜单

`GET /posts/hot?limit=7` 按 `views` 倒序返回已发布文章(浏览量相同时按 id 倒序, 保证顺序稳定) 首页左侧栏 
(个人信息与常用网站之间)与文章详情页右侧栏下方共用 `HotPostsCard.vue`, 展示名次, 标题(单行截断)与彩色阅读量标签; 
排序口径完全由后端决定, 两处保持一致 

### 7.25 静态资源访问控制

`core/middleware.py` 的 `restrict_assets_to_admin` 给 `/assets`(上传目录与迁移数据的静态托管, 见 9.2)加了一层鉴权 
判断规则在纯函数 `asset_requires_admin(path)` 里, 只放行**浏览器会直接渲染的媒体**: 

| 路径 | 是否公开 | 原因 |
| --- | --- | --- |
| `/assets/uploads/**` 的图片/音视频(`IMAGE_EXTS / VIDEO_EXTS / AUDIO_EXTS`) | 公开 | 正文配图, 站点图标, 头像都指向这里, 锁掉等于前台全站图片 404 |
| `/assets/wordpress/**` | 仅 admin | WordPress 迁移的原始导出(WXR/XML, 媒体库导出 zip, 个人信息导出), 只是导入来源, 前台从不引用 |
| `/assets/uploads/**` 的其它扩展名(csv/txt/md/zip 等)与无扩展名文件 | 仅 admin | 附件类文件不参与渲染, 没有匿名下载的必要 |

公开扩展名直接复用 `services/upload.py` 的白名单子集, 不再单独维护一份 - 上传白名单决定了 
目录里会出现哪些类型, 两处各写一份必然漂移 

注意 `/assets/uploads/wordpress/**` **不能整目录锁掉**: 里面的图片是已发布文章正文在用的 
(导入脚本把旧站链接改写成了这个路径), 只有其中的非媒体文件会被拦下 鉴权走与 /docs 相同的 
令牌来源与权限码, 因此未登录 401, 非 admin 403; 后台界面上的图片与下载链接靠 `phxxblog_doc_token` 
cookie 自动通过(同源代理下浏览器会带上, 见 9.2 第 4 条) 

### 7.26 看板娘

形象与运行时来自 [kanbanniang](https://github.com/Vanessa219/kanbanniang)(MIT; 模型版权属原作者, 上游注明仅供研究学习),
自托管在 `frontend/public/kanbanniang/` 下, 运行时不请求任何外部地址 - 形象清单与搬运时做过的本地化改动记在该目录的 README 里 

- 上游把模型基址写死在 `live2d.js` 中(`https://unpkg.com/kanbanniang@0.2.12/`), 模型 json 的纹理也写成 unpkg 绝对地址 这里把基址改成 `/kanbanniang/`, 
  并去掉 json 里的 unpkg 前缀 
- 上游 `Potion-Maker/Pio`、`Potion-Maker/Tia` 与 `bilibili-live/22`、`bilibili-live/33` 的 `index.json` 里 `textures` 是空数组(换装由上游 widget 读 `textures.json` 完成, 本运行时读不到), 
  这里按上游 `textures.json` 的首套服装显式补上纹理路径 
- 形象清单在 `src/kanbanniang/registry.ts`(id / 名字 / 系列 / 模型 json 路径, 以及可选的画布尺寸), 加形象只需放模型目录 + 追加一条 
  上游仓库共 26 个模型, 本仓库收录 9 个: Pio / Tia / Murakumo / Shizuku / Shizuku Pajama / Blanc / 22娘 / 33娘 来自上游, Miku 来自上游之外的来源(见下) 
  上游剩下的都是 HyperdimensionNeptunia 系列的服装变体, 单套体积 2 MB 上下且会互相引用兄弟目录的纹理, 默认不收, 需要时按该目录 README 的步骤补 
- Miku 上游没有, 取自 [live2d-widget-models](https://github.com/xiazeyu/live2d-widget-models) 的 `live2d-widget-model-miku`(包声明 GPL-2.0, 模型版权属原作者), 
  按本运行时的路径约定改写(路径前缀与 `layout` 取景)后放在 `model/miku/` 
  它是全身像, 默认的 280x250 画布只够看到膝盖以上, 因此清单里单独给它 280x420 的画布(`canvas` 字段), 并调 `layout` 让头到脚填满这块画布 
- 开关、形象与浮层位置存在 localStorage(`blog_kanbanniang` / `blog_kanbanniang_model` / `blog_kanbanniang_pos`), 默认展示, 关掉后刷新不再发任何模型请求 
- 后台 `系统设置 → 前台展示` 的看板娘开关经 `/settings/public` 下发, 前台布局加载公开配置后写入 store 的 `allowed`; 关掉后顶栏那组控件与浮层一起消失, 连运行时与模型都不会去请求(拿到公开配置前 `allowed` 默认 false, 请求失败时回退为展示) 
- 浮层默认停在左下角, 按住模型本体可挪到视口内任意位置, 松手后写入 localStorage 
  容器整体 `pointer-events: none`(运行时在 `window` 上监听鼠标, 不需要命中 canvas), 拖动也靠挂在 `window` 上的鼠标事件, 命中判定用一张从 canvas 拷下来的模型轮廓掩膜(每 1 s 刷新一次; 掩膜取不到时退化成整块都算命中) 
  按在透明处照旧把点击透给下面的正文; 命中模型的那次按下在捕获阶段 `stopPropagation` 拦下, 否则运行时挂在 `window` 上的 `mousedown` 会把拖动当成点到了模型而触发摸头动作 
  没拖动(位移小于 4 px)时补发一次 `mousedown` + `mouseup`, 点击互动照旧; 拖动过则吃掉紧随其后的一次 `click`, 免得点到浮层下面的链接 
  坐标按浮层尺寸与视口大小收进可视范围(上边界让开顶栏高度, 顶栏层级高于浮层), 窗口缩小或重新打开看板娘时再次收拢 
- 运行时(151 KB)与模型都等首屏之后再加载: 优先 `requestIdleCallback`, 没有该 API 的浏览器退回 200ms 定时器, 不与页面自身的请求抢带宽 
- 窄屏(≤ 900px)不展示看板娘, 顶栏那组控件用同一断点隐藏 - 手机上浮层会盖住正文, 也白白多下载一份模型 
- 关闭时只隐藏 canvas 不销毁: 运行时持有它的 WebGL 上下文, 反复销毁重建会消耗浏览器的 WebGL 上下文配额 
- 缺少 WebGL 或运行时加载失败时打一条 `console.warn` 并放弃展示, 页面其余部分不受影响 

## 8. 数据模型概览

| 表 | 说明 |
| --- | --- |
| users / roles / permissions | 用户, 角色, 权限及两张多对多关联表; refresh_tokens 存刷新令牌散列 |
| posts / categories / tags | 文章(状态, 摘要, 封面, 阅读量, 点赞数, IP/归属地), 分类与标签(含颜色), 文章-分类与文章-标签都是多对多 |
| comments / post_likes | 评论(自关联多级回复)与点赞去重记录 |
| media | 上传文件元数据与实际路径 |
| diaries | 日记(仅管理员, 支持附件) |
| visit_logs / daily_stats | 访问明细与按日聚合统计(PV/UV/点赞数) |
| operation_logs | 操作日志 |
| settings | 键值对配置(站点信息, 前台展示开关, 页脚, 一言缓存等) |

字段级说明见 [mysql.md](./mysql.md) 

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

也可直接双击根目录 `start.bat`: 脚本会检查虚拟环境与依赖, 缺少 `.env` 时自动从示例复制, 然后分别开两个窗口启动前后端并打印访问地址 

### 9.2 生产部署要点

1. 前端执行 `npm run build`(内部先跑 `vue-tsc` 类型检查), 产物在 `frontend/dist`, 交给静态服务器托管 
   注意 `dist` 里含 `vditor/`(约 21 MB), `kanbanniang/`(约 11 MB, 看板娘的运行时与模型) 与 `fonts/`(约 58 KB), 都是运行时按需加载的资源, 不要裁剪 
2. **确认静态服务器开启了 gzip/brotli 压缩** 可用 `npm run check:size`(内部读 `dist/index.html` 
   实际引用的资源, 不是估算)打印当前体积, 当前值: 

   | 口径 | 未压缩 | gzip 后 |
   | --- | --- | --- |
   | 首屏(渲染首屏前必须下载的 js/css) | 约 290 KB | 约 83 KB |
   | 按需资源(路由/功能懒加载) | 约 1430 KB | 约 430 KB |

   若托管方未压缩, 首屏传输量会从 83 KB 涨到 290 KB Nginx 参考: 
   `gzip on; gzip_types text/css application/javascript font/woff2;` 
   改动体积后记得同步更新本节数字(`npm run check:size` 的输出即上表口径) 
3. 后端以 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 或 gunicorn + uvicorn worker 运行, 建议关闭 `PHXXBLOG_DEBUG` 
4. 反向代理需要转发 `/api`, `/assets`, 如需在线文档再转发 `/docs`, `/redoc`, `/openapi.json`; 若前端与后端不同域, 还要把前端域名加入 `PHXXBLOG_CORS_ORIGINS` 
   反代必须**透传 Cookie**(`phxxblog_doc_token`): `/docs` 与 `/assets` 下的非公开文件都靠它鉴权, 丢掉 Cookie 会让管理员自己也打不开 
5. 生产环境启动前**必须**设置 `PHXXBLOG_SECRET_KEY`(长度 ≥ 32): 
   应用会拒绝用仓库里的默认占位值启动, 因为那等于任何人都能伪造 admin 令牌 
   生成方式: `python -c "import secrets; print(secrets.token_urlsafe(48))"` 
6. 若部署在反向代理之后, 把反代的内网地址填入 `PHXXBLOG_TRUSTED_PROXIES`(逗号分隔) 
   否则应用不采信 `X-Forwarded-For`, 直接用 TCP 直连地址 - 这是刻意的: 
   XFF 可被客户端伪造, 无条件采信会导致点赞去重/游客评论归属/UV 统计全部失真 
7. 保证 `backend/data/ip2region_v4.xdb` 已下载(否则评论归属地显示为空) 
8. 静态资源建议由反代直出并加长缓存; `/assets/uploads` 目录建议关闭脚本执行权限 
   (上传目录与站点同源, 虽然上传已做扩展名白名单, 仍是纵深防御的一层) 

### 9.3 数据保留与定时清理

`visit_logs`(访问明细)会随时间无限增长, `refresh_tokens`(已吊销/已过期)与 `operation_logs` 同理 
应用**不会**自动删除这些行 - 清理是显式的运维动作, 由 `backend/scripts/cleanup_old_data.py` 执行: 

```bash
cd backend
.venv/Scripts/python.exe scripts/cleanup_old_data.py            # 预览(默认 dry-run)
.venv/Scripts/python.exe scripts/cleanup_old_data.py --apply    # 实际删除
```

保留期由 `.env` 控制, 默认 `PHXXBLOG_DATA_RETENTION_DAYS=180`(访问明细), 
`PHXXBLOG_AUDIT_LOG_RETENTION_DAYS=365`(操作日志); 刷新令牌只按状态/有效期清理, 与保留天数无关 

清理的影响范围: 

| 数据 | 清理后是否受影响 |
| --- | --- |
| 趋势图 `/stats/trend` | 不受影响(读按日聚合的 `daily_stats`, 永久保留) |
| 访问明细 `/stats/visits`, 来源分布 `/stats/sources` | 只反映保留期内的数据 |
| 贡献热力图 | 不受影响(同样读 `daily_stats`) |

建议**每月执行一次** Windows 计划任务(单行, 路径按实际仓库位置替换): 

```powershell
schtasks /create /tn "phxxblog-cleanup" /sc monthly /d 1 /st 04:00 /tr "D:\Projects\phxxblog\backend\.venv\Scripts\python.exe D:\Projects\phxxblog\backend\scripts\cleanup_old_data.py --apply"
```

Linux cron(注意工作目录要是 `backend`, 脚本按自身位置定位 `PROJECT_ROOT`): 

```cron
0 4 1 * *  cd /path/to/phxxblog/backend && .venv/bin/python scripts/cleanup_old_data.py --apply >> /var/log/phxxblog-cleanup.log 2>&1
```

首次部署如果已经积攒了大量历史数据, 先跑一次 dry-run 确认删除量, 再 `--apply` 

## 10. 开发约定

- 代码注释与文档统一使用中文, 注释说明"为什么"而非重复代码本身 
- 所有接口统一返回 `{code, message, data}`, 列表统一分页结构(后端用 `core/pagination.py` 的 `paginate()`); 前端只解包一次 
- 权限校验放在路由层, 一律用**权限码**(`Depends(require_permission(Perm.X))` 或 `user.permission_codes`), 
  **不要判断角色名**(`"admin" in role_codes`) - 角色 code 可被后台修改, 角色名判断会静默失效 
- 新增数据库列时: 修改模型后手工写迁移 SQL 到 `backend/scripts/` 并在自己的库执行, 同时往 `schema_version` 登记 
  应用启动会校验模型与库结构, 缺列会拒绝启动(而不是等到查询才炸 `Unknown column`) 
- 改动主题令牌: 改 `frontend/src/styles/themes/_source/tokens.mjs`, 然后 
  `npm run themes:generate`(生成)与 `npm run themes:audit`(校验), 不要手改生成的 CSS 
- 新增图标: 加到 `components/MetaIcon.vue` 的 `PATHS`, 然后 `npm run check:icons` 
  (能抓到 `7.5.5` 这类不会报错但会让笔画丢失的手误) 
- 用到 Element Plus 的程序式 API(ElMessage / ElMessageBox / ElNotification / ElLoading)时, 
  必须在 `main.ts` 引入对应样式, 然后 `npm run check:element-styles` 复核(按需引入看不到 JS 调用) 
- 表单里带 Markdown 编辑器时, 保存前要用编辑器实例的 `getValue()`/`syncContent()` 取内容, 
  不要只读 v-model: 中文输入法组字期间 Vditor 不回调 input, 会丢掉刚输入的内容 
- 后端改动后跑测试: `cd backend && .venv/Scripts/python.exe -m pytest tests -q` 
  测试用内存 SQLite, 不会碰开发库; CI 见 `.github/workflows/ci.yml`(含前端类型/测试/构建两个 job) 
- 前端必须用 Node >= 22.19(CI 与 `.nvmrc` 用 24): jsdom 30 依赖 undici 8, 而 undici 8 需要 
  `node:worker_threads.markAsUncloneable` 低于该版本加载 jsdom 会直接抛 
  `TypeError: webidl.util.markAsUncloneable is not a function`, 所有测试文件都起不来 
- 前端提交前建议执行类型检查与构建: `cd frontend && npm run build` 
- 关注体积变化时跑 `cd frontend && npm run build && npm run check:size`(先量再改, 避免"感觉变快了") 
- 前端单测: `cd frontend && npm run test`(Vitest + jsdom) 视图里重复的流程逻辑不要复制第二份, 
  抽到 `src/composables/`; 视图之间的差异用 options 注入(参见 `usePostEditor` / `useImportExport`) 
- 测试的分层, 用例清单, 检查脚本与 CI 的完整说明见 [测试与检查说明](./testing.md) 
- 前端任何地方都不要直接写 `blog_access_token` 这类 key 字面量, 统一走 `utils/tokenStorage.ts` 
- 功能变更同步更新根目录 `CHANGELOG.md`(前台可展示给访客) 
