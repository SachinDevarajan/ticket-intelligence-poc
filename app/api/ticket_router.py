from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.ticket import (TicketAnalyzeRequest, TicketAnalysisResponse,
                                GenerateResponseRequest, GenerateResponseResult)
from app.repositories.ticket_repository import get_analysis
from app.services.ticket_service import analyse_ticket, generate_draft
from app.services.llm_service import LLMProviderError

router = APIRouter(prefix="/ai/tickets", tags=["Ticket Intelligence"])

@router.post("/analyze", response_model=TicketAnalysisResponse)
def analyze(request: TicketAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        row, result, llm = analyse_ticket(db, request.customerId, request.query, request.prompt_version)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return TicketAnalysisResponse(
        **result.model_dump(), ticket_id=row.id, prompt_version=row.prompt_version,
        model=row.model_name, provider=row.provider, duration_ms=row.duration_ms,
        input_tokens=row.input_tokens, output_tokens=row.output_tokens, created_at=created.isoformat(),
    )

@router.post("/generate-response", response_model=GenerateResponseResult)
def generate_response(request: GenerateResponseRequest):
    try:
        draft = generate_draft(request.ticket_details, request.business_instructions)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GenerateResponseResult(suggested_response=draft)

@router.get("/{ticket_id}")
def retrieve_ticket(ticket_id: int, db: Session = Depends(get_db)):
    row = get_analysis(db, ticket_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Ticket analysis not found")
    return {
        "ticket_id": row.id, "customer_id": row.customer_id, "query": row.query,
        "category": row.category, "sentiment": row.sentiment, "priority": row.priority,
        "summary": row.summary, "extractedEntities": row.extracted_entities,
        "suggestedResponse": row.suggested_response, "prompt_version": row.prompt_version,
        "model": row.model_name, "provider": row.provider, "duration_ms": row.duration_ms,
        "input_tokens": row.input_tokens, "output_tokens": row.output_tokens,
        "created_at": row.created_at.isoformat(),
    }
