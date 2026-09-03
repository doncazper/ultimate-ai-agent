from __future__ import annotations

import base64
import ctypes
import errno
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

MAX_JSON_BYTES = 16 * 1024 * 1024
REQUEST_ENV = "UAA_TAW08_PHASE_REQUEST"
WORKER_DIGEST_ENV = "UAA_TAW08_PHASE_WORKER_DIGEST"
DRIVER_PATH_REF = (
    "repo-path-ref:scripts/run_tool_aware_cognition_taw08_evidence_phases.py"
)
WORKER_PATH_REF = "repo-path-ref:scripts/taw08_evidence_phase_worker.py"
SOURCE_DIGEST_FIELDS = {
    "driver_source_digest_ref",
    "worker_source_digest_ref",
}


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _require_posix_private_path_support() -> None:
    if os.name != "posix" or not hasattr(os, "getuid"):
        raise ValueError("private path enforcement is unavailable on this platform")


def _darwin_extended_acl_tags(
    descriptor: int,
    *,
    purpose: str,
) -> tuple[int, ...]:
    if sys.platform != "darwin":
        return ()
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        acl_get_fd_np = libc.acl_get_fd_np
        acl_get_fd_np.argtypes = (ctypes.c_int, ctypes.c_int)
        acl_get_fd_np.restype = ctypes.c_void_p
        acl_get_entry = libc.acl_get_entry
        acl_get_entry.argtypes = (
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        )
        acl_get_entry.restype = ctypes.c_int
        acl_get_tag_type = libc.acl_get_tag_type
        acl_get_tag_type.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
        )
        acl_get_tag_type.restype = ctypes.c_int
        acl_free = libc.acl_free
        acl_free.argtypes = (ctypes.c_void_p,)
        acl_free.restype = ctypes.c_int
    except (AttributeError, OSError) as exc:
        raise ValueError(f"{purpose} access controls cannot be verified") from exc
    ctypes.set_errno(0)
    acl = acl_get_fd_np(descriptor, 0x100)
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return ()
        raise ValueError(f"{purpose} access controls cannot be verified")
    try:
        tags: list[int] = []
        for index in range(170):
            ctypes.set_errno(0)
            entry = ctypes.c_void_p()
            entry_selector = 0 if index == 0 else -1  # FIRST, then NEXT
            entry_result = acl_get_entry(acl, entry_selector, ctypes.byref(entry))
            if entry_result == -1 and ctypes.get_errno() == errno.EINVAL and index:
                break
            if entry_result != 0 or entry.value is None:
                raise ValueError(f"{purpose} access controls cannot be verified")
            tag = ctypes.c_int()
            if acl_get_tag_type(entry, ctypes.byref(tag)) != 0:
                raise ValueError(f"{purpose} access controls cannot be verified")
            tags.append(tag.value)
        else:
            raise ValueError(f"{purpose} access controls cannot be verified")
    finally:
        free_result = acl_free(acl)
    if free_result != 0:
        raise ValueError(f"{purpose} access controls cannot be verified")
    return tuple(tags)


def _require_no_extended_acl_fd(descriptor: int, *, purpose: str) -> None:
    if _darwin_extended_acl_tags(descriptor, purpose=purpose):
        raise ValueError(f"{purpose} must not have an extended ACL")


def _require_no_extended_acl_grants_fd(
    descriptor: int,
    *,
    purpose: str,
) -> None:
    if any(
        tag != 2 for tag in _darwin_extended_acl_tags(descriptor, purpose=purpose)
    ):
        raise ValueError(f"{purpose} has unsafe extended ACL grants")


def _private_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _require_root_owned_lexical_symlinks(path: Path, *, purpose: str) -> None:
    if not path.is_absolute():
        raise ValueError(f"{purpose} must be absolute")
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    lexical = Path(path.anchor)
    try:
        for component in path.parent.parts[1:]:
            lexical /= component
            metadata = os.lstat(lexical)
            if stat.S_ISLNK(metadata.st_mode):
                if metadata.st_uid != 0:
                    raise ValueError(
                        f"{purpose} contains an unsafe linked ancestor"
                    )
                continue
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid not in {0, os.getuid()}
                or (
                    stat.S_IMODE(metadata.st_mode) & 0o022
                    and not stat.S_IMODE(metadata.st_mode) & stat.S_ISVTX
                )
            ):
                raise ValueError(f"{purpose} has an unsafe lexical ancestor")
            descriptor = os.open(
                lexical,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            try:
                opened = os.fstat(descriptor)
                if not os.path.samestat(metadata, opened):
                    raise ValueError(
                        f"{purpose} lexical ancestor changed during inspection"
                    )
                _require_no_extended_acl_grants_fd(descriptor, purpose=purpose)
                closed_over = os.fstat(descriptor)
                final = os.lstat(lexical)
            finally:
                os.close(descriptor)
            if (
                _private_identity(opened) != _private_identity(closed_over)
                or _private_identity(opened) != _private_identity(final)
                or not os.path.samestat(opened, final)
            ):
                raise ValueError(
                    f"{purpose} lexical ancestor changed during inspection"
                )
    except OSError as exc:
        raise ValueError(f"{purpose} ancestor is unavailable") from exc


def _require_safe_private_ancestor_chain(path: Path, *, purpose: str) -> None:
    _require_root_owned_lexical_symlinks(path, purpose=purpose)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    ancestor = resolved.parent
    while True:
        descriptor = -1
        try:
            initial = os.lstat(ancestor)
            if (
                not stat.S_ISDIR(initial.st_mode)
                or initial.st_uid not in {0, os.getuid()}
                or (
                    stat.S_IMODE(initial.st_mode) & 0o022
                    and not stat.S_IMODE(initial.st_mode) & stat.S_ISVTX
                )
            ):
                raise ValueError(f"{purpose} has an unsafe ancestor")
            descriptor = os.open(
                ancestor,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            opened = os.fstat(descriptor)
            if not os.path.samestat(initial, opened):
                raise ValueError(f"{purpose} ancestor changed during inspection")
            _require_no_extended_acl_grants_fd(descriptor, purpose=purpose)
            closed_over = os.fstat(descriptor)
            final = os.lstat(ancestor)
        except OSError as exc:
            raise ValueError(f"{purpose} ancestor is unavailable") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if (
            _private_identity(opened) != _private_identity(closed_over)
            or _private_identity(opened) != _private_identity(final)
            or not os.path.samestat(opened, final)
        ):
            raise ValueError(f"{purpose} ancestor changed during inspection")
        if ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent


def _read_owner_only_file(path: Path, *, purpose: str) -> tuple[Path, bytes]:
    _require_posix_private_path_support()
    if not path.is_absolute() or path.is_symlink():
        raise ValueError(f"{purpose} must be an absolute regular file")
    _require_safe_private_ancestor_chain(path, purpose=purpose)
    resolved = path.resolve(strict=True)
    initial = os.lstat(resolved)
    if (
        not stat.S_ISREG(initial.st_mode)
        or initial.st_uid != os.getuid()
        or stat.S_IMODE(initial.st_mode) & 0o077
        or initial.st_nlink != 1
        or initial.st_size <= 0
        or initial.st_size > MAX_JSON_BYTES
    ):
        raise ValueError(f"{purpose} must be owner-only")
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    descriptor = os.open(
        resolved,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | nofollow_flag,
    )
    try:
        opened = os.fstat(descriptor)
        if not os.path.samestat(initial, opened):
            raise ValueError(f"{purpose} changed during inspection")
        _require_no_extended_acl_fd(descriptor, purpose=purpose)
        chunks: list[bytes] = []
        observed = 0
        while observed <= MAX_JSON_BYTES:
            chunk = os.read(
                descriptor,
                min(64 * 1024, MAX_JSON_BYTES + 1 - observed),
            )
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
        closed_over = os.fstat(descriptor)
        final = os.lstat(resolved)
    finally:
        os.close(descriptor)
    if (
        observed != opened.st_size
        or observed > MAX_JSON_BYTES
        or _private_identity(opened) != _private_identity(closed_over)
        or _private_identity(opened) != _private_identity(final)
        or not os.path.samestat(opened, final)
    ):
        raise ValueError(f"{purpose} changed during inspection")
    return resolved, b"".join(chunks)


def _owner_only_file(path: Path, *, purpose: str) -> Path:
    resolved, _content = _read_owner_only_file(path, purpose=purpose)
    return resolved


def _load_owner_json(path: Path, *, purpose: str) -> dict[str, object]:
    _resolved, content = _read_owner_only_file(path, purpose=purpose)
    try:
        value = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"{purpose} is invalid") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{purpose} is invalid")
    return value


def _require_directory(path_value: object, *, purpose: str) -> Path:
    if not isinstance(path_value, str):
        raise ValueError(f"{purpose} is invalid")
    path = Path(path_value)
    if not path.is_absolute() or path.is_symlink():
        raise ValueError(f"{purpose} is invalid")
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"{purpose} is invalid")
    return resolved


def _load_repository_modules(candidate_root: Path) -> tuple[ModuleType, ModuleType]:
    # This worker is invoked only by the repository's authenticated -I/-S
    # preflight. Repository imports are deliberately delayed until that boundary.
    if (
        not sys.flags.isolated
        or not sys.flags.no_site
        or os.environ.get("UAA_TAW08_PREFLIGHT_COMPLETE") != "1"
    ):
        raise RuntimeError("TAW-08 phase worker requires the locked preflight")
    source_root = candidate_root / "src"
    if not source_root.is_dir():
        raise RuntimeError("TAW-08 candidate source root is unavailable")
    sys.path.insert(0, str(candidate_root))
    sys.path.insert(0, str(source_root))
    import scripts.verify_tool_aware_cognition_taw08 as repository_verifier
    import ultimate_ai_agent.core.evals.tool_aware_acceptance as acceptance

    return repository_verifier, acceptance


def _verify_candidate_operational_sources(
    verifier: ModuleType,
    *,
    candidate_root: Path,
    request: dict[str, object],
) -> None:
    revision = os.environ.get("UAA_TAW08_LOCKED_CHILD_REVISION")
    if not revision:
        raise RuntimeError("TAW-08 locked candidate revision is unavailable")
    lock, _content = verifier._candidate_lock(
        revision,
        repository_root=candidate_root,
    )
    digest_by_ref = {item.path_ref: item.content_digest_ref for item in lock.entries}
    actual_worker_digest = (
        "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    )
    if (
        request.get("driver_source_digest_ref") != digest_by_ref.get(DRIVER_PATH_REF)
        or request.get("worker_source_digest_ref") != digest_by_ref.get(WORKER_PATH_REF)
        or actual_worker_digest != digest_by_ref.get(WORKER_PATH_REF)
    ):
        raise RuntimeError("TAW-08 phase operational source binding drift")


def _require_clean_exact_worktree(
    verifier: ModuleType,
    repository_root: Path,
    *,
    expected_revision: str | None = None,
) -> str:
    top_level = Path(
        verifier._git("rev-parse", "--show-toplevel", repository_root=repository_root)
        .decode("utf-8")
        .strip()
    ).resolve()
    if top_level != repository_root:
        raise RuntimeError("TAW-08 phase repository root drift")
    revision = (
        verifier._git("rev-parse", "HEAD", repository_root=repository_root)
        .decode("ascii")
        .strip()
    )
    if expected_revision is not None and revision != expected_revision:
        raise RuntimeError("TAW-08 phase repository revision drift")
    if verifier._git(
        "status",
        "--porcelain",
        "--untracked-files=all",
        repository_root=repository_root,
    ) or verifier._index_has_hidden_worktree_entries(repository_root=repository_root):
        raise RuntimeError("TAW-08 phase repository must be clean")
    return revision


def _load_founder_evidence(acceptance: ModuleType, path_value: object) -> Any:
    if not isinstance(path_value, str):
        raise ValueError("founder evidence path is invalid")
    payload = _load_owner_json(Path(path_value), purpose="founder evidence")
    evidence = acceptance.FounderPrivateAcceptanceEvidence.model_validate(payload)
    if acceptance.durable_payload_has_forbidden_fields(
        evidence.model_dump(mode="json")
    ):
        raise ValueError("founder evidence contains forbidden durable fields")
    if any(
        (
            evidence.runtime_model_calls_added,
            evidence.provider_calls_added,
            evidence.execution_authority_added,
            evidence.raw_content_persisted,
        )
    ):
        raise ValueError("founder evidence expands authority")
    return evidence


def _candidate_context(
    verifier: ModuleType,
    acceptance: ModuleType,
    *,
    candidate_root: Path,
    founder_evidence: Any,
) -> tuple[Any, Any, Any]:
    candidate_revision = founder_evidence.candidate_revision_ref.removeprefix(
        "git-sha:"
    )
    _require_clean_exact_worktree(
        verifier, candidate_root, expected_revision=candidate_revision
    )
    candidate_lock, _content = verifier._candidate_lock(
        candidate_revision, repository_root=candidate_root
    )
    if (
        candidate_lock.git_revision_ref != founder_evidence.candidate_revision_ref
        or candidate_lock.manifest_digest_ref
        != founder_evidence.candidate_manifest_digest_ref
        or founder_evidence.exact_head_foundation_receipt.stage != "exact_head"
        or founder_evidence.exact_head_foundation_receipt.revision_ref
        != candidate_lock.git_revision_ref
        or not founder_evidence.exact_head_foundation_receipt.passed
    ):
        raise ValueError("founder evidence candidate binding drift")
    candidate_receipt = verifier.verify_repository_candidate(
        candidate_lock, repository_root=candidate_root
    )
    report = acceptance.evaluate_taw08_acceptance(
        candidate_lock=candidate_lock,
        candidate_verification_receipt=candidate_receipt,
        founder_evidence=founder_evidence,
    )
    _require_report(
        report,
        expected_status="founder_private_accepted_postmerge_pending",
    )
    return candidate_lock, candidate_receipt, report


def _require_report(report: Any, *, expected_status: str) -> None:
    status = getattr(report.status, "value", report.status)
    if (
        status != expected_status
        or not report.founder_private_accepted
        or report.failure_refs
        or report.independent_promotion_ready
        or report.sealed_holdout_evidence_verified
        or report.public_quality_claims_allowed
        or report.production_authority_added
        or report.runtime_model_calls_added
        or report.provider_calls_added
        or report.execution_authority_added
        or report.raw_content_persisted
    ):
        raise RuntimeError("TAW-08 phase report status or authority drift")


def _json_bytes(model: Any) -> bytes:
    return (
        json.dumps(
            model.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def replace_reconciliation_block(
    candidate_content: bytes,
    *,
    start_marker: str,
    json_marker: str,
    end_marker: str,
    narrative: str,
    artifact_json: str,
) -> bytes:
    try:
        candidate_text = candidate_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("TAW-08 reconciliation candidate is not UTF-8") from exc
    if any(
        candidate_text.count(marker) != 1
        for marker in (start_marker, json_marker, end_marker)
    ):
        raise ValueError("TAW-08 reconciliation marker census drift")
    prefix, found_start, after_start = candidate_text.partition(start_marker)
    _old_narrative, found_json, after_json = after_start.partition(json_marker)
    _old_json, found_end, suffix = after_json.partition(end_marker)
    if not found_start or not found_json or not found_end:
        raise ValueError("TAW-08 reconciliation marker order drift")
    replacement = (
        prefix
        + start_marker
        + "\n"
        + narrative
        + "\n"
        + json_marker
        + "\n"
        + artifact_json
        + "\n"
        + end_marker
        + suffix
    )
    rendered = replacement.encode("utf-8")
    # A second split proves the bytes outside the exact marker span did not move.
    rendered_prefix, _, rendered_after_start = replacement.partition(start_marker)
    _, _, rendered_after_json = rendered_after_start.partition(json_marker)
    _, _, rendered_suffix = rendered_after_json.partition(end_marker)
    if rendered_prefix != prefix or rendered_suffix != suffix:
        raise RuntimeError("TAW-08 reconciliation changed bytes outside markers")
    return rendered


def _reconciliation_content(
    acceptance: ModuleType,
    verifier: ModuleType,
    *,
    candidate_root: Path,
    candidate_revision: str,
    path_ref: str,
    report: Any,
    founder_evidence: Any,
) -> bytes:
    evidence_refs = tuple(
        sorted((report.report_fingerprint_ref, founder_evidence.evidence_digest_ref))
    )
    artifact = acceptance.ClaimReconciliationArtifact(
        entries=(
            acceptance.ClaimReconciliationEntry(
                claim_ref=acceptance.TAW08_RECONCILIATION_CLAIM_REFS[path_ref],
                status="implemented",
                evidence_refs=evidence_refs,
            ),
        )
    )
    artifact_payload = artifact.model_dump(mode="json")
    if acceptance.durable_payload_has_forbidden_fields(artifact_payload):
        raise ValueError("TAW-08 reconciliation contains forbidden durable fields")
    artifact_json = json.dumps(artifact_payload, sort_keys=True, separators=(",", ":"))
    relative_path = path_ref.removeprefix("repo-path-ref:")
    candidate_content = verifier._git(
        "show",
        f"{candidate_revision}:{relative_path}",
        repository_root=candidate_root,
    )
    content = replace_reconciliation_block(
        candidate_content,
        start_marker=acceptance.TAW08_RECONCILIATION_START,
        json_marker=acceptance.TAW08_RECONCILIATION_JSON,
        end_marker=acceptance.TAW08_RECONCILIATION_END,
        narrative=acceptance.TAW08_RECONCILIATION_NARRATIVES[path_ref]["implemented"],
        artifact_json=artifact_json,
    )
    if (
        acceptance._parse_bounded_claim_reconciliation_markdown(
            path_ref, content, candidate_content
        )
        != artifact
    ):
        raise RuntimeError("TAW-08 reconciliation output failed validation")
    return content


def _artifact_transport(
    *, path_ref: str, artifact_kind: str, content: bytes
) -> dict[str, object]:
    if not content or len(content) > 4 * 1024 * 1024:
        raise ValueError("TAW-08 phase artifact size is invalid")
    return {
        "path_ref": path_ref,
        "artifact_kind": artifact_kind,
        "content_digest_ref": f"sha256:{hashlib.sha256(content).hexdigest()}",
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def _phase_receipt(payload: dict[str, object]) -> dict[str, object]:
    return {**payload, "receipt_digest_ref": _canonical_digest(payload)}


def _prepare_delta(
    verifier: ModuleType,
    acceptance: ModuleType,
    request: dict[str, object],
) -> dict[str, object]:
    expected = {
        "schema_version",
        "phase",
        "candidate_repository",
        "founder_evidence_path",
        *SOURCE_DIGEST_FIELDS,
    }
    if set(request) != expected:
        raise ValueError("TAW-08 prepare request schema drift")
    candidate_root = _require_directory(
        request["candidate_repository"], purpose="candidate repository"
    )
    founder_evidence = _load_founder_evidence(
        acceptance, request["founder_evidence_path"]
    )
    candidate_lock, _candidate_receipt, report = _candidate_context(
        verifier,
        acceptance,
        candidate_root=candidate_root,
        founder_evidence=founder_evidence,
    )
    acceptance_artifact = acceptance.redacted_acceptance_report_artifact(report)
    acceptance_content = _json_bytes(acceptance_artifact)
    artifacts = [
        _artifact_transport(
            path_ref=acceptance.TAW08_ACCEPTANCE_REPORT_PATH_REF,
            artifact_kind="acceptance_report",
            content=acceptance_content,
        )
    ]
    for path_ref in acceptance.TAW08_ACTIVE_TRUTH_PATH_REFS:
        artifacts.append(
            _artifact_transport(
                path_ref=path_ref,
                artifact_kind="claim_reconciliation",
                content=_reconciliation_content(
                    acceptance,
                    verifier,
                    candidate_root=candidate_root,
                    candidate_revision=candidate_lock.git_revision_ref.removeprefix(
                        "git-sha:"
                    ),
                    path_ref=path_ref,
                    report=report,
                    founder_evidence=founder_evidence,
                ),
            )
        )
    artifacts = sorted(artifacts, key=lambda item: str(item["path_ref"]))
    expected_refs = tuple(
        sorted(
            (
                acceptance.TAW08_ACCEPTANCE_REPORT_PATH_REF,
                *acceptance.TAW08_ACTIVE_TRUTH_PATH_REFS,
            )
        )
    )
    if tuple(item["path_ref"] for item in artifacts) != expected_refs:
        raise RuntimeError("TAW-08 prepare artifact census drift")
    receipt = _phase_receipt(
        {
            "schema_version": "uaa-taw08-prepare-delta-phase.v1",
            "phase": "prepare_delta",
            "candidate_revision_ref": candidate_lock.git_revision_ref,
            "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
            "founder_evidence_digest_ref": founder_evidence.evidence_digest_ref,
            "driver_source_digest_ref": request["driver_source_digest_ref"],
            "worker_source_digest_ref": request["worker_source_digest_ref"],
            "pre_delta_report_fingerprint_ref": report.report_fingerprint_ref,
            "status": "founder_private_accepted_postmerge_pending",
            "artifact_path_refs": expected_refs,
            "independent_promotion_ready": False,
            "public_quality_claims_allowed": False,
            "production_authority_added": False,
            "runtime_model_calls_added": False,
            "provider_calls_added": False,
            "execution_authority_added": False,
            "raw_content_persisted": False,
        }
    )
    _require_clean_exact_worktree(
        verifier,
        candidate_root,
        expected_revision=candidate_lock.git_revision_ref.removeprefix("git-sha:"),
    )
    return {
        "schema_version": "uaa-taw08-phase-worker-response.v1",
        "phase": "prepare_delta",
        "receipt": receipt,
        "artifacts": artifacts,
    }


def _manifest_from_git(
    verifier: ModuleType,
    acceptance: ModuleType,
    *,
    candidate_root: Path,
    candidate_lock: Any,
    delta_revision: str,
) -> tuple[Any, Any, dict[str, bytes]]:
    delta_revision_ref = f"git-sha:{delta_revision}"
    census = verifier.derive_revision_delta_census(
        candidate_lock.git_revision_ref,
        delta_revision_ref,
        repository_root=candidate_root,
    )
    expected_path_refs = tuple(
        sorted(
            (
                acceptance.TAW08_ACCEPTANCE_REPORT_PATH_REF,
                *acceptance.TAW08_ACTIVE_TRUTH_PATH_REFS,
            )
        )
    )
    if (
        census.path_refs != expected_path_refs
        or census.history_path_refs != expected_path_refs
    ):
        raise ValueError("TAW-08 M1-to-M2 path census drift")
    content_by_ref = {
        path_ref: verifier._git(
            "show",
            f"{delta_revision}:{path_ref.removeprefix('repo-path-ref:')}",
            repository_root=candidate_root,
        )
        for path_ref in census.path_refs
    }
    manifest = acceptance.bind_evidence_only_delta(
        candidate_revision_ref=candidate_lock.git_revision_ref,
        candidate_manifest_digest_ref=candidate_lock.manifest_digest_ref,
        delta_revision_ref=delta_revision_ref,
        entries=tuple(
            acceptance.EvidenceOnlyDeltaEntry(
                path_ref=path_ref,
                artifact_kind=(
                    "acceptance_report"
                    if path_ref == acceptance.TAW08_ACCEPTANCE_REPORT_PATH_REF
                    else "claim_reconciliation"
                ),
                content_digest_ref=(
                    f"sha256:{hashlib.sha256(content_by_ref[path_ref]).hexdigest()}"
                ),
            )
            for path_ref in sorted(content_by_ref)
        ),
    )
    return manifest, census, content_by_ref


def _verify_delta(
    verifier: ModuleType,
    acceptance: ModuleType,
    request: dict[str, object],
) -> dict[str, object]:
    expected = {
        "schema_version",
        "phase",
        "candidate_repository",
        "delta_repository",
        "founder_evidence_path",
        *SOURCE_DIGEST_FIELDS,
    }
    if set(request) != expected:
        raise ValueError("TAW-08 delta request schema drift")
    candidate_root = _require_directory(
        request["candidate_repository"], purpose="candidate repository"
    )
    delta_root = _require_directory(
        request["delta_repository"], purpose="delta repository"
    )
    founder_evidence = _load_founder_evidence(
        acceptance, request["founder_evidence_path"]
    )
    candidate_lock, candidate_receipt, pre_report = _candidate_context(
        verifier,
        acceptance,
        candidate_root=candidate_root,
        founder_evidence=founder_evidence,
    )
    delta_revision = _require_clean_exact_worktree(verifier, delta_root)
    if delta_revision == candidate_lock.git_revision_ref.removeprefix("git-sha:"):
        raise ValueError("TAW-08 evidence delta requires a later revision")
    manifest, _census, _content = _manifest_from_git(
        verifier,
        acceptance,
        candidate_root=candidate_root,
        candidate_lock=candidate_lock,
        delta_revision=delta_revision,
    )
    delta_receipt = verifier.verify_repository_evidence_delta(
        candidate_lock=candidate_lock,
        delta=manifest,
        validated_acceptance_reports_by_path_ref={
            acceptance.TAW08_ACCEPTANCE_REPORT_PATH_REF: pre_report
        },
        repository_root=candidate_root,
    )
    postmerge_receipt = verifier.verify_repository_foundation_gate(
        stage="postmerge", repository_root=delta_root
    )
    if (
        postmerge_receipt.revision_ref != manifest.delta_revision_ref
        or postmerge_receipt.stage != "postmerge"
        or not postmerge_receipt.passed
        or not postmerge_receipt.redacted
        or postmerge_receipt.raw_content_persisted
    ):
        raise RuntimeError("TAW-08 postmerge Foundation receipt drift")
    report = acceptance.evaluate_taw08_acceptance(
        candidate_lock=candidate_lock,
        candidate_verification_receipt=candidate_receipt,
        founder_evidence=founder_evidence,
        evidence_only_delta=manifest,
        evidence_only_delta_verification_receipt=delta_receipt,
        postmerge_foundation_receipt=postmerge_receipt,
    )
    _require_report(
        report,
        expected_status="founder_private_accepted_final_publication_pending",
    )
    final_artifact = acceptance.build_final_acceptance_publication_artifact(
        candidate_revision_ref=candidate_lock.git_revision_ref,
        candidate_manifest_digest_ref=candidate_lock.manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence.evidence_digest_ref,
        delta=manifest,
        delta_verification_receipt=delta_receipt,
        postmerge_foundation_receipt=postmerge_receipt,
    )
    if (
        final_artifact.independent_promotion_ready
        or final_artifact.public_quality_claims_allowed
        or final_artifact.raw_content_persisted
    ):
        raise RuntimeError("TAW-08 final artifact expands authority")
    receipt = _phase_receipt(
        {
            "schema_version": "uaa-taw08-verified-delta-phase.v1",
            "phase": "verify_delta",
            "candidate_revision_ref": candidate_lock.git_revision_ref,
            "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
            "founder_evidence_digest_ref": founder_evidence.evidence_digest_ref,
            "driver_source_digest_ref": request["driver_source_digest_ref"],
            "worker_source_digest_ref": request["worker_source_digest_ref"],
            "pre_delta_report_fingerprint_ref": pre_report.report_fingerprint_ref,
            "delta_revision_ref": manifest.delta_revision_ref,
            "evidence_only_delta": manifest.model_dump(mode="json"),
            "evidence_only_delta_verification_receipt": (
                delta_receipt.model_dump(mode="json")
            ),
            "postmerge_foundation_receipt": postmerge_receipt.model_dump(mode="json"),
            "intermediate_report_fingerprint_ref": report.report_fingerprint_ref,
            "status": "founder_private_accepted_final_publication_pending",
            "independent_promotion_ready": False,
            "public_quality_claims_allowed": False,
            "production_authority_added": False,
            "runtime_model_calls_added": False,
            "provider_calls_added": False,
            "execution_authority_added": False,
            "raw_content_persisted": False,
        }
    )
    _require_clean_exact_worktree(
        verifier,
        candidate_root,
        expected_revision=candidate_lock.git_revision_ref.removeprefix("git-sha:"),
    )
    _require_clean_exact_worktree(
        verifier, delta_root, expected_revision=delta_revision
    )
    return {
        "schema_version": "uaa-taw08-phase-worker-response.v1",
        "phase": "verify_delta",
        "receipt": receipt,
        "artifacts": [
            _artifact_transport(
                path_ref=acceptance.TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
                artifact_kind="final_acceptance_report",
                content=_json_bytes(final_artifact),
            )
        ],
    }


def _load_verified_delta_receipt(
    acceptance: ModuleType, path_value: object
) -> tuple[dict[str, object], Any, Any, Any]:
    if not isinstance(path_value, str):
        raise ValueError("verified delta receipt path is invalid")
    payload = _load_owner_json(Path(path_value), purpose="verified delta phase receipt")
    expected = {
        "schema_version",
        "phase",
        "candidate_revision_ref",
        "candidate_manifest_digest_ref",
        "founder_evidence_digest_ref",
        "driver_source_digest_ref",
        "worker_source_digest_ref",
        "pre_delta_report_fingerprint_ref",
        "delta_revision_ref",
        "evidence_only_delta",
        "evidence_only_delta_verification_receipt",
        "postmerge_foundation_receipt",
        "intermediate_report_fingerprint_ref",
        "status",
        "independent_promotion_ready",
        "public_quality_claims_allowed",
        "production_authority_added",
        "runtime_model_calls_added",
        "provider_calls_added",
        "execution_authority_added",
        "raw_content_persisted",
        "receipt_digest_ref",
    }
    if (
        set(payload) != expected
        or payload.get("schema_version") != "uaa-taw08-verified-delta-phase.v1"
        or payload.get("phase") != "verify_delta"
        or payload.get("status") != "founder_private_accepted_final_publication_pending"
        or any(
            payload.get(field) is not False
            for field in (
                "independent_promotion_ready",
                "public_quality_claims_allowed",
                "production_authority_added",
                "runtime_model_calls_added",
                "provider_calls_added",
                "execution_authority_added",
                "raw_content_persisted",
            )
        )
    ):
        raise ValueError("verified delta phase receipt schema drift")
    digest_payload = {
        key: value for key, value in payload.items() if key != "receipt_digest_ref"
    }
    if payload["receipt_digest_ref"] != _canonical_digest(digest_payload):
        raise ValueError("verified delta phase receipt digest drift")
    manifest = acceptance.EvidenceOnlyDeltaManifest.model_validate(
        payload["evidence_only_delta"]
    )
    delta_receipt = acceptance._EvidenceOnlyDeltaVerificationReceipt.model_validate(
        payload["evidence_only_delta_verification_receipt"]
    )
    foundation_receipt = acceptance.FoundationGateReceipt.model_validate(
        payload["postmerge_foundation_receipt"]
    )
    return payload, manifest, delta_receipt, foundation_receipt


def _verify_current_postmerge_foundation_receipt(
    verifier: ModuleType,
    *,
    delta_root: Path,
    stored_receipt: Any,
) -> Any:
    current_receipt = verifier.verify_repository_foundation_gate(
        stage="postmerge",
        repository_root=delta_root,
    )
    stable_fields = (
        "stage",
        "revision_ref",
        "command_mode",
        "evaluator_environment_receipt",
        "evaluator_environment_digest_ref",
        "passed",
        "redacted",
        "raw_content_persisted",
    )
    if (
        any(
            getattr(current_receipt, field, None)
            != getattr(stored_receipt, field, None)
            for field in stable_fields
        )
        or current_receipt.stage != "postmerge"
        or not current_receipt.passed
        or not current_receipt.redacted
        or current_receipt.raw_content_persisted
    ):
        raise ValueError("stored postmerge Foundation receipt differs from Git")
    return stored_receipt


def _verify_publication(
    verifier: ModuleType,
    acceptance: ModuleType,
    request: dict[str, object],
) -> dict[str, object]:
    expected = {
        "schema_version",
        "phase",
        "candidate_repository",
        "delta_repository",
        "publication_repository",
        "founder_evidence_path",
        "verified_delta_receipt_path",
        *SOURCE_DIGEST_FIELDS,
    }
    if set(request) != expected:
        raise ValueError("TAW-08 publication request schema drift")
    candidate_root = _require_directory(
        request["candidate_repository"], purpose="candidate repository"
    )
    delta_root = _require_directory(
        request["delta_repository"], purpose="delta repository"
    )
    publication_root = _require_directory(
        request["publication_repository"], purpose="publication repository"
    )
    founder_evidence = _load_founder_evidence(
        acceptance, request["founder_evidence_path"]
    )
    phase_receipt, stored_manifest, stored_delta_receipt, postmerge_receipt = (
        _load_verified_delta_receipt(acceptance, request["verified_delta_receipt_path"])
    )
    candidate_lock, candidate_receipt, pre_report = _candidate_context(
        verifier,
        acceptance,
        candidate_root=candidate_root,
        founder_evidence=founder_evidence,
    )
    if (
        phase_receipt["candidate_revision_ref"] != candidate_lock.git_revision_ref
        or phase_receipt["candidate_manifest_digest_ref"]
        != candidate_lock.manifest_digest_ref
        or phase_receipt["founder_evidence_digest_ref"]
        != founder_evidence.evidence_digest_ref
        or phase_receipt["driver_source_digest_ref"]
        != request["driver_source_digest_ref"]
        or phase_receipt["worker_source_digest_ref"]
        != request["worker_source_digest_ref"]
        or phase_receipt["pre_delta_report_fingerprint_ref"]
        != pre_report.report_fingerprint_ref
    ):
        raise ValueError("verified delta phase candidate binding drift")
    delta_revision = _require_clean_exact_worktree(
        verifier,
        delta_root,
        expected_revision=stored_manifest.delta_revision_ref.removeprefix("git-sha:"),
    )
    manifest, _census, _content = _manifest_from_git(
        verifier,
        acceptance,
        candidate_root=candidate_root,
        candidate_lock=candidate_lock,
        delta_revision=delta_revision,
    )
    if manifest != stored_manifest:
        raise ValueError("verified delta manifest differs from Git")
    delta_receipt = verifier.verify_repository_evidence_delta(
        candidate_lock=candidate_lock,
        delta=manifest,
        validated_acceptance_reports_by_path_ref={
            acceptance.TAW08_ACCEPTANCE_REPORT_PATH_REF: pre_report
        },
        repository_root=candidate_root,
    )
    if delta_receipt != stored_delta_receipt:
        raise ValueError("verified delta receipt differs from Git")
    postmerge_receipt = _verify_current_postmerge_foundation_receipt(
        verifier,
        delta_root=delta_root,
        stored_receipt=postmerge_receipt,
    )
    if (
        postmerge_receipt.stage != "postmerge"
        or postmerge_receipt.revision_ref != manifest.delta_revision_ref
        or not postmerge_receipt.passed
        or postmerge_receipt.raw_content_persisted
    ):
        raise ValueError("stored postmerge Foundation receipt drift")
    intermediate_report = acceptance.evaluate_taw08_acceptance(
        candidate_lock=candidate_lock,
        candidate_verification_receipt=candidate_receipt,
        founder_evidence=founder_evidence,
        evidence_only_delta=manifest,
        evidence_only_delta_verification_receipt=delta_receipt,
        postmerge_foundation_receipt=postmerge_receipt,
    )
    _require_report(
        intermediate_report,
        expected_status="founder_private_accepted_final_publication_pending",
    )
    if (
        phase_receipt["intermediate_report_fingerprint_ref"]
        != intermediate_report.report_fingerprint_ref
    ):
        raise ValueError("verified delta report fingerprint drift")
    publication_revision = _require_clean_exact_worktree(verifier, publication_root)
    if publication_revision == delta_revision:
        raise ValueError("TAW-08 publication requires a later revision")
    history = verifier.derive_publication_history_census(
        manifest.delta_revision_ref,
        f"git-sha:{publication_revision}",
        repository_root=candidate_root,
    )
    expected_publication_paths = (acceptance.TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,)
    if (
        history.path_refs != expected_publication_paths
        or history.history_path_refs != expected_publication_paths
    ):
        raise ValueError("TAW-08 M2-to-M3 path census drift")
    publication_receipt = verifier.verify_repository_final_acceptance_publication(
        publication_revision_ref=f"git-sha:{publication_revision}",
        candidate_revision_ref=candidate_lock.git_revision_ref,
        candidate_manifest_digest_ref=candidate_lock.manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence.evidence_digest_ref,
        delta=manifest,
        delta_verification_receipt=delta_receipt,
        postmerge_foundation_receipt=postmerge_receipt,
        repository_root=candidate_root,
    )
    final_report = acceptance.evaluate_taw08_acceptance(
        candidate_lock=candidate_lock,
        candidate_verification_receipt=candidate_receipt,
        founder_evidence=founder_evidence,
        evidence_only_delta=manifest,
        evidence_only_delta_verification_receipt=delta_receipt,
        postmerge_foundation_receipt=postmerge_receipt,
        final_acceptance_publication_receipt=publication_receipt,
    )
    _require_report(
        final_report,
        expected_status="founder_private_accepted_promotion_blocked",
    )
    receipt = _phase_receipt(
        {
            "schema_version": "uaa-taw08-final-publication-phase.v1",
            "phase": "verify_publication",
            "candidate_revision_ref": candidate_lock.git_revision_ref,
            "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
            "founder_evidence_digest_ref": founder_evidence.evidence_digest_ref,
            "driver_source_digest_ref": request["driver_source_digest_ref"],
            "worker_source_digest_ref": request["worker_source_digest_ref"],
            "delta_revision_ref": manifest.delta_revision_ref,
            "delta_manifest_digest_ref": manifest.manifest_digest_ref,
            "delta_verification_receipt_digest_ref": delta_receipt.receipt_digest_ref,
            "postmerge_foundation_receipt_digest_ref": (
                postmerge_receipt.receipt_digest_ref
            ),
            "publication_revision_ref": f"git-sha:{publication_revision}",
            "final_acceptance_publication_receipt": (
                publication_receipt.model_dump(mode="json")
            ),
            "final_report_fingerprint_ref": final_report.report_fingerprint_ref,
            "status": "founder_private_accepted_promotion_blocked",
            "independent_promotion_blocker_refs": (
                final_report.independent_promotion_blocker_refs
            ),
            "independent_promotion_ready": False,
            "sealed_holdout_evidence_verified": False,
            "public_quality_claims_allowed": False,
            "production_authority_added": False,
            "runtime_model_calls_added": False,
            "provider_calls_added": False,
            "execution_authority_added": False,
            "raw_content_persisted": False,
        }
    )
    _require_clean_exact_worktree(
        verifier,
        candidate_root,
        expected_revision=candidate_lock.git_revision_ref.removeprefix("git-sha:"),
    )
    _require_clean_exact_worktree(
        verifier, delta_root, expected_revision=delta_revision
    )
    _require_clean_exact_worktree(
        verifier, publication_root, expected_revision=publication_revision
    )
    return {
        "schema_version": "uaa-taw08-phase-worker-response.v1",
        "phase": "verify_publication",
        "receipt": receipt,
        "artifacts": [],
    }


def main() -> int:
    _require_posix_private_path_support()
    expected_worker_digest = os.environ.get(WORKER_DIGEST_ENV)
    actual_worker_digest = (
        "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    )
    if expected_worker_digest != actual_worker_digest:
        raise RuntimeError("TAW-08 phase worker source binding drift")
    request_value = os.environ.get(REQUEST_ENV)
    if not request_value:
        raise RuntimeError("TAW-08 phase request is unavailable")
    request = _load_owner_json(Path(request_value), purpose="phase request")
    if request.get("schema_version") != "uaa-taw08-phase-request.v1":
        raise ValueError("TAW-08 phase request version drift")
    candidate_root = _require_directory(
        request.get("candidate_repository"), purpose="candidate repository"
    )
    verifier, acceptance = _load_repository_modules(candidate_root)
    _verify_candidate_operational_sources(
        verifier,
        candidate_root=candidate_root,
        request=request,
    )
    phase = request.get("phase")
    if phase == "prepare_delta":
        response = _prepare_delta(verifier, acceptance, request)
    elif phase == "verify_delta":
        response = _verify_delta(verifier, acceptance, request)
    elif phase == "verify_publication":
        response = _verify_publication(verifier, acceptance, request)
    else:
        raise ValueError("TAW-08 phase is invalid")
    encoded = json.dumps(response, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > MAX_JSON_BYTES:
        raise RuntimeError("TAW-08 phase response bound exceeded")
    sys.stdout.buffer.write(encoded + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
