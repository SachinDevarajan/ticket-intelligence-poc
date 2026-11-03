# Architecture and request flow

```mermaid
flowchart TD
    A[Client / Postman] --> B[FastAPI Router]
    B --> C[Ticket Service]
    C --> D[Prompt Builder: V1 / V2 / V3]
    D --> E[LLM Service]
    E --> F{Provider}
    F --> G[Groq API]
    F --> H[Ollama local]
    G --> I[JSON parsing + Pydantic validation]
    H --> I
    I -->|valid| J[Repository / SQLAlchemy]
    J --> K[(PostgreSQL)]
    J --> L[Validated API response]
    I -->|invalid| M[Controlled 502 error]
    N[Evaluation script + labelled cases] --> B
```

1. Router validates the incoming request with Pydantic.
2. Ticket service loads the requested reusable prompt version.
3. LLM service calls Groq or Ollama with a timeout and bounded retry.
4. The response is parsed as JSON and validated against the Pydantic response schema and allowed enums.
5. Validated output and provider/prompt/timing/token metadata are persisted in PostgreSQL.
6. The API returns a draft for a human agent. No customer message is sent.
7. The evaluation script sends the same fixed labelled cases through V1, V2 and V3 and writes a comparable report.
