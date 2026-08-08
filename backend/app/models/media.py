"""媒体/附件模型(图片、视频、文件)。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Media(Base):
    """媒体表, 文件实际存储在 assets/ 目录。"""

    __tablename__ = "media"
    __table_args__ = (Index("idx_related", "related_type", "related_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uploader_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # image/video/file
    related_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    related_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    uploader: Mapped["User | None"] = relationship("User", lazy="joined")
