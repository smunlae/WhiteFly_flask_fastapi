from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    framework: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    honeypot_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    fp_visitor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fp_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fp_confidence_score: Mapped[float| None] = mapped_column(Float, nullable=True)
    fp_is_suspect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fp_verification_error: Mapped[str | None] = mapped_column(Text, nullable=True)
