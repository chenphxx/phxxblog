"""杂项接口: 更新日志(仅管理员)"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.user import User
from app.modules.deps import permission_or_module_public

router = APIRouter(prefix="/misc", tags=["其他"])


class ChangelogIn(BaseModel):
    """更新日志内容"""

    content: str = Field(min_length=1, max_length=200000)


@router.get("/changelog", response_model=dict)
def changelog(
    _user: User | None = Depends(permission_or_module_public(Perm.CHANGELOG_MANAGE, "changelog")),
    _db: Session = Depends(get_db),
):
    """更新日志内容(内容同 CHANGELOG.md)

    管理员随时可读; 更新日志模块的可见范围配成公开时, 访客也能读
    """
    path = PROJECT_ROOT / "CHANGELOG.md"
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    return ok({"content": content})


@router.put("/changelog", response_model=dict)
def update_changelog(
    data: ChangelogIn,
    user: User = Depends(require_permission(Perm.CHANGELOG_MANAGE)),
    _db: Session = Depends(get_db),
):
    """保存更新日志(需 changelog:manage 权限, 写回 CHANGELOG.md)"""
    path = PROJECT_ROOT / "CHANGELOG.md"
    path.write_text(data.content, encoding="utf-8")
    return ok(message="更新日志已保存")
