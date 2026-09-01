from __future__ import annotations

import base64
import hashlib
import importlib.metadata as importlib_metadata
import os
import platform
import re
import subprocess
import sys
import tempfile
import tomllib
from collections import defaultdict, deque
from pathlib import Path
from typing import Literal

from packaging.markers import InvalidMarker, Marker, default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
_LOCKED_CHILD_REVISION_ENV = "UAA_TAW08_LOCKED_CHILD_REVISION"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.evals.tool_aware_acceptance import (  # noqa: E402
    TAW08_DELTA_VERIFICATION_MISSING_REF,
    TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
    TAW08_FINAL_PUBLICATION_MISSING_REF,
    TAW08_FOUNDATION_GATE_SOURCE_PREFIX,
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    TAW08AcceptanceStatus,
    TAW08AcceptanceReport,
    TAW08_REQUIRED_ACCEPTANCE_PATH_REFS,
    TAW08_REPOSITORY_VERIFIER_PATH_REF,
    TAW08_UNRESOLVED_DYNAMIC_IMPORT_PATH_REFS,
    _CandidateLockVerificationReceipt,
    _EvaluatorEnvironmentReceipt,
    EvidenceOnlyDeltaManifest,
    _EvidenceOnlyDeltaVerificationReceipt,
    FinalAcceptancePublicationReceipt,
    FoundationGateReceipt,
    PublicationHistoryCensus,
    RevisionDeltaCensus,
    RevisionPathCensus,
    bind_revision_delta_census,
    bind_revision_path_census,
    evaluate_taw08_acceptance,
    _bind_candidate_lock_verification_receipt,
    _verify_and_bind_evidence_only_delta,
    _bind_publication_history_census,
    _bind_evaluator_environment_receipt,
    _verify_and_bind_final_acceptance_publication,
    _verify_and_bind_foundation_gate_report,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (  # noqa: E402
    CandidateLock,
    CandidateManifestEntry,
    SourceDependencyClosure,
    SourceDependencyEntry,
    SourceProjection,
    canonical_digest,
    derive_local_python_dependencies,
    verify_candidate_lock,
)
from scripts.run_foundation_gate import (  # noqa: E402
    evaluate_foundation_gate_at_exact_repository_revision,
    report_only_receipt,
)


SLICE_CANDIDATE_PATHS = tuple(
    sorted(
        {
            *(
                ref.removeprefix("repo-path-ref:")
                for ref in TAW08_REQUIRED_ACCEPTANCE_PATH_REFS
            ),
            "docs/evals/TOOL_AWARE_COGNITION_TAW08_ACCEPTANCE.md",
            "scripts/verify_tool_aware_cognition_taw08.py",
            "src/ultimate_ai_agent/core/evals/__init__.py",
            "tests/test_tool_aware_cognition_taw08.py",
        }
    )
)
EVIDENCE_ONLY_DELTA_PATHS = (
    "docs/evals/tool_aware_cognition_taw08_acceptance_report_v1.json",
    "docs/evals/tool_aware_cognition_taw08_final_acceptance_report_v1.json",
    "docs/evals/tool_aware_cognition_taw08_board_reconciliation_v1.json",
    "docs/evals/tool_aware_cognition_taw08_release_truth_reconciliation_v1.json",
    "docs/kanban/current_board.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
)


def _git(*args: str, repository_root: Path = ROOT) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    return result.stdout


def verify_executing_repository_sources(
    revision: str,
    *,
    repository_root: Path = ROOT,
    source_root: Path = ROOT,
) -> tuple[tuple[str, ...], str]:
    """Bind every loaded repository Python source to the candidate Git tree."""

    resolved_source_root = source_root.resolve()
    source_paths: dict[str, Path] = {}
    for module in tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            continue
        try:
            source_path = Path(module_file).resolve()
        except OSError:
            continue
        if source_path.suffix != ".py" or not source_path.is_relative_to(
            resolved_source_root
        ):
            continue
        relative_path = source_path.relative_to(resolved_source_root).as_posix()
        if relative_path.startswith((".venv/", ".ci-bootstrap/")):
            continue
        existing = source_paths.get(relative_path)
        if existing is not None and existing != source_path:
            raise RuntimeError("TAW-08 executing repository source census is invalid")
        source_paths[relative_path] = source_path
    tree_entries: dict[str, str] = {}
    for line in _git(
        "ls-tree",
        "-r",
        revision,
        repository_root=repository_root,
    ).decode("utf-8").splitlines():
        metadata, separator, path = line.partition("\t")
        parts = metadata.split()
        if separator and len(parts) == 3 and parts[1] == "blob":
            tree_entries[path] = parts[2]
    if not set(source_paths) <= set(tree_entries):
        raise RuntimeError("TAW-08 executing repository source census is incomplete")
    for path, source_path in source_paths.items():
        if source_path.read_bytes() != _git(
            "show",
            f"{revision}:{path}",
            repository_root=repository_root,
        ):
            raise RuntimeError(
                "TAW-08 executing repository source differs from the candidate"
            )
    sources = {
        f"repo-path-ref:{path}": f"git-blob-ref:{tree_entries[path]}"
        for path in source_paths
    }
    required = {
        TAW08_REPOSITORY_VERIFIER_PATH_REF,
        "repo-path-ref:scripts/run_foundation_gate.py",
        "repo-path-ref:src/ultimate_ai_agent/core/evals/tool_aware_acceptance.py",
    }
    if not required <= set(sources):
        raise RuntimeError("TAW-08 executing repository source census is incomplete")
    path_refs = tuple(sorted(sources))
    return path_refs, canonical_digest({path_ref: sources[path_ref] for path_ref in path_refs})


def _installed_distribution_content_identity(
    distribution: importlib_metadata.Distribution,
    *,
    environment_root: Path,
) -> tuple[tuple[str, int, str], ...]:
    files = distribution.files
    if not files or len(files) > 100_000:
        raise RuntimeError("TAW-08 evaluator distribution file census is invalid")
    environment_root = environment_root.resolve()
    total_bytes = 0
    identities: list[tuple[str, int, str]] = []
    for entry in sorted(files, key=str):
        entry_ref = str(entry)
        if (
            not entry_ref
            or len(entry_ref) > 1024
            or any(character in entry_ref for character in ("\x00", "\n", "\r"))
        ):
            raise RuntimeError("TAW-08 evaluator distribution file census is invalid")
        path = Path(distribution.locate_file(entry)).resolve()
        if not path.is_relative_to(environment_root) or not path.is_file():
            raise RuntimeError("TAW-08 evaluator distribution file is unavailable")
        content = path.read_bytes()
        total_bytes += len(content)
        if len(content) > 64 * 1024 * 1024 or total_bytes > 1024 * 1024 * 1024:
            raise RuntimeError("TAW-08 evaluator distribution content bound exceeded")
        if entry.size is not None and entry.size != len(content):
            raise RuntimeError("TAW-08 evaluator distribution size differs from RECORD")
        if entry.hash is not None:
            if entry.hash.mode != "sha256":
                raise RuntimeError("TAW-08 evaluator distribution hash mode is invalid")
            actual_record_hash = base64.urlsafe_b64encode(
                hashlib.sha256(content).digest()
            ).rstrip(b"=").decode("ascii")
            if actual_record_hash != entry.hash.value:
                raise RuntimeError(
                    "TAW-08 evaluator distribution content differs from RECORD"
                )
        identities.append(
            (entry_ref, len(content), hashlib.sha256(content).hexdigest())
        )
    return tuple(identities)


def _read_bounded_msgpack_value(
    content: bytes,
    offset: int = 0,
    *,
    depth: int = 0,
) -> tuple[object, int]:
    """Decode the small, documented-by-shape prefix of one uv cache record."""

    if depth > 8 or offset >= len(content):
        raise RuntimeError("TAW-08 uv cache metadata is invalid")
    marker = content[offset]
    offset += 1
    if marker <= 0x7F:
        return marker, offset
    if 0x90 <= marker <= 0x9F:
        count = marker & 0x0F
        values: list[object] = []
        for _ in range(count):
            value, offset = _read_bounded_msgpack_value(
                content, offset, depth=depth + 1
            )
            values.append(value)
        return values, offset
    if 0xA0 <= marker <= 0xBF:
        length = marker & 0x1F
    elif marker == 0xD9:
        if offset >= len(content):
            raise RuntimeError("TAW-08 uv cache metadata is invalid")
        length = content[offset]
        offset += 1
    elif marker == 0xDA:
        if offset + 2 > len(content):
            raise RuntimeError("TAW-08 uv cache metadata is invalid")
        length = int.from_bytes(content[offset : offset + 2], "big")
        offset += 2
    else:
        raise RuntimeError("TAW-08 uv cache metadata is invalid")
    if length > 4096 or offset + length > len(content):
        raise RuntimeError("TAW-08 uv cache metadata is invalid")
    try:
        value = content[offset : offset + length].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("TAW-08 uv cache metadata is invalid") from exc
    return value, offset + length


def _locked_wheel_distribution_identity(
    *,
    name: str,
    version: str,
    locked_wheels: list[object],
    installed_identity: tuple[tuple[str, int, str], ...],
) -> tuple[str, tuple[tuple[str, int, str], ...]]:
    allowed_wheels: dict[str, str] = {}
    for item in locked_wheels:
        if not isinstance(item, dict):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        url = item.get("url")
        digest_ref = item.get("hash")
        size = item.get("size")
        if (
            not isinstance(url, str)
            or not isinstance(digest_ref, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest_ref)
            or not isinstance(size, int)
            or size <= 0
        ):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        filename = url.rsplit("/", 1)[-1]
        if not filename.endswith(".whl") or len(filename) > 512:
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        allowed_wheels[filename] = digest_ref.removeprefix("sha256:")
    if not allowed_wheels:
        raise RuntimeError("TAW-08 locked distribution has no wheel artifacts")

    cache_roots: list[Path] = []
    configured_cache = os.environ.get("UV_CACHE_DIR")
    if configured_cache:
        cache_roots.append(Path(configured_cache))
    cache_roots.extend(
        (
            Path.home() / ".cache" / "uv",
            Path.home() / "Library" / "Caches" / "uv",
        )
    )
    matching_identities: list[
        tuple[str, tuple[tuple[str, int, str], ...]]
    ] = []
    for cache_root in dict.fromkeys(path.resolve() for path in cache_roots):
        wheel_directory = cache_root / "wheels-v6" / "pypi" / name
        if not wheel_directory.is_dir():
            continue
        metadata_paths = tuple(sorted(wheel_directory.glob("*.http")))
        if len(metadata_paths) > 1024:
            raise RuntimeError("TAW-08 uv cache wheel census exceeds bound")
        for metadata_path in metadata_paths:
            content = metadata_path.read_bytes()
            if len(content) > 64 * 1024:
                raise RuntimeError("TAW-08 uv cache metadata exceeds bound")
            metadata, _offset = _read_bounded_msgpack_value(content)
            if not isinstance(metadata, list) or len(metadata) != 4:
                continue
            archive_key, hash_entries, filename, _cache_policy = metadata
            if (
                not isinstance(archive_key, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", archive_key)
                or not isinstance(hash_entries, list)
                or not isinstance(filename, str)
                or filename not in allowed_wheels
            ):
                continue
            hashes = {
                value
                for entry in hash_entries
                if isinstance(entry, list)
                and len(entry) == 2
                and entry[0] == "Sha256"
                and isinstance((value := entry[1]), str)
            }
            expected_hash = allowed_wheels[filename]
            if hashes != {expected_hash}:
                continue
            archive_root = (cache_root / "archive-v0" / archive_key).resolve()
            if (
                not archive_root.is_relative_to(
                    (cache_root / "archive-v0").resolve()
                )
                or not archive_root.is_dir()
            ):
                continue
            distribution_candidates = tuple(archive_root.glob("*.dist-info"))
            if len(distribution_candidates) != 1:
                continue
            cached_distribution = importlib_metadata.PathDistribution(
                distribution_candidates[0]
            )
            if (
                canonicalize_name(
                    str(cached_distribution.metadata.get("Name", ""))
                )
                != name
                or str(cached_distribution.version) != version
            ):
                continue
            cached_identity = _installed_distribution_content_identity(
                cached_distribution,
                environment_root=archive_root,
            )
            cached_by_ref = {entry[0]: entry[1:] for entry in cached_identity}
            installed_by_ref = {
                entry[0]: entry[1:] for entry in installed_identity
            }
            wheel_payload_refs = {
                entry_ref
                for entry_ref in cached_by_ref
                if not entry_ref.endswith(".dist-info/RECORD")
            }
            installer_metadata_refs = {
                entry_ref
                for entry_ref in installed_by_ref
                if entry_ref.endswith(
                    (
                        ".dist-info/RECORD",
                        ".dist-info/INSTALLER",
                        ".dist-info/REQUESTED",
                        ".dist-info/direct_url.json",
                    )
                )
            }
            installer_script_refs = {
                entry_ref
                for entry_ref in installed_by_ref
                if entry_ref.startswith("../../../bin/")
                and re.fullmatch(
                    r"[A-Za-z0-9_.-]{1,255}",
                    entry_ref.rsplit("/", 1)[-1],
                )
            }

            def installed_entry_matches_locked_wheel(entry_ref: str) -> bool:
                data_script_marker = ".data/scripts/"
                if data_script_marker not in entry_ref:
                    return (
                        installed_by_ref.get(entry_ref)
                        == cached_by_ref[entry_ref]
                    )
                script_name = entry_ref.rsplit("/", 1)[-1]
                installed_script_ref = f"../../../bin/{script_name}"
                try:
                    cached_script = (archive_root / entry_ref).read_bytes()
                    installed_script = (
                        Path(sys.prefix) / "bin" / script_name
                    ).read_bytes()
                except OSError:
                    return False
                cached_lines = cached_script.splitlines(keepends=True)
                installed_lines = installed_script.splitlines(keepends=True)
                if cached_lines and cached_lines[0] not in {
                    b"#!python\n",
                    b"#!pythonw\n",
                }:
                    return (
                        installed_script == cached_script
                        and installed_script_ref in installer_script_refs
                    )
                return (
                    bool(cached_lines)
                    and cached_lines[0] in {b"#!python\n", b"#!pythonw\n"}
                    and bool(installed_lines)
                    and installed_lines[0]
                    == f"#!{sys.executable}\n".encode("utf-8")
                    and installed_lines[1:] == cached_lines[1:]
                    and installed_script_ref in installer_script_refs
                )

            if (
                all(
                    installed_entry_matches_locked_wheel(entry_ref)
                    for entry_ref in wheel_payload_refs
                )
                and set(installed_by_ref) - wheel_payload_refs
                <= installer_metadata_refs | installer_script_refs
            ):
                matching_identities.append(
                    (f"sha256:{expected_hash}", cached_identity)
                )
    unique = tuple(dict.fromkeys(matching_identities))
    if len(unique) != 1:
        raise RuntimeError(
            "TAW-08 installed distribution is not bound to one locked wheel "
            f"artifact: {name}"
        )
    return unique[0]


def verify_locked_evaluator_environment(
    *,
    locked_content_by_path_ref: dict[str, bytes],
    repository_root: Path = ROOT,
) -> _EvaluatorEnvironmentReceipt:
    """Bind the exact active interpreter only after an offline frozen lock check."""

    required_paths = {
        "repo-path-ref:pyproject.toml": repository_root / "pyproject.toml",
        "repo-path-ref:uv.lock": repository_root / "uv.lock",
    }
    if set(locked_content_by_path_ref) != set(required_paths):
        raise RuntimeError("TAW-08 evaluator environment lock census is incomplete")
    for path_ref, path in required_paths.items():
        if (
            not path.is_file()
            or path.read_bytes() != locked_content_by_path_ref[path_ref]
        ):
            raise RuntimeError(
                "TAW-08 evaluator environment lock differs from the candidate"
            )
    if sys.implementation.name != "cpython" or sys.prefix == sys.base_prefix:
        raise RuntimeError(
            "TAW-08 evaluator environment requires an active CPython project venv"
        )
    venv_configuration = Path(sys.prefix) / "pyvenv.cfg"
    try:
        venv_configuration_text = venv_configuration.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(
            "TAW-08 evaluator environment venv configuration is unavailable"
        ) from exc
    if not re.search(
        r"(?im)^include-system-site-packages\s*=\s*false\s*$",
        venv_configuration_text,
    ):
        raise RuntimeError(
            "TAW-08 evaluator environment must exclude system site packages"
        )
    try:
        pyproject = tomllib.loads(
            locked_content_by_path_ref["repo-path-ref:pyproject.toml"].decode(
                "utf-8"
            )
        )
        locked = tomllib.loads(
            locked_content_by_path_ref["repo-path-ref:uv.lock"].decode("utf-8")
        )
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError("TAW-08 evaluator lock metadata is invalid") from exc
    project = pyproject.get("project")
    packages = locked.get("package")
    if not isinstance(project, dict) or not isinstance(packages, list):
        raise RuntimeError("TAW-08 evaluator lock metadata is incomplete")
    project_name_value = project.get("name")
    project_dependencies = project.get("dependencies")
    optional_dependencies = project.get("optional-dependencies")
    if (
        not isinstance(project_name_value, str)
        or not isinstance(project_dependencies, list)
        or not isinstance(optional_dependencies, dict)
        or not isinstance(optional_dependencies.get("dev"), list)
        or any(
            not isinstance(item, str)
            for item in (*project_dependencies, *optional_dependencies["dev"])
        )
    ):
        raise RuntimeError("TAW-08 evaluator dependency roots are invalid")
    project_name = canonicalize_name(project_name_value)
    marker_environment = default_environment()
    locked_versions: dict[str, set[str]] = defaultdict(set)
    locked_wheels_by_identity: dict[tuple[str, str], list[object]] = {}
    for item in packages:
        if not isinstance(item, dict):
            raise RuntimeError("TAW-08 uv.lock package census is invalid")
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise RuntimeError("TAW-08 uv.lock package identity is invalid")
        resolution_markers = item.get("resolution-markers", [])
        if not isinstance(resolution_markers, list) or any(
            not isinstance(marker, str) for marker in resolution_markers
        ):
            raise RuntimeError("TAW-08 uv.lock resolution markers are invalid")
        try:
            active_for_environment = not resolution_markers or any(
                Marker(marker).evaluate(marker_environment)
                for marker in resolution_markers
            )
        except InvalidMarker as exc:
            raise RuntimeError(
                "TAW-08 uv.lock resolution markers are invalid"
            ) from exc
        if not active_for_environment:
            continue
        canonical_name = canonicalize_name(name)
        locked_versions[canonical_name].add(version)
        wheels = item.get("wheels", [])
        if not isinstance(wheels, list):
            raise RuntimeError("TAW-08 locked wheel census is invalid")
        locked_wheels_by_identity[(canonical_name, version)] = wheels
    installed_by_name: dict[str, importlib_metadata.Distribution] = {}
    for distribution in importlib_metadata.distributions():
        name_value = str(distribution.metadata.get("Name", "")).strip()
        name = canonicalize_name(name_value)
        if not name:
            raise RuntimeError("TAW-08 evaluator distribution census is invalid")
        if name in installed_by_name:
            if (
                name == project_name
                and str(installed_by_name[name].version) == str(distribution.version)
            ):
                continue
            raise RuntimeError("TAW-08 evaluator distribution census is invalid")
        installed_by_name[name] = distribution
    if (
        not installed_by_name
        or len(installed_by_name) > 2048
        or any(
            not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,127}", name)
            or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.+!-]{0,127}", value)
            for name, distribution in installed_by_name.items()
            for value in (str(distribution.version).strip(),)
        )
    ):
        raise RuntimeError("TAW-08 evaluator distribution census is invalid")
    active_extras: dict[str, set[str]] = defaultdict(set)
    reachable: set[str] = set()
    pending: deque[str] = deque()

    def require(requirement_text: str, marker_extras: set[str]) -> None:
        try:
            requirement = Requirement(requirement_text)
        except InvalidRequirement as exc:
            raise RuntimeError("TAW-08 evaluator requirement is invalid") from exc
        contexts = marker_extras or {""}
        if requirement.marker is not None and not any(
            requirement.marker.evaluate({**marker_environment, "extra": extra})
            for extra in contexts
        ):
            return
        name = canonicalize_name(requirement.name)
        distribution = installed_by_name.get(name)
        if distribution is None:
            raise RuntimeError("TAW-08 evaluator dependency closure is incomplete")
        try:
            installed_version = Version(str(distribution.version))
        except InvalidVersion as exc:
            raise RuntimeError("TAW-08 evaluator distribution version is invalid") from exc
        if (
            installed_version not in requirement.specifier
            or str(distribution.version) not in locked_versions.get(name, set())
        ):
            raise RuntimeError("TAW-08 evaluator environment does not match uv.lock")
        new_extras = set(requirement.extras) - active_extras[name]
        if name not in reachable or new_extras:
            reachable.add(name)
            active_extras[name].update(new_extras)
            pending.append(name)

    for requirement_text in (*project_dependencies, *optional_dependencies["dev"]):
        require(requirement_text, {""})
    processed_extras: dict[str, frozenset[str]] = {}
    while pending:
        name = pending.popleft()
        extras = frozenset(active_extras[name])
        if processed_extras.get(name) == extras:
            continue
        processed_extras[name] = extras
        for requirement_text in installed_by_name[name].requires or ():
            require(requirement_text, {"", *extras})
    unexpected = set(installed_by_name) - reachable - {project_name}
    if unexpected:
        raise RuntimeError("TAW-08 evaluator environment has unlocked distributions")
    distribution_refs = tuple(
        f"{name}=={str(distribution.version).strip()}"
        for name, distribution in sorted(installed_by_name.items())
    )
    distribution_content_identities = []
    for name in sorted(reachable):
        version = str(installed_by_name[name].version).strip()
        installed_identity = _installed_distribution_content_identity(
            installed_by_name[name],
            environment_root=Path(sys.prefix),
        )
        locked_wheel_identity = _locked_wheel_distribution_identity(
            name=name,
            version=version,
            locked_wheels=locked_wheels_by_identity.get((name, version), []),
            installed_identity=installed_identity,
        )
        distribution_content_identities.append(
            (name, version, locked_wheel_identity, installed_identity)
        )
    distribution_content_identities = tuple(distribution_content_identities)
    return _bind_evaluator_environment_receipt(
        python_implementation="cpython",
        python_version=".".join(str(item) for item in sys.version_info[:3]),
        platform_system=platform.system().strip().lower(),
        platform_machine=platform.machine().strip().lower(),
        installed_distribution_count=len(distribution_refs),
        installed_distributions_digest_ref=canonical_digest(
            {
                "distributions": distribution_refs,
                "reachable_distribution_contents": (
                    distribution_content_identities
                ),
            }
        ),
        pyproject_digest_ref=(
            "sha256:"
            + hashlib.sha256(
                locked_content_by_path_ref["repo-path-ref:pyproject.toml"]
            ).hexdigest()
        ),
        uv_lock_digest_ref=(
            "sha256:"
            + hashlib.sha256(
                locked_content_by_path_ref["repo-path-ref:uv.lock"]
            ).hexdigest()
        ),
        lock_check_command_ref=(
            "command-ref:python-installed-distribution-lock-closure"
        ),
        independent_lock_closure_verified=True,
        locked_environment_verified=True,
        raw_content_persisted=False,
    )


def derive_revision_path_census(
    revision_ref: str, *, repository_root: Path = ROOT
) -> RevisionPathCensus:
    revision = revision_ref.removeprefix("git-sha:")
    paths = tuple(
        sorted(
            f"repo-path-ref:{path}"
            for path in _git(
                "ls-tree",
                "-r",
                "--name-only",
                revision,
                repository_root=repository_root,
            )
            .decode("utf-8")
            .splitlines()
            if path
        )
    )
    return bind_revision_path_census(
        revision_ref=revision_ref,
        path_refs=paths,
        provenance_ref="provenance-ref:git-ls-tree",
    )


def derive_revision_delta_census(
    candidate_revision_ref: str,
    delta_revision_ref: str,
    *,
    repository_root: Path = ROOT,
) -> RevisionDeltaCensus:
    candidate = candidate_revision_ref.removeprefix("git-sha:")
    delta = delta_revision_ref.removeprefix("git-sha:")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", candidate, delta],
        cwd=repository_root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise ValueError("evidence delta must descend from the locked candidate")
    commits = tuple(
        item
        for item in _git(
            "rev-list",
            "--reverse",
            f"{candidate}..{delta}",
            repository_root=repository_root,
        )
        .decode("ascii")
        .splitlines()
        if item
    )
    if not commits:
        raise ValueError("evidence delta history must contain at least one commit")
    paths = tuple(
        sorted(
            f"repo-path-ref:{path}"
            for path in _git(
                "diff",
                "--name-only",
                "--no-renames",
                candidate,
                delta,
                "--",
                repository_root=repository_root,
            )
            .decode("utf-8")
            .splitlines()
            if path
        )
    )
    history_paths = tuple(
        sorted(
            {
                f"repo-path-ref:{path}"
                for commit in commits
                for path in _git(
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "--no-renames",
                    "-r",
                    "-m",
                    commit,
                    repository_root=repository_root,
                )
                .decode("utf-8")
                .splitlines()
                if path
            }
        )
    )
    return bind_revision_delta_census(
        candidate_revision_ref=candidate_revision_ref,
        delta_revision_ref=delta_revision_ref,
        path_refs=paths,
        history_path_refs=history_paths,
        commit_count=len(commits),
        candidate_ancestor_verified=True,
        provenance_ref="provenance-ref:git-history-path-census",
    )


def derive_publication_history_census(
    delta_revision_ref: str,
    publication_revision_ref: str,
    *,
    repository_root: Path = ROOT,
) -> PublicationHistoryCensus:
    history = derive_revision_delta_census(
        delta_revision_ref,
        publication_revision_ref,
        repository_root=repository_root,
    )
    return _bind_publication_history_census(
        delta_revision_ref=delta_revision_ref,
        publication_revision_ref=publication_revision_ref,
        path_refs=history.path_refs,
        history_path_refs=history.history_path_refs,
        commit_count=history.commit_count,
        delta_ancestor_verified=True,
        provenance_ref="provenance-ref:git-history-path-census",
    )


def _candidate_lock(revision: str) -> tuple[CandidateLock, dict[str, bytes]]:
    entries: list[CandidateManifestEntry] = []
    content_by_ref: dict[str, bytes] = {}
    gate_paths = tuple(
        path
        for path in _git("ls-tree", "-r", "--name-only", revision)
        .decode("utf-8")
        .splitlines()
        if f"repo-path-ref:{path}".startswith(TAW08_FOUNDATION_GATE_SOURCE_PREFIX)
        and path.endswith(".py")
    )
    candidate_paths = tuple(sorted({*SLICE_CANDIDATE_PATHS, *gate_paths}))
    for path in candidate_paths:
        comparison = subprocess.run(
            ["git", "diff", "--quiet", revision, "--", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if comparison.returncode == 1:
            raise RuntimeError(f"TAW-08 contract path is dirty at {revision}: {path}")
        if comparison.returncode != 0:
            raise RuntimeError(f"TAW-08 contract path comparison failed: {path}")
        content = _git("show", f"{revision}:{path}")
        path_ref = f"repo-path-ref:{path}"
        content_by_ref[path_ref] = content
        entries.append(
            CandidateManifestEntry(
                path_ref=path_ref,
                content_digest_ref=f"sha256:{hashlib.sha256(content).hexdigest()}",
            )
        )
    candidate_ref = "candidate-ref:taw08:contract-slice:v1"
    git_revision_ref = f"git-sha:{revision}"
    evidence_only_delta_path_refs = tuple(
        f"repo-path-ref:{path}" for path in EVIDENCE_ONLY_DELTA_PATHS
    )
    digest_payload = {
        "candidate_ref": candidate_ref,
        "git_revision_ref": git_revision_ref,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "evidence_only_delta_path_refs": evidence_only_delta_path_refs,
    }
    return (
        CandidateLock(
            candidate_ref=candidate_ref,
            git_revision_ref=git_revision_ref,
            entries=tuple(entries),
            manifest_digest_ref=canonical_digest(digest_payload),
            evidence_only_delta_path_refs=evidence_only_delta_path_refs,
        ),
        content_by_ref,
    )


def _source_evidence_from_git(
    lock: CandidateLock,
    revision_path_census: RevisionPathCensus,
    *,
    repository_root: Path = ROOT,
) -> tuple[SourceProjection, SourceDependencyClosure, dict[str, bytes]]:
    root_entries = tuple(
        item
        for item in lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
        and item.path_ref.endswith(".py")
    )
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "source-projection-ref:taw08:repository-derived",
        "source_revision_ref": lock.git_revision_ref,
        "status": "transitive_dependency_closed",
        "entries": [item.model_dump(mode="json") for item in root_entries],
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
    projection = SourceProjection(
        **projection_payload,
        projection_digest_ref=canonical_digest(projection_payload),
    )
    revision = lock.git_revision_ref.removeprefix("git-sha:")
    available = set(revision_path_census.path_refs)
    content_by_ref: dict[str, bytes] = {}
    dependencies_by_ref: dict[str, tuple[str, ...]] = {}
    frontier = [item.path_ref for item in root_entries]
    while frontier:
        path_ref = frontier.pop()
        if path_ref in content_by_ref:
            continue
        path = path_ref.removeprefix("repo-path-ref:")
        content = _git(
            "show",
            f"{revision}:{path}",
            repository_root=repository_root,
        )
        content_by_ref[path_ref] = content
        dependencies = derive_local_python_dependencies(
            path_ref,
            content,
            available_path_refs=available,
            allow_unresolved_dynamic_imports=(
                path_ref in TAW08_UNRESOLVED_DYNAMIC_IMPORT_PATH_REFS
            ),
        )
        dependencies_by_ref[path_ref] = dependencies
        frontier.extend(ref for ref in dependencies if ref not in content_by_ref)
    closure_entries = tuple(
        SourceDependencyEntry(
            path_ref=path_ref,
            content_digest_ref=(
                f"sha256:{hashlib.sha256(content_by_ref[path_ref]).hexdigest()}"
            ),
            dependency_path_refs=dependencies_by_ref[path_ref],
        )
        for path_ref in sorted(content_by_ref)
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": lock.git_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": tuple(item.path_ref for item in root_entries),
        "entries": [item.model_dump(mode="json") for item in closure_entries],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    return projection, closure, content_by_ref


def verify_repository_candidate(
    lock: CandidateLock,
    *,
    repository_root: Path = ROOT,
) -> _CandidateLockVerificationReceipt:
    revision = lock.git_revision_ref.removeprefix("git-sha:")
    if os.environ.get(_LOCKED_CHILD_REVISION_ENV) != revision:
        raise RuntimeError(
            "TAW-08 candidate receipts require the locked verifier child"
        )
    if (
        _git("rev-parse", "HEAD", repository_root=repository_root)
        .decode("ascii")
        .strip()
        != revision
        or _git(
            "status",
            "--porcelain",
            "--untracked-files=all",
            repository_root=repository_root,
        )
    ):
        raise RuntimeError(
            "TAW-08 locked verifier child requires the clean candidate checkout"
        )
    revision_path_census = derive_revision_path_census(
        lock.git_revision_ref,
        repository_root=repository_root,
    )
    projection, closure, closure_content = _source_evidence_from_git(
        lock,
        revision_path_census,
        repository_root=repository_root,
    )
    content_by_ref = {
        item.path_ref: _git(
            "show",
            f"{revision}:{item.path_ref.removeprefix('repo-path-ref:')}",
            repository_root=repository_root,
        )
        for item in lock.entries
    }
    if Path(__file__).read_bytes() != content_by_ref[
        TAW08_REPOSITORY_VERIFIER_PATH_REF
    ]:
        raise RuntimeError(
            "TAW-08 repository verifier differs from the candidate revision"
        )
    evaluator_environment_receipt = verify_locked_evaluator_environment(
        locked_content_by_path_ref={
            path_ref: content_by_ref[path_ref]
            for path_ref in (
                "repo-path-ref:pyproject.toml",
                "repo-path-ref:uv.lock",
            )
        },
        repository_root=repository_root,
    )
    executing_source_path_refs, executing_source_census_digest_ref = (
        verify_executing_repository_sources(
            revision,
            repository_root=repository_root,
        )
    )
    return _bind_candidate_lock_verification_receipt(
        candidate_lock=lock,
        expected_path_refs=tuple(item.path_ref for item in lock.entries),
        revision_content_by_path_ref=content_by_ref,
        source_projection=projection,
        source_closure=closure,
        closure_content_by_path_ref=closure_content,
        revision_path_census=revision_path_census,
        evaluator_environment_receipt=evaluator_environment_receipt,
        executing_source_path_refs=executing_source_path_refs,
        executing_source_census_digest_ref=executing_source_census_digest_ref,
    )


def verify_repository_evidence_delta(
    *,
    candidate_lock: CandidateLock,
    delta: EvidenceOnlyDeltaManifest,
    validated_acceptance_reports_by_path_ref: dict[str, TAW08AcceptanceReport]
    | None = None,
    repository_root: Path = ROOT,
) -> _EvidenceOnlyDeltaVerificationReceipt:
    census = derive_revision_delta_census(
        candidate_lock.git_revision_ref,
        delta.delta_revision_ref,
        repository_root=repository_root,
    )
    delta_revision = delta.delta_revision_ref.removeprefix("git-sha:")
    candidate_revision = candidate_lock.git_revision_ref.removeprefix("git-sha:")
    content_by_ref = {
        path_ref: _git(
            "show",
            f"{delta_revision}:{path_ref.removeprefix('repo-path-ref:')}",
            repository_root=repository_root,
        )
        for path_ref in census.path_refs
    }
    candidate_content_by_ref = {
        path_ref: _git(
            "show",
            f"{candidate_revision}:{path_ref.removeprefix('repo-path-ref:')}",
            repository_root=repository_root,
        )
        for path_ref in census.path_refs
        if path_ref.endswith(".md")
    }
    return _verify_and_bind_evidence_only_delta(
        candidate_lock=candidate_lock,
        delta=delta,
        changed_content_by_path_ref=content_by_ref,
        revision_delta_census=census,
        candidate_content_by_path_ref=candidate_content_by_ref,
        validated_acceptance_reports_by_path_ref=(
            validated_acceptance_reports_by_path_ref
        ),
    )


def verify_repository_foundation_gate(
    *,
    stage: Literal["exact_head", "postmerge"],
    repository_root: Path = ROOT,
) -> FoundationGateReceipt:
    if stage not in {"exact_head", "postmerge"}:
        raise ValueError("Foundation receipt stage is invalid")
    revision_ref, report = evaluate_foundation_gate_at_exact_repository_revision(
        repository_root
    )
    verify_executing_repository_sources(
        revision_ref.removeprefix("git-sha:"),
        repository_root=repository_root,
    )
    revision = revision_ref.removeprefix("git-sha:")
    evaluator_environment_receipt = verify_locked_evaluator_environment(
        locked_content_by_path_ref={
            path_ref: _git(
                "show",
                f"{revision}:{path_ref.removeprefix('repo-path-ref:')}",
                repository_root=repository_root,
            )
            for path_ref in (
                "repo-path-ref:pyproject.toml",
                "repo-path-ref:uv.lock",
            )
        },
        repository_root=repository_root,
    )
    report = report.model_copy(
        update={
            "command_mode": "report-only",
            "command_receipts": [report_only_receipt("report-only")],
        }
    )
    return _verify_and_bind_foundation_gate_report(
        report=report,
        stage=stage,
        revision_ref=revision_ref,
        evaluator_environment_receipt=evaluator_environment_receipt,
    )


def verify_repository_final_acceptance_publication(
    *,
    publication_revision_ref: str,
    candidate_revision_ref: str,
    candidate_manifest_digest_ref: str,
    founder_evidence_digest_ref: str,
    delta: EvidenceOnlyDeltaManifest,
    delta_verification_receipt: _EvidenceOnlyDeltaVerificationReceipt,
    postmerge_foundation_receipt: FoundationGateReceipt,
    repository_root: Path = ROOT,
) -> FinalAcceptancePublicationReceipt:
    publication_revision = publication_revision_ref.removeprefix("git-sha:")
    publication_path = TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF.removeprefix(
        "repo-path-ref:"
    )
    publication_content = _git(
        "show",
        f"{publication_revision}:{publication_path}",
        repository_root=repository_root,
    )
    publication_history_census = derive_publication_history_census(
        delta.delta_revision_ref,
        publication_revision_ref,
        repository_root=repository_root,
    )
    return _verify_and_bind_final_acceptance_publication(
        publication_revision_ref=publication_revision_ref,
        publication_path_ref=TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
        publication_content=publication_content,
        publication_history_census=publication_history_census,
        candidate_revision_ref=candidate_revision_ref,
        candidate_manifest_digest_ref=candidate_manifest_digest_ref,
        founder_evidence_digest_ref=founder_evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=delta_verification_receipt,
        postmerge_foundation_receipt=postmerge_foundation_receipt,
    )


def verify() -> None:
    revision = _git("rev-parse", "HEAD").decode("ascii").strip()
    lock, content_by_ref = _candidate_lock(revision)
    expected_refs = tuple(item.path_ref for item in lock.entries)
    failures = verify_candidate_lock(
        lock,
        expected_path_refs=expected_refs,
        revision_content_by_path_ref=content_by_ref,
    )
    if failures:
        raise RuntimeError(f"TAW-08 contract candidate lock failed: {failures}")
    candidate_receipt = verify_repository_candidate(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=candidate_receipt,
    )
    expected_missing = tuple(
        sorted(
            (
                *(
                    ref
                    for ref in TAW08_FOUNDER_EVIDENCE_MISSING_REFS
                    if ref
                    != "evidence-missing-ref:taw08:candidate-lock-verification-receipt"
                ),
                TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
                TAW08_FINAL_PUBLICATION_MISSING_REF,
            )
            + (TAW08_DELTA_VERIFICATION_MISSING_REF,)
        )
    )
    if (
        report.status != TAW08AcceptanceStatus.blocked_missing_founder_evidence
        or report.founder_private_accepted
        or report.founder_evidence_missing_refs != expected_missing
        or report.independent_promotion_ready
        or report.sealed_holdout_evidence_verified
        or report.public_quality_claims_allowed
    ):
        raise RuntimeError(
            "TAW-08 acceptance contract failed closed-state verification"
        )
    if any(
        (
            report.production_authority_added,
            report.runtime_model_calls_added,
            report.provider_calls_added,
            report.execution_authority_added,
            report.raw_content_persisted,
        )
    ):
        raise RuntimeError("TAW-08 verifier detected authority or content expansion")


def _run_locked_candidate_verifier() -> None:
    revision = _git("rev-parse", "HEAD").decode("ascii").strip()
    if _git("status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("TAW-08 verifier launcher requires a clean worktree")
    with tempfile.TemporaryDirectory(prefix="uaa-taw08-locked-") as temporary:
        candidate_root = Path(temporary) / "candidate"
        added = False
        try:
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "--detach",
                    str(candidate_root),
                    revision,
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            added = True
            child = subprocess.run(
                [
                    sys.executable,
                    str(candidate_root / "scripts/verify_tool_aware_cognition_taw08.py"),
                ],
                cwd=candidate_root,
                check=False,
                capture_output=True,
                env={
                    "PATH": os.environ.get("PATH", ""),
                    _LOCKED_CHILD_REVISION_ENV: revision,
                },
                timeout=300,
            )
            if child.returncode != 0:
                raise RuntimeError("TAW-08 locked candidate verifier failed")
        finally:
            if added:
                subprocess.run(
                    ["git", "worktree", "remove", str(candidate_root)],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                )


def main() -> int:
    if os.environ.get(_LOCKED_CHILD_REVISION_ENV):
        verify()
    else:
        _run_locked_candidate_verifier()
    print(
        "Tool-aware cognition TAW-08 acceptance contract verified; founder-private "
        "acceptance remains blocked on exact measured evidence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
