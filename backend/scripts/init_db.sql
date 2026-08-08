-- 数据库初始化脚本
-- 用法: mysql -u root -p < backend/scripts/init_db.sql

CREATE DATABASE IF NOT EXISTS phxxblog
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 可选: 创建专用账号(按需取消注释并修改密码)
-- CREATE USER IF NOT EXISTS 'blog'@'localhost' IDENTIFIED BY 'blog123456';
-- GRANT ALL PRIVILEGES ON phxxblog.* TO 'blog'@'localhost';
-- FLUSH PRIVILEGES;
