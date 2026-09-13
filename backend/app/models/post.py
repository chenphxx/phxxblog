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
from app.services.text import count_words, reading_minutes


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
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
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
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)


class Post(Base):
    """文章表, 状态: 0草稿 1审核中 2已发布 3私密 4回收站。"""

    __tablename__ = "posts"
    __table_args__ = (
        Index("idx_status_published", "status", "published_at"),
        Index("idx_category", "category_id"),
        Index("idx_author", "author_id"),
        # 这里原先还有一个 FULLTEXT + ngram 的 ft_post 索引, 已移除。
        #
        # 移除原因(实测, 不是推测):
        #   搜索实现走的是 `LIKE '%kw%'`(见 api/v1/posts.py 与 search.py), 前导 % 使
        #   B-Tree/FULLTEXT 索引都无法命中, 所以这个索引一直只是写入开销。
        #   那为什么不用 MATCH ... AGAINST 把它利用起来? 因为实测 ngram 分词器在
        #   本项目的关键词上表现更差:
        #       "网盘"  LIKE 2 命中 / MATCH 2 命中
        #       "Git"   LIKE 4 命中 / MATCH 0 命中   ← 短英文词不在 ngram 词表里
        #       "的"     LIKE 14 命中 / MATCH 0 命中  ← 单字不满足 ngram 最小词长
        #   改为 MATCH 反而会让搜索退化, 因此保留 LIKE, 删掉索引。
        #
        # 如何恢复: 如果将来文章量很大且需要全文检索, 删掉上面这条注释并执行
        #   ALTER TABLE posts ADD FULLTEXT INDEX ft_post (title, summary, content_md) WITH PARSER ngram;
        # 同时把查询改成 MATCH(...) AGAINST(... IN BOOLEAN MODE), 并接受短词/单字
        # 无法命中的限制(或改用专门的中文分词方案)。
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
    #
    # lazy 策略说明(改动前请先读):
    #   author / category -> joined:  列表与详情都要显示, 一次 JOIN 取回最省。
    #   tags              -> selectin: PostListItem 要序列化标签, 必须预加载。
    #   comments / likes  -> raise:   列表与详情接口都**不**使用这两个关系
    #                     (评论走 Comment 表独立查询, 点赞数读 Post.likes_count 字段),
    #                     以前是 selectin, 导致每列 10 篇文章都要多查一次
    #                     全量评论行与点赞行 —— 纯浪费。
    #                     用 raise 而不是 select: 一旦有人真的误用会立刻报错,
    #                     而不是悄悄退化成 N+1。真需要时用 selectinload() 显式加载。
    author: Mapped["User"] = relationship("User", back_populates="posts", lazy="joined")
    category: Mapped[Category | None] = relationship(lazy="joined")
    tags: Mapped[list[Tag]] = relationship(secondary=post_tags, lazy="selectin")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", lazy="raise"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", lazy="raise"
    )

    @property
    def word_count(self) -> int:
        """正文字数(用于列表/详情展示)。"""
        return count_words(self.content_md)

    @property
    def reading_minutes(self) -> int:
        """预计阅读时间(分钟)。"""
        return reading_minutes(self.word_count)


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
