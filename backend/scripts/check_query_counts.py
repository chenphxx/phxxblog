"""量化统计关键接口的 SQL 条数(用于验证关联加载策略)。

跑法: backend/.venv/Scripts/python.exe scripts/check_query_counts.py
只读, 不写数据库。
"""
import logging
import sys
from pathlib import Path

# 关掉 SQLAlchemy 的 echo 日志(由 settings.debug 打开), 只保留统计输出
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import event  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.models.post import Post  # noqa: E402
from app.schemas.post import PostListItem  # noqa: E402

counters = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count(conn, cursor, statement, parameters, context, executemany):
    counters["n"] += 1


def run(label, fn):
    counters["n"] = 0
    try:
        result = fn()
    except Exception as e:  # noqa: BLE001
        print(f"  {label:<46} 异常: {type(e).__name__}: {e}")
        return None
    print(f"  {label:<46} {counters['n']:>3} 条 SQL   -> {result}")
    return counters["n"]


def scenario_auth(db: Session):
    """模拟 get_current_user: db.get(User) + 权限码聚合(每个鉴权接口都会走)。"""
    from app.models.user import User

    user = db.get(User, 1)
    if user is None:
        return "无 id=1 的用户"
    codes = user.permission_codes
    return f"user={user.username}, 权限 {len(codes)} 个"


def scenario_list(db: Session):
    """模拟 GET /api/v1/posts: 列 10 篇已发布文章并序列化。"""
    posts = (
        db.query(Post)
        .filter(Post.status == 2)
        .order_by(Post.published_at.desc())
        .limit(10)
        .all()
    )
    for p in posts:
        PostListItem.model_validate(p)
    return f"{len(posts)} 篇"


def scenario_admin_page(db: Session):
    """模拟典型后台页面: 鉴权 + 列 10 篇(含草稿)。"""
    from app.models.user import User

    user = db.get(User, 1)
    if user is None:
        return "无 id=1 的用户"
    _ = user.permission_codes
    posts = db.query(Post).order_by(Post.id.desc()).limit(10).all()
    for p in posts:
        PostListItem.model_validate(p)
    return f"{len(posts)} 篇"


print("=" * 74)
print("SQL 条数统计(只读)")
print("=" * 74)
with SessionLocal() as db:
    run("A. 鉴权: db.get(User) + permission_codes", lambda: scenario_auth(db))
    run("B. 公开列表: 取 10 篇文章 + 序列化", lambda: scenario_list(db))
    run("C. 后台页: 鉴权 + 列 10 篇 + 序列化", lambda: scenario_admin_page(db))

print()
print("参考: 改动前的基线(子代理实测, 未改 lazy 之前)")
print("  A. 鉴权                                                     9 条")
print("  B. 公开列表 10 篇                                            9 条")
print("  C. 后台页(鉴权 + 列 10 篇)                                 15 条")
print()
print("说明: B 的剩余条数 = 1(文章) + 1(tags) + 2(角色/权限, 来自 author->roles)。")

