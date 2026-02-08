from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ContactSubmission(Base):
    __tablename__ = "contact_submission"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    submission_type: Mapped[str] = mapped_column(String(50), default="feedback")  # feedback, grievance
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)

    user: Mapped[Optional["User"]] = relationship("User", backref="contact_submissions")
