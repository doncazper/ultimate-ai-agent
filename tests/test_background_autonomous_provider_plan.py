from pathlib import Path

from scripts import verify_background_autonomous_provider_plan as verifier


def test_background_autonomous_provider_plan_verifier_passes() -> None:
    assert verifier.main() == 0


def test_background_autonomous_provider_plan_is_in_make_verify_sequence() -> None:
    import scripts.verify_all as verify_all

    assert (
        "background/autonomous provider promotion plan scan",
        "verify_background_autonomous_provider_plan",
    ) in verify_all.SCAN_SEQUENCE


def _write_supporting_docs(tmp_path: Path, *, text: str = "supporting ok") -> dict[Path, str]:
    paths = {
        tmp_path / "product_language.md": (
            "No background/autonomous provider-call promotion authority drift"
        ),
        tmp_path / "current_board.md": (
            "Background and Autonomous Provider Calls Promotion Plan"
        ),
        tmp_path / "documentation_index.md": (
            "BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md"
        ),
        tmp_path / "readme.md": (
            "BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md"
        ),
        tmp_path / "canonical_map.md": (
            "BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md"
        ),
        tmp_path / "truth_packet.md": (
            "Background and Autonomous Provider Calls Promotion Plan"
        ),
        tmp_path / "roadmap.md": "Background/autonomous provider calls remain blocked.",
    }
    for path, fragment in paths.items():
        path.write_text(f"{fragment}\n{text}\n", encoding="utf-8")
    return paths


def test_background_autonomous_provider_plan_verifier_rejects_missing_gate(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text(
        "\n".join(
            fragment
            for fragment in verifier.REQUIRED_DOC_FRAGMENTS
            if fragment != "CostGovernor must run before enqueue, before dispatch, and before every fallback attempt."
        ),
        encoding="utf-8",
    )
    supporting = _write_supporting_docs(tmp_path)
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_background_autonomous_provider_plan()

    assert any("CostGovernor must run" in failure for failure in failures)


def test_background_autonomous_provider_plan_verifier_rejects_authority_drift(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text(
        "\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS))
        + "\nbackground provider calls are enabled\n",
        encoding="utf-8",
    )
    supporting = _write_supporting_docs(tmp_path)
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_background_autonomous_provider_plan()

    assert any("authority drift" in failure for failure in failures)


def test_background_autonomous_provider_plan_verifier_rejects_supporting_doc_drift(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(
        tmp_path,
        text="billing authority is granted",
    )
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_background_autonomous_provider_plan()

    assert any("billing_authority_granted" in failure for failure in failures)


def test_background_autonomous_provider_plan_verifier_rejects_missing_supporting_link(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(tmp_path)
    missing_fragment_path = next(iter(supporting))
    missing_fragment_path.write_text("supporting doc without required fragment\n", encoding="utf-8")
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_background_autonomous_provider_plan()

    assert any("missing background/autonomous provider plan fragment" in failure for failure in failures)


def test_background_autonomous_provider_plan_verifier_rejects_api_route_fragment(
    monkeypatch, tmp_path: Path
) -> None:
    api_root = tmp_path / "src/ultimate_ai_agent/api"
    api_root.mkdir(parents=True)
    (api_root / "provider_setup.py").write_text(
        'route = "/providers/background"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    failures: list[str] = []
    verifier._append_api_route_failures(failures)

    assert any("forbidden runtime route fragment" in failure for failure in failures)
