"""杂项接口: 更新日志等。"""
import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import requests
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.setting import Setting
from app.models.user import User

router = APIRouter(prefix="/misc", tags=["其他"])


class ChangelogIn(BaseModel):
    """更新日志内容。"""

    content: str = Field(min_length=1, max_length=200000)


@router.get("/changelog", response_model=dict)
def changelog(
    user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
):
    """更新日志内容(仅管理员, 内容同 CHANGELOG.md)。"""
    if "admin" not in user.role_codes:
        raise HTTPException(status_code=403, detail="仅管理员可查看")
    path = PROJECT_ROOT / "CHANGELOG.md"
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    return ok({"content": content})


@router.put("/changelog", response_model=dict)
def update_changelog(
    data: ChangelogIn,
    user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
):
    """保存更新日志(仅管理员, 写回 CHANGELOG.md)。"""
    if "admin" not in user.role_codes:
        raise HTTPException(status_code=403, detail="仅管理员可编辑")
    path = PROJECT_ROOT / "CHANGELOG.md"
    path.write_text(data.content, encoding="utf-8")
    return ok(message="更新日志已保存")


# 一言缓存存在 settings 表里: 同一天内所有访客共用一条, 每天只真正请求一次外部接口
SAYING_CACHE_KEY = "saying_cache"


def _read_saying_cache(db: Session) -> dict:
    """读取一言缓存(格式: {"date": "YYYY-MM-DD", "text": "..."}), 解析失败返回空。"""
    row = db.get(Setting, SAYING_CACHE_KEY)
    if not row:
        return {}
    try:
        data = json.loads(row.setting_value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


@router.get("/saying", response_model=dict)
def saying(force: bool = False, db: Session = Depends(get_db)):
    """一言(随机语录): 代理 uapis.cn 接口, 避免前端跨域。

    默认每天只刷新一次(结果缓存在 settings 表), 前端手动点"换一句"时传 force=true 强制刷新。
    """
    today = date.today().isoformat()
    cache = _read_saying_cache(db)
    if not force and cache.get("date") == today and cache.get("text"):
        return ok({"text": cache["text"], "cached": True})
    try:
        resp = requests.get("https://uapis.cn/api/v1/saying", timeout=10)
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
        db.add(Setting(setting_key=SAYING_CACHE_KEY, setting_value=value, description="一言每日缓存(自动维护)"))
    db.commit()
    return ok({"text": text, "cached": False})


@router.get("/history/programmer-today", response_model=dict)
def programmer_history_today():
    """程序员历史上的今天(公开): 代理 uapis.cn 接口, 避免前端跨域。"""
    try:
        resp = requests.get("https://uapis.cn/api/v1/history/programmer/today", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return ok({
            "date": data.get("date") or "",
            "events": data.get("events") or [],
        })
    except Exception:
        return ok({"date": "", "events": []})
