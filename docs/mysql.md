# 数据库设计(mysql.md)

> 数据库: MySQL 9, 默认字符集 `utf8mb4`, 排序规则 `utf8mb4_unicode_ci`, 存储引擎 InnoDB。
> 本文档为表结构设计说明, 文末附完整可执行 DDL。应用启动时也可由 SQLAlchemy 自动建表。

## 命名约定

- 表名、字段名使用小写蛇形命名
- 主键统一为 `id BIGINT UNSIGNED AUTO_INCREMENT`
- 创建时间统一为 `created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`
- 更新时间统一为 `updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`
- 外键字段使用 `_id` 后缀

## 表清单

| 表名 | 说明 |
| --- | --- |
| users | 用户(含管理员) |
| roles | 角色 |
| permissions | 权限 |
| role_permissions | 角色-权限关联 |
| user_roles | 用户-角色关联 |
| refresh_tokens | 登录刷新令牌会话 |
| categories | 文章分类(支持父子层级) |
| tags | 文章标签 |
| posts | 文章 |
| post_tags | 文章-标签关联 |
| comments | 评论(游客/注册用户, 支持回复) |
| media | 媒体/附件(图片、视频、文件) |
| post_likes | 文章点赞(游客按 IP, 用户按账号) |
| visit_logs | 访问明细(PV/UV/来源/浏览器/IP) |
| daily_stats | 按日聚合统计数据 |
| operation_logs | 操作日志 |
| settings | 系统设置(站点信息/SEO/社交链接等) |

## 表结构说明

### users 用户表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 用户ID |
| username | VARCHAR(50) UNIQUE | 登录名 |
| email | VARCHAR(100) UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | bcrypt 密码散列 |
| nickname | VARCHAR(50) | 昵称 |
| avatar | VARCHAR(255) | 头像URL |
| bio | VARCHAR(500) | 个人简介 |
| website | VARCHAR(255) | 个人网站 |
| social | JSON | 社交账号链接(GitHub/掘金/B站等) |
| status | TINYINT | 1启用 0禁用 |
| last_login_at | DATETIME | 最近登录时间 |
| created_at / updated_at | DATETIME | 创建/更新时间 |

### roles 角色表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 角色ID |
| name | VARCHAR(50) | 角色名(管理员/编辑/作者) |
| code | VARCHAR(50) UNIQUE | 角色代码(admin/editor/author) |
| description | VARCHAR(200) | 描述 |
| created_at | DATETIME | 创建时间 |

### permissions 权限表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 权限ID |
| name | VARCHAR(50) | 权限名 |
| code | VARCHAR(100) UNIQUE | 权限代码(post:create / post:publish / user:manage 等) |
| description | VARCHAR(200) | 描述 |
| created_at | DATETIME | 创建时间 |

### role_permissions 角色权限关联

`(role_id, permission_id)` 联合主键, 分别外键关联 roles、permissions。

### user_roles 用户角色关联

`(user_id, role_id)` 联合主键, 分别外键关联 users、roles。

### refresh_tokens 刷新令牌表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 会话ID |
| user_id | BIGINT FK | 用户 |
| token_hash | CHAR(64) UNIQUE | 令牌 SHA-256 散列 |
| expires_at | DATETIME | 过期时间 |
| revoked | TINYINT | 是否已吊销(1是 0否) |
| ip | VARCHAR(45) | 登录IP |
| user_agent | VARCHAR(500) | 登录设备UA |
| created_at | DATETIME | 创建时间 |

### categories 分类表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 分类ID |
| name | VARCHAR(50) | 分类名 |
| slug | VARCHAR(80) UNIQUE | URL别名 |
| parent_id | BIGINT NULL | 父分类, 支持层级 |
| description | VARCHAR(200) | 描述 |
| sort_order | INT | 排序(小在前) |
| created_at / updated_at | DATETIME | 时间 |

### tags 标签表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 标签ID |
| name | VARCHAR(50) UNIQUE | 标签名 |
| slug | VARCHAR(80) UNIQUE | URL别名 |
| created_at | DATETIME | 创建时间 |

### posts 文章表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 文章ID |
| author_id | BIGINT FK | 作者 |
| title | VARCHAR(200) | 标题 |
| slug | VARCHAR(220) UNIQUE | URL别名(SEO) |
| summary | VARCHAR(500) | 摘要 |
| content_md | LONGTEXT | Markdown 原文 |
| content_html | LONGTEXT | 渲染后的 HTML |
| cover_image | VARCHAR(255) | 封面图URL |
| category_id | BIGINT NULL FK | 所属分类 |
| status | TINYINT | 0草稿 1审核中 2已发布 3私密 4回收站 |
| views | INT UNSIGNED | 阅读量 |
| likes_count | INT UNSIGNED | 点赞数(冗余, 便于列表展示) |
| ip | VARCHAR(45) | 发布时的IP |
| published_at | DATETIME NULL | 发布时间 |
| created_at / updated_at | DATETIME | 创建/更新时间 |

索引: `idx_status_published(status, published_at)`, `idx_category(category_id)`, `idx_author(author_id)`, 全文索引 `ft_post(title, summary, content_md) WITH PARSER ngram`(支持中文搜索)。

### post_tags 文章标签关联

`(post_id, tag_id)` 联合主键, 分别外键关联 posts、tags。

### comments 评论表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 评论ID |
| post_id | BIGINT FK | 所属文章 |
| parent_id | BIGINT NULL | 父评论(回复) |
| user_id | BIGINT NULL | 登录用户(游客为空) |
| author_name | VARCHAR(50) | 游客昵称 |
| author_email | VARCHAR(100) | 游客邮箱 |
| content | TEXT | 评论内容 |
| ip | VARCHAR(45) | 评论IP |
| status | TINYINT | 1正常 0隐藏 2回收站 |
| created_at | DATETIME | 评论时间 |

索引: `idx_post_status(post_id, status)`, `idx_parent(parent_id)`。

### media 媒体表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 媒体ID |
| uploader_id | BIGINT NULL FK | 上传者 |
| original_name | VARCHAR(255) | 原始文件名 |
| filename | VARCHAR(255) UNIQUE | 落盘文件名 |
| path | VARCHAR(255) | 相对 `assets/` 的路径 |
| url | VARCHAR(255) | 访问URL |
| mime_type | VARCHAR(100) | MIME 类型 |
| size | BIGINT | 文件大小(字节) |
| type | VARCHAR(20) | image / video / file |
| related_type | VARCHAR(20) NULL | 关联对象类型(post/comment) |
| related_id | BIGINT NULL | 关联对象ID |
| created_at | DATETIME | 上传时间 |

### post_likes 文章点赞表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 点赞ID |
| post_id | BIGINT FK | 文章 |
| user_id | BIGINT NULL | 用户(游客为空) |
| ip | VARCHAR(45) | 游客IP |
| created_at | DATETIME | 点赞时间 |

唯一约束: `uk_post_user(post_id, user_id)`, `uk_post_ip(post_id, ip)` —— 同一用户或同一 IP 对同一文章只能点赞一次。

### visit_logs 访问明细表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 访问ID |
| post_id | BIGINT NULL FK | 访问的文章(可为空) |
| ip | VARCHAR(45) | 访问IP |
| user_agent | VARCHAR(500) | UA |
| referer | VARCHAR(500) | 来源地址 |
| url | VARCHAR(255) | 访问URL |
| browser | VARCHAR(50) | 浏览器 |
| os | VARCHAR(50) | 操作系统 |
| device | VARCHAR(20) | 设备(desktop/mobile) |
| visit_time | DATETIME | 访问时间 |

索引: `idx_visit_time(visit_time)`, `idx_post(post_id)`。

### daily_stats 按日聚合表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 统计ID |
| stat_date | DATE UNIQUE | 日期 |
| pv | INT | 页面访问量 |
| uv | INT | 独立访客数 |
| post_views | INT | 文章阅读量 |
| likes | INT | 点赞数 |
| comments | INT | 评论数 |
| updated_at | DATETIME | 更新时间 |

### operation_logs 操作日志表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED PK | 日志ID |
| user_id | BIGINT NULL | 操作人 |
| username | VARCHAR(50) | 操作人用户名(冗余) |
| module | VARCHAR(50) | 模块(post/user/comment...) |
| action | VARCHAR(50) | 动作(create/update/delete/publish...) |
| target_type | VARCHAR(50) | 目标类型 |
| target_id | BIGINT NULL | 目标ID |
| detail | JSON | 变更详情 |
| ip | VARCHAR(45) | 操作IP |
| created_at | DATETIME | 操作时间 |

### settings 系统设置表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| setting_key | VARCHAR(100) PK | 配置键(site_name/site_desc/seo_keywords/social_links...) |
| setting_value | TEXT | 配置值 |
| description | VARCHAR(255) | 说明 |
| updated_at | DATETIME | 更新时间 |

## 完整 DDL

以下 SQL 可直接执行创建全部表(需先创建数据库, 见 `backend/scripts/init_db.sql`):

```sql
CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nickname VARCHAR(50) NOT NULL,
  avatar VARCHAR(255) DEFAULT NULL,
  bio VARCHAR(500) DEFAULT NULL,
  website VARCHAR(255) DEFAULT NULL,
  social JSON DEFAULT NULL,
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1启用 0禁用',
  last_login_at DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE roles (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  code VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(200) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

CREATE TABLE permissions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  code VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(200) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

CREATE TABLE role_permissions (
  role_id BIGINT UNSIGNED NOT NULL,
  permission_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  CONSTRAINT fk_rp_perm FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

CREATE TABLE user_roles (
  user_id BIGINT UNSIGNED NOT NULL,
  role_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

CREATE TABLE refresh_tokens (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  revoked TINYINT NOT NULL DEFAULT 0,
  ip VARCHAR(45) DEFAULT NULL,
  user_agent VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='刷新令牌表';

CREATE TABLE categories (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  slug VARCHAR(80) NOT NULL UNIQUE,
  parent_id BIGINT UNSIGNED DEFAULT NULL,
  description VARCHAR(200) DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_cat_parent FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章分类表';

CREATE TABLE tags (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  slug VARCHAR(80) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章标签表';

CREATE TABLE posts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  author_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(200) NOT NULL,
  slug VARCHAR(220) NOT NULL UNIQUE,
  summary VARCHAR(500) DEFAULT NULL,
  content_md LONGTEXT NOT NULL,
  content_html LONGTEXT DEFAULT NULL,
  cover_image VARCHAR(255) DEFAULT NULL,
  category_id BIGINT UNSIGNED DEFAULT NULL,
  status TINYINT NOT NULL DEFAULT 0 COMMENT '0草稿 1审核中 2已发布 3私密 4回收站',
  views INT UNSIGNED NOT NULL DEFAULT 0,
  likes_count INT UNSIGNED NOT NULL DEFAULT 0,
  ip VARCHAR(45) DEFAULT NULL,
  published_at DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_post_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_post_cat FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
  INDEX idx_status_published (status, published_at),
  INDEX idx_category (category_id),
  INDEX idx_author (author_id),
  FULLTEXT KEY ft_post (title, summary, content_md) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章表';

CREATE TABLE post_tags (
  post_id BIGINT UNSIGNED NOT NULL,
  tag_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (post_id, tag_id),
  CONSTRAINT fk_pt_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_pt_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章标签关联表';

CREATE TABLE comments (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  post_id BIGINT UNSIGNED NOT NULL,
  parent_id BIGINT UNSIGNED DEFAULT NULL,
  user_id BIGINT UNSIGNED DEFAULT NULL,
  author_name VARCHAR(50) DEFAULT NULL,
  author_email VARCHAR(100) DEFAULT NULL,
  content TEXT NOT NULL,
  ip VARCHAR(45) DEFAULT NULL,
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 0隐藏 2回收站',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cmt_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_cmt_parent FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE,
  CONSTRAINT fk_cmt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_post_status (post_id, status),
  INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

CREATE TABLE media (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uploader_id BIGINT UNSIGNED DEFAULT NULL,
  original_name VARCHAR(255) NOT NULL,
  filename VARCHAR(255) NOT NULL UNIQUE,
  path VARCHAR(255) NOT NULL,
  url VARCHAR(255) NOT NULL,
  mime_type VARCHAR(100) DEFAULT NULL,
  size BIGINT NOT NULL DEFAULT 0,
  type VARCHAR(20) NOT NULL COMMENT 'image/video/file',
  related_type VARCHAR(20) DEFAULT NULL,
  related_id BIGINT UNSIGNED DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_media_user FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_related (related_type, related_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体表';

CREATE TABLE post_likes (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  post_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED DEFAULT NULL,
  ip VARCHAR(45) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_like_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_like_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_post_user (post_id, user_id),
  UNIQUE KEY uk_post_ip (post_id, ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章点赞表';

CREATE TABLE visit_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  post_id BIGINT UNSIGNED DEFAULT NULL,
  ip VARCHAR(45) DEFAULT NULL,
  user_agent VARCHAR(500) DEFAULT NULL,
  referer VARCHAR(500) DEFAULT NULL,
  url VARCHAR(255) DEFAULT NULL,
  browser VARCHAR(50) DEFAULT NULL,
  os VARCHAR(50) DEFAULT NULL,
  device VARCHAR(20) DEFAULT NULL,
  visit_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_visit_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE SET NULL,
  INDEX idx_visit_time (visit_time),
  INDEX idx_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='访问明细表';

CREATE TABLE daily_stats (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  stat_date DATE NOT NULL UNIQUE,
  pv INT NOT NULL DEFAULT 0,
  uv INT NOT NULL DEFAULT 0,
  post_views INT NOT NULL DEFAULT 0,
  likes INT NOT NULL DEFAULT 0,
  comments INT NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='按日聚合统计表';

CREATE TABLE operation_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED DEFAULT NULL,
  username VARCHAR(50) DEFAULT NULL,
  module VARCHAR(50) NOT NULL,
  action VARCHAR(50) NOT NULL,
  target_type VARCHAR(50) DEFAULT NULL,
  target_id BIGINT UNSIGNED DEFAULT NULL,
  detail JSON DEFAULT NULL,
  ip VARCHAR(45) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_user (user_id),
  INDEX idx_module (module),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

CREATE TABLE settings (
  setting_key VARCHAR(100) PRIMARY KEY,
  setting_value TEXT,
  description VARCHAR(255) DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';
```
