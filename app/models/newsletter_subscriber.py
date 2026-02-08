from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscriber"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
