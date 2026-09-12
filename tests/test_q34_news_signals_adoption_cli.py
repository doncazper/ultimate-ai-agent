from __future__ import annotations

import json
import subprocess
import sys


def test_adoption_inspection_cli_is_content_safe(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_news_signals_adoption.py",
            "--state-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["schema_version"] == (
        "uaa-news-signals-adoption-inspection.v1"
    )
    assert payload["workspace"]["revision"] == 0
    assert payload["workspace"]["status"] == "blocked_no_graduated_source"
    assert payload["external_network_read_performed"] is False
    assert payload["model_call_performed"] is False
    assert payload["raw_paths_included"] is False
    assert str(tmp_path) not in result.stdout
