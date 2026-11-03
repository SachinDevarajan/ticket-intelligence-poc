import json
import re
import time
from dataclasses import dataclass
from typing import Any
import httpx
from app.core.config import settings

class LLMProviderError(RuntimeError):
    pass

@dataclass
class LLMResult:
    content: str
    model: str
    provider: str
    input_tokens: int | None = None
    output_tokens: int | None = None

class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider.strip().lower()
        if self.provider not in {"groq", "ollama"}:
            raise LLMProviderError("LLM_PROVIDER must be either 'groq' or 'ollama'.")

    def _groq(self, system_prompt: str, user_prompt: str) -> LLMResult:
        if not settings.groq_api_key:
            raise LLMProviderError("GROQ_API_KEY is missing. Add it to your .env file.")
        try:
            from groq import Groq
        except ImportError as exc:
            raise LLMProviderError("Groq SDK is not installed. Run: pip install -r requirements.txt") from exc
        client = Groq(api_key=settings.groq_api_key, timeout=settings.llm_timeout_seconds, max_retries=0)
        try:
            completion = client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            usage = completion.usage
            return LLMResult(
                content=completion.choices[0].message.content or "",
                model=completion.model or settings.groq_model,
                provider="groq",
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=getattr(usage, "completion_tokens", None),
            )
        except Exception as exc:
            raise LLMProviderError(f"Groq request failed: {type(exc).__name__}: {exc}") from exc

    def _ollama(self, system_prompt: str, user_prompt: str) -> LLMResult:
        url = settings.ollama_base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
            return LLMResult(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", settings.ollama_model),
                provider="ollama",
                input_tokens=data.get("prompt_eval_count"),
                output_tokens=data.get("eval_count"),
            )
        except Exception as exc:
            raise LLMProviderError(f"Ollama request failed: {type(exc).__name__}: {exc}") from exc

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        attempts = max(0, min(settings.llm_max_retries, 2)) + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return self._groq(system_prompt, user_prompt) if self.provider == "groq" else self._ollama(system_prompt, user_prompt)
            except LLMProviderError as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(0.5 * (2 ** attempt))
        raise LLMProviderError(str(last_error or "LLM request failed"))

def parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("The model returned malformed JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("The model response must be a JSON object.")
    return parsed
