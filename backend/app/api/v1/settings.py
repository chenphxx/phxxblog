"""系统设置接口。"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.core.settings_schema import BOOL_KEYS, DEFAULTS, PUBLIC_KEYS
from app.models.setting import Setting
from app.models.user import User
from app.services.log import write_operation_log

router = APIRouter(prefix="/settings", tags=["设置"])


@router.get("/public", response_model=dict)
def public_settings(db: Session = Depends(get_db)):
    """前台公开配置(首页展示用)。"""
    rows = db.query(Setting).filter(Setting.setting_key.in_(PUBLIC_KEYS)).all()
    data = {row.setting_key: row.setting_value for row in rows}
    result = {key: data.get(key, DEFAULTS.get(key, "")) for key in PUBLIC_KEYS}
    # 对列表型字段尝试 JSON 解析
    import json

    for key in ("tech_tags", "social_links", "website_links", "beian_info"):
        raw = result.get(key, "")
        if isinstance(raw, str):
            try:
                result[key] = json.loads(raw)
            except json.JSONDecodeError:
                result[key] = [item.strip() for item in raw.split(",") if item.strip()]
    # 布尔开关统一转成 true/false, 前端直接当布尔值使用
    for key in BOOL_KEYS:
        result[key] = str(result.get(key, "")).strip().lower() in ("1", "true", "yes", "on")
    return ok(result)


@router.get("", response_model=dict)
def admin_settings(
    _: User = Depends(require_permission(Perm.SETTING_MANAGE)),
    db: Session = Depends(get_db),
):
    """后台全部设置。"""
    rows = db.query(Setting).order_by(Setting.setting_key).all()
    return ok({row.setting_key: row.setting_value for row in rows})


@router.put("", response_model=dict)
def update_settings(
    data: dict,
    request: Request,
    admin: User = Depends(require_permission(Perm.SETTING_MANAGE)),
    db: Session = Depends(get_db),
):
    """批量更新设置(键值对)。"""
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            import json

            value = json.dumps(value, ensure_ascii=False)
        row = db.get(Setting, key)
        if row:
            row.setting_value = str(value)
        else:
            db.add(Setting(setting_key=key, setting_value=str(value)))
    db.commit()
    write_operation_log(
        db, request=request, user=admin, module="setting", action="update",
        detail={"keys": list(data.keys())},
    )
    return ok(message="设置已保存")
