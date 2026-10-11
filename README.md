# phxxblog

## 快速开始

> 双击项目根中的 `start.bat`, 脚本会自动检查环境并启动项目 

### 环境要求

- Node.js ≥ 22.19(`.nvmrc` 与 CI 用 24) 
- Python ≥ 3.10(本项目使用3.14.7, 其他版本自行测试即可) 
- MySQL 9(本项目使用的是MySQL 9, 其他版本自行测试即可) 

### 初始化数据库

创建数据库: 

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

编辑 `.env`, 需改动数据库连接串里的密码, 以及 `PHXXBLOG_SECRET_KEY`(`.env.example` 里的占位值长度不足 32, 不改会拒绝启动): 

```ini
PHXXBLOG_DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/phxxblog?charset=utf8mb4
PHXXBLOG_SECRET_KEY=至少 32 位的随机字符串
```

密钥生成方式: 

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

初始化管理员账号, 角色权限和默认设置, 并下载离线 IP 定位库(用于评论显示省市区): 

```bash
python -m app.seed
python scripts/download_ip2region.py
```

启动后端服务: 

```bash
uvicorn app.main:app --reload --port 8000
```

> 首次初始化会创建管理员账号 admin: 密码取 `PHXXBLOG_ADMIN_PASSWORD`, 没配则随机生成并在 seed 的输出里打印一次(只显示这一次), 请登录后台后尽快修改 

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

检查类型, 主题令牌一致性, 图标路径, 格式: 

```bash
cd backend
.venv/Scripts/python.exe scripts/verify_all.py
```

CI 见 `.github/workflows/ci.yml`(后端静态检查, 前端类型检查/主题/图标/构建); 前端构建发布见 `.github/workflows/build-frontend.yml` 

### 访问地址

| 地址                              | 说明                          |
| ------------------------------- | --------------------------- |
| <http://localhost:5173>         | 博客前台(首页/文章/归档/全部文章/日记)      |
| <http://localhost:5173/#/admin> | 管理后台(登录后使用)                 |
| <http://localhost:8000/docs>    | 后端 API 文档(Swagger, 仅管理员可访问) |

前端开发服务器会把 `/api`, `/assets` 以及文档路径 `/docs`, `/redoc`, `/openapi.json` 自动代理到后端(见 `frontend/vite.config.ts`), 因此只需分别启动后端和前端即可联调 

## 文档

见`docs/` 
