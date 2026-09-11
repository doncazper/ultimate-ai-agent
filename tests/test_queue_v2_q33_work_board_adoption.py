from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify_queue_v2_q33_work_board_adoption.py"


def test_q33_work_board_adoption_verifier_passes() -> None:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(ROOT / "src"),
    }
    result = subprocess.run(
        [sys.executable, "-B", str(VERIFIER)],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout or result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "verified"
    assert payload["create_update_move_archive_recover_undo_verified"] is True
    assert payload["encrypted_backup_restore_recovery_verified"] is True
    assert payload["exact_restore_replay_verified"] is True
    assert payload["exact_local_approval_and_authority_lease_verified"] is True
    assert payload["task_execution_performed"] is False
    assert payload["connector_write_performed"] is False
    assert payload["provider_model_call_performed"] is False
    assert payload["public_or_production_claim"] is False
