"""初始化脚本: 建表、创建权限/角色/管理员、写入默认设置。"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine
from app.core.permissions import Perm
from app.core.security import hash_password
from app.models.post import Category, Tag
from app.models.setting import Setting
from app.models.user import Permission, Role, User


PERMISSIONS = [
    (Perm.POST_CREATE, "创建文章", "post:create"),
    (Perm.POST_EDIT, "编辑文章", "post:edit"),
    (Perm.POST_PUBLISH, "发布文章", "post:publish"),
    (Perm.POST_DELETE, "删除文章", "post:delete"),
    (Perm.POST_MANAGE, "管理所有文章", "post:manage"),
    (Perm.COMMENT_MANAGE, "管理评论", "comment:manage"),
    (Perm.USER_MANAGE, "管理用户", "user:manage"),
    (Perm.ROLE_MANAGE, "管理角色", "role:manage"),
    (Perm.MEDIA_MANAGE, "管理媒体", "media:manage"),
    (Perm.SETTING_MANAGE, "管理设置", "setting:manage"),
    (Perm.LOG_VIEW, "查看日志", "log:view"),
    (Perm.STATS_VIEW, "查看统计", "stats:view"),
    (Perm.DATA_EXPORT, "导出数据", "data:export"),
]


ROLES = {
    "admin": {
        "name": "管理员",
        "description": "拥有全部权限",
        "permissions": [p[0] for p in PERMISSIONS],
    },
    "editor": {
        "name": "编辑",
        "description": "可发布与管理内容",
        "permissions": [
            Perm.POST_CREATE, Perm.POST_EDIT, Perm.POST_PUBLISH,
            Perm.POST_DELETE, Perm.POST_MANAGE, Perm.COMMENT_MANAGE,
            Perm.MEDIA_MANAGE, Perm.STATS_VIEW, Perm.LOG_VIEW,
        ],
    },
    "author": {
        "name": "作者",
        "description": "可创作文章并提交审核",
        "permissions": [Perm.POST_CREATE, Perm.POST_EDIT, Perm.POST_DELETE],
    },
}


DEFAULT_SETTINGS = {
    "site_name": ("chenphxx's blog", "站点名称"),
    "site_desc": ("记录技术成长与生活点滴的个人博客", "站点描述"),
    "site_keywords": ("blog, 技术, 分享", "SEO 关键词"),
    "site_icon": ("", "站点图标URL"),
    "site_avatar": ("", "首页头像URL"),
    "site_bio": ("一个热爱编程的开发者", "首页个人简介"),
    "site_readme": ("", "主页 README(Markdown)"),
    "tech_tags": ('["Python", "Vue", "FastAPI", "MySQL"]', "首页技术标签(JSON数组)"),
    "social_links": ('[{"name": "GitHub", "url": "https://github.com/chenphxx"}]', "社交账号链接(JSON数组)"),
    "website_links": ("[]", "网站链接(JSON数组)"),
}


def seed() -> None:
    """执行初始化。"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. 权限
        perm_map: dict[str, Permission] = {}
        for code, name, _ in PERMISSIONS:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if perm is None:
                perm = Permission(name=name, code=code)
                db.add(perm)
                db.flush()
            perm_map[code] = perm
        db.commit()

        # 2. 角色
        role_map: dict[str, Role] = {}
        for code, conf in ROLES.items():
            role = db.query(Role).filter(Role.code == code).first()
            if role is None:
                role = Role(name=conf["name"], code=code, description=conf["description"])
                db.add(role)
                db.flush()
            role.name = conf["name"]
            role.description = conf["description"]
            role.permissions = [perm_map[c] for c in conf["permissions"]]
            role_map[code] = role
        db.commit()

        # 3. 管理员账号(仅当没有任何用户时创建)
        if db.query(User).count() == 0:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("admin123456"),
                nickname="管理员",
                bio="博客管理员",
            )
            admin.roles = [role_map["admin"]]
            db.add(admin)
            print("已创建管理员账号: admin / admin123456(请尽快修改密码)")
        db.commit()

        # 4. 默认设置
        for key, (value, description) in DEFAULT_SETTINGS.items():
            if db.get(Setting, key) is None:
                db.add(Setting(setting_key=key, setting_value=value, description=description))
        db.commit()

        # 5. 默认分类/标签
        if db.query(Category).count() == 0:
            db.add(Category(name="默认分类", slug="default", description="系统默认分类"))
        if db.query(Tag).count() == 0:
            db.add(Tag(name="随笔", slug="essay"))
        db.commit()
        print("初始化完成!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
