from pathlib import Path


def test_api_handlers_do_not_return_raw_exception_messages():
    app_source = Path("src/ultimate_ai_agent/api/app.py").read_text(encoding="utf-8")

    assert "safe_message=str(e)" not in app_source
    assert "safe_message = str(e)" not in app_source
    assert "detail=str(e)" not in app_source
    assert "detail = str(e)" not in app_source
