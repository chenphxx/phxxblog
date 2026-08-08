# chenphxx's Blog

个人博客项目(开发初期), 前后端分离架构。

## 功能特性

- **文章模块**: 支持新增、编辑、删除、发布、草稿保存; 状态包含 草稿 / 审核中 / 已发布 / 私密 / 回收站; 支持 Markdown 语法, 可插入图片、视频、附件, 嵌入链接可预览内容; 代码块高亮 + 一键复制
- **文章属性**: 标题、摘要、发布时间、更新时间、IP、分类、标签、阅读量、点赞量(游客可点赞)
- **评论**: 游客可评论, 展示 IP 地址, 支持回复, 评论可带链接/图片/附件
- **归档**: 按顺序展示所有文章的时间轴, 支持点击跳转到特定时间段
- **主题**: 深色/浅色模式切换, 默认浅色, 记住上次选择
- **首页**: 昵称、头像、个人简介、技术标签、社交账号链接、网站链接
- **首页**: GitHub 风格个人主页(左侧资料 + 右侧 README), 文章发布贡献热力图, 右侧常用网站栏(管理员可见)
- **日记**: 仅管理员可见的时间轴日记, 支持图片/视频/附件/链接, 独立贡献热力图
- **更新日志**: 前端页面展示 CHANGELOG.md 内容(仅管理员)
- **后台管理**: Dashboard 数据看板(文章数/访问量/评论量/用户数)、内容管理(文章/分类/标签/评论/媒体)、用户管理(用户/角色/权限/密码/邮箱)、数据导出
- **其他**: 操作日志、PV/UV/来源/浏览器/IP 统计、SEO、RSS、搜索

## 技术栈

| 端 | 技术 |
| --- | --- |
| 前端 | Vue 3 + TypeScript + Vite, Element Plus, Vditor(Markdown), Pinia(状态), Vue Router, Axios |
| 后端 | Python FastAPI, SQLAlchemy 2.x, PyMySQL, JWT 认证, bcrypt 密码加密 |
| 数据库 | MySQL 9 |

## 架构设计

前后端分离, 通过 RESTful API 通信, 前端开发时由 Vite 代理 `/api` 到后端; 生产环境可将前端构建产物交给任意静态服务器, 后端独立部署。

```text
┌───────────────────┐        HTTP / JSON        ┌─────────────────────┐
│  前端 Vue3 SPA      │ ────────────────────────▶ │  后端 FastAPI        │
│  博客前台 + 后台管理  │ ◀──────────────────────── │  REST API + JWT 认证  │
└───────────────────┘                           └──────────┬──────────┘
                                                           │ SQLAlchemy
                                                ┌──────────▼──────────┐
                                                │   MySQL 9           │
                                                └─────────────────────┘
```

### 目录结构

```text
phxxblog/
├── README.md              # 本文件: 架构与模块设计说明
├── mysql.md               # 数据库表结构设计
├── docs/                  # 开发文档(API 设计、开发进度等)
├── assets/                # 附件/媒体存放目录(上传文件落盘位置)
├── frontend/              # 前端工程(Vue3 + TS + Vite)
│   └── src/
│       ├── api/           # 接口封装(Axios)
│       ├── components/    # 通用组件
│       ├── router/        # 路由
│       ├── stores/        # Pinia 状态(主题/认证等)
│       ├── styles/        # 全局样式(深浅色主题变量)
│       └── views/         # 页面(home / post / archive / admin ...)
└── backend/               # 后端工程(FastAPI)
    ├── app/
    │   ├── api/v1/        # 路由: auth / users / posts / comments / media / stats / logs / rss / search / dashboard ...
    │   ├── core/          # 配置、数据库、安全、依赖
    │   ├── models/        # ORM 模型(按模块拆分)
    │   ├── schemas/       # Pydantic 请求/响应模型
    │   └── services/      # 业务逻辑
    ├── scripts/           # 数据库初始化脚本
    └── requirements.txt
```

### 模块设计

| 模块 | 说明 |
| --- | --- |
| 账号管理 | 注册/登录(JWT)、刷新令牌、密码/邮箱修改、用户/角色/权限管理 |
| 文章 | 草稿、审核中、已发布、私密、回收站五态; 分类/标签; 归档时间轴; 阅读量/点赞 |
| 评论 | 游客评论、回复、附件, 记录 IP |
| 媒体 | 图片/视频/附件上传, 存储于 `assets/`, 数据库记录元数据 |
| 统计 | PV/UV/访问来源/浏览器/IP, 按日聚合; Dashboard 数据看板 |
| 日志 | 操作日志: 谁在什么时间改了什么内容 |
| 其他 | RSS 订阅、全文搜索、SEO(sitemap / meta)、深浅色主题 |

## 快速开始

### 1. 数据库

1. 确认本机 MySQL 9 服务已启动
2. 按 [mysql.md](./mysql.md) 创建数据库, 或直接执行初始化脚本:

```bash
mysql -u root -p < backend/scripts/init_db.sql
```

### 2. 后端

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env               # 修改数据库连接等配置
python -m app.seed                   # 初始化管理员账号、角色权限、默认设置
uvicorn app.main:app --reload --port 8000
```

> 首次初始化会创建管理员账号, 请登录后台后尽快修改密码。

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:5173> 即可访问; 后端 API 文档见 <http://localhost:8000/docs>。

## WordPress 数据迁移

如果你有 WordPress 导出文件(WXR XML, 如 `assets/wordpress/所有内容.xml`), 可一键迁移文章、分类、评论和附件:

```bash
cd backend
python scripts/import_wordpress.py                 # 自动找 assets/wordpress 下最大的 xml
python scripts/import_wordpress.py --xml 路径.xml --no-download   # 跳过附件下载
```

迁移规则: 文章正文会从 Gutenberg/HTML 转为 Markdown; 作者账号自动创建(随机密码, 可在后台重置); 可下载的附件保存到 `assets/uploads/wordpress/` 并登记到媒体库, 正文中的旧站图片链接会自动改写为本地地址。

> 部分旧站附件已丢失(404), 缺失清单见 `assets/wordpress/missing-images.md`。将原图放入 `assets/wordpress/images/` 后执行 `python scripts/import_local_images.py` 即可自动补全并改写文章链接。

## 数据库设计

完整表结构见 [mysql.md](./mysql.md), 包含: 用户/角色/权限、文章/分类/标签、评论、媒体、点赞、访问统计、操作日志、系统设置等。

## 开发文档

- [更新日志](./CHANGELOG.md)
- [API 接口设计](./docs/api.md)
- [开发进度](./docs/progress.md)

## 联系作者

可通过 [GitHub 主页](https://github.com/chenphxx) 或仓库 Issues 反馈。
