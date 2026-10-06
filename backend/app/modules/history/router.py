"""程序员历史上的今天: 代理第三方接口, 避免前端跨域

接口地址是模块配置(见 app/modules/history/spec.py), 换个数据源不用改代码
"""

import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.modules.registry import registry
from app.modules.state import module_config

router = APIRouter(prefix="/misc", tags=["历史上的今天"])

# 上游接口地址的缺省值: 模块配置(module.history.api_url)优先, 没配置时用它
DEFAULT_API_URL = "https://uapis.cn/api/v1/history/programmer/today"


@router.get("/history/programmer-today", response_model=dict)
def programmer_history_today(db: Session = Depends(get_db)):
    """程序员历史上的今天(公开)"""
    spec = registry.get("history")
    configured = module_config(db, spec).get("api_url") if spec else None
    api_url = str(configured or DEFAULT_API_URL).strip()
    if not api_url:
        return ok({"date": "", "events": []})
    try:
        resp = requests.get(api_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return ok(
            {
                "date": data.get("date") or "",
                "events": data.get("events") or [],
            }
        )
    except Exception:
        return ok({"date": "", "events": []})
