from sqlalchemy import String, Integer, DateTime, Text, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from datetime import datetime

class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("url", name="uq_articles_url"), )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(256))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # optional fields
    subtitle: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    image_url: Mapped[str | None] = mapped_column(String(512))
    word_count: Mapped[int | None] = mapped_column(Integer)
    reading_time: Mapped[str | None] = mapped_column(String(32))
    related_articles: Mapped[list[str] | None] = mapped_column(JSON)
