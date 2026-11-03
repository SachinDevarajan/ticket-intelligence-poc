"""API tests with a fake LLM and in-memory SQLite: no Groq key or PostgreSQL needed."""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models.ticket import TicketAnalysis  # noqa: F401
from app.services import llm_service
from app.services.llm_service import LLMResult


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)  # no `with`: startup/create_all on PostgreSQL is skipped
    app.dependency_overrides.clear()


def fake_llm(monkeypatch, payload):
    content = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr(
        llm_service.LLMService, "generate",
        lambda self, system, user: LLMResult(content=content, model="fake", provider="groq", input_tokens=1, output_tokens=2),
    )


GOOD = {
    "category": "payment_issue", "sentiment": "NEGATIVE", "priority": "HIGH",
    "summary": "Customer was charged twice.",
    "extractedEntities": {"orderId": 77, "other": {"amount": 20}},
    "suggestedResponse": "Sorry about that. Could you share the transaction reference?",
}


def test_analyze_and_retrieve(client, monkeypatch):
    fake_llm(monkeypatch, GOOD)
    r = client.post("/api/ai/tickets/analyze", json={"customerId": 1, "query": "Charged twice for order 77", "prompt_version": "v3"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["category"] == "PAYMENT_ISSUE"
    assert body["extractedEntities"]["orderId"] == "77"
    got = client.get(f"/api/ai/tickets/{body['ticket_id']}")
    assert got.status_code == 200 and got.json()["priority"] == "HIGH"


def test_malformed_model_output_returns_502(client, monkeypatch):
    fake_llm(monkeypatch, "not json")
    r = client.post("/api/ai/tickets/analyze", json={"query": "Please help with my order"})
    assert r.status_code == 502


def test_invalid_label_returns_502(client, monkeypatch):
    fake_llm(monkeypatch, {**GOOD, "category": "SOMETHING_ELSE"})
    r = client.post("/api/ai/tickets/analyze", json={"query": "Please help with my order"})
    assert r.status_code == 502


def test_validation_and_404(client):
    assert client.post("/api/ai/tickets/analyze", json={"query": "  "}).status_code == 422
    assert client.post("/api/ai/tickets/analyze", json={"query": "hello there", "prompt_version": "v9"}).status_code == 422
    assert client.get("/api/ai/tickets/999").status_code == 404


def test_generate_response(client, monkeypatch):
    fake_llm(monkeypatch, {"suggested_response": "Could you share your order ID?"})
    r = client.post("/api/ai/tickets/generate-response", json={"ticket_details": "Payment deducted, order pending"})
    assert r.status_code == 200 and "order ID" in r.json()["suggested_response"]
