from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class TicketAnalysis(Base):
    __tablename__ = "ticket_analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_entities: Mapped[dict] = mapped_column(JSON, nullable=False)
    suggested_response: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(10), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
