"""访问统计模型: 明细与按日聚合。"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VisitLog(Base):
    """访问明细表, 用于 PV/UV/来源/浏览器/IP 分析。"""

    __tablename__ = "visit_logs"
    __table_args__ = (
        Index("idx_visit_time", "visit_time"),
        Index("idx_post", "post_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device: Mapped[str | None] = mapped_column(String(20), nullable=True)
    visit_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    post: Mapped["Post | None"] = relationship("Post", lazy="joined")


class DailyStat(Base):
    """按日聚合统计表。"""

    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stat_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    pv: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uv: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    post_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
