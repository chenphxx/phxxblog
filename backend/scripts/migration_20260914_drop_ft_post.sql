-- 迁移: 删除未使用的全文索引 ft_post
--
-- 背景: 该索引以 FULLTEXT + ngram 建立, 但搜索实现一直用 LIKE '%kw%'
-- (前导 % 使任何索引都无法命中), 因此它只带来写入开销。
--
-- 为什么不改成 MATCH ... AGAINST 来利用它: 实测 ngram 在本项目的关键词上更差 ——
--   "网盘" LIKE 2 / MATCH 2
--   "Git"  LIKE 4 / MATCH 0   (短英文词不在词表)
--   "的"   LIKE 14 / MATCH 0  (单字不满足 ngram 最小词长)
-- 详见 app/models/post.py 中 posts.__table_args__ 的注释。
--
-- 执行: mysql -u root -p phxxblog < backend/scripts/migration_20260914_drop_ft_post.sql
-- 幂等: 先判断索引是否存在。

SET @exists := (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'posts' AND index_name = 'ft_post'
);

SET @sql := IF(@exists > 0,
  'ALTER TABLE posts DROP INDEX ft_post',
  'SELECT ''ft_post 不存在, 跳过'' AS result');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
