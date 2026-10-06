"""模块相关的 FastAPI 依赖"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.state import effective_enabled


def require_module(module_id: str) -> Callable:
    """模块依赖工厂: 模块未启用时接口按"不存在"处理

    为什么用依赖而不是"启动时只装配启用的模块":
      - 后台把模块关掉后要立刻生效, 不能要求重启服务;
      - 挂在 include_router 上, 一条依赖覆盖该模块的全部路由, 不必逐个接口加判断;
      - 返回 404 而不是 403: 能力整体不存在, 语义上就是"没有这个接口"

    get_db 与路由自身的 Depends(get_db) 由 FastAPI 缓存为同一个会话, 不会多开连接

    @param module_id: 模块 id
    @return 可直接传给 include_router 的依赖函数
    """

    def checker(db: Session = Depends(get_db)) -> None:
        if not effective_enabled(db, module_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"模块未启用: {module_id}"
            )

    return checker
