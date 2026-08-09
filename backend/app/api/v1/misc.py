"""杂项接口: 更新日志等。"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
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
