"""QueryLog model — records Copilot / RCA / search queries for history and the dashboard."""
import json
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    query_type: Mapped[str] = mapped_column(String(20), nullable=False)  # copilot|rca|search
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_document_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def set_source_ids(self, ids: list[str]) -> None:
        self.source_document_ids = json.dumps(ids)

    def get_source_ids(self) -> list[str]:
        return json.loads(self.source_document_ids) if self.source_document_ids else []
