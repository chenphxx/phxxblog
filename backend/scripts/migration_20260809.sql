-- 2026-08-09 数据迁移与清理
-- 1) 合并 WordPress 迁移作者 chenphxx(id=5) 到 admin(id=1)
UPDATE posts SET author_id = 1 WHERE author_id = 5;
UPDATE media SET uploader_id = 1 WHERE uploader_id = 5;
UPDATE comments SET user_id = 1 WHERE user_id = 5;
UPDATE operation_logs SET user_id = 1, username = 'admin' WHERE user_id = 5;
DELETE FROM user_roles WHERE user_id = 5;
DELETE FROM refresh_tokens WHERE user_id = 5;
DELETE FROM users WHERE id = 5;

-- 2) 管理员昵称改为博客作者名
UPDATE users SET nickname = 's1asH' WHERE id = 1;

-- 3) 彻底删除两篇测试文章(级联删除评论/点赞/标签关联)
DELETE FROM posts WHERE id IN (1, 2);

-- 4) 删除测试上传的 txt 媒体记录
DELETE FROM media WHERE original_name LIKE '%upload%' OR url LIKE '%phxxblog-upload%';
