# phxxblog

一款博客系统, 采用FastAPI+Vite实现 

## 功能

- **博客**, 提供博客系统基础功能支持, 写文章, 发表评论等 
- **Markdown支持**, 文章/日记均支持markdown格式 
- **插件系统**, 除基础功能外, 其余功能均作为插件加载, 可配置是否要加载 
- **可见范围**, 除核心功能外, 其余功能均能够配置可见范围, 公开可见或仅管理员可见 
- **其他**, `模块管理`中可见更多功能 

## 快速开始

> 可通过脚本`start.bat`一键启动 

### 后端

首先创建数据库 

> 表结构会在后端首次启动时自动创建, 无需手工建表 

```sql
source D:/Projects/phxxblog/backend/scripts/init_db.sql;
```

在终端中按顺序执行以下命令 

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

编辑`.env`配置文件 

```ini
PHXXBLOG_DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/phxxblog?charset=utf8mb4
PHXXBLOG_SECRET_KEY=至少 32 位的随机字符串
```

密钥生成方式 

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

初始化管理员账号, 并下载离线IP定位库(用于评论显示省市区) 

```bash
python -m app.seed
python scripts/download_ip2region.py
```

启动后端服务 

```bash
uvicorn app.main:app --reload --port 8000
```

> 首次初始化会创建管理员账号admin: 密码取`PHXXBLOG_ADMIN_PASSWORD`, 没配则随机生成并在seed的输出里打印一次(只显示这一次), 请登录后台后尽快修改 

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 可选操作

检查类型, 主题令牌一致性, 图标路径, 格式 

```bash
cd backend
.venv/Scripts/python.exe scripts/verify_all.py
```

CI见`.github/workflows/ci.yml`(后端静态检查, 前端类型检查/主题/图标/构建); 前端构建发布见`.github/workflows/build-frontend.yml` 

### 访问地址

| 地址                            | 说明                           |
| ------------------------------- | ------------------------------ |
| <http://localhost:5173>         | 博客前台                       |
| <http://localhost:5173/#/admin> | 管理后台                       |
| <http://localhost:8000/docs>    | 后端API文档(Swagger, 仅管理员) |

## 文档

见`docs/` 
