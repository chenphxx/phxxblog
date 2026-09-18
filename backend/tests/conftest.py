"""pytest 共享装置。

要点(踩过的坑都记在这里):
  1. 用**内存 SQLite** 跑测试, 不碰开发用的 MySQL —— 测试必须能随便跑。
  2. 模型的 BigInteger 主键在 SQLite 上不会自增(SQLite 只有 INTEGER PRIMARY KEY 才自增),
     所以要把 BigInteger 编译成 INTEGER。这是 sqlalchemy 官方文档给的做法。
  3. app 启动时会做 schema 校验(compare model vs db), 在 SQLite 上没问题;
     但 main.py 的 lifespan 会 create_all, 这里我们自己也建表。
  4. 每个测试用独立的内存库(fixture function 作用域), 避免相互污染。
"""

import os
import sys
from pathlib import Path

# 让 `import app.*` 生效
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# 必须在导入 app.core.config 之前设置, 否则会被 .env 覆盖
os.environ.setdefault("PHXXBLOG_SECRET_KEY", "test-secret-key-0123456789abcdefghijklmnop")

import pytest  # noqa: E402
from sqlalchemy import BigInteger, create_engine, event  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


@compiles(BigInteger, "sqlite")
def _bigint_as_integer(type_, compiler, **kw):
    """SQLite 上没有 BIGINT 自增语义, 编译成 INTEGER 才能 AUTOINCREMENT。"""
    return "INTEGER"


@pytest.fixture()
def db_session():
    """一个独立的内存数据库会话(每次测试全新)。"""
    import app.models  # noqa: F401  确保所有模型都注册到 Base.metadata
    from app.core.database import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
    )

    # 打开外键约束, 让级联删除的行为与 MySQL 一致
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded(db_session):
    """建好权限/角色/管理员的最小数据集, 返回 (admin_user, author_user, 明文密码)。"""
    from app.core.permissions import Perm
    from app.core.security import hash_password
    from app.models.user import Permission, Role, User

    password = "TestPassw0rd!"
    perms = {}
    for code in (
        Perm.POST_CREATE,
        Perm.POST_EDIT,
        Perm.POST_PUBLISH,
        Perm.POST_DELETE,
        Perm.POST_MANAGE,
        Perm.COMMENT_MANAGE,
        Perm.MEDIA_MANAGE,
        Perm.SETTING_MANAGE,
        Perm.DIARY_MANAGE,
        Perm.CHANGELOG_MANAGE,
        Perm.STATS_VIEW,
        Perm.LOG_VIEW,
    ):
        perm = Permission(name=code, code=code)
        db_session.add(perm)
        perms[code] = perm
    db_session.flush()

    admin_role = Role(name="管理员", code="admin")
    admin_role.permissions = list(perms.values())
    author_role = Role(name="作者", code="author")
    author_role.permissions = [perms[Perm.POST_CREATE], perms[Perm.POST_EDIT]]
    db_session.add_all([admin_role, author_role])
    db_session.flush()

    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password(password),
        nickname="管理员",
    )
    admin.roles = [admin_role]
    author = User(
        username="author",
        email="author@example.com",
        password_hash=hash_password(password),
        nickname="作者",
    )
    author.roles = [author_role]
    db_session.add_all([admin, author])
    db_session.commit()

    return admin, author, password
