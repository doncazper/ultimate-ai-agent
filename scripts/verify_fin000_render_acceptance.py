#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ROOT = Path(__file__).resolve().parent.parent
RENDER_DIR = (
    ROOT / "docs/design/control_center_north_star/renders/finance-compliance-v1"
)
LEDGER_PATH = RENDER_DIR / "acceptance-ledger-v1.json"
SCHEMA_PATH = ROOT / "docs/schemas/fin000_render_acceptance_ledger_v1.schema.json"
GALLERY_PATH = RENDER_DIR / "REVIEW_GALLERY.md"
TRUSTED_REVIEWERS_PATH = RENDER_DIR / "trusted-reviewers-v1.json"
NORMATIVE_SUBJECT_PATHS = (
    "docs/design/control_center_north_star/renders/finance-compliance-v1/README.md",
    "docs/design/control_center_north_star/renders/finance-compliance-v1/REVIEW_GALLERY.md",
    "docs/design/control_center_north_star/renders/finance-compliance-v1/trusted-reviewers-v1.json",
    "docs/product/UAA_FINANCE_FIN000_INDEPENDENT_REVIEW_PACKET.md",
    "docs/product/UAA_FINANCE_FIN000_STATE_ACCESSIBILITY_MATRIX.md",
    "docs/schemas/fin000_render_acceptance_ledger_v1.schema.json",
    "scripts/verify_fin000_render_acceptance.py",
)
EXACT_INVENTORY = {
    "01-finance-command-desktop.png": ("desktop", 1440, 900),
    "02-source-statement-inbox-desktop.png": ("desktop", 1440, 900),
    "03-extraction-reconciliation-workbench.png": ("desktop", 1440, 900),
    "04-transfer-balance-sheet-review.png": ("desktop", 1440, 900),
    "05-review-batches-desktop.png": ("desktop", 1440, 900),
    "06-transaction-review-desktop.png": ("desktop", 1440, 900),
    "07-transaction-evidence-inspector.png": ("desktop", 1440, 900),
    "08-books-reconciliation-desktop.png": ("desktop", 1440, 900),
    "09-tax-readiness-accountant-desktop.png": ("desktop", 1440, 900),
    "10-compliance-obligations-desktop.png": ("desktop", 1440, 900),
    "11-calendar-finance-saved-view.png": ("desktop", 1440, 900),
    "12-founder-loop-finance-projections.png": ("desktop", 1440, 900),
    "13-finance-command-narrow.png": ("narrow", 720, 1080),
    "14-transaction-review-narrow.png": ("narrow", 720, 1080),
    "15-evidence-capture-narrow.png": ("narrow", 720, 1080),
    "16-upcoming-obligations-narrow.png": ("narrow", 720, 1080),
}

EXPECTED_CHECKS = {
    "check-ref:fin000:desktop-inventory",
    "check-ref:fin000:narrow-inventory",
    "check-ref:fin000:coherent-fixture-story",
    "check-ref:fin000:canonical-ownership",
    "check-ref:fin000:state-language",
    "check-ref:fin000:no-unavailable-authority",
    "check-ref:fin000:consequence-readability",
    "check-ref:fin000:synthetic-sensitive-values",
    "check-ref:fin000:accessibility",
    "check-ref:fin000:role-acceptance",
}
AUTOMATED_CHECKS = {
    "check-ref:fin000:desktop-inventory",
    "check-ref:fin000:narrow-inventory",
}
EXPECTED_ROLES = {
    "reviewer-role-ref:fin000:product-design",
    "reviewer-role-ref:fin000:accounting-domain",
    "reviewer-role-ref:fin000:privacy-security",
    "reviewer-role-ref:fin000:accessibility",
    "reviewer-role-ref:fin000:implementation",
}
SAFE_REF = re.compile(r"^[a-z][a-z0-9-]*(?::[a-z0-9][a-z0-9._-]*)+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PACK_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SECRET_TOKEN_PREFIX = re.compile(
    r"(?i)(?:^|[:_-])(?:sk_(?:live|test)|gh[pousr]|akia|asia)[_-]?[a-z0-9]+"
)
INDEPENDENT_HUMAN_IDENTITY_AUTHORITY_CONFIGURED = False
FORBIDDEN_DURABLE_MARKERS = (
    "raw prompt",
    "raw response",
    "raw provider payload",
    "raw log",
    "api key",
    "password",
    "raw screenshot",
    "raw ocr",
    "username",
    "hostname",
    "serial number",
    "environment dump",
    "credential",
    "private key",
    "bearer ",
    "cookie",
    "/users/",
    "/home/",
)


def _load(path: Path = LEDGER_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ledger must be a JSON object")
    return payload


def _safe_ref(value: Any) -> bool:
    if not isinstance(value, str) or not SAFE_REF.fullmatch(value):
        return False
    try:
        validate_execution_ref(value, "durable_ref")
    except ValueError:
        return False
    return not contains_obvious_secret(value) and not SECRET_TOKEN_PREFIX.search(value)


def _decode_base64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def review_decision_message(
    ledger_ref: str, candidate_author_ref: str, reviewer: dict[str, Any]
) -> bytes:
    payload = {
        "ledger_ref": ledger_ref,
        "candidate_author_ref": candidate_author_ref,
        "candidate_pack_digest": reviewer.get("candidate_pack_digest"),
        "acceptance_subject_digest": reviewer.get("acceptance_subject_digest"),
        "role_ref": reviewer.get("role_ref"),
        "reviewer_ref": reviewer.get("reviewer_ref"),
        "trusted_key_ref": reviewer.get("trusted_key_ref"),
        "decision": reviewer.get("decision"),
        "receipt_ref": reviewer.get("receipt_ref"),
        "finding_refs": reviewer.get("finding_refs"),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _png_metadata(path: Path) -> tuple[bytes, int, int]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"render must be a regular non-symlink file: {path.name}")
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"render has malformed PNG header: {path.name}")
    width, height = struct.unpack(">II", data[16:24])
    return data, width, height


def _actual_assets_and_digest() -> tuple[list[dict[str, Any]], str]:
    assets: list[dict[str, Any]] = []
    for path in sorted(RENDER_DIR.glob("*.png")):
        data, width, height = _png_metadata(path)
        assets.append(
            {
                "name": path.name,
                "sha256": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "width": width,
                "height": height,
            }
        )
    canonical = json.dumps(assets, sort_keys=True, separators=(",", ":")).encode()
    return assets, f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _acceptance_subject_digest(assets: list[dict[str, Any]]) -> str:
    normalized_assets = [
        {
            "path_ref": item.get("path_ref"),
            "filename": item.get("filename"),
            "sha256": f"sha256:{item.get('sha256')}",
            "width": item.get("width"),
            "height": item.get("height"),
            "viewport_class": item.get("viewport_class"),
        }
        for item in sorted(assets, key=lambda item: str(item.get("filename")))
    ]
    contracts = []
    for relative in NORMATIVE_SUBJECT_PATHS:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"normative acceptance subject is missing: {relative}")
        contracts.append(
            {
                "path_ref": f"repo-path-ref:{relative}",
                "sha256": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
            }
        )
    canonical = json.dumps(
        {"assets": normalized_assets, "contracts": contracts},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _trusted_reviewer_map(
    payload: dict[str, Any], failures: list[str]
) -> dict[tuple[str, str, str], Ed25519PublicKey]:
    if set(payload) != {"registry_ref", "candidate_pack_ref", "status", "reviewers"}:
        failures.append("trusted reviewer registry fields drifted")
    if payload.get("registry_ref") != "registry-ref:fin000:trusted-reviewers:v1":
        failures.append("trusted reviewer registry ref drifted")
    if payload.get("candidate_pack_ref") != "render-pack-ref:finance-compliance-v1":
        failures.append("trusted reviewer registry pack ref drifted")
    entries = payload.get("reviewers")
    if not isinstance(entries, list):
        failures.append("trusted reviewer registry reviewers must be a list")
        return {}
    expected_status = "active" if entries else "pending_reviewer_enrollment"
    if payload.get("status") != expected_status:
        failures.append(f"trusted reviewer registry status must be {expected_status}")
    trusted: dict[tuple[str, str, str], Ed25519PublicKey] = {}
    seen_reviewers: set[str] = set()
    seen_keys: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("trusted reviewer entry must be an object")
            continue
        if set(entry) != {
            "role_ref",
            "reviewer_ref",
            "key_ref",
            "public_key_base64url",
            "public_key_fingerprint_ref",
        }:
            failures.append("trusted reviewer entry fields drifted")
            continue
        role_ref = entry.get("role_ref")
        reviewer_ref = entry.get("reviewer_ref")
        key_ref = entry.get("key_ref")
        public_key_base64url = entry.get("public_key_base64url")
        fingerprint_ref = entry.get("public_key_fingerprint_ref")
        if not all(_safe_ref(value) for value in (role_ref, reviewer_ref, key_ref)):
            failures.append("trusted reviewer entry contains an invalid safe ref")
            continue
        if role_ref not in EXPECTED_ROLES:
            failures.append(f"trusted reviewer has an unknown role: {role_ref}")
        if reviewer_ref in seen_reviewers or key_ref in seen_keys:
            failures.append("trusted reviewer identities and keys must be unique")
        seen_reviewers.add(reviewer_ref)
        seen_keys.add(key_ref)
        try:
            raw_key = _decode_base64url(public_key_base64url)
            if len(raw_key) != 32:
                raise ValueError("Ed25519 public key must contain 32 bytes")
            expected_fingerprint = f"sha256:{hashlib.sha256(raw_key).hexdigest()}"
            if fingerprint_ref != expected_fingerprint:
                failures.append(f"trusted reviewer key fingerprint drift: {key_ref}")
                continue
            trusted[(role_ref, reviewer_ref, key_ref)] = (
                Ed25519PublicKey.from_public_bytes(raw_key)
            )
        except (TypeError, ValueError):
            failures.append(f"trusted reviewer key is invalid: {key_ref}")
    return trusted


def verify(
    payload: dict[str, Any] | None = None,
    *,
    trusted_reviewers_payload: dict[str, Any] | None = None,
) -> tuple[list[str], str]:
    ledger = payload if payload is not None else _load()
    failures: list[str] = []

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        failures.extend(
            f"schema validation: {error.message}"
            for error in sorted(
                Draft202012Validator(schema).iter_errors(ledger),
                key=lambda error: list(error.absolute_path),
            )
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"acceptance schema could not be validated: {exc}")

    expected_constants = {
        "ledger_ref": "ledger-ref:fin000-render-acceptance:v1",
        "program_ref": "program-ref:fin000",
        "candidate_pack_ref": "render-pack-ref:finance-compliance-v1",
        "candidate_manifest_ref": "manifest-ref:fin000-render-pack:v1",
        "schema_ref": "schema-ref:fin000-render-acceptance-ledger:v1",
        "review_scope": "planning_only_render_candidate_pack",
    }
    for field, expected in expected_constants.items():
        if ledger.get(field) != expected:
            failures.append(f"{field} must equal {expected}")
    if ledger.get("candidate_manifest_locked") is not True:
        failures.append("candidate manifest must be locked before review")
    if ledger.get("runtime_authority_added") is not False:
        failures.append("FIN-000 review cannot add runtime authority")

    try:
        trust_payload = (
            trusted_reviewers_payload
            if trusted_reviewers_payload is not None
            else _load(TRUSTED_REVIEWERS_PATH)
        )
        trusted_reviewers = _trusted_reviewer_map(trust_payload, failures)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"trusted reviewer registry could not be validated: {exc}")
        trusted_reviewers = {}

    candidate_author_ref = ledger.get("candidate_author_ref")
    if not _safe_ref(candidate_author_ref):
        failures.append("candidate_author_ref must be a safe ref")
    if not PACK_SHA256.fullmatch(str(ledger.get("candidate_pack_digest", ""))):
        failures.append("candidate_pack_digest must be a sha256 ref")

    try:
        actual_assets, actual_pack_digest = _actual_assets_and_digest()
    except (OSError, ValueError) as exc:
        failures.append(str(exc))
        actual_assets, actual_pack_digest = [], ""
    if ledger.get("candidate_pack_digest") != actual_pack_digest:
        failures.append("candidate pack digest does not match current renders")

    assets = ledger.get("assets")
    if not isinstance(assets, list) or len(assets) != 16:
        failures.append("asset manifest must contain exactly sixteen entries")
        assets = []
    filenames: set[str] = set()
    path_refs: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            failures.append("every asset entry must be an object")
            continue
        filename = asset.get("filename")
        path_ref = asset.get("path_ref")
        digest = asset.get("sha256")
        width = asset.get("width")
        height = asset.get("height")
        viewport_class = asset.get("viewport_class")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not filename.endswith(".png")
        ):
            failures.append("asset filename must be a basename ending in .png")
            continue
        if filename in filenames:
            failures.append(f"duplicate asset filename: {filename}")
        filenames.add(filename)
        if not _safe_ref(path_ref) or path_ref in path_refs:
            failures.append(f"asset has invalid or duplicate path_ref: {path_ref!r}")
        else:
            path_refs.add(path_ref)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            failures.append(f"asset has invalid sha256: {filename}")
            continue
        path = RENDER_DIR / filename
        try:
            data, actual_width, actual_height = _png_metadata(path)
        except (OSError, ValueError) as exc:
            failures.append(str(exc))
            continue
        if hashlib.sha256(data).hexdigest() != digest:
            failures.append(f"manifest digest mismatch: {filename}")
        if (width, height) != (actual_width, actual_height):
            failures.append(f"manifest dimensions mismatch: {filename}")
        inventory_contract = EXACT_INVENTORY.get(filename)
        if inventory_contract is None:
            failures.append(f"unexpected render filename: {filename}")
            continue
        expected_viewport, minimum_width, minimum_height = inventory_contract
        if viewport_class != expected_viewport:
            failures.append(f"manifest viewport class mismatch: {filename}")
        if actual_width < minimum_width or actual_height < minimum_height:
            failures.append(f"render dimensions below minimum: {filename}")
    actual_pngs = {asset["name"] for asset in actual_assets}
    if filenames != actual_pngs:
        failures.append("manifest filenames do not match the render directory")
    if filenames != set(EXACT_INVENTORY):
        failures.append("render inventory does not match the exact required filenames")
    try:
        actual_subject_digest = _acceptance_subject_digest(assets)
        if ledger.get("acceptance_subject_digest") != actual_subject_digest:
            failures.append(
                "acceptance subject digest does not match assets and contracts"
            )
    except (OSError, ValueError) as exc:
        failures.append(str(exc))
        actual_subject_digest = ""

    checklist = ledger.get("checklist")
    if not isinstance(checklist, list):
        failures.append("checklist must be a list")
        checklist = []
    checks = {
        item.get("check_ref"): item for item in checklist if isinstance(item, dict)
    }
    if set(checks) != EXPECTED_CHECKS or len(checklist) != len(EXPECTED_CHECKS):
        failures.append("checklist must contain each required check exactly once")
    for check_ref, item in checks.items():
        decision = item.get("decision")
        evidence_refs = item.get("evidence_refs")
        allowed = (
            {"verified_by_automation"}
            if check_ref in AUTOMATED_CHECKS
            else {"pending_independent_review", "accepted", "changes_requested"}
        )
        if decision not in allowed:
            failures.append(f"invalid decision for {check_ref}: {decision!r}")
        if not isinstance(evidence_refs, list) or any(
            not _safe_ref(ref) for ref in evidence_refs
        ):
            failures.append(f"{check_ref} evidence_refs must contain only safe refs")
        if (
            decision in {"verified_by_automation", "accepted", "changes_requested"}
            and not evidence_refs
        ):
            failures.append(f"{check_ref} decision requires evidence refs")

    reviewers = ledger.get("reviewers")
    if not isinstance(reviewers, list):
        failures.append("reviewers must be a list")
        reviewers = []
    roles = {item.get("role_ref"): item for item in reviewers if isinstance(item, dict)}
    if set(roles) != EXPECTED_ROLES or len(reviewers) != len(EXPECTED_ROLES):
        failures.append("reviewers must contain each required role exactly once")
    completed_reviewer_refs: list[str] = []
    completed_key_refs: list[str] = []
    for role_ref, item in roles.items():
        decision = item.get("decision")
        reviewer_ref = item.get("reviewer_ref")
        trusted_key_ref = item.get("trusted_key_ref")
        receipt_ref = item.get("receipt_ref")
        decision_digest = item.get("candidate_pack_digest")
        decision_subject_digest = item.get("acceptance_subject_digest")
        finding_refs = item.get("finding_refs")
        signature_base64url = item.get("signature_base64url")
        if decision not in {"pending", "accepted", "changes_requested"}:
            failures.append(f"invalid reviewer decision for {role_ref}: {decision!r}")
        if decision == "pending":
            if (
                reviewer_ref is not None
                or trusted_key_ref is not None
                or receipt_ref is not None
                or decision_digest is not None
                or decision_subject_digest is not None
                or signature_base64url is not None
            ):
                failures.append(
                    f"pending reviewer {role_ref} cannot claim identity, evidence, digest, or signature fields"
                )
        elif not all(
            _safe_ref(value) for value in (reviewer_ref, trusted_key_ref, receipt_ref)
        ):
            failures.append(
                f"completed reviewer {role_ref} requires safe reviewer, key, and receipt refs"
            )
        elif reviewer_ref == candidate_author_ref:
            failures.append(
                f"reviewer {role_ref} must be independent of the candidate author"
            )
        elif decision_digest != ledger.get("candidate_pack_digest"):
            failures.append(
                f"reviewer {role_ref} decision is stale or not bound to the pack digest"
            )
        elif decision_subject_digest != actual_subject_digest:
            failures.append(
                f"reviewer {role_ref} decision is stale or not bound to the acceptance subject"
            )
        else:
            completed_reviewer_refs.append(reviewer_ref)
            completed_key_refs.append(trusted_key_ref)
            public_key = trusted_reviewers.get(
                (role_ref, reviewer_ref, trusted_key_ref)
            )
            if public_key is None:
                failures.append(
                    f"reviewer {role_ref} is not enrolled for the exact role and key"
                )
            elif not isinstance(signature_base64url, str):
                failures.append(f"reviewer {role_ref} signature is missing")
            else:
                try:
                    public_key.verify(
                        _decode_base64url(signature_base64url),
                        review_decision_message(
                            ledger["ledger_ref"], candidate_author_ref, item
                        ),
                    )
                except (InvalidSignature, TypeError, ValueError):
                    failures.append(f"reviewer {role_ref} signature is invalid")
        if not isinstance(finding_refs, list) or any(
            not _safe_ref(ref) for ref in finding_refs
        ):
            failures.append(
                f"reviewer {role_ref} finding_refs must contain only safe refs"
            )
        if decision == "changes_requested" and not finding_refs:
            failures.append(
                f"reviewer {role_ref} changes_requested requires finding refs"
            )
        if decision == "accepted" and finding_refs:
            failures.append(f"accepted reviewer {role_ref} cannot retain open findings")

    if len(completed_reviewer_refs) != len(set(completed_reviewer_refs)):
        failures.append("completed reviewer identities must be distinct across roles")
    if len(completed_key_refs) != len(set(completed_key_refs)):
        failures.append("completed reviewer keys must be distinct across roles")

    checks_accepted = bool(checks) and all(
        item.get("decision") in {"verified_by_automation", "accepted"}
        for item in checks.values()
    )
    roles_accepted = bool(roles) and all(
        item.get("decision") == "accepted" for item in roles.values()
    )
    if roles_accepted and not INDEPENDENT_HUMAN_IDENTITY_AUTHORITY_CONFIGURED:
        failures.append(
            "independent human identity authority is not externally configured"
        )
    serialized = json.dumps(ledger, sort_keys=True).lower()
    for marker in FORBIDDEN_DURABLE_MARKERS:
        if marker in serialized:
            failures.append(f"ledger contains forbidden durable marker: {marker}")

    try:
        gallery = GALLERY_PATH.read_text(encoding="utf-8")
        for filename in actual_pngs:
            if gallery.count(f"({filename})") != 1:
                failures.append(f"gallery must link {filename} exactly once")
    except OSError as exc:
        failures.append(f"review gallery could not be read: {exc}")

    try:
        validate_safe_execution_text(
            str(ledger.get("next_safe_action", "")), "next_safe_action"
        )
    except ValueError as exc:
        failures.append(f"next_safe_action is unsafe: {exc}")

    promotion_ready = (
        checks_accepted
        and roles_accepted
        and INDEPENDENT_HUMAN_IDENTITY_AUTHORITY_CONFIGURED
        and not failures
    )
    if ledger.get("promotion_ready") is not promotion_ready:
        failures.append(
            "promotion_ready does not match all integrity, checklist, and reviewer gates"
        )
        promotion_ready = False
    expected_status = "accepted" if promotion_ready else "pending_independent_review"
    if any(
        item.get("decision") == "changes_requested"
        for item in [*checks.values(), *roles.values()]
    ):
        expected_status = "changes_requested"
    if ledger.get("status") != expected_status:
        failures.append(f"status must be {expected_status}")
        promotion_ready = False

    return failures, "ACCEPTED" if promotion_ready and not failures else "PENDING"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the FIN-000 render acceptance ledger."
    )
    parser.add_argument(
        "--require-accepted",
        action="store_true",
        help=(
            "fail unless every independent review bound to the current pack is accepted"
        ),
    )
    args = parser.parse_args()
    try:
        failures, state = verify()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    if args.require_accepted and state != "ACCEPTED":
        print("FAIL: FIN-000 independent render acceptance is still pending")
        return 2
    print(f"FIN-000 render acceptance ledger verified: {state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
