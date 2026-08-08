"""评论模型(游客/注册用户, 支持回复)。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Comment(Base):
    """评论表, 状态: 1正常 0隐藏 2回收站。"""

    __tablename__ = "comments"
    __table_args__ = (
        Index("idx_post_status", "post_id", "status"),
        Index("idx_parent", "parent_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    # 关系
    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    user: Mapped["User | None"] = relationship("User", lazy="joined")
    parent: Mapped["Comment | None"] = relationship(
        remote_side="Comment.id", back_populates="replies", lazy="joined"
    )
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent", lazy="selectin"
    )
