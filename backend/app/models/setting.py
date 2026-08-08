"""系统设置模型。"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Setting(Base):
    """键值对形式的系统设置。"""

    __tablename__ = "settings"

    setting_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    setting_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
