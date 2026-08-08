"""权限码常量定义。"""


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
