from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.config import settings

class Category(str, Enum):
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    ACCOUNT_ISSUE = "ACCOUNT_ISSUE"
    PRODUCT_ISSUE = "PRODUCT_ISSUE"
    DELIVERY_ISSUE = "DELIVERY_ISSUE"
    GENERAL_FEEDBACK = "GENERAL_FEEDBACK"
    PRODUCT_ENQUIRY = "PRODUCT_ENQUIRY"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    OTHER = "OTHER"

class Sentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TicketAnalyzeRequest(BaseModel):
    customerId: int | None = Field(default=None, ge=1, alias="customerId")
    query: str = Field(min_length=3, max_length=settings.max_query_length)
    prompt_version: str = Field(default="v3", pattern="^v[123]$")
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("query must contain at least 3 non-whitespace characters")
        return value

class ExtractedEntities(BaseModel):
    issue: str | None = None
    orderStatus: str | None = None
    orderId: str | None = None
    transactionReference: str | None = None
    product: str | None = None
    other: dict[str, str] = Field(default_factory=dict)

class TicketAnalysisResult(BaseModel):
    category: Category
    sentiment: Sentiment
    priority: Priority
    summary: str = Field(min_length=3, max_length=500)
    extractedEntities: ExtractedEntities
    suggestedResponse: str = Field(min_length=3, max_length=1500)

class TicketAnalysisResponse(TicketAnalysisResult):
    ticket_id: int
    prompt_version: str
    model: str
    provider: str
    duration_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    created_at: str

class GenerateResponseRequest(BaseModel):
    ticket_details: str = Field(min_length=3, max_length=settings.max_query_length)
    business_instructions: str = Field(default="Be concise, professional and empathetic. Do not invent facts.", max_length=2000)

class GenerateResponseResult(BaseModel):
    suggested_response: str = Field(min_length=3, max_length=1500)
    safety_note: str = "Draft only. A human support agent must review it before sending."
