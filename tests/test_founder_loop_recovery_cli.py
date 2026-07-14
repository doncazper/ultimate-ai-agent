from __future__ import annotations

import pytest

from scripts.dev import uaa_founder_loop_recovery as recovery_cli


def test_recovery_cli_redacts_unexpected_local_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    private_path = "/private/local/operator/state.sqlite3"
    monkeypatch.setattr(
        recovery_cli,
        "verify_founder_loop_backup",
        lambda _backup_dir: (_ for _ in ()).throw(OSError(private_path)),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["uaa-founder-loop-recovery", "verify", "--backup-dir", "ignored"],
    )

    assert recovery_cli.main() == 1
    output = capsys.readouterr().out
    assert private_path not in output
    assert "founder-loop-recovery-internal-error" in output
