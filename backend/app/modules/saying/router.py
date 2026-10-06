"""一言接口: 代理第三方接口, 避免前端跨域

接口地址与"每天只刷一次"的开关都是模块配置(见 app/modules/saying/spec.py),
换一个语录源不需要改代码
"""

import json
from datetime import date

import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.models.setting import Setting
from app.modules.registry import registry
from app.modules.state import module_config

router = APIRouter(prefix="/misc", tags=["一言"])

# 上游接口地址的缺省值: 模块配置(module.saying.api_url)优先, 没配置时用它
DEFAULT_API_URL = "https://uapis.cn/api/v1/saying"

# 一言缓存存在 settings 表里: 同一天内所有访客共用一条, 每天只真正请求一次外部接口
SAYING_CACHE_KEY = "saying_cache"


def _read_cache(db: Session) -> dict:
    """读取一言缓存(格式: {"date": "YYYY-MM-DD", "text": "..."}), 解析失败返回空

    @param db: 数据库会话
    @return 缓存字典
    """
    row = db.get(Setting, SAYING_CACHE_KEY)
    if not row:
        return {}
    try:
        data = json.loads(row.setting_value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _config(db: Session) -> dict:
    """取一言模块的配置

    @param db: 数据库会话
    @return 配置字典(api_url / daily_cache)
    """
    spec = registry.get("saying")
    return module_config(db, spec) if spec else {}


@router.get("/saying", response_model=dict)
def saying(force: bool = False, db: Session = Depends(get_db)):
    """一言(随机语录)

    默认每天只刷新一次(结果缓存在 settings 表), 前端手动点"换一句"时传 force=true
    强制刷新; 关闭每日缓存后每次请求都会真正调用上游接口
    """
    config = _config(db)
    api_url = str(config.get("api_url") or DEFAULT_API_URL).strip()
    daily_cache = bool(config.get("daily_cache", True))
    cache = _read_cache(db)
    today = date.today().isoformat()

    if not api_url:
        return ok({"text": cache.get("text", ""), "cached": bool(cache.get("text"))})
    if daily_cache and not force and cache.get("date") == today and cache.get("text"):
        return ok({"text": cache["text"], "cached": True})
    try:
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("text") or "").strip()
    except Exception:
        text = ""
    if not text:
        # 拉取失败时退回旧缓存(可能不是今天的), 避免页面空白
        return ok({"text": cache.get("text", ""), "cached": bool(cache.get("text"))})
    row = db.get(Setting, SAYING_CACHE_KEY)
    value = json.dumps({"date": today, "text": text}, ensure_ascii=False)
    if row:
        row.setting_value = value
    else:
        db.add(
            Setting(
                setting_key=SAYING_CACHE_KEY,
                setting_value=value,
                description="一言每日缓存(自动维护)",
            )
        )
    db.commit()
    return ok({"text": text, "cached": False})
