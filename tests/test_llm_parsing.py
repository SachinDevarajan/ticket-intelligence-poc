import pytest
from app.services.llm_service import parse_json_object

def test_parse_json():
    assert parse_json_object('{"ok": true}') == {"ok": True}

def test_parse_fenced_json():
    assert parse_json_object('```json\n{"ok": true}\n```') == {"ok": True}

def test_reject_invalid_json():
    with pytest.raises(ValueError):
        parse_json_object("not json")

def test_reject_non_object_json():
    with pytest.raises(ValueError):
        parse_json_object('["not", "object"]')
