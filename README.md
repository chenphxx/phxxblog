# phxxblog

## 快速开始

> 最简单的方式: 双击项目根目录的 `start.bat`, 脚本会自动检查环境并同时启动前后端 

### 环境要求

- Node.js ≥ 18(推荐 20+) 
- Python ≥ 3.10 
- MySQL 9(本项目使用的是MySQL 9, 其他版本自行测试即可) 

### 初始化数据库

确认 MySQL 服务已启动后, 创建数据库: 

```bash
mysql -u root -p < backend/scripts/init_db.sql
```

> 表结构会在后端首次启动时自动创建, 无需手工建表 

### 启动后端

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env               # Windows: copy; macOS/Linux: cp
```

编辑 `.env`, 把数据库连接串里的密码改成你的 MySQL 密码: 

```ini
PHXXBLOG_DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/phxxblog?charset=utf8mb4
```

初始化管理员账号、角色权限和默认设置, 并下载离线 IP 定位库(用于评论显示省市区): 

```bash
python -m app.seed
python scripts/download_ip2region.py
```

启动后端服务:

```bash
uvicorn app.main:app --reload --port 8000
```

> 首次初始化会创建管理员账号(admin), 请登录后台后尽快修改密码 

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 访问地址

| 地址                              | 说明                          |
| ------------------------------- | --------------------------- |
| <http://localhost:5173>         | 博客前台(首页/文章/归档/全部文章/日记)      |
| <http://localhost:5173/#/admin> | 管理后台(登录后使用)                 |
| <http://localhost:8000/docs>    | 后端 API 文档(Swagger, 仅管理员可访问) |

前端开发服务器会把 `/api`、`/assets` 以及文档路径 `/docs`、`/redoc`、`/openapi.json` 自动代理到后端(见 `frontend/vite.config.ts`), 因此只需分别启动后端和前端即可联调 

### 常见问题

- **`npm` 无法执行(PowerShell 执行策略)**: 改用 `npm.cmd install` / `npm.cmd run dev`, 或以管理员身份执行 `Set-ExecutionPolicy RemoteSigned` 
- **后端启动报数据库连接失败**: 检查 `.env` 中 `PHXXBLOG_DATABASE_URL` 的用户名/密码/端口是否正确, 且 MySQL 服务已启动 
- **评论显示「未知地区」**: 未下载离线 IP 库, 执行 `python scripts/download_ip2region.py` 
- **端口被占用**: 后端用 `--port 8001` 换端口; 前端换端口需同步修改 `frontend/vite.config.ts` 里的代理目标 

## WordPress 数据迁移

如果你有 WordPress 导出文件(WXR XML, 如 `assets/wordpress/所有内容.xml`), 可一键迁移文章、分类、评论和附件:

```bash
cd backend
python scripts/import_wordpress.py                 # 自动找 assets/wordpress 下最大的 xml
python scripts/import_wordpress.py --xml 路径.xml --no-download   # 跳过附件下载
```

迁移规则: 文章正文会从 Gutenberg/HTML 转为 Markdown; 作者账号自动创建(随机密码, 可在后台重置); 可下载的附件保存到 `assets/uploads/wordpress/` 并登记到媒体库, 正文中的旧站图片链接会自动改写为本地地址

## 开发文档

- [技术架构与实现说明](docs/architecture.md) — 技术栈、系统架构、目录职责与各功能的实现方式
- [接口文档](docs/api.md)
- [数据库表结构设计](docs/mysql.md)
- [更新日志](CHANGELOG.md)
