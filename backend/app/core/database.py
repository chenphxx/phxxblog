"""数据库连接与会话管理。

关于表结构演进(重要):
    本项目**没有引入 Alembic** —— 对单实例个人博客是过度设计。约定如下:

      1. 新表: 由 Base.metadata.create_all() 在启动时自动创建, 无需干预。
      2. 已有表加列: 目前**不会自动补**, 必须手工写迁移 SQL 放到
         backend/scripts/ 下按日期命名, 并在自己的环境执行。
      3. 检测: 启动时会调用 check_schema(), 如果模型里定义了某个列而库里没有,
         直接报错拒绝启动, 并打印出需要执行的 ALTER 语句 —— 宁可启动失败,
         也不要等到某个查询才炸 "Unknown column"。
      4. 版本记录: schema_version 表记录已应用的迁移文件名, 便于判断某个库
         停在哪个版本。

    将来若需要多环境部署(本地 + 服务器 + CI), 再迁移到 Alembic。
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖: 提供数据库会话, 请求结束后关闭。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_version_table() -> None:
    """建立 schema_version 表(记录已应用的迁移文件名)。"""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version     VARCHAR(120) NOT NULL PRIMARY KEY,
                    applied_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4
                """
            )
        )


def applied_versions() -> set[str]:
    """读取已记录的迁移版本。"""
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT version FROM schema_version")).fetchall()
        return {row[0] for row in rows}
    except Exception:
        # 表还不存在(首次启动)时视作空
        return set()


def record_version(version: str) -> None:
    """记录一个已应用的迁移版本(幂等)。"""
    with engine.begin() as conn:
        conn.execute(
            text("INSERT IGNORE INTO schema_version (version) VALUES (:v)"),
            {"v": version},
        )


def missing_columns() -> list[tuple[str, str, str]]:
    """返回「模型里有、数据库里没有」的列: [(表, 列, 类型提示)]。"""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing: list[tuple[str, str, str]] = []

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # 新表交给 create_all
        db_columns = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name not in db_columns:
                type_hint = column.type.compile(engine.dialect)
                missing.append((table.name, column.name, type_hint))
    return missing


def check_schema(strict: bool = True) -> list[tuple[str, str, str]]:
    """启动时校验表结构; 有缺失列则报错(或仅告警)。

    Args:
        strict: True 时直接抛 RuntimeError; False 时只打印告警。

    Returns:
        缺失列清单。
    """
    missing = missing_columns()
    if not missing:
        return []

    lines = [
        "数据库表结构与模型不一致, 缺少以下列:",
        *[f"    {table}.{column}  ({type_hint})" for table, column, type_hint in missing],
        "",
        "本项目不自动改表结构, 请手工执行对应的 ALTER 语句, 例如:",
        *[
            f"    ALTER TABLE {table} ADD COLUMN {column} {type_hint};"
            for table, column, type_hint in missing
        ],
        "",
        "执行完成后把迁移文件放到 backend/scripts/ 下, 并在 schema_version 表里登记。",
    ]
    message = "\n".join(lines)

    if strict:
        raise RuntimeError(message)
    print("[schema] " + message)
    return missing
