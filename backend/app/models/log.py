"""操作日志模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OperationLog(Base):
    """操作日志: 记录谁在什么时候改了什么。"""

    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("idx_user", "user_id"),
        Index("idx_module", "module"),
        Index("idx_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    user: Mapped["User | None"] = relationship("User", lazy="joined")
