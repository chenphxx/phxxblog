"""对比 categories / tags 接口的 SQL 条数(验证 n+1 优化)。

只读。用法: backend/.venv/Scripts/python.exe scripts/check_list_query_counts.py
"""
import logging
import sys
from pathlib import Path

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import event  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402

counters = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count(conn, cursor, statement, parameters, context, executemany):
    counters["n"] += 1


def run(label, fn):
    counters["n"] = 0
    result = fn()
    print(f"  {label:<38} {counters['n']:>3} 条 SQL   {result}")


with SessionLocal() as db:
    from app.api.v1.categories import list_categories  # noqa: E402
    from app.api.v1.tags import list_tags  # noqa: E402

    run("GET /categories", lambda: f"{len(list_categories(db=db)['data'])} 个分类")
    run("GET /tags", lambda: f"{len(list_tags(db=db)['data'])} 个标签")

print()
print("  改动前: categories 为 1 + N 条(每个分类一次 COUNT), 6 个分类 = 7 条")
print("  改动后: 固定 2 条(1 次列表 + 1 次 GROUP BY)")
