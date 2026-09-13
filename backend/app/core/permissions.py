"""权限码常量定义。

约定: 所有需要授权的判断都走权限码(require_permission 依赖, 或
user.permission_codes), **不要在业务代码里判断角色名**(如 `"admin" in role_codes`)。
原因: 角色 code 是可以被后台修改的(users.py 的 update_role), 一旦改名,
基于角色名的判断会静默失效或误放行; 而权限码经角色聚合, 语义稳定。
"""


class Perm:
    """权限码, 与 seed 初始化数据保持一致。"""

    POST_CREATE = "post:create"
    POST_EDIT = "post:edit"
    POST_PUBLISH = "post:publish"
    POST_DELETE = "post:delete"
    POST_MANAGE = "post:manage"
    COMMENT_MANAGE = "comment:manage"
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    MEDIA_MANAGE = "media:manage"
    SETTING_MANAGE = "setting:manage"
    LOG_VIEW = "log:view"
    STATS_VIEW = "stats:view"
    DATA_EXPORT = "data:export"
    # 日记与更新日志原本是硬编码"仅 admin 角色", 抽成语义化权限码
    DIARY_MANAGE = "diary:manage"
    CHANGELOG_MANAGE = "changelog:manage"
