"""清理过期数据。

清理三类:
  1. visit_logs       —— 访问明细, 超过 PHXXBLOG_DATA_RETENTION_DAYS(默认 180 天)
  2. refresh_tokens   —— 已吊销或已过期的令牌记录(与保留天数无关, 只看状态/有效期)
  3. operation_logs   —— 操作日志, 超过 PHXXBLOG_AUDIT_LOG_RETENTION_DAYS(默认 365 天)

影响说明(执行前请确认能接受):
  - 趋势图读的是 daily_stats(按日聚合, **永久保留**), 因此清理明细不影响趋势曲线。
  - 但 `/stats/visits`(访问明细列表)与 `/stats/sources`(来源/浏览器/设备分布)
    读的是 visit_logs, 清理后它们只反映最近 N 天。
  - 清理后表中数据量稳定, `/stats/sources` 的 GROUP BY 全表扫描不会随年限变慢。

用法:
  python scripts/cleanup_old_data.py            # 只统计将删除多少(dry-run)
  python scripts/cleanup_old_data.py --apply    # 实际删除

建议: 每月跑一次(Windows 计划任务 / Linux cron 均可), 例如
  0 4 1 * *  cd /path/to/backend && .venv/bin/python scripts/cleanup_old_data.py --apply
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.analytics import VisitLog  # noqa: E402
from app.models.log import OperationLog  # noqa: E402

APPLY = "--apply" in sys.argv

retention = settings.data_retention_days
audit_retention = settings.audit_log_retention_days
visit_cutoff = datetime.now() - timedelta(days=retention)
log_cutoff = datetime.now() - timedelta(days=audit_retention)
now = datetime.now()

print(f"  模式: {'实际删除' if APPLY else '预览(dry-run, 加 --apply 才删除)'}")
print(f"  访问明细保留: {retention} 天 (早于 {visit_cutoff:%Y-%m-%d %H:%M} 的记录)")
print(f"  操作日志保留: {audit_retention} 天 (早于 {log_cutoff:%Y-%m-%d %H:%M} 的记录)")
print()

with SessionLocal() as db:
    # ---- 1. 访问明细 ----
    visit_q = db.query(VisitLog).filter(VisitLog.visit_time < visit_cutoff)
    visit_count = visit_q.count()
    total_visits = db.query(VisitLog).count()

    # ---- 2. 刷新令牌(已吊销 或 已过期) ----
    from sqlalchemy import or_

    from app.models.user import refresh_tokens

    token_q = db.query(refresh_tokens).filter(
        or_(
            refresh_tokens.c.revoked == True,  # noqa: E712
            refresh_tokens.c.expires_at < now,
        )
    )
    token_count = token_q.count()
    total_tokens = db.query(refresh_tokens).count()

    # ---- 3. 操作日志 ----
    log_q = db.query(OperationLog).filter(OperationLog.created_at < log_cutoff)
    log_count = log_q.count()
    total_logs = db.query(OperationLog).count()

    print(f"  visit_logs      : 共 {total_visits:>6} 条, 将删除 {visit_count:>6} 条")
    print(
        f"  refresh_tokens  : 共 {total_tokens:>6} 条, 将删除 {token_count:>6} 条 (已吊销/已过期)"
    )
    print(f"  operation_logs  : 共 {total_logs:>6} 条, 将删除 {log_count:>6} 条")

    if APPLY:
        deleted_visits = visit_q.delete(synchronize_session=False)
        deleted_tokens = token_q.delete(synchronize_session=False)
        deleted_logs = log_q.delete(synchronize_session=False)
        db.commit()
        print()
        print(
            f"  已删除: visit_logs {deleted_visits}, refresh_tokens {deleted_tokens}, operation_logs {deleted_logs}"
        )
    else:
        print()
        if visit_count or token_count or log_count:
            print("  确认无误后执行: python scripts/cleanup_old_data.py --apply")
        else:
            print("  无需清理")

        # 顺带给出保留策略生效后的预估影响
        if visit_count:
            remaining = total_visits - visit_count
            print()
            print(f"  清理后 visit_logs 剩约 {remaining} 条;")
            print("  /stats/sources 的分布将只反映保留期内的数据(趋势图不受影响)。")
