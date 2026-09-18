"""分页辅助。

以前 9 个路由各自手写 `query.count()` + `.offset((page - 1) * page_size).limit(page_size)`
+ 组装 `{items, total, page, page_size}`, 现在统一到这里:

    return ok(paginate(query, page, page_size, DiaryOut))

收益不只是少写几行 —— 分页参数校验、count 与 items 的取数顺序、返回结构都只有一处定义,
将来改协议(比如换成游标分页)不用再翻 9 个文件。
"""

from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar("T")

MAX_PAGE_SIZE = 100


def paginate(
    query: Query,
    page: int,
    page_size: int,
    schema: type[BaseModel] | None = None,
) -> dict[str, Any]:
    """对查询做分页并组装配页结果。

    Args:
        query: 已带好过滤与排序的 SQLAlchemy Query(不要提前 limit)。
        page: 页码, 从 1 开始。
        page_size: 每页条数。
        schema: 传入 Pydantic 模型时, items 会逐条 model_validate; 不传则原样返回 ORM 对象。

    Returns:
        {"items": [...], "total": int, "page": int, "page_size": int}
    """
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    items: list[Any] = [schema.model_validate(row) for row in rows] if schema else rows
    return {"items": items, "total": total, "page": page, "page_size": page_size}
