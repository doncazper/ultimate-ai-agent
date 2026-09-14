from __future__ import annotations

import json

import pytest

from scripts.dev import uaa_finance
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.workspace import (
    FinanceWorkspace,
    FinanceWorkspaceConfiguration,
)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    value = FinanceWorkspace(
        FinanceWorkspaceConfiguration(tmp_path / "book", tmp_path / "helper", "a" * 64),
        crypto_backend=InMemoryFinanceCryptoBackend(),
    )
    monkeypatch.setattr(
        uaa_finance.FinanceWorkspace, "from_env", classmethod(lambda cls: value)
    )
    return value


def _run(capsys, *args):
    parsed = uaa_finance.parser().parse_args(list(args))
    code = parsed.func(parsed)
    return code, json.loads(capsys.readouterr().out)


def _save_bundle(tmp_path, bundle):
    path = tmp_path / "reviewed-bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    path.chmod(0o600)
    return path


def _prepare(capsys, operation, revision, suffix, *extra):
    code, prepared = _run(
        capsys,
        "workspace-prepare",
        "--operation",
        operation,
        "--expected-revision",
        str(revision),
        "--request-ref",
        f"request-ref:finance:cli-workspace:{suffix}",
        "--idempotency-ref",
        f"idempotency-ref:finance:cli-workspace:{suffix}",
        *extra,
    )
    assert code == 0
    return prepared


def test_cli_workspace_runs_same_setup_import_save_and_undo_contract(
    workspace, tmp_path, capsys
):
    code, view = _run(capsys, "workspace")
    assert code == 0
    assert view["status"] == "book_setup_required"
    for operation, revision in (("create", 0), ("import_commit", 1)):
        bundle = _prepare(capsys, operation, revision, operation)
        path = _save_bundle(tmp_path, bundle)
        code, result = _run(
            capsys, "workspace-run", "--bundle", str(path), "--confirmed"
        )
        assert code == 0
        assert result["schema_version"] == "uaa-finance-workspace-commit.v1"
        assert result["receipt"]["phase"] == "committed"
    _, view = _run(capsys, "workspace", "--limit", "1")
    assert view["item_count"] == 2
    assert len(view["review_items"]) == 1
    prepared = _prepare(
        capsys,
        "review_decision",
        2,
        "review",
        "--review-item-ref",
        view["review_items"][0]["review_item_ref"],
        "--decision",
        "reject",
    )
    path = _save_bundle(tmp_path, prepared)
    _run(capsys, "workspace-run", "--bundle", str(path), "--confirmed")
    _, read = _run(capsys, "workspace")
    assert read["review_items"][0]["state"] == "rejected"
    undo = _prepare(
        capsys,
        "review_undo",
        3,
        "undo",
        "--review-item-ref",
        read["review_items"][0]["review_item_ref"],
        "--compensates-event-ref",
        read["review_items"][0]["effective_decision_ref"],
    )
    path = _save_bundle(tmp_path, undo)
    _run(capsys, "workspace-run", "--bundle", str(path), "--confirmed")
    _, final = _run(capsys, "workspace")
    assert final["review_items"][0]["state"] == "needs_review"
    assert final["history_count"] == 2


def test_cli_workspace_needs_explicit_confirmation_before_reading_bundle(
    workspace, tmp_path
):
    args = uaa_finance.parser().parse_args(
        ["workspace-run", "--bundle", str(tmp_path / "absent")]
    )
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        args.func(args)
    assert not workspace.configuration.repository_dir.exists()


def test_cli_workspace_disable_rejects_before_reading_bundle(workspace, tmp_path):
    args = uaa_finance.parser().parse_args(
        [
            "workspace-run",
            "--bundle",
            str(tmp_path / "absent"),
            "--confirmed",
            "--safe-disable-engaged",
        ]
    )
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        args.func(args)
    assert not workspace.configuration.repository_dir.exists()


def test_cli_workspace_bounds_nesting_before_preparation_materialization(
    workspace, tmp_path
):
    path = tmp_path / "deep-bundle.json"
    path.write_bytes(b"[" * 10_000 + b"0" + b"]" * 10_000)
    path.chmod(0o600)
    args = uaa_finance.parser().parse_args(
        ["workspace-run", "--bundle", str(path), "--confirmed"]
    )
    with pytest.raises(ValueError, match="BODY_LIMIT_EXCEEDED"):
        args.func(args)
    assert not workspace.configuration.repository_dir.exists()
