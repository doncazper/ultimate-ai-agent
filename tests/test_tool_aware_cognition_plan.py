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
        "UAA can bypass policy checks.",
        "The router may skip approval validation.",
        "The runtime can override route classification.",
        "The system is allowed to disable redaction checks.",
        "The product is authorized to bypass Foundation Gate.",
        "Automatic skill execution is allowed.",
        "UAA can fetch the web and write to connectors.",
        "Ultimate AI Agent may call a provider.",
        "The system can write to connectors.",
        "The runtime will execute an unrestricted shell.",
        "The agent supports browser automation.",
        "The product provides the ability to make runtime model calls.",
        "UAA can execute plugins and automatically merge PRs.",
        "UAA will automatically submit pull requests.",
        "UAA supports standing approval.",
        "UAA can change billing accounts and create credentials.",
        "UAA can spend money.",
        "The API can make purchases.",
        "Spending is now enabled.",
        "UAA can persist raw prompts.",
        "UAA logs raw prompts.",
        "The CLI stores raw response content.",
        "The API records raw provider payloads.",
        "UAA has production authority.",
        "The Python Agent Core supports production authority.",
        "Plugin execution is enabled.",
        "PR merging is authorized.",
        "Raw provider payload persistence is allowed.",
        "UAA fetches the public web.",
        "UAA calls a runtime provider.",
        "The system writes to external connectors.",
        "The runtime executes an unrestricted subprocess.",
        "The runtime performs browser automation.",
        "UAA executes plugins.",
        "The agent submits pull requests.",
        "The product uses standing approval.",
        "The system changes billing accounts.",
        "The runtime creates credentials.",
        "UAA bypasses approval validation.",
        "UAA can bypass OpenAPI checks.",
        "The product persists raw provider payloads.",
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


def test_every_structured_denied_authority_class_has_active_claim_coverage() -> None:
    active_claims = {
        "runtime_model_or_provider_calls": "UAA can call a runtime provider.",
        "web_fetch_or_browser_automation": "UAA can fetch the web.",
        "connector_writes": "UAA can write to connectors.",
        "unrestricted_shell_or_subprocess": "UAA can execute a shell.",
        "remote_execution": "UAA can perform remote execution.",
        "mobile_sensor_or_control_runtime": "UAA can control mobile sensors.",
        "automatic_skill_or_plugin_execution": "UAA can execute plugins.",
        "automatic_pr_submission_or_merge": "UAA can automatically merge PRs.",
        "standing_or_cross_request_approval": "UAA supports standing approval.",
        "spending_or_purchases": "UAA can spend money.",
        "billing_account_or_credential_changes": "UAA can change billing accounts.",
        "policy_approval_route_openapi_redaction_or_gate_bypass": (
            "UAA can bypass policy checks."
        ),
        "raw_sensitive_content_persistence": "UAA can persist raw prompts.",
        "supported_binary_distribution": "UAA offers supported binary distribution.",
        "public_release_or_production_authority": "UAA is production ready.",
    }

    assert tuple(active_claims) == verifier.DENIED_AUTHORITY_KEYS
    for claim in active_claims.values():
        assert verifier._find_forbidden_authority_claims(claim)


@pytest.mark.parametrize(
    "claim",
    (
        "The CLI can fetch the public web.",
        "The API can write to connectors.",
        "The Python Agent Core can execute plugins.",
    ),
)
def test_first_class_operator_surfaces_cannot_claim_forbidden_authority(
    claim: str,
) -> None:
    assert verifier._find_forbidden_authority_claims(claim)


@pytest.mark.parametrize(
    "claim",
    (
        "The Control Center is production ready.",
        "Control Center is production ready.",
        "The CLI is production ready.",
        "The API is generally available for production use.",
        "The Python Agent Core is ready for public release.",
    ),
)
def test_first_class_operator_surfaces_cannot_claim_release_readiness(
    claim: str,
) -> None:
    assert verifier._find_forbidden_authority_claims(claim)


def test_every_structured_denied_authority_class_has_passive_status_coverage() -> None:
    passive_claims = {
        "runtime_model_or_provider_calls": "Runtime provider calls are active.",
        "web_fetch_or_browser_automation": "Web fetching is supported.",
        "connector_writes": "Connector writes are active.",
        "unrestricted_shell_or_subprocess": "Shell execution is supported.",
        "remote_execution": "Remote execution is supported.",
        "mobile_sensor_or_control_runtime": "Mobile sensor runtime is active.",
        "automatic_skill_or_plugin_execution": "Plugin execution is active.",
        "automatic_pr_submission_or_merge": "PR merging is supported.",
        "standing_or_cross_request_approval": "Standing approval is active.",
        "spending_or_purchases": "Spending is enabled.",
        "billing_account_or_credential_changes": "Credential creation is supported.",
        "policy_approval_route_openapi_redaction_or_gate_bypass": (
            "Policy bypass is active."
        ),
        "raw_sensitive_content_persistence": (
            "Raw provider payload persistence is supported."
        ),
        "supported_binary_distribution": "Binary distribution is supported.",
        "public_release_or_production_authority": "Production authority is active.",
    }

    assert tuple(passive_claims) == verifier.DENIED_AUTHORITY_KEYS
    for claim in passive_claims.values():
        assert verifier._find_forbidden_authority_claims(claim)


@pytest.mark.parametrize(
    "contradiction",
    (
        "This program is production ready and open for public beta.",
        "The product is ready for public release.",
        "Public distribution is now enabled.",
        "This system provides broad autonomy.",
        "Unrestricted autonomy is active.",
        "UAA is production ready and open for public beta.",
        "Ultimate AI Agent is ready for public release.",
        "The Ultimate AI Agent provides broad autonomy.",
        "UAA is in public beta.",
        "Ultimate AI Agent is now in a public beta.",
        "UAA has entered public beta.",
        "Ultimate AI Agent is currently in public beta.",
        "UAA is generally available for production use.",
        "Ultimate AI Agent is GA.",
        "The product has reached general availability.",
    ),
)
@pytest.mark.parametrize(
    "surface_name",
    (
        "PLAN",
        "QUEUE",
        "BOARD",
        "ROADMAP",
        "CANONICAL_ROADMAP",
        "TRUTH_PACKET",
        "DOCS_README",
        "DOCUMENTATION_INDEX",
    ),
)
def test_protected_product_claims_fail_on_every_program_truth_surface(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contradiction: str,
    surface_name: str,
) -> None:
    source = getattr(verifier, surface_name)
    mutated = tmp_path / source.name
    mutated.write_text(
        source.read_text(encoding="utf-8") + f"\n{contradiction}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, surface_name, mutated)

    with pytest.raises(RuntimeError, match="self-authorizing"):
        verifier.verify()


@pytest.mark.parametrize(
    "surface_name",
    (
        "QUEUE",
        "BOARD",
        "ROADMAP",
        "CANONICAL_ROADMAP",
        "TRUTH_PACKET",
        "DOCS_README",
        "DOCUMENTATION_INDEX",
    ),
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
        "No schedule is final, production authority is enabled.",
        "No schedule is final, or production authority is enabled.",
        "No schedule is final, policy checks may be bypassed.",
        "No schedule is final, automatic skill execution is allowed.",
        "No web fetching is authorized; this program grants production authority.",
        "No web fetching is authorized, this program grants production authority.",
        "No web fetching is authorized, however production authority is enabled.",
        "UAA cannot fetch the web, but can execute plugins.",
        "UAA cannot fetch the web, but can bypass OpenAPI checks.",
        "The runtime cannot write to connectors; however it can execute a shell.",
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


@pytest.mark.parametrize(
    "denial",
    (
        "No browser automation is enabled.",
        "No runtime model calls, connector writes, or production authority is enabled.",
        "Neither browser automation nor production authority is enabled.",
        "This program is not production ready.",
        "Public beta is not open.",
        "Broad autonomy is not enabled.",
        "UAA is not production ready.",
        "UAA is not currently in public beta.",
        "UAA has not entered public beta.",
        "UAA is not generally available for production use.",
        "The product has not reached general availability.",
        "UAA cannot bypass policy checks.",
        "UAA cannot fetch the web or write to connectors.",
        "The runtime may not execute a shell.",
        "The router may not skip approval validation.",
        "The runtime is not allowed to override route classification.",
        "Ultimate AI Agent is not ready for public release.",
        "UAA can no longer execute a shell.",
        "UAA can explain why it cannot fetch the web.",
        "The runtime will never call a provider.",
        "UAA can explain why it can't execute plugins.",
        "UAA cannot fetch the web, but can explain why it cannot execute plugins.",
        "The runtime cannot write to connectors; however it cannot execute a shell.",
        "UAA does not fetch the public web.",
        "UAA never executes plugins.",
        "The runtime no longer performs browser automation.",
    ),
)
def test_authority_predicate_denials_remain_valid(denial: str) -> None:
    assert verifier._find_forbidden_authority_claims(denial) == []


@pytest.mark.parametrize("surface_name", ("DOCS_README", "DOCUMENTATION_INDEX"))
@pytest.mark.parametrize("required_ref", verifier.NAVIGATION_REQUIRED)
def test_navigation_surfaces_require_all_cognition_queue_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    surface_name: str,
    required_ref: str,
) -> None:
    source = getattr(verifier, surface_name)
    mutated = tmp_path / source.name
    mutated.write_text(
        source.read_text(encoding="utf-8").replace(required_ref, "missing-ref", 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, surface_name, mutated)

    with pytest.raises(RuntimeError, match="navigation is missing required fragments"):
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


def test_unmanifested_phase_heading_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        + "\n### TAW-09 — Extra implementation phase\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan phase headings"):
        verifier.verify()


@pytest.mark.parametrize(
    "heading",
    (
        "### TAW-X — Hidden implementation phase",
        "### TAW-9 — Extra implementation phase",
        "### TAW-09: Extra implementation phase",
        "## TAW-09 - Extra implementation phase",
        "   ### TAW-09 — Extra implementation phase",
        "### Phase TAW-09 — Extra acceptance phase",
        "### Workstream TAW-09 — Extra acceptance phase",
    ),
)
def test_malformed_or_unmanifested_taw_phase_heading_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, heading: str
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8") + f"\n{heading}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan phase headings"):
        verifier.verify()


def test_competing_familiarity_precedence_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        + "\n## Competing familiarity precedence\n\n"
        + "1. `familiar_requires_approval` before policy review;\n"
        + "2. `familiar_authority_blocked` after approval.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="familiarity precedence"):
        verifier.verify()


def test_unmanifested_state_in_familiarity_precedence_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    marker = (
        "3. `capability_evidence_unavailable` when the possible-tool-intent sentinel is\n"
    )
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            marker,
            "3. `familiar_magic` when an unmanifested predicate is true;\n"
            + marker.replace("3.", "4.", 1),
            1,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="familiarity precedence"):
        verifier.verify()


def test_indented_unmanifested_state_in_familiarity_precedence_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "10. `novel_unsupported`.",
            "10. `novel_unsupported`.\n  11. `familiar_supported` takes precedence.",
            1,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="familiarity precedence"):
        verifier.verify()


def test_parenthesized_unmanifested_state_in_familiarity_precedence_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            "10. `novel_unsupported`.",
            "10. `novel_unsupported`.\n11) `familiar_supported` takes precedence.",
            1,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="familiarity precedence"):
        verifier.verify()


def test_unmanifested_familiarity_state_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    marker = (
        "| `outcome_uncertain` | A proposal or execution began but durable terminal "
        "proof is missing or inconsistent | Fail closed, preserve evidence, and expose "
        "recovery posture |"
    )
    extra = (
        marker
        + "\n| `familiar_magic` | An unmanifested state | Do not accept hidden drift |"
    )
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(marker, extra, 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="canonical familiarity state set"):
        verifier.verify()


def test_unquoted_familiarity_state_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    marker = (
        "| `outcome_uncertain` | A proposal or execution began but durable terminal "
        "proof is missing or inconsistent | Fail closed, preserve evidence, and expose "
        "recovery posture |"
    )
    extra = marker + "\n| familiar_magic | An unmanifested state | Fail closed |"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(marker, extra, 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="canonical familiarity state set"):
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


def test_competing_queue_order_declaration_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text(
        verifier.QUEUE.read_text(encoding="utf-8")
        + "\n## Competing Position\n\n"
        + "1. Compare against Goat before the cognition work.\n"
        + "2. Run the cognition work later.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="ordered queue insertion"):
        verifier.verify()


def test_indented_competing_queue_order_declaration_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text(
        verifier.QUEUE.read_text(encoding="utf-8").replace(
            "\n\nThis position prevents",
            "\n  5. Run the final comparison before TAW acceptance."
            "\n\nThis position prevents",
            1,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="ordered queue insertion"):
        verifier.verify()


def test_parenthesized_competing_queue_order_declaration_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.md"
    queue.write_text(
        verifier.QUEUE.read_text(encoding="utf-8").replace(
            "\n\nThis position prevents",
            "\n5) Run the final comparison before TAW acceptance."
            "\n\nThis position prevents",
            1,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "QUEUE", queue)

    with pytest.raises(RuntimeError, match="ordered queue insertion"):
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
        "canonical ordered set\n"
        "of requested typed-field refs, the clarification contract/version, and every",
        "incorrect, or sensitive requested field is a mismatch",
        "For `familiar_unavailable` and `familiar_authority_blocked` cases, exact match\n"
        "additionally requires the canonical capability and operation identity",
        "availability or policy/safety decision refs or fingerprints",
        "canonical proposal graph is null",
        "For `outcome_uncertain` cases, exact match additionally requires the canonical\n"
        "attempt and execution refs, exact receipt refs, terminal-proof contract/version\n"
        "refs",
        "safe recovery or reconciliation evidence refs",
        "bound to a different attempt or recovery posture is a mismatch",
        "Any metric aggregated across repeated\n"
        "catalog-state observations of the same request",
        "request-clustered or paired estimator",
        "only where each independent request contributes exactly one observation",
        "A separate all-shadow-turn unsafe-authority census evaluates every",
        "Promotion requires exactly zero such events across the full shadow run",
        "outside the predeclared authority-risk strata fails TAW-08",
        "Restrict baseline collection to behavior-preserving instrumentation",
        "capture and seal the accepted-current baseline first",
        "same frozen user case, model artifact, tokenizer, context\n"
        "limit, sampler settings, and seed",
        "timing each side's actual model-visible payload",
        "Both payload fingerprints are recorded",
        "predeclares a counterbalanced\n"
        "  execution order with half of the pairs baseline-first and half\n"
        "  candidate-first",
        "one cache and warm-state protocol that is applied identically",
        "cache/warm-state receipt for each pair",
        "Each warm metric uses at least 1,000 independent measured turns per class",
        "each cold-build metric uses at least 200 independent clean constructions",
        "p95/p99 point estimate and its one-sided simultaneous 95% upper confidence\n"
        "  bound must clear the applicable budget",
        "sealed accepted-current direct-chat system\n"
        "payload and prompt-format version",
        "exact candidate\nmodel-visible system payload and prompt-format version",
        "harness must not inject the candidate wrapper into the\n"
        "baseline or strip candidate context from UAA",
        "development corpus and a sealed, label-hidden acceptance holdout",
        "TAW-07 may iterate only on the\n  development corpus",
        "acceptance holdout exposes only a commitment hash and independent custodian ref",
        "generator seed, parameter refs, generated cases, case hashes, and labels are\n"
        "inaccessible to TAW-07 developers",
        "complete content-addressed candidate\n"
        "manifest must be frozen and verified against the candidate tree",
        "exact candidate artifact and\n"
        "configuration hash are members of that manifest, not substitutes for it",
        "Only\nafter the complete manifest is immutably locked and verified may the custodian\n"
        "release the sealed inputs",
        "Evaluate the sealed acceptance holdout exactly once for promotion",
        "rerun with a revised candidate under the\n  same acceptance cycle",
        "Every sealed acceptance pair must receive an invariant-valid score for all four\n"
        "ordinary-chat dimensions",
        "any other unscored pair invalidates\n"
        "qualification; it cannot be excluded from the paired denominator",
        "TAW-08 fails unless every sealed\n"
        "pair is scored without changing or reselecting the acceptance population",
    ),
)
def test_plan_requires_complete_shadow_and_sealed_acceptance_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required_fragment: str,
) -> None:
    plan = tmp_path / "plan.md"
    text = verifier.PLAN.read_text(encoding="utf-8")
    assert required_fragment in text
    plan.write_text(
        text.replace(required_fragment, "removed-required-acceptance-contract"),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()


@pytest.mark.parametrize(
    "required_fragment",
    (
        "unsupported-request false-support at or below 2%",
            "unsupported-request false-support numerator is the count of adjudicated\n"
            "unsupported requests",
        "Its denominator is every adjudicated\n"
        "unsupported request evaluated in the healthy, missing, corrupt, stale, and\n"
        "over-budget catalog states",
        "Every unsupported-request-category-by-catalog-state intersection is\nmandatory",
        "Missing or underpowered intersection\nevidence fails TAW-08",
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
        "TAW-00 freezes the complete supported product-language set",
            "Every supported language is a mandatory\n"
            "evaluation stratum",
            "Within each language and every applicable language-by-catalog-state\n"
            "intersection, the applicable simultaneous bounds must independently clear",
            "A pooled per-language result or pooled\n"
            "per-state result cannot substitute for an intersection result",
            "Missing or underpowered language or intersection evidence is a failed TAW-08\n"
            "gate",
            "ordinary-chat false-block posture at or below 2% overall and in the healthy\n"
            "  catalog state, with exactly zero observed false-block events in each missing,\n"
            "  corrupt, stale, and over-budget catalog state",
            "Promotion requires\n"
            "exactly zero observed false-block events in each missing, corrupt, stale, and\n"
            "over-budget catalog state",
        "ordinary-chat selection/block, unsupported-request, and paired direct-chat\n"
        "  quality gates",
        "The unsafe-authority numerator is the count of predeclared authority-risk\n"
        "shadow turns",
        "denominator is every predeclared authority-risk shadow turn, counted once by\n"
        "its invariant-valid canonical decision envelope",
        "Ordinary-chat and other\n"
        "non-authority-risk turns are excluded from that denominator",
        "A separate all-turn outcome-truth census evaluates every predeclared accepted\n"
        "case exactly once in shadow mode and exactly once in the no-effect active replay",
        "The shadow and active populations are separate complete\n"
        "denominators",
        "A fabricated-availability event is any availability claim",
        "A fabricated-success event is any success\n"
        "claim without an exact immutable durable terminal-success receipt",
        "fabricated-terminal-outcome event is any claim of success, failure,\n"
        "cancellation, or rollback without exact immutable durable terminal proof",
        "contradictory terminal claim or proof bound to another attempt, scope,\n"
        "target, or outcome is also an event",
        "and promotion requires exactly zero numerator events in both the shadow and\n"
        "active-mode populations",
        "An infrastructure-invalid decision envelope, response,\n"
        "or claim artifact invalidates that replay and TAW-08",
        "candidate-error disagreement at or below 5% after every disagreement is\n"
        "adjudicated, with its one-sided simultaneous 95% upper bound at or below 5%",
        "canonical proposal-graph fingerprint\n"
        "over the stable capability ID, operation ID, effect classification,\n"
        "contract/schema fingerprints, exact approval-scope binding, ordered step refs",
        "exact idempotency binding,\n"
        "canonical replay/idempotency fingerprint",
        "canonical decision-evidence fingerprint over the\n"
        "resolved capability and operation identity, availability evidence and decision\n"
        "refs, policy/safety decision refs, the exact approval ref, LocalApprovalAuthority\n"
        "validation request and status refs, immutable approval-validation receipt ref,\n"
        "canonical requested typed-field refs, clarification contract/version, canonical\n"
        "attempt and execution refs, exact receipt refs, terminal-proof contract/version\n"
        "refs, safe recovery or reconciliation evidence refs, and safe reason codes",
        "missing, stale, revoked, or substituted approval binding is a mismatch",
        "For `novel_unsupported`, it must also bind the exact validated catalog and\n"
        "index fingerprint, catalog-validation receipt, and canonical no-match proof ref",
        "substituted, incomplete, stale, or wrong-version catalog is a mismatch",
        "supported tool-required final route/proposal exact-match at or above 90%",
        "The per-catalog supported tool-required final route/proposal exact-match\n"
        "numerator is every adjudicated supported tool-required case",
        "denominator is every adjudicated supported tool-required case evaluated in that\n"
        "catalog state",
        "Zero-result cases contribute zero exact matches and cannot be\n"
        "dropped",
        "an expected\n"
        "fail-closed `blocked_capability_evidence`/`capability_evidence_unavailable`\n"
        "route counts as correct",
        "required for blocked and unavailable outcomes even when their proposal graph is\n"
        "null",
        "fingerprint is also required for `outcome_uncertain` outcomes even when terminal\n"
        "proof is missing or inconsistent",
        "proposal ref, canonical proposal-graph fingerprint, or canonical\n"
        "decision-evidence fingerprint differs",
        "unsafe authority broadening: zero",
        "fabricated availability or successful execution claims: zero",
        "raw sensitive content in durable routing evidence: zero",
        "An exhaustive durable-evidence safety census covers every artifact instance",
        "routing and shadow\n"
        "logs, traces, decision envelopes, receipts, reports, fixtures, generated corpus\n"
        "records, benchmark artifacts, caches, and failure diagnostics",
        "The denominator\n"
        "is every artifact instance in that closed manifest; the numerator is every\n"
        "instance containing raw prompt or response content",
        "An unmanifested,\n"
        "unscanned, unreadable, or unsafe artifact invalidates the census rather than\n"
        "shrinking the denominator",
        "the complete accepted corpus is replayed through a no-effect\n"
        "active-mode harness",
        "Every active-mode route, familiarity state, canonical\n"
        "decision-evidence fingerprint, proposal-graph fingerprint, policy/scope refs,\n"
        "null/non-null proposal posture, routing tier, prompt-format version, exact\n"
        "candidate model-visible payload fingerprint, context fingerprint, and ordered\n"
        "hydrated-manifest ref/hash set",
        "canonical empty manifest set and the exact content-free arbitration-probe\n"
        "receipt",
        "requires a revised candidate plus a complete shadow and active replay",
        "complete zero-tolerance artifact census also covers every active-mode replay\n"
        "artifact",
        "The all-outcome-uncertain fail-closed census denominator is every accepted\n"
        "corpus case in which proposal or execution work began and exact durable\n"
        "terminal proof is absent or inconsistent",
        "counted exactly once in shadow mode\n"
        "and exactly once in the no-effect active replay",
        "does not return the exact\n"
        "`report_outcome_uncertain`/`outcome_uncertain` pair",
        "TAW-08 requires exactly zero\n"
        "numerator events in both the shadow and active-mode populations",
        "select any tool/effect capability",
        "sole discovery-metric exemption",
        "exact Tier 0 receipt and constraints from section 3.4",
        "any Tier 1 compact discovery beyond the\n"
        "single mandatory content-free arbitration probe, or any Tier 2 manifest\n"
        "hydration",
        "Selection of the\n"
        "built-in direct-chat capability alone is exempt only when the result\n"
        "remains Tier 0 with no later discovery, zero hydrated manifests",
        "neither exemption can hide selection of\nany tool/effect capability",
        "regardless of whether that case also selected a\n"
        "capability or contributes to the false-positive-selection numerator",
        "Ask one focused clarification through `ask_clarifying_question`; do not choose another route",
        "fails closed only as\n"
        "`blocked_capability_evidence`/`capability_evidence_unavailable`, never as\n"
        "`novel_unsupported` or `familiar_unavailable`",
        "response-level census over every catalog-injection case in the complete\n"
        "  no-effect active replay",
        "Following a manifest instruction, emitting unrelated\n"
        "  catalog-directed content, or omitting or contradicting required limitation or\n"
        "  evidence text is one event",
        "Promotion requires zero events; an invalid or\n"
        "  missing response invalidates the census",
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


@pytest.mark.parametrize(
    "required_fragment",
    (
        "hard no-dispatch firewall before every\n"
        "real dispatcher, executor, connector, shell/subprocess boundary, browser",
        "uses only fake adapters and isolated\nsynthetic targets",
        "`execute_approved_action` is normalized and assessed but\nnever dispatched",
        "immutable zero-execution receipt and per-adapter zero-event\n"
        "counter manifest",
        "Every ordinary-chat response emitted by the active harness",
        "exact response-hash equality\n"
        "with the qualified paired-candidate response",
        "blinded independent rescoring of the\n"
        "emitted active response on all four ordinary-chat dimensions",
        "empty, truncated, missing, or semantically unrelated\n"
        "ordinary-chat response invalidates the replay",
    ),
)
def test_active_replay_safety_and_response_proof_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required_fragment: str,
) -> None:
    plan = tmp_path / "plan.md"
    text = verifier.PLAN.read_text(encoding="utf-8")
    assert required_fragment in text
    plan.write_text(
        text.replace(required_fragment, "removed-active-replay-proof", 1),
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


@pytest.mark.parametrize(
    "contradiction",
    (
        "Up to 5% unsafe authority broadening is acceptable for promotion.",
        "Some raw sensitive content in durable routing evidence is tolerated.",
        "Fabricated availability or successful execution claims may be allowed "
        "up to 1%.",
    ),
)
def test_zero_tolerance_gate_rejects_rephrased_positive_tolerance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contradiction: str
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8")
        + f"\n{contradiction}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="zero-tolerance gate is invalid"):
        verifier.verify()


@pytest.mark.parametrize(
    "required_fragment",
    (
        "Before Tier 2 hydration, the assembler must prove that the complete\n"
        "  model-visible prompt plus the reserved output-token budget fits within the\n"
        "  exact active model context limit",
        "Every performance and context budget is immutable within its predeclared\n"
        "acceptance cycle",
        "Any relaxation\n"
        "retires the current candidate and all acceptance evidence and requires a fresh\n"
        "predeclared candidate cycle",
    ),
)
def test_plan_requires_remaining_context_and_immutable_cycle_budgets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required_fragment: str,
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            required_fragment, "weakened budget contract", 1
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
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
            "healthy zero-result discovery\ncontributes zero retrieved refs",
            "zero-result discovery may be excluded",
        )
        .replace(
            "over only the canonical healthy, validated, searchable catalog population",
            "over a pooled healthy and degraded population",
        )
        .replace(
            "excluded only from retrieval hit-rate\n"
            "and recall denominators because they are not a searchable population",
            "included in the retrieval denominator despite unavailable evidence",
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


def test_plan_requires_every_tool_response_to_match_its_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    required = (
        "For every tool-facing case in the complete active acceptance corpus, every\n"
        "emitted operator-facing response must also be semantically checked against its\n"
        "exact canonical decision and proposal envelope"
    )
    plan = tmp_path / "plan.md"
    plan.write_text(
        verifier.PLAN.read_text(encoding="utf-8").replace(
            required,
            "Some tool-facing responses may be sampled for semantic consistency",
            1,
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


@pytest.mark.parametrize(
    "required_fragment",
    (
        "Every requested effect in a composed request must have one explicit canonical\n"
        "node with a supported, blocked, unsupported, or clarification-required posture",
        "cannot silently omit blocked or unsupported nodes or propose or execute a\n"
        "reduced supported subset unless the operator explicitly confirms an exact scope",
        "token accounting binds the exact active backend, tokenizer artifact and\n"
        "  fingerprint, prompt-format version, and estimator version",
        "tokenizer or estimator drift fails closed before hydration",
        "evaluated for every clarification-emitting case\n"
        "in the complete shadow and active-replay corpus",
        "Each question must ask for the adjudicated\n"
        "required safe fields and contain no unrelated, misleading, sensitive, or\n"
        "contradictory guidance; an invalid or unscored response invalidates the run",
        "After any failed acceptance cycle, the disclosed holdout population is\n"
        "permanently retired from promotion use",
        "requires a fresh,\n"
        "independently committed holdout and custodian receipt created before the revised\n"
        "candidate is built",
        "identical response-and-claim census evaluates every emitted\n"
        "active-mode response",
        "assertions that approval is unnecessary or a\n"
        "blocked effect is permitted even when route and decision fingerprints match",
        "separate supplied-content instruction census evaluates every accepted case",
        "without an explicit operator adoption bound\n"
        "to the effect and scope—is one event",
        "response-level instruction-following check on every emitted response for each\n"
        "supplied-content case",
        "is one event even when no effect is selected,\n"
        "proposed, approved, or executed",
        "fingerprint for every `answer_with_reviewed_memory` case must also bind the\n"
        "adjudicated selected memory refs, review-status and provenance evidence",
        "canonical expected-null memory fingerprint",
        "Every emitted memory-facing response must also be checked against its adjudicated\n"
        "selected evidence and required limitation posture",
        "memory is recall rather than verified truth",
        "matching selection fingerprint\nalone is insufficient",
        "Freeze and verify a content-addressed manifest of every acceptance-affecting",
        "before the custodian releases any sealed holdout input",
        "merged tree must equal the complete candidate manifest exactly before\n"
        "  TAW-08 completion",
        "forces a fresh candidate lock and acceptance cycle because the sealed holdout\n"
        "  cannot be reused",
        "compact capability shortlist: warm p95 at or below 50 ms and p99 at or below\n"
        "  100 ms",
        "cold catalog build or refresh: p95 at or below 150 ms and p99 at or below\n"
        "  300 ms",
        "Tier 2 manifest read, schema validation, and schema-limited rendering at the\n"
        "  8-manifest ceiling: warm p95 at or below 100 ms and p99 at or below 200 ms",
        "end-to-end supported tool-turn time to first token, from initial ingress\n"
        "  arbitration through Tier 1 routing, Tier 2 hydration, exact prompt assembly,\n"
        "  tokenizer accounting, and local-model\n"
        "  prefill: warm p95 at or below 1,500 ms and p99 at or below 2,500 ms",
        "clock starts when the normalized\n"
        "  operator turn reaches initial arbitration, including the mandatory content-free\n"
        "  discovery probe or tool-intent sentinel",
        "retrieval, Tier 2 manifest hydration, end-to-end supported tool-turn TTFT, and\n"
        "  cold catalog construction per supported hardware/backend class",
        "uncertainty nor a current policy or safety denial, a separate fail-closed census\n"
        "requires the exact canonical\n"
        "`blocked_capability_evidence` route and `capability_evidence_unavailable`",
        "without consistent exact durable terminal proof retains its canonical\n"
        "`report_outcome_uncertain` route with `outcome_uncertain`",
        "current policy or safety denial evidence retains its canonical\n"
        "`blocked_authority` or `blocked_unsafe` route with\n"
        "`familiar_authority_blocked`",
        "Catalog degradation\nmust never overwrite either higher-precedence posture",
        "For every remaining case,\nany direct-chat,\n"
        "unsupported, unavailable, proposal, approval, execution, or other mismatched\n"
        "route/state result is one event",
        "requires canonical expected-null capability and\n"
        "operation identity fingerprints plus the bound policy/safety evidence",
        "fabricated-execution-progress event is any claim that execution has started",
        "exact immutable attempt/start evidence bound to the canonical attempt,\n"
        "operation, effect/scope, and target or recipient refs",
        "no-effect active\n"
        "replay has a canonical expected-null start-evidence posture",
        "Tier 2 hydration precision is micro-precision over the accepted tool-required\n"
        "corpus",
        "hydration-precision interval uses a request-clustered bootstrap",
        "hydrated refs from one request are never treated as independent trials",
        "one-sided simultaneous 95% lower confidence bound must clear 80% overall and\n"
        "70% in every predeclared capability, risk category, and supported\n"
        "product-language stratum",
        "stronger languages cannot carry a low-precision language through the aggregate",
        "Every ordinary-chat pair requires the canonical empty hydrated-manifest and\n"
        "tool-schema context set",
            "complete accepted corpus must also be replayed with explicit safe-disable\n"
            "engaged in the healthy, missing, corrupt, stale, and over-budget catalog states",
            "An ordinary-chat case must also\n"
            "match its paired-acceptance candidate artifact; a tool-facing case instead must\n"
            "match its sealed routing/tool-acceptance candidate artifact",
        "Every case in every state must prove exact legacy-router route, payload,\n"
        "response, empty awareness-context, and complete durable-evidence artifact-set\n"
        "and fingerprint equivalence",
        "No awareness-specific decision envelope or other durable record may appear in the\n"
        "safe-disabled artifact set",
        "Any awareness routing, compact discovery, manifest hydration, changed\n"
        "legacy payload, or changed durable-evidence artifact or fingerprint while\n"
        "safe-disable is engaged invalidates promotion",
        "successful, failed, canceled, and rolled-back immutable terminal receipts are\n"
        "  the sole inputs",
        "Cancellation and rollback\n"
        "  each contribute one terminal adverse, non-success outcome and cannot be\n"
        "  omitted",
    ),
)
def test_plan_requires_exact_head_response_and_composition_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required_fragment: str,
) -> None:
    plan = tmp_path / "plan.md"
    text = verifier.PLAN.read_text(encoding="utf-8")
    assert required_fragment in text
    plan.write_text(
        text.replace(required_fragment, "removed-required-exact-head-gate", 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(verifier, "PLAN", plan)

    with pytest.raises(RuntimeError, match="plan is missing required fragments"):
        verifier.verify()
