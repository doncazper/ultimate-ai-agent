#!/usr/bin/env python3
"""Verify the UAA parity gap-closure Phase 01 convergence ledger."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
REPORT_REF = "reports/parity_gap_closure/2026-07-22-convergence-ledger.md"
REPORT = ROOT / REPORT_REF
SUCCESS = "parity gap closure Phase 01 convergence ledger verification passed"
ALLOWED_STATUSES = {
    "merged_proven",
    "merged_partial",
    "open_pr_owned_elsewhere",
    "in_flight_branch_owned_elsewhere",
    "mock_or_contract_only",
    "planned_only",
    "blocked_by_authority",
    "blocked_by_external_facility",
    "missing",
    "superseded",
}
EXPECTED_IDS = tuple(
    [f"H{number:02d}" for number in range(1, 7)]
    + [f"O{number:02d}" for number in range(1, 9)]
    + [f"P{number:02d}" for number in range(1, 11)]
    + [f"B{number:02d}" for number in range(1, 15)]
    + [f"L{number:02d}" for number in range(1, 17)]
)
EXPECTED_STATUSES = {item_id: "merged_partial" for item_id in EXPECTED_IDS}
EXPECTED_STATUSES.update(
    {
        "H01": "planned_only",
        "H04": "blocked_by_authority",
        "O01": "planned_only",
        "O06": "mock_or_contract_only",
        "O08": "blocked_by_authority",
        "P10": "merged_proven",
        "B01": "open_pr_owned_elsewhere",
        "B03": "mock_or_contract_only",
        "L06": "planned_only",
        "L08": "blocked_by_authority",
        "L14": "merged_proven",
    }
)
EXPECTED_PHASES = {
    "H01": "04",
    "H02": "04",
    "H03": "07",
    "H04": "06",
    "H05": "03",
    "H06": "07",
    "O01": "04",
    "O02": "02",
    "O03": "04",
    "O04": "07",
    "O05": "05",
    "O06": "09",
    "O07": "05",
    "O08": "06",
    "P01": "08",
    "P02": "08",
    "P03": "07, 08",
    "P04": "08",
    "P05": "09",
    "P06": "08, 09",
    "P07": "04, 08",
    "P08": "06, 08",
    "P09": "08",
    "P10": "08",
    "B01": "09",
    "B02": "09",
    "B03": "09",
    "B04": "04, 09",
    "B05": "02, 09",
    "B06": "04, 09",
    "B07": "09",
    "B08": "07, 09",
    "B09": "07, 09",
    "B10": "07, 09",
    "B11": "09",
    "B12": "05, 09",
    "B13": "04, 09",
    "B14": "02, 09",
    "L01": "02",
    "L02": "03",
    "L03": "02",
    "L04": "02",
    "L05": "05",
    "L06": "04",
    "L07": "04",
    "L08": "06",
    "L09": "05",
    "L10": "04, 06",
    "L11": "07",
    "L12": "07",
    "L13": "08",
    "L14": "08",
    "L15": "05",
    "L16": "07",
}
EXPECTED_OUTCOMES = {
    "H01": "outcome:persistent-goal-lifecycle",
    "H02": "outcome:durable-event-lifecycle",
    "H03": "outcome:memory-integrity",
    "H04": "outcome:briefing-worker",
    "H05": "outcome:local-setup-lifecycle",
    "H06": "outcome:cross-session-search",
    "O01": "outcome:persistent-goal-lifecycle",
    "O02": "outcome:backend-truth",
    "O03": "outcome:durable-event-lifecycle",
    "O04": "outcome:verified-backup-restore",
    "O05": "outcome:work-board-reconciliation",
    "O06": "outcome:connector-delivery-evidence",
    "O07": "outcome:session-ux",
    "O08": "outcome:briefing-worker",
    "P01": "outcome:startup-budgets",
    "P02": "outcome:ordered-read-fanout",
    "P03": "outcome:cross-session-search",
    "P04": "outcome:bounded-cache-policy",
    "P05": "outcome:single-flight-provider-work",
    "P06": "outcome:abort-aware-io",
    "P07": "outcome:event-backpressure",
    "P08": "outcome:briefing-worker",
    "P09": "outcome:frontend-work-deduplication",
    "P10": "outcome:exact-head-ci-budget",
    "B01": "outcome:exact-approval-ownership",
    "B02": "outcome:approval-fail-closed",
    "B03": "outcome:connector-delivery-evidence",
    "B04": "outcome:restart-admission-fence",
    "B05": "outcome:backend-truth",
    "B06": "outcome:event-backpressure",
    "B07": "outcome:provider-side-effect-fence",
    "B08": "outcome:memory-integrity",
    "B09": "outcome:storage-budget-integrity",
    "B10": "outcome:archive-path-safety",
    "B11": "outcome:chunk-redaction",
    "B12": "outcome:revisioned-autosave",
    "B13": "outcome:approval-wait-lifecycle",
    "B14": "outcome:backend-truth",
    "L01": "outcome:backend-truth",
    "L02": "outcome:local-setup-lifecycle",
    "L03": "outcome:backend-truth",
    "L04": "outcome:backend-truth",
    "L05": "outcome:action-inbox-ux",
    "L06": "outcome:persistent-goal-lifecycle",
    "L07": "outcome:durable-event-lifecycle",
    "L08": "outcome:briefing-worker",
    "L09": "outcome:work-board-reconciliation",
    "L10": "outcome:briefing-worker",
    "L11": "outcome:verified-backup-restore",
    "L12": "outcome:memory-integrity",
    "L13": "outcome:product-performance-budgets",
    "L14": "outcome:locked-supply-chain",
    "L15": "outcome:session-ux",
    "L16": "outcome:cross-session-search",
}
EXPECTED_MERGED_PROOF_REFS = {
    "P10": {
        ".github/workflows/ci.yml",
        "scripts/verification/verify_ci_evidence_dag.py",
        "tests/test_ci_workflow.py",
        "tests/test_ci_command_manifest.py",
    },
    "L14": {
        ".github/workflows/supply-chain.yml",
        "uv.lock",
        "apps/control-center/package-lock.json",
        "tests/test_supply_chain_workflow.py",
    },
}
EXPECTED_ALIASES = {
    "outcome:persistent-goal-lifecycle": {"H01", "O01", "L06"},
    "outcome:durable-event-lifecycle": {"H02", "O03", "L07"},
    "outcome:memory-integrity": {"H03", "B08", "L12"},
    "outcome:briefing-worker": {"H04", "O08", "P08", "L08", "L10"},
    "outcome:local-setup-lifecycle": {"H05", "L02"},
    "outcome:cross-session-search": {"H06", "P03", "L16"},
    "outcome:backend-truth": {"O02", "B05", "B14", "L01", "L03", "L04"},
    "outcome:verified-backup-restore": {"O04", "L11"},
    "outcome:work-board-reconciliation": {"O05", "L09"},
    "outcome:connector-delivery-evidence": {"O06", "B03"},
    "outcome:session-ux": {"O07", "L15"},
}
ROW = re.compile(
    r"^\| (?P<id>[HOPBL]\d{2}) \| `(?P<outcome>outcome:[^`]+)` \| "
    r"(?P<phase>[^|]+?) \| `(?P<status>[^`]+)` \| (?P<proof>[^|]+) \| "
    r"(?P<delta>[^|]+) \|$",
    re.MULTILINE,
)
ALIAS = re.compile(
    r"^- `(?P<outcome>outcome:[^`]+)`: (?P<ids>[HOPBL0-9, ]+)$",
    re.MULTILINE,
)
EXPECTED_DEPENDENCIES = (
    "- Phase 01 precedes Phases 02–10.",
    "- Phase 02 precedes Phases 04, 05, 06, and 10.",
    "- Phase 03 precedes Phase 10.",
    "- Phase 04 precedes Phases 05, 06, 08, 09, and 10.",
    "- Phase 05 precedes Phases 06 and 10.",
    "- Phase 06 precedes Phases 08, 09, and 10.",
    "- Phase 07 precedes Phases 08, 09, and 10.",
    "- Phase 08 precedes Phases 09 and 10.",
    "- Phase 09 precedes Phase 10.",
)
EXPECTED_EXECUTION_ROWS = (
    ("02", "ready", "backend truth and real rendered founder-loop proof"),
    ("03", "ready", "integrate existing installer core into shared governed Setup lifecycle"),
    ("04", "ready after 02", "persistent goals and durable event lifecycle"),
    ("05", "ready after 02/04", "Action Inbox, Work Board, session UX"),
    (
        "06",
        "independent code ready after 02/04/05; execution authority blocked",
        "sources and exact worker lane",
    ),
    ("07", "ready", "memory/search/backup integrity"),
    ("08", "ready after 04/06/07", "performance; preserve proven P10/L14"),
    (
        "09",
        "ready after 04/06/07/08 except B01 overlap",
        "reliability and future-lane proofs",
    ),
    ("10", "ready after 02–09", "terminal acceptance and honest residual ledger"),
)
EXECUTION_ROW = re.compile(
    r"^\| (?P<phase>\d{2}) \| (?P<state>[^|]+?) \| (?P<action>[^|]+?) \|$",
    re.MULTILINE,
)
VISIBLE_SURFACE_ROW = re.compile(
    r"^\| (?P<surface>[^|]+?) \| (?P<posture>[^|]+?) \| (?P<gap>[^|]+?) \|$",
    re.MULTILINE,
)
EXPECTED_VISIBLE_SURFACE_ROWS = (
    ("Start Here", "backend-owned, partial", "proof/detail completion and full failure-state walkthrough"),
    ("Today", "storage-backed, partial", "complete readable loop and source adapters"),
    ("Inbox", "backend source status only", "live email/calendar ingestion absent"),
    ("Action Inbox", "backend-owned, proofed exact local decision lane", "broader actions remain blocked; UX/revision hardening remains"),
    ("Morning Briefing", "storage-backed, partial", "live sources and exact refresh worker absent"),
    ("Plans / Work Board", "backend-owned, partial", "durable goals and multi-client reconciliation incomplete"),
    ("Memory", "reviewed local state, partial", "integrity/ranking/migration hardening incomplete"),
    ("Evidence / Proof", "backend-owned, partial", "stale-evidence end-to-end truth proof incomplete"),
    ("Setup", "real installer core, partial product integration", "shared Setup API/UI lifecycle incomplete"),
    ("Chat / Sessions", "backend-owned local state, partial", "session UX and compact cross-session search remain"),
    ("Runtime", "backend status only", "broad execution stays blocked"),
    ("Settings", "backend status and authority cockpit only", "no authority-minting toggles or unsupported writes"),
)
EXPECTED_AUTHORITY_BULLETS = (
    "The exact Morning Briefing source-refresh/background-worker lane remains `blocked_by_authority`; Phase 06 may implement independent contracts and tests but cannot claim execution without a separately accepted exact lane.",
    "Connector account reads, sends, writes, notifications, provider/model calls, browser execution, unrestricted shell execution, and production authority remain blocked.",
    "`pr:319` owns its exact approval/admin/destructive semantics paths until merge or explicit handoff.",
)
ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9_.:/~-])(?:"
    r"file:(?://)?/|"
    r"/(?!control-center(?:/|\b)|runtime(?:/|\b)|api(?:/|\b)|v1(?:/|\b))"
    r"[A-Za-z0-9._~-]+(?:/[A-Za-z0-9._~-]+)*|"
    r"/(?:Users|home|root|private|tmp|var|etc|System|Library|Applications|opt|usr|"
    r"Volumes|srv|mnt|proc|dev|run|bin|sbin|workspace|build|runner|github)(?:/|\b)|"
    r"~/|[A-Za-z]:\\|\\\\"
    r")",
    re.IGNORECASE | re.MULTILINE,
)
OPAQUE_PROOF_REF = re.compile(r"^(?:pr|commit):[A-Za-z0-9._-]+$")
REPOSITORY_PATH_PREFIXES = (
    ".github/",
    "apps/",
    "docs/",
    "packaging/",
    "reports/",
    "scripts/",
    "src/",
    "tests/",
)
ROOT_REPOSITORY_REF = re.compile(
    r"^(?:Makefile|[A-Za-z0-9][A-Za-z0-9_.-]*\."
    r"(?:json|lock|md|toml|txt|yaml|yml))$"
)
EXPECTED_INVENTORY_BASE = "35d66a04680cbe6fa5356001dd90256bd36f9fd8"
EXPECTED_ACTIVE_BASELINE = "v0.104.0"
EXPECTED_REPORT_SHA256 = "789f9af379d633cfa5a3a1e182fe39d8d99bc1131fb50d563a5472fbe92134d4"
REQUIRED_SNIPPETS = (
    "Status: current-main inventory; no runtime authority grant",
    f"- Inventory base: `commit:{EXPECTED_INVENTORY_BASE}`",
    f"- Active baseline: `{EXPECTED_ACTIVE_BASELINE}`",
    "`pr:319`",
    "branch:codex/harden-verification-recovery-auth-ci-identity",
    "## Recent Merge And Remote Ledger",
    "commit:2073ae77651e43585d0448a513c104a9a5530fea",
    "do not edit `src/ultimate_ai_agent/core/authority/contracts.py`",
    "## Canonical Alias Graph",
    "## Phase Dependency Graph",
    "## Visible Surface Truth",
    "## Authority Prerequisites",
    "## Phase Execution Ledger",
    "Connector account reads, sends, writes, notifications, provider/model calls",
    "Phase 09 precedes Phase 10.",
)
FORBIDDEN = (
    "INVENTORY_SHA",
    "MERGE_SHA",
    "raw prompt",
    "raw response",
    "raw provider payload",
    "raw local path",
    "production authority granted",
    "unrestricted browsing enabled",
)


def _clean_ref(value: str) -> str:
    return value.strip().rstrip(".,:;()")


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    if marker not in text:
        return ""
    remainder = text.split(marker, 1)[1]
    return remainder.split("\n## ", 1)[0]


def _markdown_bullets(text: str) -> tuple[str, ...]:
    bullets: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("- "):
            if current:
                bullets.append(" ".join(current))
            current = [line[2:].strip()]
        elif current and line.strip():
            current.append(line.strip())
    if current:
        bullets.append(" ".join(current))
    return tuple(bullets)


def _repo_path(ref: str) -> Path | None:
    """Return a contained repository path for a canonical POSIX proof ref."""
    cleaned = _clean_ref(ref)
    posix = PurePosixPath(cleaned)
    if not cleaned or posix.is_absolute() or ".." in posix.parts or "\\" in cleaned:
        return None
    candidate = (ROOT / Path(*posix.parts)).resolve(strict=False)
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _repository_refs(text: str, rows: list[re.Match[str]]) -> set[str]:
    refs = {
        ref
        for ref in re.findall(r"`([^`]+)`", text)
        if ref.startswith(REPOSITORY_PATH_PREFIXES)
        or ROOT_REPOSITORY_REF.fullmatch(ref)
    }
    refs.update(
        ref
        for row in rows
        for ref in re.findall(r"`([^`]+)`", row.group("proof"))
        if not OPAQUE_PROOF_REF.fullmatch(ref)
    )
    return refs


def verify(*, report_text: str | None = None, check_refs: bool = True) -> list[str]:
    failures: list[str] = []
    try:
        text = REPORT.read_text(encoding="utf-8") if report_text is None else report_text
    except OSError:
        return ["Phase 01 convergence ledger is missing or unreadable"]

    report_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if report_digest != EXPECTED_REPORT_SHA256:
        failures.append("convergence ledger content digest drifted")

    for snippet in REQUIRED_SNIPPETS:
        if snippet not in text:
            failures.append(f"ledger missing required section marker: {snippet}")
    lowered = text.casefold()
    for forbidden in FORBIDDEN:
        if forbidden.casefold() in lowered:
            failures.append(f"ledger contains forbidden or unresolved marker: {forbidden}")
    if ABSOLUTE_PATH.search(text):
        failures.append("ledger contains an absolute local path")

    rows = list(ROW.finditer(text))
    observed = tuple(row.group("id") for row in rows)
    if observed != EXPECTED_IDS:
        failures.append("coverage ledger must contain all 54 IDs exactly once and in order")
    if tuple(EXPECTED_PHASES) != EXPECTED_IDS:
        failures.append("internal expected phase mapping must cover all 54 IDs in order")
    if tuple(EXPECTED_OUTCOMES) != EXPECTED_IDS:
        failures.append("internal expected outcome mapping must cover all 54 IDs in order")
    outcomes_by_id: dict[str, str] = {}
    for row in rows:
        item_id = row.group("id")
        status = row.group("status")
        outcomes_by_id[item_id] = row.group("outcome")
        expected_outcome = EXPECTED_OUTCOMES.get(item_id)
        if expected_outcome is not None and row.group("outcome") != expected_outcome:
            failures.append(
                f"{item_id} outcome drifted: expected {expected_outcome}, "
                f"observed {row.group('outcome')}"
            )
        if status not in ALLOWED_STATUSES:
            failures.append(f"{item_id} has invalid status {status}")
        expected_status = EXPECTED_STATUSES.get(item_id)
        if expected_status is not None and status != expected_status:
            failures.append(
                f"{item_id} status drifted: expected {expected_status}, observed {status}"
            )
        phase = row.group("phase")
        phases = [part.strip() for part in phase.split(",")]
        if not phases or any(
            not part.isdigit() or not 2 <= int(part) <= 9 for part in phases
        ):
            failures.append(f"{item_id} has invalid phase mapping")
        expected_phase = EXPECTED_PHASES.get(item_id)
        if expected_phase is not None and phase != expected_phase:
            failures.append(
                f"{item_id} phase drifted: expected {expected_phase}, observed {phase}"
            )
        proof = row.group("proof")
        if status == "merged_proven":
            if "tests/" not in proof:
                failures.append(f"{item_id} merged_proven status lacks focused test proof")
            if not any(marker in proof for marker in ("src/", "scripts/", ".github/")):
                failures.append(
                    f"{item_id} merged_proven status lacks implementation or operator proof"
                )
            if not row.group("delta").casefold().startswith("none;"):
                failures.append(f"{item_id} merged_proven status retains an unresolved delta")
            required_refs = EXPECTED_MERGED_PROOF_REFS.get(item_id, set())
            missing_refs = sorted(
                ref for ref in required_refs if f"`{ref}`" not in proof
            )
            if missing_refs:
                failures.append(
                    f"{item_id} merged_proven proof drifted; missing exact refs: "
                    + ", ".join(missing_refs)
                )
        if (
            status.endswith("owned_elsewhere")
            and "do not" not in row.group("delta").casefold()
            and "wait" not in row.group("delta").casefold()
        ):
            failures.append(f"{item_id} owned overlap lacks a non-invasive disposition")

    aliases = {
        match.group("outcome"): {
            item.strip() for item in match.group("ids").split(",") if item.strip()
        }
        for match in ALIAS.finditer(text)
    }
    if aliases != EXPECTED_ALIASES:
        failures.append("canonical alias graph drifted")
    for outcome, item_ids in EXPECTED_ALIASES.items():
        for item_id in item_ids:
            if outcomes_by_id.get(item_id) != outcome:
                failures.append(f"{item_id} does not point to canonical alias {outcome}")

    dependency_lines = tuple(
        line
        for line in _section(text, "Phase Dependency Graph").splitlines()
        if line.startswith("- Phase ")
    )
    if dependency_lines != EXPECTED_DEPENDENCIES:
        failures.append("phase dependency graph drifted")

    execution_rows = tuple(
        (match.group("phase"), match.group("state"), match.group("action"))
        for match in EXECUTION_ROW.finditer(_section(text, "Phase Execution Ledger"))
    )
    if execution_rows != EXPECTED_EXECUTION_ROWS:
        failures.append("phase execution ledger drifted")

    visible_surface_rows = tuple(
        (match.group("surface"), match.group("posture"), match.group("gap"))
        for match in VISIBLE_SURFACE_ROW.finditer(
            _section(text, "Visible Surface Truth")
        )
        if match.group("surface") not in {"Surface", "---"}
    )
    if visible_surface_rows != EXPECTED_VISIBLE_SURFACE_ROWS:
        failures.append("visible surface truth ledger drifted")

    authority_bullets = _markdown_bullets(_section(text, "Authority Prerequisites"))
    if authority_bullets != EXPECTED_AUTHORITY_BULLETS:
        failures.append("authority prerequisites drifted")

    if check_refs:
        refs = _repository_refs(text, rows)
        for ref in sorted(refs):
            path = _repo_path(ref)
            if path is None:
                failures.append(f"ledger proof ref is unsafe: {_clean_ref(ref)}")
            elif not path.exists():
                failures.append(f"ledger proof ref is missing: {_clean_ref(ref)}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(SUCCESS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
