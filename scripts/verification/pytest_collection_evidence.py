from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SHARD_SCHEMA_VERSION = "uaa_pytest_collection_shard.v1"
AGGREGATE_SCHEMA_VERSION = "uaa_pytest_collection_aggregate.v1"
MAX_TESTS = 100_000
MAX_SHARDS = 64
MAX_EVIDENCE_BYTES = 8 * 1024
_DIGEST_REF_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
_PLAN_REF_RE = re.compile(r"^pytest-shard-plan-ref:sha256:[a-f0-9]{64}$")
_STATE_ATTR = "_uaa_collection_evidence_state"
_COLLECTION_ERROR_COUNT = 0


class CollectionEvidenceError(ValueError):
    """A content-free pytest collection proof could not be validated."""


_COLLECTION_EVIDENCE_REASON_REFS = {
    "collection evidence input is unavailable": (
        "reason-ref:ci:pytest-collection-evidence-unavailable"
    ),
    "collection evidence input is unsafe": (
        "reason-ref:ci:pytest-collection-evidence-unsafe"
    ),
    "collection evidence input changed while read": (
        "reason-ref:ci:pytest-collection-evidence-changed"
    ),
    "collection evidence input is malformed": (
        "reason-ref:ci:pytest-collection-evidence-malformed"
    ),
    "collection aggregate evidence fields are invalid": (
        "reason-ref:ci:pytest-collection-evidence-fields-invalid"
    ),
    "collection aggregate binding types are invalid": (
        "reason-ref:ci:pytest-collection-evidence-types-invalid"
    ),
    "collection aggregate evidence binding is invalid": (
        "reason-ref:ci:pytest-collection-evidence-binding-invalid"
    ),
    "collection aggregate counts are invalid": (
        "reason-ref:ci:pytest-collection-evidence-counts-invalid"
    ),
    "collection aggregate digest is invalid": (
        "reason-ref:ci:pytest-collection-evidence-digest-invalid"
    ),
}


def collection_evidence_reason_ref(error: CollectionEvidenceError) -> str:
    """Return a bounded diagnostic ref without exposing paths or test names."""

    return _COLLECTION_EVIDENCE_REASON_REFS.get(
        str(error),
        "reason-ref:ci:pytest-collection-evidence-rejected",
    )


@dataclass(frozen=True)
class ShardCollectionEvidence:
    shard_index: int
    shard_count: int
    plan_fingerprint_ref: str
    collected_test_count: int
    unique_test_count: int
    duplicate_test_count: int
    collection_error_count: int
    collection_digest_ref: str

    def __post_init__(self) -> None:
        integer_values = (
            self.shard_index,
            self.shard_count,
            self.collected_test_count,
            self.unique_test_count,
            self.duplicate_test_count,
            self.collection_error_count,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in integer_values
        ):
            raise CollectionEvidenceError("collection bounds and counts must be integers")
        if not 0 <= self.shard_index < self.shard_count <= MAX_SHARDS:
            raise CollectionEvidenceError("collection shard bounds are invalid")
        if (
            not isinstance(self.plan_fingerprint_ref, str)
            or _PLAN_REF_RE.fullmatch(self.plan_fingerprint_ref) is None
        ):
            raise CollectionEvidenceError("collection plan fingerprint is invalid")
        if not 0 <= self.collected_test_count <= MAX_TESTS:
            raise CollectionEvidenceError("collected test count is out of bounds")
        if not 0 <= self.unique_test_count <= self.collected_test_count:
            raise CollectionEvidenceError("unique test count is out of bounds")
        if self.duplicate_test_count != (
            self.collected_test_count - self.unique_test_count
        ):
            raise CollectionEvidenceError("duplicate test count is inconsistent")
        if not 0 <= self.collection_error_count <= MAX_TESTS:
            raise CollectionEvidenceError("collection error count is out of bounds")
        if (
            not isinstance(self.collection_digest_ref, str)
            or _DIGEST_REF_RE.fullmatch(self.collection_digest_ref) is None
        ):
            raise CollectionEvidenceError("collection digest is invalid")

    def to_payload(self) -> dict[str, Any]:
        return {
            "collected_test_count": self.collected_test_count,
            "collection_digest_ref": self.collection_digest_ref,
            "collection_error_count": self.collection_error_count,
            "duplicate_test_count": self.duplicate_test_count,
            "plan_fingerprint_ref": self.plan_fingerprint_ref,
            "redaction_status": "content_free",
            "schema_version": SHARD_SCHEMA_VERSION,
            "shard_count": self.shard_count,
            "shard_index": self.shard_index,
            "unique_test_count": self.unique_test_count,
        }


def _digest_ref(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _collection_digest(nodeids: Iterable[str]) -> tuple[str, int, int, bool]:
    hashed_nodeids: list[bytes] = []
    observed = 0
    overflow = False
    for nodeid in nodeids:
        observed += 1
        if observed > MAX_TESTS:
            overflow = True
            break
        hashed_nodeids.append(hashlib.sha256(nodeid.encode("utf-8")).digest())
    hashed_nodeids.sort()
    unique_count = len(set(hashed_nodeids))
    digest = hashlib.sha256(b"uaa-pytest-collection-v1\0")
    digest.update(len(hashed_nodeids).to_bytes(8, "big"))
    for nodeid_hash in hashed_nodeids:
        digest.update(nodeid_hash)
    return f"sha256:{digest.hexdigest()}", len(hashed_nodeids), unique_count, overflow


def build_shard_evidence(
    nodeids: Iterable[str],
    *,
    shard_index: int,
    shard_count: int,
    plan_fingerprint_ref: str,
    collection_error_count: int = 0,
) -> ShardCollectionEvidence:
    digest_ref, collected_count, unique_count, overflow = _collection_digest(nodeids)
    return ShardCollectionEvidence(
        shard_index=shard_index,
        shard_count=shard_count,
        plan_fingerprint_ref=plan_fingerprint_ref,
        collected_test_count=collected_count,
        unique_test_count=unique_count,
        duplicate_test_count=collected_count - unique_count,
        collection_error_count=collection_error_count + int(overflow),
        collection_digest_ref=digest_ref,
    )


def _open_parent_directory(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CollectionEvidenceError("collection evidence parent is unsafe") from exc
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o022
    ):
        os.close(descriptor)
        raise CollectionEvidenceError("collection evidence parent is unsafe")
    return descriptor


def prepare_private_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700, parents=False, exist_ok=False)
    except FileExistsError:
        pass
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CollectionEvidenceError("collection evidence directory is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise CollectionEvidenceError("collection evidence directory is unsafe")


def _encoded_payload(payload: dict[str, Any]) -> bytes:
    encoded = (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_BYTES:
        raise CollectionEvidenceError("collection evidence exceeds the size bound")
    return encoded


def validate_new_evidence_target(path: Path) -> None:
    """Fail before running tests when an immutable output cannot be published."""

    parent_descriptor = _open_parent_directory(path.parent)
    try:
        try:
            os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise CollectionEvidenceError(
                "collection evidence output target is unsafe"
            ) from exc
        raise CollectionEvidenceError("collection evidence output already exists")
    finally:
        os.close(parent_descriptor)


def write_new_evidence(path: Path, payload: dict[str, Any]) -> None:
    """Atomically publish a new, owner-only regular evidence file."""

    encoded = _encoded_payload(payload)
    parent_descriptor = _open_parent_directory(path.parent)
    temporary_name = f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    file_descriptor: int | None = None
    temporary_created = False
    try:
        file_descriptor = os.open(
            temporary_name,
            flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        temporary_created = True
        metadata = os.fstat(file_descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise CollectionEvidenceError("collection evidence output is unsafe")
        view = memoryview(encoded)
        while view:
            written = os.write(file_descriptor, view)
            if written <= 0:
                raise CollectionEvidenceError("collection evidence write made no progress")
            view = view[written:]
        os.fsync(file_descriptor)
        os.close(file_descriptor)
        file_descriptor = None
        os.link(
            temporary_name,
            path.name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        os.unlink(temporary_name, dir_fd=parent_descriptor)
        temporary_created = False
        os.fsync(parent_descriptor)
        published_descriptor = os.open(
            path.name,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0),
            dir_fd=parent_descriptor,
        )
        try:
            published = os.fstat(published_descriptor)
            if (
                not stat.S_ISREG(published.st_mode)
                or published.st_nlink != 1
                or published.st_uid != os.getuid()
                or stat.S_IMODE(published.st_mode) != 0o600
                or published.st_size != len(encoded)
            ):
                raise CollectionEvidenceError(
                    "collection evidence publication could not be verified"
                )
        finally:
            os.close(published_descriptor)
    except FileExistsError as exc:
        raise CollectionEvidenceError("collection evidence output already exists") from exc
    except OSError as exc:
        raise CollectionEvidenceError("collection evidence output could not be published") from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except OSError:
                pass
        os.close(parent_descriptor)


def read_evidence(path: Path) -> dict[str, Any]:
    parent_descriptor = _open_parent_directory(path.parent)
    flags = os.O_RDONLY
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or not 0 < metadata.st_size <= MAX_EVIDENCE_BYTES
        ):
            raise CollectionEvidenceError("collection evidence input is unsafe")
        chunks: list[bytes] = []
        remaining = MAX_EVIDENCE_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65_536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        encoded = b"".join(chunks)
        after_read = os.fstat(descriptor)
        unchanged_identity = (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        ) == (
            after_read.st_dev,
            after_read.st_ino,
            after_read.st_size,
            after_read.st_mtime_ns,
            after_read.st_ctime_ns,
        )
        if (
            len(encoded) != metadata.st_size
            or len(encoded) > MAX_EVIDENCE_BYTES
            or not unchanged_identity
        ):
            raise CollectionEvidenceError("collection evidence input changed while read")
    except OSError as exc:
        raise CollectionEvidenceError("collection evidence input is unavailable") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_descriptor)
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        decoded: dict[str, Any] = {}
        for key, value in pairs:
            if key in decoded:
                raise CollectionEvidenceError(
                    "collection evidence input has duplicate fields"
                )
            decoded[key] = value
        return decoded

    try:
        payload = json.loads(encoded, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectionEvidenceError("collection evidence input is malformed") from exc
    if not isinstance(payload, dict):
        raise CollectionEvidenceError("collection evidence input is malformed")
    return payload


def load_shard_evidence(path: Path) -> ShardCollectionEvidence:
    payload = read_evidence(path)
    expected_keys = {
        "collected_test_count",
        "collection_digest_ref",
        "collection_error_count",
        "duplicate_test_count",
        "plan_fingerprint_ref",
        "redaction_status",
        "schema_version",
        "shard_count",
        "shard_index",
        "unique_test_count",
    }
    if set(payload) != expected_keys:
        raise CollectionEvidenceError("collection shard evidence fields are invalid")
    if (
        payload["schema_version"] != SHARD_SCHEMA_VERSION
        or payload["redaction_status"] != "content_free"
    ):
        raise CollectionEvidenceError("collection shard evidence posture is invalid")
    return ShardCollectionEvidence(
        shard_index=payload["shard_index"],
        shard_count=payload["shard_count"],
        plan_fingerprint_ref=payload["plan_fingerprint_ref"],
        collected_test_count=payload["collected_test_count"],
        unique_test_count=payload["unique_test_count"],
        duplicate_test_count=payload["duplicate_test_count"],
        collection_error_count=payload["collection_error_count"],
        collection_digest_ref=payload["collection_digest_ref"],
    )


def aggregate_shard_evidence(
    paths: Iterable[Path],
    *,
    expected_shard_count: int,
    expected_plan_fingerprint_ref: str,
) -> dict[str, Any]:
    if not 1 <= expected_shard_count <= MAX_SHARDS:
        raise CollectionEvidenceError("expected collection shard count is invalid")
    evidence = [load_shard_evidence(path) for path in paths]
    by_index = {item.shard_index: item for item in evidence}
    if len(by_index) != len(evidence):
        raise CollectionEvidenceError("collection shard evidence is duplicated")
    if sorted(by_index) != list(range(expected_shard_count)):
        raise CollectionEvidenceError("collection shard evidence is not contiguous")
    ordered = [by_index[index] for index in range(expected_shard_count)]
    if any(
        item.shard_count != expected_shard_count
        or item.plan_fingerprint_ref != expected_plan_fingerprint_ref
        for item in ordered
    ):
        raise CollectionEvidenceError("collection shard evidence binding is invalid")
    if any(item.collection_error_count for item in ordered):
        raise CollectionEvidenceError("pytest collection reported an error")
    if any(item.duplicate_test_count for item in ordered):
        raise CollectionEvidenceError("pytest collection reported duplicate node IDs")
    collected_count = sum(item.collected_test_count for item in ordered)
    if collected_count > MAX_TESTS:
        raise CollectionEvidenceError("aggregate collected test count is out of bounds")
    digest = hashlib.sha256(b"uaa-pytest-collection-aggregate-v1\0")
    digest.update(expected_plan_fingerprint_ref.encode("ascii"))
    digest.update(expected_shard_count.to_bytes(2, "big"))
    for item in ordered:
        digest.update(item.shard_index.to_bytes(2, "big"))
        digest.update(item.collected_test_count.to_bytes(8, "big"))
        digest.update(item.collection_digest_ref.encode("ascii"))
    return {
        "collected_test_count": collected_count,
        "collection_digest_ref": f"sha256:{digest.hexdigest()}",
        "collection_error_count": 0,
        "plan_fingerprint_ref": expected_plan_fingerprint_ref,
        "redaction_status": "content_free",
        "schema_version": AGGREGATE_SCHEMA_VERSION,
        "shard_count": expected_shard_count,
    }


def publish_aggregate_evidence(
    sidecar_paths: Iterable[Path],
    *,
    output_path: Path,
    expected_shard_count: int,
    expected_plan_fingerprint_ref: str,
) -> dict[str, Any]:
    payload = aggregate_shard_evidence(
        sidecar_paths,
        expected_shard_count=expected_shard_count,
        expected_plan_fingerprint_ref=expected_plan_fingerprint_ref,
    )
    write_new_evidence(output_path, payload)
    return payload


def load_aggregate_evidence(
    path: Path,
    *,
    expected_shard_count: int,
    expected_plan_fingerprint_ref: str,
) -> dict[str, Any]:
    """Load an exact, content-free aggregate proof for downstream receipts."""

    if (
        isinstance(expected_shard_count, bool)
        or not isinstance(expected_shard_count, int)
        or not 1 <= expected_shard_count <= MAX_SHARDS
    ):
        raise CollectionEvidenceError("expected collection shard count is invalid")
    if (
        not isinstance(expected_plan_fingerprint_ref, str)
        or _PLAN_REF_RE.fullmatch(expected_plan_fingerprint_ref) is None
    ):
        raise CollectionEvidenceError("expected collection plan fingerprint is invalid")
    payload = read_evidence(path)
    expected_keys = {
        "collected_test_count",
        "collection_digest_ref",
        "collection_error_count",
        "plan_fingerprint_ref",
        "redaction_status",
        "schema_version",
        "shard_count",
    }
    if set(payload) != expected_keys:
        raise CollectionEvidenceError("collection aggregate evidence fields are invalid")
    if (
        isinstance(payload["shard_count"], bool)
        or not isinstance(payload["shard_count"], int)
        or isinstance(payload["collection_error_count"], bool)
        or not isinstance(payload["collection_error_count"], int)
    ):
        raise CollectionEvidenceError("collection aggregate binding types are invalid")
    if (
        payload["schema_version"] != AGGREGATE_SCHEMA_VERSION
        or payload["redaction_status"] != "content_free"
        or payload["plan_fingerprint_ref"] != expected_plan_fingerprint_ref
        or payload["shard_count"] != expected_shard_count
        or payload["collection_error_count"] != 0
    ):
        raise CollectionEvidenceError("collection aggregate evidence binding is invalid")
    collected_count = payload["collected_test_count"]
    if isinstance(collected_count, bool) or not isinstance(collected_count, int):
        raise CollectionEvidenceError("collection aggregate counts are invalid")
    if not 0 <= collected_count <= MAX_TESTS:
        raise CollectionEvidenceError("collection aggregate counts are invalid")
    digest_ref = payload["collection_digest_ref"]
    if not isinstance(digest_ref, str) or _DIGEST_REF_RE.fullmatch(digest_ref) is None:
        raise CollectionEvidenceError("collection aggregate digest is invalid")
    return payload


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("uaa-collection-evidence")
    group.addoption("--uaa-collection-evidence-sidecar", default=None)
    group.addoption("--uaa-collection-shard-index", type=int, default=None)
    group.addoption("--uaa-collection-shard-count", type=int, default=None)
    group.addoption("--uaa-collection-plan-fingerprint", default=None)


def pytest_configure(config: Any) -> None:
    global _COLLECTION_ERROR_COUNT
    _COLLECTION_ERROR_COUNT = 0
    setattr(config, _STATE_ATTR, {"evidence": None})


def pytest_collectreport(report: Any) -> None:
    global _COLLECTION_ERROR_COUNT
    if report.failed:
        _COLLECTION_ERROR_COUNT += 1


def pytest_collection_finish(session: Any) -> None:
    if session.config.getoption("--uaa-collection-evidence-sidecar") is None:
        return
    state = getattr(session.config, _STATE_ATTR)
    state["evidence"] = build_shard_evidence(
        (str(item.nodeid) for item in session.items),
        shard_index=session.config.getoption("--uaa-collection-shard-index"),
        shard_count=session.config.getoption("--uaa-collection-shard-count"),
        plan_fingerprint_ref=session.config.getoption(
            "--uaa-collection-plan-fingerprint"
        ),
        collection_error_count=_COLLECTION_ERROR_COUNT,
    )


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    del exitstatus
    output = session.config.getoption("--uaa-collection-evidence-sidecar")
    if output is None:
        return
    state = getattr(session.config, _STATE_ATTR)
    evidence = state["evidence"]
    if evidence is None:
        evidence = build_shard_evidence(
            (),
            shard_index=session.config.getoption("--uaa-collection-shard-index"),
            shard_count=session.config.getoption("--uaa-collection-shard-count"),
            plan_fingerprint_ref=session.config.getoption(
                "--uaa-collection-plan-fingerprint"
            ),
            collection_error_count=_COLLECTION_ERROR_COUNT + 1,
        )
    write_new_evidence(Path(output), evidence.to_payload())
