"""文章、分类、标签模型。"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# 文章-标签关联表
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    """文章分类, 支持父子层级。"""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", lazy="selectin"
    )


class Tag(Base):
    """文章标签。"""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)


class Post(Base):
    """文章表, 状态: 0草稿 1审核中 2已发布 3私密 4回收站。"""

    __tablename__ = "posts"
    __table_args__ = (
        Index("idx_status_published", "status", "published_at"),
        Index("idx_category", "category_id"),
        Index("idx_author", "author_id"),
        # 全文索引(ngram 分词器, 支持中文搜索)
        Index(
            "ft_post", "title", "summary", "content_md",
            mysql_prefix="FULLTEXT", mysql_with_parser="ngram",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # 关系
    author: Mapped["User"] = relationship("User", back_populates="posts", lazy="joined")
    category: Mapped[Category | None] = relationship(lazy="joined")
    tags: Mapped[list[Tag]] = relationship(secondary=post_tags, lazy="selectin")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", lazy="selectin"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", lazy="selectin"
    )


class PostLike(Base):
    """文章点赞表: 同一用户或同一 IP 对同一文章只能点赞一次。"""

    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uk_post_user"),
        UniqueConstraint("post_id", "ip", name="uk_post_ip"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    post: Mapped[Post] = relationship(back_populates="likes")
