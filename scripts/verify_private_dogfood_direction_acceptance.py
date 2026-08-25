#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = ROOT / "docs/product/private_dogfood_direction_acceptance_v1.json"
SCHEMA_PATH = ROOT / "docs/schemas/private_dogfood_direction_acceptance_v1.schema.json"
FIN_LEDGER_PATH = (
    ROOT
    / "docs/design/control_center_north_star/renders/finance-compliance-v1"
    / "acceptance-ledger-v1.json"
)
FIN_RENDER_DIR = (
    ROOT / "docs/design/control_center_north_star/renders/finance-compliance-v1"
)
Q25_RENDER_DIR = ROOT / "docs/design/control_center_north_star/renders/social-media-v1"
EXPECTED_SOURCE_REVISION_REF = "git-sha:fd1152d209fb0871873d74147bcbf391a64474a3"
EXPECTED_Q25_ASSET_DIGEST = (
    "sha256:780aab0c1352cbad4a77adfcfb981b09377772cba0ad4ba19bd328a0888b8584"
)
EXPECTED_Q26_PACK_DIGEST = (
    "sha256:95c90c25855f6408ee22f9f050a07e373b79404de37c2f3c91a0005ac532fc72"
)

EXPECTED_Q25_PATH_REFS = {
    "repo-path-ref:docs/design/control_center_north_star/renders/social-media-v1/01-social-command-view.jpg",
    "repo-path-ref:docs/design/control_center_north_star/renders/social-media-v1/02-calendar-social-publishing-view.jpg",
    "repo-path-ref:docs/design/control_center_north_star/renders/social-media-v1/03-work-board-social-content-view.jpg",
    "repo-path-ref:docs/design/control_center_north_star/renders/social-media-v1/04-communications-social-media-view.jpg",
}
EXPECTED_Q25_SCOPE_REFS = {
    "scope-ref:queue-v2/Q25/foundation-gap-closure",
    "scope-ref:queue-v2/Q25/read-only-private-dogfood-iteration",
}
EXPECTED_Q25_GATE_REFS = {
    "gate-ref:queue-v2/Q25/crm-relationship-projection",
    "gate-ref:queue-v2/Q25/independent-profile-promotion",
}
EXPECTED_Q26_SCOPE_REFS = {
    "scope-ref:queue-v2/Q26/no-real-financial-data",
    "scope-ref:queue-v2/Q26/synthetic-local-fin001-kernel",
}
EXPECTED_Q26_GATE_REFS = {
    "gate-ref:queue-v2/Q26/independent-domain-and-safety-review",
    "gate-ref:queue-v2/Q26/protected-real-data-promotion",
}
EXPECTED_ALLOWED_REFINEMENTS = {
    "refinement-ref:private-dogfood/accessibility-improvement",
    "refinement-ref:private-dogfood/copy",
    "refinement-ref:private-dogfood/interaction-polish",
    "refinement-ref:private-dogfood/responsive-layout",
    "refinement-ref:private-dogfood/spacing-density",
}
EXPECTED_REAPPROVAL_TRIGGERS = {
    "trigger-ref:private-dogfood/authority-expansion",
    "trigger-ref:private-dogfood/canonical-ownership-change",
    "trigger-ref:private-dogfood/sensitive-data-boundary-change",
    "trigger-ref:private-dogfood/workflow-purpose-change",
}
SECRET_LIKE_REF = re.compile(
    r"(?i)(?:sk_(?:live|test)|gh[pousr]_|akia|asia|api[_-]?key|tokenvalue)"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _walk_strings(value: Any, key: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            found.extend(_walk_strings(child, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_strings(child, key))
    elif isinstance(value, str):
        found.append((key, value))
    return found


def _repo_path_from_ref(path_ref: str, root: Path) -> Path:
    prefix = "repo-path-ref:"
    if not path_ref.startswith(prefix):
        raise ValueError(f"asset path ref is not repository-scoped: {path_ref}")
    relative = path_ref.removeprefix(prefix)
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError(
            f"accepted surface is missing or not a regular file: {path_ref}"
        )
    return path


def _canonical_q25_digest(assets: list[dict[str, str]]) -> str:
    normalized = [
        {"path_ref": item["path_ref"], "sha256": item["sha256"]}
        for item in sorted(assets, key=lambda item: item["path_ref"])
    ]
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _current_q25_inventory(root: Path = ROOT) -> set[str]:
    render_dir = root / "docs/design/control_center_north_star/renders/social-media-v1"
    return {
        f"repo-path-ref:{path.relative_to(root).as_posix()}"
        for pattern in ("*.jpg", "*.png")
        for path in render_dir.glob(pattern)
        if path.is_file() and not path.is_symlink()
    }


def _actual_fin_pack_digest(render_dir: Path = FIN_RENDER_DIR) -> str:
    assets: list[dict[str, Any]] = []
    for path in sorted(render_dir.glob("*.png")):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Finance render is not a regular file: {path.name}")
        data = path.read_bytes()
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            raise ValueError(f"Finance render has malformed PNG metadata: {path.name}")
        width, height = struct.unpack(">II", data[16:24])
        assets.append(
            {
                "name": path.name,
                "sha256": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "width": width,
                "height": height,
            }
        )
    canonical = json.dumps(assets, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _require_exact_set(
    actual: Any, expected: set[str], field_name: str, failures: list[str]
) -> None:
    if not isinstance(actual, list) or set(actual) != expected:
        failures.append(f"{field_name} drifted from the exact accepted set")


def verify(
    payload: dict[str, Any] | None = None,
    *,
    root: Path = ROOT,
    fin_ledger_payload: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], bool]:
    failures: list[str] = []
    advisories: list[str] = []
    payload = _load(LEDGER_PATH) if payload is None else payload

    schema = _load(SCHEMA_PATH)
    for error in sorted(Draft202012Validator(schema).iter_errors(payload), key=str):
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        failures.append(f"schema:{location}:{error.message}")

    if failures:
        return failures, advisories, False

    if contains_obvious_secret(payload):
        failures.append("acceptance ledger contains secret-like durable content")
    for key, value in _walk_strings(payload):
        try:
            if key.endswith("_ref") or key.endswith("_refs"):
                if SECRET_LIKE_REF.search(value):
                    failures.append(
                        f"acceptance ledger contains secret-like durable content in {key}"
                    )
                    continue
                validate_execution_ref(value, key)
            elif key in {"safe_summary", "next_safe_action"}:
                validate_safe_execution_text(value, key)
        except ValueError as exc:
            failures.append(f"unsafe durable value for {key}: {exc}")

    q25 = payload["programs"]["q25"]
    if payload["accepted_source_revision_ref"] != EXPECTED_SOURCE_REVISION_REF:
        failures.append("accepted source revision drifted")
    q25_assets = q25["assets"]
    path_refs = [item["path_ref"] for item in q25_assets]
    if (
        len(path_refs) != len(set(path_refs))
        or set(path_refs) != EXPECTED_Q25_PATH_REFS
    ):
        failures.append("Q25 accepted surface inventory drifted")
    if _canonical_q25_digest(q25_assets) != q25["asset_digest"]:
        failures.append("Q25 accepted asset digest does not match its recorded assets")
    if q25["asset_digest"] != EXPECTED_Q25_ASSET_DIGEST:
        failures.append(
            "Q25 accepted asset digest drifted from the founder-reviewed baseline"
        )
    if _current_q25_inventory(root) != EXPECTED_Q25_PATH_REFS:
        failures.append("current Q25 surface inventory drifted")

    current_q25_match = True
    for item in q25_assets:
        try:
            current_hash = f"sha256:{hashlib.sha256(_repo_path_from_ref(item['path_ref'], root).read_bytes()).hexdigest()}"
        except ValueError as exc:
            failures.append(str(exc))
            current_q25_match = False
            continue
        if current_hash != item["sha256"]:
            current_q25_match = False
    if not current_q25_match and not failures:
        advisories.append(
            "Q25 surface bytes changed after founder direction acceptance; private-dogfood acceptance remains valid, but material reapproval triggers must be evaluated"
        )

    _require_exact_set(
        q25["implementation_scope_refs"],
        EXPECTED_Q25_SCOPE_REFS,
        "Q25 implementation scopes",
        failures,
    )
    _require_exact_set(
        q25["remaining_gate_refs"],
        EXPECTED_Q25_GATE_REFS,
        "Q25 remaining gates",
        failures,
    )

    q26 = payload["programs"]["q26"]
    if q26["candidate_pack_digest"] != EXPECTED_Q26_PACK_DIGEST:
        failures.append("Q26 founder-reviewed candidate pack digest drifted")
    fin_ledger = (
        _load(FIN_LEDGER_PATH) if fin_ledger_payload is None else fin_ledger_payload
    )
    if q26["candidate_pack_ref"] != fin_ledger.get("candidate_pack_ref"):
        failures.append("Q26 candidate pack ref does not match the FIN-000 ledger")
    if q26["candidate_pack_digest"] != fin_ledger.get("candidate_pack_digest"):
        advisories.append(
            "Q26 independent candidate pack revision changed after founder direction acceptance; material reapproval triggers must be evaluated"
        )
    try:
        actual_fin_digest = _actual_fin_pack_digest(
            root / "docs/design/control_center_north_star/renders/finance-compliance-v1"
        )
    except ValueError as exc:
        failures.append(str(exc))
    else:
        if actual_fin_digest != fin_ledger.get("candidate_pack_digest"):
            failures.append("current FIN-000 candidate pack integrity check failed")

    _require_exact_set(
        q26["implementation_scope_refs"],
        EXPECTED_Q26_SCOPE_REFS,
        "Q26 implementation scopes",
        failures,
    )
    _require_exact_set(
        q26["remaining_gate_refs"],
        EXPECTED_Q26_GATE_REFS,
        "Q26 remaining gates",
        failures,
    )

    refinement = payload["refinement_policy"]
    _require_exact_set(
        refinement["allowed_refinement_refs"],
        EXPECTED_ALLOWED_REFINEMENTS,
        "allowed refinements",
        failures,
    )
    _require_exact_set(
        refinement["material_reapproval_trigger_refs"],
        EXPECTED_REAPPROVAL_TRIGGERS,
        "material reapproval triggers",
        failures,
    )

    return failures, advisories, current_q25_match


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the founder private-dogfood direction acceptance ledger."
    )
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    args = parser.parse_args()

    failures, advisories, current_match = verify(_load(args.ledger))
    status = "ACCEPTED_FOR_PRIVATE_DOGFOOD" if not failures else "INVALID"
    print(
        json.dumps(
            {
                "schema_version": "uaa.private-dogfood-direction-acceptance-report.v1",
                "status": status,
                "current_q25_assets_match_accepted_baseline": current_match,
                "independent_promotion_required": True,
                "failures": failures,
                "advisories": advisories,
                "safe_summary": (
                    "Founder direction acceptance is structurally valid and grants private-dogfood iteration only."
                    if not failures
                    else "Founder direction acceptance verification failed closed."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
