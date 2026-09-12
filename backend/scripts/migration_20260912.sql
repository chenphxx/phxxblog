-- 2026-09-12 数据迁移
-- 1) 分类/标签支持自定义颜色(为空时前端按名称自动生成兜底色)
ALTER TABLE categories ADD COLUMN color VARCHAR(20) NULL AFTER description;
ALTER TABLE tags ADD COLUMN color VARCHAR(20) NULL AFTER slug;

-- 2) 新增浏览器标签页名称设置(留空则回退为站点名称)
INSERT INTO settings (setting_key, setting_value, description)
VALUES ('site_title', '', '浏览器标签页名称')
ON DUPLICATE KEY UPDATE description = VALUES(description);
