"""系统设置接口"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import Perm
from app.core.response import ok
from app.core.settings_schema import (
    BOOL_KEYS,
    DEFAULTS,
    MAX_UPLOAD_SIZE_MB,
    MIN_UPLOAD_SIZE_MB,
    PUBLIC_KEYS,
    UPLOAD_SIZE_KEY,
    format_upload_size_mb,
    parse_upload_size_mb,
)
from app.models.setting import Setting
from app.models.user import User
from app.services.log import write_operation_log

router = APIRouter(prefix="/settings", tags=["设置"])


@router.get("/public", response_model=dict)
def public_settings(db: Session = Depends(get_db)):
    """前台公开配置(首页展示用)"""
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
    """后台全部设置"""
    rows = db.query(Setting).order_by(Setting.setting_key).all()
    data = {row.setting_key: row.setting_value for row in rows}
    # 后台专用键没有 seed 默认值, 库里缺行时补上当前生效值, 免得表单显示成
    # 前端写死的数字, 一保存就把环境变量配置覆盖掉
    if UPLOAD_SIZE_KEY not in data:
        data[UPLOAD_SIZE_KEY] = str(format_upload_size_mb(settings.max_upload_size))
    return ok(data)


@router.put("", response_model=dict)
def update_settings(
    data: dict,
    request: Request,
    admin: User = Depends(require_permission(Perm.SETTING_MANAGE)),
    db: Session = Depends(get_db),
):
    """批量更新设置(键值对)"""
    for key, value in data.items():
        if key == UPLOAD_SIZE_KEY and parse_upload_size_mb(value) is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"单文件上传上限必须是 {MIN_UPLOAD_SIZE_MB} ~ {MAX_UPLOAD_SIZE_MB} "
                    "之间的整数(MB)"
                ),
            )
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
        db,
        request=request,
        user=admin,
        module="setting",
        action="update",
        detail={"keys": list(data.keys())},
    )
    return ok(message="设置已保存")
