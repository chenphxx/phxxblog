-- 为互联网纪事增加与文章一致的状态流转字段
-- 已有纪事原本全部直接展示, 因此统一迁移为"已发布"并保留原创建时间作为发布时间

ALTER TABLE chronicles
  ADD COLUMN status SMALLINT NOT NULL DEFAULT 0 AFTER cover_image,
  ADD COLUMN published_at DATETIME NULL DEFAULT NULL AFTER content_html,
  ADD INDEX idx_chronicle_status_published (status, published_at);

UPDATE chronicles
SET status = 2,
    published_at = created_at
WHERE published_at IS NULL;

INSERT IGNORE INTO schema_version (version)
VALUES ('migration_20261106_chronicle_status.sql');
