from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_q34_news_source_intelligence_verifier_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts/verify_queue_v2_q34_news_source_intelligence.py"),
        ],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(ROOT / "src"),
        },
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout or result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "verified"
    assert payload["local_operator_intake_verified"] is True
    assert payload["provenance_freshness_deduplication_verified"] is True
    assert payload["ranking_and_preferences_verified"] is True
    assert payload["inspection_archive_recovery_undo_verified"] is True
    assert payload["today_and_morning_briefing_delivery_verified"] is True
    assert payload["exact_approval_authority_and_idempotency_verified"] is True
    assert payload["live_source_or_authenticated_access_performed"] is False
    assert payload["provider_model_call_performed"] is False
    assert payload["external_write_or_action_performed"] is False
    assert payload["public_or_production_claim"] is False
