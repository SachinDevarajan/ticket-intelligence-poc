from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"

def build_analysis_prompt(query: str, version: str) -> str:
    if version not in {"v1", "v2", "v3"}:
        raise ValueError("Unsupported prompt version. Choose v1, v2 or v3.")
    template = (PROMPT_DIR / f"ticket_analysis_{version}.txt").read_text(encoding="utf-8")
    return template.replace("{customer_query}", query)
