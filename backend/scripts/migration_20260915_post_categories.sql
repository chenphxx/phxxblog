-- 迁移: 文章分类由单选改多选(一篇文章可以属于多个分类)
--
-- 背景: 原 posts.category_id 让一篇文章只能挂一个分类, 现在后台/前端都支持多选,
-- 关系改由 post_categories 关联表维护(与既有的 post_tags 结构一致,
-- 见 docs/mysql.md 的 post_categories 一节 与 app/models/post.py 的注释)。
--
-- 执行: mysql -u root -p phxxblog < backend/scripts/migration_20260915_post_categories.sql
-- 幂等: 建表用 IF NOT EXISTS; 搬迁/删外键/删索引/删列前都先判断目标是否存在。
--
-- 注意: post_categories 也会被启动时的 Base.metadata.create_all() 自动创建;
-- 这里显式建表是为了老库执行一次迁移就把数据与结构都处理好。

-- 1) 建关联表
CREATE TABLE IF NOT EXISTS post_categories (
  post_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (post_id, category_id),
  CONSTRAINT fk_pc_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_pc_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章分类关联表';

-- 2) 老的单选分类搬到关联表(先判断 posts.category_id 是否还在)
SET @has_column := (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'posts' AND column_name = 'category_id'
);

SET @sql := IF(@has_column > 0,
  'INSERT IGNORE INTO post_categories (post_id, category_id) SELECT id, category_id FROM posts WHERE category_id IS NOT NULL',
  'SELECT ''posts.category_id 已不存在, 跳过数据搬迁'' AS result');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3) 删外键 fk_post_cat
SET @has_fk := (
  SELECT COUNT(*) FROM information_schema.table_constraints
  WHERE table_schema = DATABASE() AND table_name = 'posts'
    AND constraint_name = 'fk_post_cat' AND constraint_type = 'FOREIGN KEY'
);

SET @sql := IF(@has_fk > 0,
  'ALTER TABLE posts DROP FOREIGN KEY fk_post_cat',
  'SELECT ''fk_post_cat 不存在, 跳过'' AS result');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4) 删索引 idx_category(外键删除后该索引不会自动消失, 需要显式删)
SET @has_index := (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'posts' AND index_name = 'idx_category'
);

SET @sql := IF(@has_index > 0,
  'ALTER TABLE posts DROP INDEX idx_category',
  'SELECT ''idx_category 不存在, 跳过'' AS result');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5) 删列 category_id
SET @sql := IF(@has_column > 0,
  'ALTER TABLE posts DROP COLUMN category_id',
  'SELECT ''posts.category_id 已不存在, 跳过'' AS result');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6) 登记版本(与应用启动时的 record_version 保持一致的写法)
INSERT IGNORE INTO schema_version (version) VALUES ('migration_20260915_post_categories.sql');