import pytest
from app.services.prompt_service import build_analysis_prompt

def test_all_prompt_versions_include_customer_query():
    for version in ("v1", "v2", "v3"):
        prompt = build_analysis_prompt("Sample customer issue", version)
        assert "Sample customer issue" in prompt

def test_invalid_prompt_version_rejected():
    with pytest.raises(ValueError):
        build_analysis_prompt("Hello there", "v4")
