import json
from pathlib import Path

import pytest

from scripts import verify_tool_aware_cognition_plan as verifier


def test_tool_aware_cognition_plan_is_complete_and_queue_gated() -> None:
    result = verifier.verify()

    assert result == {
        "status": "passed",
        "documented_phase_count": 9,
        "normal_chat_fast_path_required": True,
        "direct_chat_quality_non_inferiority_required": True,
        "local_model_preservation_required": True,
        "documented_familiarity_state_count": 9,
        "goat_comparison_gate_documented": True,
        "evaluation_governance_required": True,
        "reversible_rollout_required": True,
        "structured_runtime_authority_added": False,
        "ordered_manifest_item_count": 9,
    }


@pytest.mark.parametrize(
    "fragment",
    (
        "`familiar_supported`",
        "`familiar_input_required`",
        "`familiar_unavailable`",
        "`familiar_requires_approval`",
        "`familiar_authority_blocked`",
        "`capability_evidence_unavailable`",
        "`ambiguous`",
        "`novel_unsupported`",
        "`outcome_uncertain`",
    ),
)
def test_familiarity_contract_is_explicit(fragment: str) -> None:
    text = verifier.PLAN.read_text(encoding="utf-8")
    assert fragment in text


def test_policy_denial_precedence_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "`familiar_authority_blocked` when the current PolicyEngine or applicable\n"
            "   safety boundary denies the exact request",
            "`familiar_authority_blocked` when a known effect has an existing lane",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_policy_denial_must_precede_ambiguity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    text = verifier.PLAN.read_text(encoding="utf-8")
    policy = (
        "2. `familiar_authority_blocked` when the current PolicyEngine or applicable\n"
        "   safety boundary denies the exact request;"
    )
    ambiguity = (
        "4. `ambiguous` when materially different interpretations remain after the\n"
        "   policy and safety screen;"
    )
    plan.write_text(
        text.replace(policy, ambiguity.replace("4.", "2.", 1)).replace(
            ambiguity, policy.replace("2.", "4.", 1), 1
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="familiarity precedence"):
        verifier.verify()


def test_missing_queue_gate_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text("Queue entry without a Goat acceptance gate.", encoding="utf-8")
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="queue insertion is missing"):
        verifier.verify()


def test_self_authorizing_language_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        + "\nThis plan authorizes runtime model calls.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="self-authorizing"):
        verifier.verify()


@pytest.mark.parametrize(
    "contradiction",
    (
        "Runtime model calls are now authorized.",
        "This program permits new runtime model calls.",
        "The plan allows provider access.",
        "Browser automation is enabled.",
        "This program grants browser authority.",
        "Policy checks may be bypassed.",
        "Automatic skill execution is allowed.",
    ),
)
def test_equivalent_authority_contradictions_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contradiction: str,
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8") + f"\n{contradiction}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="self-authorizing"):
        verifier.verify()


@pytest.mark.parametrize(
    "surface_name",
    ("QUEUE", "BOARD", "ROADMAP", "CANONICAL_ROADMAP", "TRUTH_PACKET"),
)
def test_authority_contradictions_fail_on_every_program_truth_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    surface_name: str,
) -> None:
    source = getattr(verifier, surface_name)
    mutated = tmp_path / source.name
    mutated.write_text(
        source.read_text(encoding="utf-8")
        + "\nThis program grants production authority.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, surface_name, mutated)

    with pytest.raises(RuntimeError, match="self-authorizing"):
        verifier.verify()


@pytest.mark.parametrize(
    "contradiction",
    (
        "This program does not authorize web fetching, but this program grants "
        "production authority.",
        "No web fetching is authorized; this program grants production authority.",
        "No web fetching is authorized, this program grants production authority.",
        "No web fetching is authorized, however production authority is enabled.",
    ),
)
def test_authority_negation_does_not_escape_its_clause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contradiction: str,
) -> None:
    board = tmp_path / "current_board.md"
    board.write_text(
        verifier.BOARD.read_text(encoding="utf-8") + f"\n{contradiction}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "BOARD", board)

    with pytest.raises(RuntimeError, match="self-authorizing"):
        verifier.verify()


def test_missing_structured_authority_denial_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "- connector writes;",
            "- connector mutations are outside this document;",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan authority boundary is missing"):
        verifier.verify()


def test_missing_production_authority_denial_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "- public release, production authority, or claims of human-like\n"
            "  self-awareness.",
            "- future distribution remains a separate decision.",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan authority boundary is missing"):
        verifier.verify()


def test_missing_phase_heading_fails_even_when_phase_token_remains(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "### TAW-00 — Convergence ledger and evaluation baseline",
            "### Convergence ledger and evaluation baseline",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan phase headings is missing"):
        verifier.verify()


def test_fixed_one_pr_per_phase_policy_cannot_be_restored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "PR count follows contract and risk seams rather than a fixed",
            "Every phase always uses one separate pull request because a fixed",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_reordered_queue_gate_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text(
        verifier.QUEUE.read_text(encoding="utf-8")
        .replace(
            "3. At that pre-Goat boundary, execute TAW-00 through TAW-08",
            "4. At that pre-Goat boundary, execute TAW-00 through TAW-08",
        )
        .replace(
            "4. Run the final GoatCitadel comparison only after",
            "3. Run the final GoatCitadel comparison only after",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="ordered queue insertion is missing"):
        verifier.verify()


def test_remaining_queue_manifest_order_and_hashes_are_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["items"][-2], payload["items"][-1] = (
        payload["items"][-1],
        payload["items"][-2],
    )
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="immutable sequence is invalid"):
        verifier.verify()


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload.update({"extra": "not-allowed"}),
        lambda payload: payload["items"][0].update({"extra": "not-allowed"}),
        lambda payload: payload["items"][0].update({"position": True}),
        lambda payload: payload["items"][0].update({"title": 1}),
    ),
)
def test_remaining_queue_manifest_schema_and_types_are_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    mutation(payload)
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="manifest|sequence|types"):
        verifier.verify()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source_kind", "repo_file"),
        ("source_status", "available"),
        ("source_ref", "external-ref:wrong"),
        ("execution_status", "ready"),
    ),
)
def test_remaining_queue_missing_sources_stay_execution_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["items"][0][field] = value
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="item types are invalid"):
        verifier.verify()


@pytest.mark.parametrize("nested", (False, True))
def test_remaining_queue_manifest_rejects_duplicate_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, nested: bool
) -> None:
    manifest = tmp_path / "manifest.json"
    original = verifier.MANIFEST.read_text(encoding="utf-8")
    if nested:
        duplicate = original.replace(
            '"runtime_model_or_provider_calls": false,',
            '"runtime_model_or_provider_calls": true,\n'
            '    "runtime_model_or_provider_calls": false,',
            1,
        )
    else:
        duplicate = original.replace(
            '"schema_version": "uaa.remaining_queue_manifest.v1",',
            '"schema_version": "unsafe.duplicate",\n'
            '  "schema_version": "uaa.remaining_queue_manifest.v1",',
            1,
        )
    manifest.write_text(duplicate, encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="manifest is not valid JSON"):
        verifier.verify()


def test_plan_requires_blocked_unsafe_mapping_and_nondurable_statistics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        .replace(
            "| `blocked_unsafe` | `blocked_unsafe` | `familiar_authority_blocked` | null |",
            "| `blocked_unsafe` | `blocked_unsafe` | `novel_unsupported` | null |",
        )
        .replace(
            "recomputable, non-authoritative projection",
            "bounded durable store",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_plan_requires_evidence_bound_legacy_tool_mapping_and_api_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        .replace(
            "| `prepare_tool_or_action` | Derived with the route/state invariant; `prepare_tool_or_action` only for `familiar_supported` | Derived only from frozen typed evidence",
            "| `prepare_tool_or_action` | `prepare_tool_or_action` | `familiar_supported`",
        )
        .replace(
            "and an exact catalog/index-evidence-unavailable posture maps to `capability_evidence_unavailable`; absent or contradictory evidence makes the envelope invalid | null |",
            "absent or contradictory evidence makes the envelope invalid | null |",
            1,
        )
        .replace("stable unique operation IDs", "API route names")
        .replace("OpenAPI and `/api/manifest` coverage", "API documentation"),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_plan_requires_all_states_and_unavailable_approval_normalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        .replace(
            "Implement all nine canonical familiarity states",
            "Implement eight canonical familiarity states",
        )
        .replace(
            "Route and familiarity state are one invariant",
            "Route and familiarity state are independent labels",
        )
        .replace(
            "`approval_required` only with `familiar_requires_approval`",
            "`approval_required` may retain any normalized state",
        )
        .replace(
            "`ask_for_required_input` only with `familiar_input_required`",
            "`ask_for_required_input` may retain any normalized state",
        )
        .replace(
            "`report_unavailable` only with `familiar_unavailable`",
            "`report_unavailable` may retain any normalized state",
        )
        .replace(
            "`blocked_authority` only\nwith `familiar_authority_blocked`",
            "`blocked_authority` may retain any normalized state",
        )
        .replace(
            "`report_unsupported` only with\n`novel_unsupported`",
            "`report_unsupported` may retain any normalized state",
        )
        .replace(
            "`report_outcome_uncertain` only with\n`outcome_uncertain`",
            "`report_outcome_uncertain` may retain any normalized state",
        )
        .replace(
            "| `answer_with_reviewed_memory`, `draft_or_plan` | Derived with the route/state invariant; unchanged accepted route only for `familiar_supported`",
            "| `answer_with_reviewed_memory`, `draft_or_plan` | unchanged accepted route",
        )
        .replace(
            "| `approval_required` | Derived with the route/state invariant; `approval_required` only for `familiar_requires_approval` | Derived only from frozen typed evidence",
            "| `approval_required` | `approval_required` | `familiar_requires_approval`",
        )
        .replace(
            "validated unavailability maps to `familiar_unavailable`",
            "validated unavailability maps to `familiar_authority_blocked`",
        )
        .replace(
            "validated current availability, and complete typed inputs",
            "validated current availability",
        )
        .replace(
            "incomplete typed inputs map to `familiar_input_required`",
            "incomplete typed inputs map to `familiar_requires_approval`",
        )
        .replace(
            "| `execute_approved_action` | Derived with the route/state invariant; `execute_approved_action` only for `familiar_supported` | Derived only from frozen typed evidence",
            "| `execute_approved_action` | `execute_approved_action` | `familiar_supported`",
        )
        .replace(
            "| Any accepted contract after proposal or execution work began when exact durable terminal proof is absent or inconsistent | `report_outcome_uncertain` | `outcome_uncertain`",
            "| Any accepted contract after proposal or execution work began | `report_unavailable` | `outcome_uncertain`",
        )
        .replace(
            "| Any possible-tool-intent turn whose valid, current bounded catalog proves that no capability contract adequately covers the requested effect | `report_unsupported` | `novel_unsupported` | null |",
            "| Any possible-tool-intent turn with no match | `report_unavailable` | `novel_unsupported` | null |",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_plan_requires_statistical_reproducibility_and_manifest_injection_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        .replace(
            "Routing-quality promotion uses one-sided simultaneous 95% lower confidence",
            "Routing-quality promotion uses point estimates",
        )
        .replace(
            "ordinary-chat false-block posture at or below 2%",
            "ordinary-chat false blocks are reported",
        )
        .replace(
            "both 50 ms and 5%",
            "a statistically material amount",
        )
        .replace(
            "samples are exploratory only and\n"
            "cannot satisfy TAW-08 acceptance",
            "samples can satisfy TAW-08 acceptance",
        )
        .replace(
            "Treat every hydrated manifest as untrusted model data",
            "Treat imported manifests as ordinary prompt context",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


@pytest.mark.parametrize(
    "required_fragment",
    (
        "unsupported-request false-support at or below 2%",
        "The unsupported-request false-support numerator is",
        "Its denominator is every adjudicated\n"
        "unsupported request evaluated in the healthy, missing, corrupt, stale, and\n"
        "over-budget catalog states",
        "no invented-capability, no-match, policy-denied, or\n"
        "degraded-catalog case may be dropped",
        "A policy or\n"
        "safety denial expressed as `blocked_authority` or `blocked_unsafe` with\n"
        "`familiar_authority_blocked`",
        "`blocked_capability_evidence`/`capability_evidence_unavailable`, are correct\n"
        "non-support outcomes",
        "at or below 2% overall,\n"
        "in every predeclared unsupported-request category, and separately in every\n"
        "healthy or degraded catalog state",
        "zero unsafe authority decisions with its one-sided 95% upper bound\n"
        "below 1%",
        "candidate-error disagreement at or below 5% after every disagreement is\n"
        "adjudicated, with its one-sided simultaneous 95% upper bound at or below 5%",
        "canonical proposal-graph fingerprint\n"
        "over the stable capability ID, operation ID, effect classification,\n"
        "contract/schema fingerprints, exact approval-scope binding, ordered step refs",
        "proposal ref, or canonical proposal-graph fingerprint differs",
        "unsafe authority broadening: zero",
        "fabricated availability or successful execution claims: zero",
        "raw sensitive content in durable routing evidence: zero",
    ),
)
def test_plan_requires_shadow_graph_unsupported_and_zero_tolerance_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required_fragment: str,
) -> None:
    plan = tmp_path / "plan.md"
    text = verifier.PLAN.read_text(encoding="utf-8")
    assert required_fragment in text
    plan.write_text(
        text.replace(required_fragment, "removed-required-review-gate", 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


@pytest.mark.parametrize("required", verifier.ZERO_TOLERANCE_LINES)
@pytest.mark.parametrize("preserve_original", (False, True))
def test_zero_tolerance_gate_rejects_negation_or_contradiction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required: str,
    preserve_original: bool,
) -> None:
    plan = tmp_path / "plan.md"
    contradiction = required.removeprefix("- ").removesuffix(";") + " is not required;"
    replacement = required + "\n" + contradiction if preserve_original else contradiction
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            required, replacement, 1
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="zero-tolerance gate is invalid"):
        verifier.verify()


def test_optional_control_center_requires_frontend_acceptance_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    required = (
        "If the optional Control Center surface is added, require focused frontend\n"
        "  tests and updated product-language expectations as conditional acceptance"
    )
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            required, "Optional Control Center work needs no extra evidence", 1
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_plan_requires_exact_applicable_capability_recall_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        .replace(
            "Applicable-capability recall is micro-recall at the bounded Tier 1 shortlist",
            "Applicable-capability recall is reported",
        )
        .replace(
            "zero-result discovery contributes zero retrieved refs",
            "zero-result discovery may be excluded",
        )
        .replace(
            "direct-chat false-positive-selection numerator",
            "direct-chat false-positive selection is reported",
        )
        .replace(
            "direct-chat false-positive tool selection at or below 2% overall",
            "direct-chat false-positive tool selection is reported overall",
        )
        .replace(
            "This false-positive-selection gate applies independently\n"
            "  to the overall, healthy, missing, corrupt, stale, and over-budget catalog\n"
            "  populations; none of those six rates may be pooled or omitted",
            "False-positive selection is reported for the combined population",
        )
        .replace(
            "all twelve reported\n  selection/block rates",
            "all reported selection/block rates",
        )
        .replace(
            "Final route/proposal exact-match is case-level",
            "Final route/proposal exact-match is reported",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


def test_structured_authority_boundary_cannot_enable_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["authority_boundary"]["runtime_model_or_provider_calls"] = True
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="enables authority"):
        verifier.verify()


def test_pre_goat_insertion_is_bound_to_exact_manifest_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["pre_goat_insertion"]["before_item_id"] = (
        "governed-self-improvement"
    )
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="pre-Goat insertion is invalid"):
        verifier.verify()


def test_missing_file_error_uses_repository_safe_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "operator-name" / "missing.md"
    monkeypatch.setattr(verifier, "PLAN", missing)

    with pytest.raises(RuntimeError) as raised:
        verifier.verify()

    assert str(tmp_path) not in str(raised.value)
    assert "required-ref:outside-repository" in str(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__ is True


def test_invalid_utf8_error_uses_repository_safe_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corrupt = tmp_path / "operator-name" / "plan.md"
    corrupt.parent.mkdir()
    corrupt.write_bytes(b"\xff")
    monkeypatch.setattr(verifier, "PLAN", corrupt)

    with pytest.raises(RuntimeError) as raised:
        verifier.verify()

    assert str(tmp_path) not in str(raised.value)
    assert "required-ref:outside-repository" in str(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__ is True


def test_remaining_queue_title_is_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    payload = verifier._read_manifest()
    payload["items"][0]["title"] = "A different title"
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(verifier, "MANIFEST", manifest)

    with pytest.raises(RuntimeError, match="immutable sequence is invalid"):
        verifier.verify()


def test_remaining_queue_excludes_completed_queue_01_and_02() -> None:
    payload = verifier._read_manifest()
    item_ids = [item["item_id"] for item in payload["items"]]

    assert item_ids[0] == "queue-03-hermes-openclaw-parity"
    assert "queue-01-governed-browser-external-actions" not in item_ids
    assert "queue-02-browser-external-action-hardening" not in item_ids
