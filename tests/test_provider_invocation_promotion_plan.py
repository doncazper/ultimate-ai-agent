from pathlib import Path

from scripts import verify_provider_invocation_promotion_plan as verifier


def test_provider_invocation_promotion_plan_verifier_passes() -> None:
    assert verifier.main() == 0


def _write_supporting_docs(tmp_path: Path, *, text: str = "supporting ok") -> dict[Path, str]:
    paths = {
        tmp_path / "product_language.md": (
            "No provider invocation promotion authority drift\n"
            "exact approval"
        ),
        tmp_path / "current_board.md": (
            "Tiny Exact-Approved Provider Invocation Lane\n"
            "exact approval"
        ),
        tmp_path / "documentation_index.md": "EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
        tmp_path / "readme.md": "EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
        tmp_path / "canonical_map.md": "EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
        tmp_path / "truth_packet.md": (
            "Tiny Exact-Approved Provider Invocation Lane\n"
            "exact-approval-bound"
        ),
    }
    for path, fragment in paths.items():
        path.write_text(f"{fragment}\n{text}\n", encoding="utf-8")
    return paths


def test_provider_invocation_plan_verifier_rejects_missing_policy_gate(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text(
        "\n".join(
            fragment
            for fragment in verifier.REQUIRED_DOC_FRAGMENTS
            if fragment != "`PolicyEngine` policy validation"
        ),
        encoding="utf-8",
    )
    supporting = _write_supporting_docs(tmp_path)
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)

    failures = verifier.validate_provider_invocation_promotion_plan()

    assert any("`PolicyEngine` policy validation" in failure for failure in failures)


def test_provider_invocation_plan_verifier_rejects_supporting_doc_authority_drift(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(
        tmp_path,
        text="runtime invocation is available",
    )
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)

    failures = verifier.validate_provider_invocation_promotion_plan()

    assert any("authority drift" in failure for failure in failures)


def test_provider_invocation_plan_verifier_rejects_authority_drift_variants(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(tmp_path)
    current_board_path = next(
        path for path in supporting if path.name == "current_board.md"
    )
    current_board_path.write_text(
        "Tiny Exact-Approved Provider Invocation Lane\n"
        "exact approval\n"
        "providers are callable\n"
        "provider SDK calls are available\n"
        "model output has authority\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)

    failures = verifier.validate_provider_invocation_promotion_plan()

    assert any("providers_callable" in failure for failure in failures)
    assert any("provider_sdk_calls_available" in failure for failure in failures)
    assert any("model_output_authority" in failure for failure in failures)


def test_provider_invocation_plan_verifier_rejects_missing_supporting_policy_gate(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(tmp_path)
    current_board_path = next(
        path for path in supporting if path.name == "current_board.md"
    )
    current_board_path.write_text(
        "Tiny Exact-Approved Provider Invocation Lane\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)
    monkeypatch.setattr(
        verifier,
        "REQUIRED_SUPPORTING_POLICY_FRAGMENTS",
        {current_board_path: "exact approval"},
    )

    failures = verifier.validate_provider_invocation_promotion_plan()

    assert any("missing provider policy gate fragment" in failure for failure in failures)


def test_provider_invocation_plan_verifier_rejects_missing_supporting_doc_link(
    monkeypatch, tmp_path: Path
) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text("\n".join(sorted(verifier.REQUIRED_DOC_FRAGMENTS)), encoding="utf-8")
    supporting = _write_supporting_docs(tmp_path)
    missing_fragment_path = next(iter(supporting))
    missing_fragment_path.write_text("supporting doc without required fragment\n", encoding="utf-8")
    monkeypatch.setattr(verifier, "DOC_PATH", doc)
    monkeypatch.setattr(verifier, "REQUIRED_SUPPORTING_FRAGMENTS", supporting)

    failures = verifier.validate_provider_invocation_promotion_plan()

    assert any("missing provider invocation plan fragment" in failure for failure in failures)
