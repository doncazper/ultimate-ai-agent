#!/usr/bin/env python3
"""Verify the tool-aware cognition plan and ordered queue insertion."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "strategy" / "UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md"
QUEUE = ROOT / "docs" / "roadmap" / "UAA_TOOL_AWARE_COGNITION_QUEUE_INSERTION.md"
BOARD = ROOT / "docs" / "kanban" / "current_board.md"
ROADMAP = ROOT / "docs" / "roadmap" / "OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
CANONICAL_ROADMAP = ROOT / "docs" / "canonical" / "09_roadmap.md"
TRUTH_PACKET = ROOT / "docs" / "roadmap" / "PRODUCT_RELEASE_TRUTH_PACKET.md"
MANIFEST = ROOT / "docs" / "roadmap" / "UAA_REMAINING_QUEUE_MANIFEST.json"

PLAN_REQUIRED = (
    "This program extends the accepted Turn Contract Router",
    "The configured local model remains responsible for language understanding",
    "zero additional model calls to the direct-chat path",
    "`familiar_supported`",
    "`familiar_input_required`",
    "`familiar_unavailable`",
    "`familiar_requires_approval`",
    "`familiar_authority_blocked`",
    "`ambiguous`",
    "`novel_unsupported`",
    "`outcome_uncertain`",
    "approval cannot mint or broaden authority",
    "do not request an approval that cannot authorize it",
    "the current PolicyEngine or applicable",
    "`familiar_authority_blocked` when the current PolicyEngine or applicable\n"
    "   safety boundary denies the exact request",
    "Policy and safety denials are not approval-required outcomes",
    "override them or turn them into a proposal",
    "direct-chat false-positive tool selection at or below 2%",
    "recall of an applicable capability at or above 95%",
    "blind paired scoring on the accepted ordinary-chat corpus",
    "same frozen local model",
    "report point estimates plus 95% confidence intervals",
    "Human blind scoring with a versioned rubric is the default quality judge",
    "A model-as-judge call is neither implicitly authorized",
    "written to repository reports, receipts, test",
    "number of repeated paired samples",
    "cold catalog construction, and every refresh must be model- and",
    "content-free discovery probe over the cached compact catalog before a turn can",
    "paraphrases that do not match a",
    "`possible-tool-intent-sentinel:v1`",
    "`capability_evidence_unavailable`",
    "at most 8 candidate manifests as a non-overridable ceiling",
    "`min(4096, floor(model_context_tokens * 0.05))`",
    "top-3 capability hit rate at or above 80%",
    "top-3 capability hit-rate numerator",
    "simultaneous lower confidence bound",
    "one-sided familywise alpha of 0.05",
    "pinned synthetic-generator ref and version",
    "Shadow activation criteria are predeclared",
    "candidate-error disagreement at or below 5%",
    "The disagreement population `N` is every predeclared shadow turn",
    "`D = A + C`",
    "`C / N <= 0.05`",
    "`legacy-router-normalization:v1`",
    "exact receipt ref, attempt ref, contract version",
    "fail-closed precedence is mandatory",
    "TAW-00",
    "TAW-08",
    "final GoatCitadel comparison may start only after",
    "No raw conversation is added to a training or evaluation corpus automatically",
    "receipt- and attempt-keyed",
    "fully redacted transformation",
    "Those matches remain classification",
    "excluded only from proposal or execution",
    "evidence-only shadow mode",
    "explicit safe-disable boundary",
    "ordinary chat unavailable",
    "fails closed as unsupported or unavailable",
    "corrupt-index fallback",
    "PR count follows contract and risk seams rather than a fixed",
    "must remain isolated and cannot be hidden inside a delivery group",
)
QUEUE_REQUIRED = (
    "Run the final GoatCitadel comparison only after",
    "The local model remains UAA's language and reasoning engine",
    "The queue item is not complete when these documents merge",
    "Continue every already-authorized intervening queue item",
    "remaining Queue 03 parity phases",
    "governed self-improvement. Stop at the boundary immediately",
    "before the final GoatCitadel comparison",
    "UAA_REMAINING_QUEUE_MANIFEST.json",
)
BOARD_REQUIRED = (
    "Tool-Aware Cognition And Chat Quality",
    "before the final GoatCitadel comparison",
    "docs/strategy/UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md",
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
)
ROADMAP_REQUIRED = (
    "Ordered queue insertion: the Tool-Aware Cognition And Chat Quality program",
    "must reach its TAW-08 acceptance gate before",
    "does not replace the configured local model",
)
CANONICAL_ROADMAP_REQUIRED = (
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
    "TAW-00 through TAW-08",
    "completion evidence or runtime authority",
)
TRUTH_PACKET_REQUIRED = (
    "Planned comparison-order gate",
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
    "not shipped",
    "product evidence",
)
FORBIDDEN_PATTERNS = (
    r"\b(?:this plan|this program) authorizes? (?:new )?runtime model",
    r"\bruntime model calls? (?:are|is) (?:now )?authorized\b",
    r"\b(?:this plan|this program) grants? (?:browser|connector|shell|production) authority\b",
    r"\bpolicy (?:checks? )?(?:may|can) be bypassed\b",
    r"\bautomatic skill (?:activation|execution) is allowed\b",
)
AUTHORITY_DENIALS = (
    "## 12. Explicit Non-Goals",
    "- new runtime model/provider calls;",
    "- web fetching or browser automation;",
    "- connector writes;",
    "- unrestricted shell or subprocess execution;",
    "- automatic skill/plugin import or execution;",
    "- automatic PR submission or merging;",
    "- standing or cross-request approval;",
    "- billing/account changes or credential creation;",
    "- policy, approval, route, OpenAPI, redaction, or Foundation Gate bypass;",
    "- raw prompt, response, provider payload, or local-path persistence; or",
    "- public release, production authority, or claims of human-like",
)
PHASE_HEADINGS = (
    "### TAW-00 — Convergence ledger and evaluation baseline",
    "### TAW-01 — Capability evidence envelope",
    "### TAW-02 — Familiarity and uncertainty assessor",
    "### TAW-03 — Progressive capability retrieval",
    "### TAW-04 — Chat integration and clarification behavior",
    "### TAW-05 — Outcome evidence and governed improvement",
    "### TAW-06 — Operator diagnostics",
    "### TAW-07 — Quality, latency, and adversarial hardening",
    "### TAW-08 — Acceptance and GoatCitadel precondition",
)
QUEUE_ORDERED_STEPS = (
    "1. Finish the currently admitted PR or verification atomic unit",
    "2. Continue every already-authorized intervening queue item",
    "3. At that pre-Goat boundary, execute TAW-00 through TAW-08",
    "4. Run the final GoatCitadel comparison only after",
)
EXPECTED_QUEUE_ITEMS = (
    (
        1,
        "queue-01-governed-browser-external-actions",
        "Queue 01 — Governed browser external actions",
        "01_queue_01_governed_browser_external_actions.prompt.md",
        "968cab8c5a62ebb58ef22dd0a3ed3a111baa3160d346b5acefbe37e90d822e01",
    ),
    (
        2,
        "queue-02-browser-external-action-hardening",
        "Queue 02 — Browser external action hardening",
        "02_queue_02_browser_external_action_hardening.prompt.md",
        "b2f1cbf86d0762ce230183c44dda918a56b16bedd58a6a7377f8381ab6211078",
    ),
    (
        3,
        "queue-03-hermes-openclaw-parity",
        "Queue 03 — Hermes and OpenClaw parity",
        "03_queue_03_hermes_openclaw_parity.prompt.md",
        "c16cdbe70548b72d91f6f93861df87998aa24e21945238bf26004b5781ece93a",
    ),
    (
        4,
        "queue-04-delegated-mission-document-organization",
        "Queue 04 — Delegated mission and document organization",
        "04_queue_04_delegated_mission_document_organization.prompt.md",
        "4e5f3cdf7059f29bec053ce5a850754ce69e847f579bb083bf10cdb6ac1a070b",
    ),
    (
        5,
        "queue-05-capability-evaluation-lab",
        "Queue 05 — Capability evaluation lab",
        "05_queue_05_capability_evaluation_lab.prompt.md",
        "b097a483c595333a77a513fa2b4fb7231908159c3601289afa2f2324782adbda",
    ),
    (
        6,
        "queue-06-kanban-work-board",
        "Queue 06 — Kanban work board",
        "06_queue_06_kanban_work_board.prompt.md",
        "6053f24f1fd221ae48d94ab9b723047f7ecf10b85b6de5fee0fd93dbfe01de75",
    ),
    (
        7,
        "queue-07-news-signals",
        "Queue 07 — News and signals",
        "07_queue_07_news_signals.prompt.md",
        "839e2c4ecfa1241f038bf217f38e8eef733d8989c588cd7878b4ddad880ebbcd",
    ),
    (
        8,
        "queue-08-autocorrect-controls",
        "Queue 08 — Autocorrect controls",
        "08_queue_08_autocorrect_controls.prompt.md",
        "25237cf2f6f7528bc5d7490e9523c1ad4c7c840bd1b200ec3094b1c05d81dcd3",
    ),
    (
        9,
        "governed-cross-platform-social-publishing",
        "Governed cross-platform social publishing",
        "09_governed_cross_platform_social_publishing.prompt.md",
        "99691cba334deab8e5a1696681b69d7b609a7b9604e6731273e26a68972c66d9",
    ),
    (
        10,
        "governed-self-improvement",
        "Governed self-improvement program",
        "10_governed_self_improvement_program.prompt.md",
        "ec4a65e75cafe302c1173879759444813cba501f70d6cb82c4ba5c42b0daadd0",
    ),
    (
        11,
        "queue-09-final-goat-comparison",
        "Queue 09 — Final GoatCitadel comparison",
        "11_queue_09_final_goat_comparison.prompt.md",
        "b437f83fc55d22fc4d583b2553b3d043b28189f5e3e525c36f6be6b650dd26b2",
    ),
)
DENIED_AUTHORITY_KEYS = (
    "runtime_model_or_provider_calls",
    "web_fetch_or_browser_automation",
    "connector_writes",
    "unrestricted_shell_or_subprocess",
    "automatic_skill_or_plugin_execution",
    "automatic_pr_submission_or_merge",
    "standing_or_cross_request_approval",
    "billing_account_or_credential_changes",
    "policy_approval_route_openapi_redaction_or_gate_bypass",
    "raw_sensitive_content_persistence",
    "public_release_or_production_authority",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        try:
            safe_ref = path.relative_to(ROOT).as_posix()
        except ValueError:
            safe_ref = "required-ref:outside-repository"
        raise RuntimeError(f"missing or unreadable required file: {safe_ref}") from None


def _require(label: str, text: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise RuntimeError(f"{label} is missing required fragments: {missing}")


def _require_ordered(label: str, text: str, fragments: tuple[str, ...]) -> None:
    _require(label, text, fragments)
    positions = [text.index(fragment) for fragment in fragments]
    if positions != sorted(positions):
        raise RuntimeError(f"{label} is not in required order")


def _read_manifest() -> dict[str, object]:
    try:
        manifest = json.loads(_read(MANIFEST))
    except json.JSONDecodeError as exc:
        raise RuntimeError("remaining queue manifest is not valid JSON") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("remaining queue manifest root is invalid")
    return manifest


def _verify_manifest(manifest: dict[str, object]) -> None:
    expected_top_level_keys = {
        "schema_version",
        "artifact_status",
        "source_manifest_sha256",
        "authority_boundary",
        "pre_goat_insertion",
        "items",
    }
    if set(manifest) != expected_top_level_keys:
        raise RuntimeError("remaining queue manifest top-level schema is invalid")
    if any(
        not isinstance(manifest[key], str)
        for key in (
            "schema_version",
            "artifact_status",
            "source_manifest_sha256",
        )
    ):
        raise RuntimeError("remaining queue manifest scalar types are invalid")
    if manifest.get("schema_version") != "uaa.remaining_queue_manifest.v1":
        raise RuntimeError("remaining queue manifest schema is invalid")
    if manifest.get("artifact_status") != "planning_order_only":
        raise RuntimeError("remaining queue manifest artifact status is invalid")
    if (
        manifest.get("source_manifest_sha256")
        != "b039e6b977f0f49092f5100ae5665f7c07bde974c98bcd1dbdd3015e06a77b09"
    ):
        raise RuntimeError("remaining queue source manifest binding is invalid")
    authority = manifest.get("authority_boundary")
    if not isinstance(authority, dict) or set(authority) != set(DENIED_AUTHORITY_KEYS):
        raise RuntimeError("remaining queue authority boundary is invalid")
    if any(
        type(authority[key]) is not bool or authority[key] is not False
        for key in DENIED_AUTHORITY_KEYS
    ):
        raise RuntimeError("remaining queue authority boundary enables authority")

    items = manifest.get("items")
    if not isinstance(items, list):
        raise RuntimeError("remaining queue item list is invalid")
    expected_item_keys = {"position", "item_id", "title", "filename", "sha256"}
    actual_items: list[tuple[int, str, str, str, str]] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != expected_item_keys:
            raise RuntimeError("remaining queue immutable sequence is invalid")
        position = item["position"]
        item_id = item["item_id"]
        title = item["title"]
        filename = item["filename"]
        sha256 = item["sha256"]
        if (
            type(position) is not int
            or not isinstance(item_id, str)
            or not isinstance(title, str)
            or not title
            or not isinstance(filename, str)
            or not isinstance(sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", sha256) is None
        ):
            raise RuntimeError("remaining queue item types are invalid")
        actual_items.append((position, item_id, title, filename, sha256))
    if tuple(actual_items) != EXPECTED_QUEUE_ITEMS:
        raise RuntimeError("remaining queue immutable sequence is invalid")

    expected_insertion = {
        "after_item_id": "governed-self-improvement",
        "program_id": "tool-aware-cognition-and-chat-quality",
        "phase_ids": [f"TAW-{index:02d}" for index in range(9)],
        "before_item_id": "queue-09-final-goat-comparison",
    }
    insertion = manifest.get("pre_goat_insertion")
    if (
        not isinstance(insertion, dict)
        or set(insertion) != set(expected_insertion)
        or not isinstance(insertion.get("after_item_id"), str)
        or not isinstance(insertion.get("program_id"), str)
        or not isinstance(insertion.get("before_item_id"), str)
        or not isinstance(insertion.get("phase_ids"), list)
        or any(not isinstance(item, str) for item in insertion["phase_ids"])
        or insertion != expected_insertion
    ):
        raise RuntimeError("remaining queue pre-Goat insertion is invalid")


def verify() -> dict[str, object]:
    plan = _read(PLAN)
    queue = _read(QUEUE)
    board = _read(BOARD)
    roadmap = _read(ROADMAP)
    canonical_roadmap = _read(CANONICAL_ROADMAP)
    truth_packet = _read(TRUTH_PACKET)
    manifest = _read_manifest()
    _require("plan", plan, PLAN_REQUIRED)
    _require("plan authority boundary", plan, AUTHORITY_DENIALS)
    _require("queue insertion", queue, QUEUE_REQUIRED)
    _require_ordered("ordered queue insertion", queue, QUEUE_ORDERED_STEPS)
    _require("current board", board, BOARD_REQUIRED)
    _require("canonical roadmap", roadmap, ROADMAP_REQUIRED)
    _require("canonical roadmap truth", canonical_roadmap, CANONICAL_ROADMAP_REQUIRED)
    _require("product release truth", truth_packet, TRUTH_PACKET_REQUIRED)
    _verify_manifest(manifest)

    combined = "\n".join(
        (plan, queue, board, roadmap, canonical_roadmap, truth_packet)
    ).lower()
    present = [
        pattern
        for pattern in FORBIDDEN_PATTERNS
        if re.search(pattern, combined, flags=re.IGNORECASE)
    ]
    if present:
        raise RuntimeError(f"self-authorizing language found: {present}")

    _require_ordered("plan phase headings", plan, PHASE_HEADINGS)

    return {
        "status": "passed",
        "documented_phase_count": len(PHASE_HEADINGS),
        "normal_chat_fast_path_required": True,
        "direct_chat_quality_non_inferiority_required": True,
        "local_model_preservation_required": True,
        "documented_familiarity_state_count": 8,
        "goat_comparison_gate_documented": True,
        "evaluation_governance_required": True,
        "reversible_rollout_required": True,
        "structured_runtime_authority_added": False,
        "ordered_manifest_item_count": len(EXPECTED_QUEUE_ITEMS),
    }


def main() -> int:
    try:
        result = verify()
    except RuntimeError as exc:
        print(f"tool-aware cognition plan verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
