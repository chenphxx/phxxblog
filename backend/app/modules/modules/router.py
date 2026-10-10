"""模块管理接口

公开接口只暴露"启用了哪些模块"与模块公开配置, 供前台决定注册哪些路由与导航;
后台接口提供完整的模块清单(状态/依赖/权限/配置项)与批量更新
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user, is_site_manager, require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.models.user import User
from app.modules.base import CATEGORIES, VISIBILITIES
from app.modules.registry import registry
from app.modules.state import (
    admin_state,
    disabled_dependencies,
    public_state,
    set_enabled,
    set_module_config,
    set_visibility,
)
from app.services.log import write_operation_log

router = APIRouter(prefix="/modules", tags=["模块管理"])


class ModuleUpdate(BaseModel):
    """单个模块的更新内容(两者都可省略, 只改传了的字段)"""

    enabled: bool | None = None
    visibility: str | None = Field(default=None, description="可见范围: public / admin")
    settings: dict[str, object] | None = Field(default=None, description="模块配置键值对")


class ModuleUpdateIn(BaseModel):
    """批量更新请求体: { modules: { <模块 id>: { enabled, settings } } }"""

    modules: dict[str, ModuleUpdate]


@router.get("", response_model=dict)
def public_modules(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """前台公开的模块状态(当前访问者可见的模块 + 公开配置)"""
    return ok(public_state(db, is_admin=is_site_manager(user)))


@router.get("/admin", response_model=dict)
def admin_modules(
    _: User = Depends(require_permission(Perm.SETTING_MANAGE)),
    db: Session = Depends(get_db),
):
    """后台模块清单: 元数据 + 启用状态 + 依赖状态 + 配置项"""
    return ok({"modules": admin_state(db), "categories": CATEGORIES, "visibilities": VISIBILITIES})


@router.put("/admin", response_model=dict)
def update_modules(
    data: ModuleUpdateIn,
    request: Request,
    admin: User = Depends(require_permission(Perm.SETTING_MANAGE)),
    db: Session = Depends(get_db),
):
    """批量启用/禁用模块并保存模块配置

    依赖不在这里级联写入: 被依赖的模块被禁用后, 依赖它的模块由 effective_enabled
    判定为不可用(接口 404, 前台不注册), 重新启用依赖后自动恢复, 不需要回滚状态
    """
    changed: list[dict] = []
    try:
        for module_id, patch in data.modules.items():
            spec = registry.get(module_id)
            if spec is None:
                raise ValueError(f"模块不存在: {module_id}")
            if patch.enabled is not None:
                set_enabled(db, module_id, patch.enabled)
                changed.append({"module": module_id, "enabled": patch.enabled})
                if patch.enabled:
                    # 启用时顺手校验依赖, 免得"启用了却仍然不可用"让人困惑
                    missing = disabled_dependencies(db, spec)
                    if missing:
                        raise ValueError(f"{spec.name} 依赖的模块未启用: {', '.join(missing)}")
            if patch.visibility is not None:
                set_visibility(db, module_id, patch.visibility)
                changed.append({"module": module_id, "visibility": patch.visibility})
            if patch.settings is not None:
                set_module_config(db, spec, patch.settings)
                changed.append({"module": module_id, "settings": sorted(patch.settings)})
        db.commit()
    except ValueError as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err)) from err

    write_operation_log(
        db,
        request=request,
        user=admin,
        module="module",
        action="update",
        detail={"changes": changed},
    )
    return ok({"modules": admin_state(db)}, message="模块配置已保存")
