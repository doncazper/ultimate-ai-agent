from pathlib import Path

from scripts import verify_provider_billing_authority_boundary as verifier


def test_provider_billing_authority_boundary_verifier_passes() -> None:
    assert verifier.main() == 0


def test_provider_billing_authority_boundary_is_in_make_verify_sequence() -> None:
    import scripts.verify_all as verify_all

    assert (
        "provider billing authority boundary scan",
        "verify_provider_billing_authority_boundary",
    ) in verify_all.SCAN_SEQUENCE


def _write_supporting_docs(tmp_path: Path, *, text: str = "supporting ok") -> dict[Path, str]:
    paths = {
        tmp_path / "product_language.md": "No provider billing authority drift",
        tmp_path / "current_board.md": "Provider Billing Authority Boundary",
        tmp_path / "documentation_index.md": "PROVIDER_BILLING_AUTHORITY_BOUNDARY.md",
        tmp_path / "readme.md": "PROVIDER_BILLING_AUTHORITY_BOUNDARY.md",
        tmp_path / "canonical_map.md": "PROVIDER_BILLING_AUTHORITY_BOUNDARY.md",
        tmp_path / "truth_packet.md": "Provider Billing Authority Boundary",
        tmp_path / "roadmap.md": "Provider billing authority remains blocked.",
    }
    for path, fragment in paths.items():
        path.write_text(f"{fragment}\n{text}\n", encoding="utf-8")
    return paths


def test_provider_billing_boundary_verifier_rejects_missing_state(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "provider_billing_boundary.md"
    doc.write_text(
        "\n".join(
            fragment
            for fragment in verifier.REQUIRED_DOC_FRAGMENTS
            if fragment != "incomplete_cost_blocked"
        ),
        encoding="utf-8",
    )
    supporting = _write_supporting_docs(tmp_path)
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_provider_billing_authority_boundary()

    assert any("incomplete_cost_blocked" in failure for failure in failures)


def test_provider_billing_boundary_verifier_rejects_authority_drift(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "provider_billing_boundary.md"
    doc.write_text(
        "\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS))
        + "\nbilling authority is granted\n",
        encoding="utf-8",
    )
    supporting = _write_supporting_docs(tmp_path)
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_provider_billing_authority_boundary()

    assert any("billing_authority_granted" in failure for failure in failures)


def test_provider_billing_boundary_verifier_rejects_supporting_doc_drift(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "provider_billing_boundary.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(
        tmp_path,
        text="broad spend toggle is enabled",
    )
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_provider_billing_authority_boundary()

    assert any("broad_spend_toggle_enabled" in failure for failure in failures)


def test_provider_billing_boundary_verifier_rejects_missing_supporting_link(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "provider_billing_boundary.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(tmp_path)
    missing_fragment_path = next(iter(supporting))
    missing_fragment_path.write_text("supporting doc without required fragment\n", encoding="utf-8")
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(verifier, "_append_api_route_failures", lambda failures: None)

    failures = verifier.validate_provider_billing_authority_boundary()

    assert any("missing provider billing boundary fragment" in failure for failure in failures)


def test_provider_billing_boundary_verifier_rejects_api_route_fragment(
    monkeypatch, tmp_path: Path
) -> None:
    api_root = tmp_path / "src/ultimate_ai_agent/api"
    api_root.mkdir(parents=True)
    (api_root / "provider_setup.py").write_text(
        'route = "/providers/billing-authority"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    failures: list[str] = []
    verifier._append_api_route_failures(failures)

    assert any("forbidden runtime route fragment" in failure for failure in failures)
