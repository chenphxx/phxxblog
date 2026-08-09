"""杂项接口: 更新日志等。"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import requests
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
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


@router.get("/saying", response_model=dict)
def saying():
    """一言(随机语录): 代理 uapis.cn 接口, 避免前端跨域。"""
    try:
        resp = requests.get("https://uapis.cn/api/v1/saying", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return ok({"text": (data.get("text") or "").strip()})
    except Exception:
        return ok({"text": ""})


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


@router.get("/tracking/query", response_model=dict)
def tracking_query(
    tracking_number: str = Query(..., min_length=1, max_length=64, description="快递单号"),
    carrier_code: str | None = Query(None, description="快递公司编码(可选, 不填自动识别)"),
    phone: str | None = Query(None, description="收件人手机号后四位(部分快递公司必填)"),
    refresh: bool | None = Query(None, description="是否强制刷新物流信息"),
    user: User = Depends(get_current_user),
):
    """快递物流查询(仅管理员): 代理 uapis.cn 接口, 避免前端跨域。"""
    if "admin" not in user.role_codes:
        raise HTTPException(status_code=403, detail="仅管理员可查询物流")
    params: dict[str, str] = {"tracking_number": tracking_number}
    if carrier_code:
        params["carrier_code"] = carrier_code
    if phone:
        params["phone"] = phone
    if refresh is not None:
        params["refresh"] = "true" if refresh else "false"
    try:
        resp = requests.get(
            "https://uapis.cn/api/v1/misc/tracking/query",
            params=params,
            timeout=30,
        )
        try:
            data = resp.json()
        except Exception:
            raise HTTPException(status_code=502, detail="物流查询服务返回异常, 请稍后重试")
        if resp.status_code != 200:
            message = (data or {}).get("message") or "物流查询失败, 请稍后重试"
            raise HTTPException(status_code=resp.status_code, detail=message)
        return ok(data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="物流查询服务暂不可用, 请稍后重试")
