from database import get_session, Base
from datetime import datetime, timezone
from sqlalchemy import Text, String, INTEGER, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(primary_key=True)
    email:Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password:Mapped[str] = mapped_column(String(255), nullable=False)
    created_at:Mapped[datetime] = mapped_column(server_default=func.now(timezone.utc))
    tier:Mapped[str] = mapped_column(String(255), nullable=False)

    articles:Mapped[list["Article"]] = relationship(back_populates="user_id")

class Article(Base):
    __tablename__ = "articles"

    id:Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str] = mapped_column(String(255), nullable=False)
    body:Mapped[str] = mapped_column(Text, nullable=False)
    reading_time:Mapped[int|None] = mapped_column(default=None)
    created_at:Mapped[datetime] = mapped_column(server_default=func.now(timezone.utc))

    user_id:Mapped[int] = mapped_column(ForeignKey("user_id"))

    author:Mapped["User"] = relationship(back_populates="articles")