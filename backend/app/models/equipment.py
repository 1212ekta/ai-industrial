"""Equipment model — denormalized registry for quick lookups (source of truth: Neo4j)."""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    tag: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    equipment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_inspection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    compliance_standard: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
