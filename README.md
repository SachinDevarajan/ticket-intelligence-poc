# AI-Powered Customer Support & Ticket Intelligence API

A backend-only proof of concept built with Python, FastAPI, PostgreSQL and an LLM provider. Groq is the default hosted provider; Ollama can be selected for local inference. This project does **not** use the OpenAI API.

## 1. Features

- `POST /api/ai/tickets/analyze`: classifies a support message, assesses sentiment and priority, summarises it, extracts supported entities and drafts a reply.
- `POST /api/ai/tickets/generate-response`: generates a professional response draft from ticket details and business instructions.
- `GET /api/ai/tickets/{ticket_id}`: retrieves a previously analysed ticket.
- Three external, reusable prompt templates: V1 basic, V2 role/context/task/constraints, V3 with explicit schema and example.
- PostgreSQL persistence through SQLAlchemy.
- Pydantic validation for requests and LLM output.
- Groq and Ollama provider support, timeouts, bounded retries and controlled provider/output errors.
- 17 fixed labelled evaluation cases; comparison script calculates category accuracy, macro precision, macro recall, macro F1, priority accuracy and sentiment accuracy.
- Human-in-the-loop: generated replies are drafts only and are never sent automatically.

## 2. Prerequisites

- Windows 10/11, macOS or Linux.
- Python 3.11 or newer (3.12+ works).
- Docker Desktop (recommended for PostgreSQL), or an existing PostgreSQL 14+ server.
- A Groq API key for hosted inference, OR Ollama installed locally for local inference.

## 3. Extract and open the project

1. Extract the ZIP file.
2. Open the extracted `ticket_intelligence_poc` folder in VS Code.
3. Open a terminal in that folder. All commands below assume this folder is the current directory.

## 4. Create a virtual environment

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in that terminal, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Configure environment variables

Copy `.env.example` to `.env` in the project root.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

Open `.env` and configure the provider.

### Option A — Groq (recommended starting option)

```env
LLM_PROVIDER=groq
GROQ_API_KEY=put_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Create a Groq API key from the Groq developer console. Check the model list in your Groq account if the configured model is no longer available or is not enabled for your account. Free-tier limits and model availability are controlled by Groq and may change. Never commit `.env`, zip it, or share the key.

### Option B — Ollama (local model, no hosted API key)

Install Ollama from https://ollama.com/ and open its application. In another terminal, download a model:

```bash
ollama pull llama3.2:3b
```

Set the following in `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Make sure Ollama is running before calling the API. Local speed and output quality depend on your computer and the model you select. No Groq key is needed when using Ollama.

## 6. Start PostgreSQL

From the project root, run:

```bash
docker compose up -d postgres
```

Check the container:

```bash
docker compose ps
```

The default database settings in `.env.example` match the Docker Compose configuration:

```env
DATABASE_URL=postgresql+psycopg://ticket_user:ticket_password@localhost:5432/ticket_intelligence
```

**Use this exact connection string in your `.env`:**

```env
DATABASE_URL=postgresql+psycopg://ticket_user:ticket_password@localhost:5432/ticket_intelligence
```

The application creates the required table automatically at startup. For an existing PostgreSQL installation, create a database/user and update `DATABASE_URL` accordingly.

## 7. Start the FastAPI application

Keep PostgreSQL running. In the project root and with the virtual environment active:

```bash
uvicorn app.main:app --reload
```

Expected local URLs:

- API base: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

The first model call may take longer. If using Ollama, confirm the selected model has been pulled. If using Groq, confirm the key and model name.

## 8. Test the API

### Analyse a ticket

`POST http://127.0.0.1:8000/api/ai/tickets/analyze`

```json
{
  "customerId": 101,
  "query": "My payment was deducted but my order is still pending. I need this resolved immediately.",
  "prompt_version": "v3"
}
```

Use `v1`, `v2` or `v3` to select a prompt version. The API returns the validated classification, summary, entities, suggested response, ticket ID, model/provider, prompt version, duration and token usage when available.

### Generate a response draft

`POST http://127.0.0.1:8000/api/ai/tickets/generate-response`

```json
{
  "ticket_details": "Customer says payment was deducted but order is pending. Order ID is not provided.",
  "business_instructions": "Be concise, empathetic and ask for missing details. Do not promise a refund."
}
```

### Retrieve a saved analysis

`GET http://127.0.0.1:8000/api/ai/tickets/1`

Replace `1` with the `ticket_id` returned by the analysis endpoint.

A ready-to-import collection is available at `postman/Ticket_Intelligence.postman_collection.json`.

## 9. Run automated tests

With the virtual environment active:

```bash
pytest -q
```

These tests cover prompt loading, JSON parsing, and the API endpoints (using a fake LLM and an in-memory SQLite database). They do not require an LLM API key or a running PostgreSQL server.

## 10. Run the V1 / V2 / V3 evaluation

1. Start PostgreSQL and the API server.
2. Confirm the selected LLM provider works by analysing one sample ticket.
3. Open a second terminal in the project root and activate the same virtual environment.
4. Run:

```bash
python evaluation/run_evaluation.py
```

On Groq's free tier (about 8000 tokens/minute) the script waits 8 seconds between calls and retries rate-limited requests, so the full run takes roughly 8-10 minutes. On a paid tier you can set `EVAL_DELAY_SECONDS=0` to run faster.

The script submits the same 17 labelled cases to each of V1, V2 and V3 (51 API calls total). It saves `evaluation/evaluation_report.json` with per-case expected and predicted labels and summary metrics.

Metric definitions:

- **Accuracy:** correct category predictions divided by all test cases.
- **Precision (per class):** true positives divided by true positives plus false positives.
- **Recall (per class):** true positives divided by true positives plus false negatives.
- **F1 (per class):** harmonic mean of precision and recall.
- **Macro precision/recall/F1:** unweighted average across classes represented in the expected labels. The evaluation script omits labels absent from the expected test set when averaging.
- Priority and sentiment accuracy are reported separately.

LLM outputs can vary. The expected labels are fixed in `evaluation/test_cases.json` before the run; do not edit them just to improve the score. Review mismatches manually. Relevance and factual support of drafted replies require human review; classification metrics do not measure response quality.

## 11. Database inspection

The table is `ticket_analyses` in the `ticket_intelligence` database. Example using `psql`:

```sql
SELECT id, category, sentiment, priority, prompt_version, model_name, duration_ms, created_at
FROM ticket_analyses
ORDER BY created_at DESC;
```

## 12. Error handling and safety

- Request size and required fields are validated with Pydantic.
- Provider calls use a configured timeout and a bounded retry count.
- Provider failures and invalid model JSON/schema are returned as controlled HTTP 502 errors.
- Only schema-valid outputs are persisted.
- Customer message content is explicitly marked untrusted in prompts.
- Credentials are loaded from environment variables and must not be committed.
- Use synthetic or anonymised customer data only.
- Generated replies are suggestions for a support agent. No email/SMS/customer messaging integration exists.

## 13. Known limitations and next improvements

- This is a proof of concept, not a production-ready customer support platform.
- Prompt instructions reduce but cannot eliminate prompt injection or hallucinations. Add stronger isolation, policy checks and adversarial testing before production.
- Database schema creation uses `create_all` for a small POC; use Alembic migrations for a maintained application.
- Add authentication, authorisation, rate limiting, structured observability, secret management and retention policies before production.
- Add human review scoring for response relevance, completeness and factual support.
- Provider token counts are stored only when the provider exposes them. Ollama usage fields are token counts, not necessarily directly comparable with Groq billing tokens.
- The evaluation dataset is intentionally small; results are indicative and not proof of production performance.

## 14. Project walkthrough order

1. `app/api/ticket_router.py` — endpoints and HTTP responses.
2. `app/services/ticket_service.py` — business orchestration.
3. `app/services/prompt_service.py` and `app/prompts/` — reusable prompt versions.
4. `app/services/llm_service.py` — Groq/Ollama integration and provider handling.
5. `app/schemas/ticket.py` — request and output validation.
6. `app/models/ticket.py` and `app/repositories/ticket_repository.py` — PostgreSQL persistence.
7. `evaluation/test_cases.json` and `evaluation/run_evaluation.py` — fixed dataset and prompt comparison.
8. `docs/architecture.md` — architecture flow.
