from sqlalchemy.orm import Session
from app.models.ticket import TicketAnalysis
from app.schemas.ticket import TicketAnalysisResult

def save_analysis(db: Session, *, customer_id: int | None, query: str, result: TicketAnalysisResult,
                  prompt_version: str, model_name: str, provider: str, duration_ms: float,
                  input_tokens: int | None, output_tokens: int | None) -> TicketAnalysis:
    row = TicketAnalysis(
        customer_id=customer_id, query=query, category=result.category.value,
        sentiment=result.sentiment.value, priority=result.priority.value, summary=result.summary,
        extracted_entities=result.extractedEntities.model_dump(), suggested_response=result.suggestedResponse,
        prompt_version=prompt_version, model_name=model_name, provider=provider, duration_ms=duration_ms,
        input_tokens=input_tokens, output_tokens=output_tokens,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get_analysis(db: Session, ticket_id: int) -> TicketAnalysis | None:
    return db.get(TicketAnalysis, ticket_id)
