from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


DEFAULT_LOCAL_MODEL_ROOTS: tuple[Path, ...] = ()

DEFAULT_SCAN_LIMIT = 600
SAFE_REF_HASH_LEN = 12


class LocalModelRuntimeFamily(str, Enum):
    llama_cpp = "llama_cpp"
    huggingface = "huggingface"
    mlx = "mlx"
    ollama = "ollama"
    lm_studio = "lm_studio"
    unknown = "unknown"


class LocalModelArtifactKind(str, Enum):
    gguf = "gguf"
    safetensors_directory = "safetensors_directory"
    ollama_manifest = "ollama_manifest"
    ollama_blob = "ollama_blob"
    model_directory = "model_directory"
    unsupported = "unsupported"


class LocalModelSourceClass(str, Enum):
    configured_root = "configured_root"
    huggingface_style = "huggingface_style"
    mlx_style = "mlx_style"
    ollama_store = "ollama_store"
    lm_studio_store = "lm_studio_store"
    unknown = "unknown"


class LocalModelRunnableStatus(str, Enum):
    runnable_now = "runnable_now"
    needs_adapter = "needs_adapter"
    blocked = "blocked"


class LocalModelBlockedReasonCode(str, Enum):
    none = "none"
    root_missing = "root_missing"
    root_unreadable = "root_unreadable"
    unsupported_candidate = "unsupported_candidate"
    missing_metadata = "missing_metadata"
    unsupported_artifact = "unsupported_artifact"


class LocalModelAdapterRequirement(str, Enum):
    none = "none"
    llama_cpp = "llama_cpp"
    mlx_runtime = "mlx_runtime"
    ollama_runtime = "ollama_runtime"
    lm_studio_runtime = "lm_studio_runtime"
    huggingface_runtime = "huggingface_runtime"
    unsupported = "unsupported"


@dataclass(frozen=True)
class LocalModelRootSummary:
    root_ref: str
    source_class: str
    configured_default: bool
    status: str
    blocked_reason_code: str = LocalModelBlockedReasonCode.none.value

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LocalModelInventoryItem:
    model_ref: str
    runtime_family: str
    artifact_kind: str
    source_class: str
    role_hints: tuple[str, ...]
    size_bucket: str
    runnable_status: str
    blocked_reason_code: str
    memory_posture_bucket: str
    adapter_requirement: str
    summary_ref: str
    root_ref: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["role_hints"] = list(self.role_hints)
        return data


@dataclass(frozen=True)
class LocalModelInventoryReport:
    schema_version: str
    status: str
    safe_summary: str
    roots: tuple[LocalModelRootSummary, ...] = field(default_factory=tuple)
    models: tuple[LocalModelInventoryItem, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "safe_summary": self.safe_summary,
            "roots": [root.to_dict() for root in self.roots],
            "models": [model.to_dict() for model in self.models],
        }


def default_local_model_roots() -> tuple[Path, ...]:
    return DEFAULT_LOCAL_MODEL_ROOTS


def inspect_local_model_inventory(
    roots: Sequence[Path | str] | None = None,
    *,
    scan_limit: int = DEFAULT_SCAN_LIMIT,
) -> LocalModelInventoryReport:
    configured_roots = tuple(Path(root).expanduser() for root in (roots or default_local_model_roots()))
    root_summaries: list[LocalModelRootSummary] = []
    items: dict[str, LocalModelInventoryItem] = {}
    seen_candidate_paths: set[str] = set()
    visited = 0

    for index, root in enumerate(configured_roots):
        root_ref = _root_ref(index, root)
        source_class = _source_class_for_root(root)
        configured_default = roots is None
        if not root.exists():
            root_summaries.append(
                LocalModelRootSummary(
                    root_ref=root_ref,
                    source_class=source_class,
                    configured_default=configured_default,
                    status="blocked",
                    blocked_reason_code=LocalModelBlockedReasonCode.root_missing.value,
                )
            )
            continue
        if not root.is_dir() or not os.access(root, os.R_OK):
            root_summaries.append(
                LocalModelRootSummary(
                    root_ref=root_ref,
                    source_class=source_class,
                    configured_default=configured_default,
                    status="blocked",
                    blocked_reason_code=LocalModelBlockedReasonCode.root_unreadable.value,
                )
            )
            continue

        root_summaries.append(
            LocalModelRootSummary(
                root_ref=root_ref,
                source_class=source_class,
                configured_default=configured_default,
                status="scanned",
            )
        )
        for candidate in _iter_candidates(root, scan_limit=max(scan_limit - visited, 0)):
            visited += 1
            candidate_identity = _resolved_identity(candidate)
            if candidate_identity in seen_candidate_paths:
                continue
            seen_candidate_paths.add(candidate_identity)
            for item in _classify_candidate(root, root_ref, source_class, candidate):
                items.setdefault(item.model_ref, item)
            if visited >= scan_limit:
                break
        if visited >= scan_limit:
            break

    models = tuple(sorted(items.values(), key=lambda item: item.model_ref))
    blocked_roots = sum(1 for root in root_summaries if root.status == "blocked")
    if models:
        status = "inventory_available"
    elif blocked_roots:
        status = "blocked_or_empty"
    else:
        status = "empty"
    return LocalModelInventoryReport(
        schema_version="uaa_local_model_inventory.v1",
        status=status,
        safe_summary=(
            f"Read-only local model inventory inspected {len(root_summaries)} configured root refs "
            f"and found {len(models)} model candidate refs."
        ),
        roots=tuple(root_summaries),
        models=models,
    )


def inspect_local_model_ref(
    model_ref: str,
    roots: Sequence[Path | str] | None = None,
    *,
    scan_limit: int = DEFAULT_SCAN_LIMIT,
) -> LocalModelInventoryItem | None:
    report = inspect_local_model_inventory(roots, scan_limit=scan_limit)
    return next((model for model in report.models if model.model_ref == model_ref), None)


def local_model_inventory_as_json(report: LocalModelInventoryReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def _iter_candidates(root: Path, *, scan_limit: int) -> Iterable[Path]:
    if scan_limit <= 0:
        return
    yielded = 0
    stack = [root]
    while stack and yielded < scan_limit:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda path: path.name.lower())
        except OSError:
            continue
        for child in children:
            yielded += 1
            yield child
            if yielded >= scan_limit:
                return
            if child.is_dir() and not child.is_symlink():
                stack.append(child)


def _classify_candidate(
    root: Path,
    root_ref: str,
    root_source_class: str,
    candidate: Path,
) -> tuple[LocalModelInventoryItem, ...]:
    if candidate.is_file() and candidate.suffix.lower() == ".gguf":
        return (
            _build_item(
                root,
                root_ref,
                candidate,
                runtime_family=LocalModelRuntimeFamily.llama_cpp,
                artifact_kind=LocalModelArtifactKind.gguf,
                source_class=LocalModelSourceClass.configured_root,
                role_hints=_role_hints(candidate.name),
                size_bytes=_safe_size(candidate),
                runnable_status=LocalModelRunnableStatus.runnable_now,
                blocked_reason_code=LocalModelBlockedReasonCode.none,
                adapter_requirement=LocalModelAdapterRequirement.llama_cpp,
            ),
        )

    if candidate.is_file() and _looks_like_ollama_manifest(candidate, root):
        return (
            _build_item(
                root,
                root_ref,
                candidate,
                runtime_family=LocalModelRuntimeFamily.ollama,
                artifact_kind=LocalModelArtifactKind.ollama_manifest,
                source_class=LocalModelSourceClass.ollama_store,
                role_hints=("general",),
                size_bytes=0,
                runnable_status=LocalModelRunnableStatus.needs_adapter,
                blocked_reason_code=LocalModelBlockedReasonCode.none,
                adapter_requirement=LocalModelAdapterRequirement.ollama_runtime,
            ),
        )

    if candidate.is_file() and _looks_like_ollama_blob(candidate, root):
        return (
            _build_item(
                root,
                root_ref,
                candidate,
                runtime_family=LocalModelRuntimeFamily.ollama,
                artifact_kind=LocalModelArtifactKind.ollama_blob,
                source_class=LocalModelSourceClass.ollama_store,
                role_hints=("unknown",),
                size_bytes=_safe_size(candidate),
                runnable_status=LocalModelRunnableStatus.needs_adapter,
                blocked_reason_code=LocalModelBlockedReasonCode.none,
                adapter_requirement=LocalModelAdapterRequirement.ollama_runtime,
            ),
        )

    if candidate.is_dir() and _looks_like_lm_studio_directory(candidate, root):
        return (
            _build_item(
                root,
                root_ref,
                candidate,
                runtime_family=LocalModelRuntimeFamily.lm_studio,
                artifact_kind=LocalModelArtifactKind.model_directory,
                source_class=LocalModelSourceClass.lm_studio_store,
                role_hints=_role_hints(candidate.name),
                size_bytes=_directory_weight_size(candidate),
                runnable_status=LocalModelRunnableStatus.needs_adapter,
                blocked_reason_code=LocalModelBlockedReasonCode.none,
                adapter_requirement=LocalModelAdapterRequirement.lm_studio_runtime,
            ),
        )

    if candidate.is_dir() and _has_hf_metadata(candidate):
        is_mlx = _is_mlx_directory(candidate, root)
        return (
            _build_item(
                root,
                root_ref,
                candidate,
                runtime_family=LocalModelRuntimeFamily.mlx if is_mlx else LocalModelRuntimeFamily.huggingface,
                artifact_kind=LocalModelArtifactKind.safetensors_directory,
                source_class=LocalModelSourceClass.mlx_style if is_mlx else LocalModelSourceClass.huggingface_style,
                role_hints=_role_hints(candidate.name),
                size_bytes=_directory_weight_size(candidate),
                runnable_status=LocalModelRunnableStatus.needs_adapter,
                blocked_reason_code=LocalModelBlockedReasonCode.none,
                adapter_requirement=(
                    LocalModelAdapterRequirement.mlx_runtime
                    if is_mlx
                    else LocalModelAdapterRequirement.huggingface_runtime
                ),
            ),
        )

    if (
        candidate.is_file()
        and candidate.suffix.lower() in {".bin", ".safetensors"}
        and not _has_hf_metadata(candidate.parent)
    ):
        return (
            _build_item(
                root,
                root_ref,
                candidate,
                runtime_family=LocalModelRuntimeFamily.unknown,
                artifact_kind=LocalModelArtifactKind.unsupported,
                source_class=LocalModelSourceClass.unknown,
                role_hints=("unknown",),
                size_bytes=_safe_size(candidate),
                runnable_status=LocalModelRunnableStatus.blocked,
                blocked_reason_code=LocalModelBlockedReasonCode.unsupported_artifact,
                adapter_requirement=LocalModelAdapterRequirement.unsupported,
            ),
        )

    _ = root_source_class
    return ()


def _build_item(
    root: Path,
    root_ref: str,
    candidate: Path,
    *,
    runtime_family: LocalModelRuntimeFamily,
    artifact_kind: LocalModelArtifactKind,
    source_class: LocalModelSourceClass,
    role_hints: tuple[str, ...],
    size_bytes: int,
    runnable_status: LocalModelRunnableStatus,
    blocked_reason_code: LocalModelBlockedReasonCode,
    adapter_requirement: LocalModelAdapterRequirement,
) -> LocalModelInventoryItem:
    identity_hash = _safe_hash(root_ref, _relative_identity(root, candidate), artifact_kind.value)
    model_ref = f"local-model:{artifact_kind.value}:{identity_hash}"
    return LocalModelInventoryItem(
        model_ref=model_ref,
        runtime_family=runtime_family.value,
        artifact_kind=artifact_kind.value,
        source_class=source_class.value,
        role_hints=role_hints,
        size_bucket=_size_bucket(size_bytes),
        runnable_status=runnable_status.value,
        blocked_reason_code=blocked_reason_code.value,
        memory_posture_bucket=_memory_posture_bucket(size_bytes),
        adapter_requirement=adapter_requirement.value,
        summary_ref=f"local-model-summary:{identity_hash}",
        root_ref=root_ref,
    )


def _root_ref(index: int, root: Path) -> str:
    return f"local-model-root:{index}:{_source_class_for_root(root)}:{_safe_hash(str(index), root.name.lower())}"


def _relative_identity(root: Path, candidate: Path) -> str:
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return candidate.name


def _resolved_identity(candidate: Path) -> str:
    try:
        return str(candidate.resolve())
    except OSError:
        return str(candidate)


def _safe_hash(*values: str) -> str:
    joined = "\x1f".join(values)
    return hashlib.sha256(joined.encode("utf-8", errors="replace")).hexdigest()[:SAFE_REF_HASH_LEN]


def _source_class_for_root(root: Path) -> str:
    lowered = "/".join(part.lower() for part in root.parts[-4:])
    if "ollama" in lowered:
        return LocalModelSourceClass.ollama_store.value
    if "lm-studio" in lowered or "lm studio" in lowered:
        return LocalModelSourceClass.lm_studio_store.value
    if "mlx" in lowered:
        return LocalModelSourceClass.mlx_style.value
    if "huggingface" in lowered or "hf" in lowered:
        return LocalModelSourceClass.huggingface_style.value
    return LocalModelSourceClass.configured_root.value


def _has_hf_metadata(candidate: Path) -> bool:
    has_config = (candidate / "config.json").is_file()
    has_tokenizer = (candidate / "tokenizer.json").is_file() or (candidate / "tokenizer_config.json").is_file()
    has_weights = (candidate / "model.safetensors.index.json").is_file() or any(
        child.suffix == ".safetensors" for child in _safe_iterdir(candidate)
    )
    return has_config and has_tokenizer and has_weights


def _is_mlx_directory(candidate: Path, root: Path) -> bool:
    lowered = "/".join(part.lower() for part in (*root.parts[-4:], candidate.name))
    if "mlx" in lowered:
        return True
    return (candidate / "chat_template.jinja").is_file() and (candidate / "model.safetensors.index.json").is_file()


def _looks_like_lm_studio_directory(candidate: Path, root: Path) -> bool:
    lowered_root = "/".join(part.lower() for part in root.parts[-5:])
    if "lm-studio" not in lowered_root and "lm studio" not in lowered_root:
        return False
    return _has_hf_metadata(candidate) or any(child.suffix.lower() == ".gguf" for child in _safe_iterdir(candidate))


def _looks_like_ollama_manifest(candidate: Path, root: Path) -> bool:
    lowered = "/".join(part.lower() for part in root.parts[-5:])
    if "ollama" not in lowered and "manifests" not in candidate.parts:
        return False
    if candidate.suffix:
        return False
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")[:4096]
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and ("schemaVersion" in data or "layers" in data or "config" in data)


def _looks_like_ollama_blob(candidate: Path, root: Path) -> bool:
    lowered = "/".join(part.lower() for part in (*root.parts[-5:], candidate.parent.name, candidate.name))
    return "ollama" in lowered and "blobs" in lowered and candidate.name.startswith("sha256-")


def _directory_weight_size(candidate: Path) -> int:
    total = 0
    for child in _safe_iterdir(candidate):
        if child.is_file() and child.suffix.lower() in {".safetensors", ".gguf", ".bin"}:
            total += _safe_size(child)
    return total


def _safe_size(candidate: Path) -> int:
    try:
        return candidate.stat().st_size
    except OSError:
        return 0


def _safe_iterdir(candidate: Path) -> tuple[Path, ...]:
    try:
        return tuple(candidate.iterdir())
    except OSError:
        return ()


def _role_hints(name: str) -> tuple[str, ...]:
    lowered = name.lower()
    hints: list[str] = []
    for needle, hint in [
        ("coder", "coding"),
        ("code", "coding"),
        ("instruct", "instruction"),
        ("chat", "chat"),
        ("embed", "embedding"),
        ("vision", "vision"),
    ]:
        if needle in lowered and hint not in hints:
            hints.append(hint)
    return tuple(hints or ["general"])


def _size_bucket(size_bytes: int) -> str:
    gib = size_bytes / (1024**3)
    if size_bytes <= 0:
        return "unknown"
    if gib < 2:
        return "size:<2GiB"
    if gib < 8:
        return "size:2-8GiB"
    if gib < 16:
        return "size:8-16GiB"
    if gib < 32:
        return "size:16-32GiB"
    return "size:>=32GiB"


def _memory_posture_bucket(size_bytes: int) -> str:
    gib = size_bytes / (1024**3)
    if size_bytes <= 0:
        return "memory:unknown"
    if gib < 8:
        return "memory:low"
    if gib < 24:
        return "memory:medium"
    if gib < 48:
        return "memory:high"
    return "memory:very_high"
