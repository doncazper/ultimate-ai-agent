from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import re
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


DIRECT_PRODUCT_VALIDATORS = {
    "verify_control_center_release_surface": "scripts.verify_control_center_release_surface",
    "verify_control_center_capability_surface": "scripts.verify_control_center_capability_surface",
    "verify_fcc_v1_001_api_perimeter": "scripts.verify_fcc_v1_001_api_perimeter",
    "verify_fcc_v1_002_action_inbox_state_machine": "scripts.verify_fcc_v1_002_action_inbox_state_machine",
    "verify_fcc_v1_003_founder_loop_vertical_slice": "scripts.verify_fcc_v1_003_founder_loop_vertical_slice",
    "verify_fcc_v1_004_chat_durable_receipt_handoff": "scripts.verify_fcc_v1_004_chat_durable_receipt_handoff",
    "verify_fcc_v1_005_memory_review_decisions": "scripts.verify_fcc_v1_005_memory_review_decisions",
    "verify_governed_cognitive_memory_spine_v1": "scripts.verify_governed_cognitive_memory_spine_v1",
    "verify_fcc_v1_006_evidence_timeline_productization": "scripts.verify_fcc_v1_006_evidence_timeline_productization",
    "verify_founder_loop_v1": "scripts.verify_founder_loop_v1",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class ProductVerifierFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class ProductVerificationSnapshot:
    root: Path
    api_context: Any
    release_surface: dict[str, Any]
    route_status: dict[str, Any]
    milestone_status: dict[str, Any]
    content_ref: str

    @classmethod
    def capture(cls, root: Path) -> ProductVerificationSnapshot:
        from scripts.verification.api_lane import default_api_verifier_context

        release_surface = _load_json(
            root / "docs/control_center/release_surface_manifest.json"
        )
        route_status = _load_json(
            root / "docs/control_center/route_status_manifest.json"
        )
        milestone_status = _load_json(
            root / "docs/verification/milestone_status_manifest.json"
        )
        content_ref = _product_content_ref(
            release_surface,
            route_status,
            milestone_status,
        )
        return cls(
            root=root,
            api_context=default_api_verifier_context(),
            release_surface=release_surface,
            route_status=route_status,
            milestone_status=milestone_status,
            content_ref=content_ref,
        )

    def run(self, function_name: str) -> None:
        module_name = DIRECT_PRODUCT_VALIDATORS[function_name]
        verifier = getattr(importlib.import_module(module_name), "verify")
        parameters = inspect.signature(verifier).parameters
        available = {
            "context": self.api_context,
            "release_surface": self.release_surface,
            "release_surface_manifest": self.release_surface,
            "route_status": self.route_status,
            "route_status_manifest": self.route_status,
            "milestone_status": self.milestone_status,
            "include_memory_review_verifier": False,
        }
        kwargs = {
            name: value for name, value in available.items() if name in parameters
        }
        failures = verifier(self.root, **kwargs)
        self.assert_unchanged()
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            raise ProductVerifierFailure(
                f"{function_name} returned {len(failures)} verification failures"
            )
        print(f"OK: {function_name} passed with shared product context")

    def assert_unchanged(self) -> None:
        current = _product_content_ref(
            self.release_surface,
            self.route_status,
            self.milestone_status,
        )
        if current != self.content_ref:
            raise ProductVerifierFailure("shared product verification snapshot mutated")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("shared product verification document must be an object")
    return payload


def _product_content_ref(*payloads: dict[str, Any]) -> str:
    encoded = json.dumps(payloads, separators=(",", ":"), sort_keys=True).encode()
    return f"product-context-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class StaticVerificationContext:
    root: Path
    scan_refs: tuple[str, ...]
    repository_sha: str
    registry_fingerprint: str
    snapshot_ref: str

    @classmethod
    def capture(
        cls,
        root: Path,
        scan_refs: tuple[str, ...],
        repository_sha: str,
        registry_fingerprint: str,
    ) -> StaticVerificationContext:
        resolved_root = root.resolve()
        if SHA_PATTERN.fullmatch(repository_sha) is None:
            raise ValueError("static verification repository SHA is invalid")
        if not registry_fingerprint.startswith("static-registry-ref:sha256:"):
            raise ValueError("static verification registry fingerprint is invalid")
        encoded = json.dumps(
            {
                "registry_fingerprint": registry_fingerprint,
                "repository_sha": repository_sha,
                "scan_refs": scan_refs,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        return cls(
            root=resolved_root,
            scan_refs=scan_refs,
            repository_sha=repository_sha,
            registry_fingerprint=registry_fingerprint,
            snapshot_ref=f"static-context-ref:sha256:{digest}",
        )

    @contextmanager
    def cached_repository_view(self) -> Iterator[None]:
        """Install a worker-local immutable view of repository walks and reads."""
        original_rglob = Path.rglob
        original_read_text = Path.read_text
        rglob_cache: dict[tuple[Path, str], tuple[Path, ...]] = {}
        read_text_cache: dict[tuple[Path, tuple[Any, ...], tuple[Any, ...]], str] = {}
        cacheable_paths: dict[Path, bool] = {}

        def is_cacheable(path: Path) -> bool:
            if path not in cacheable_paths:
                try:
                    cacheable_paths[path] = path.resolve().is_relative_to(self.root)
                except (OSError, RuntimeError):
                    cacheable_paths[path] = False
            return cacheable_paths[path]

        def cached_rglob(path: Path, pattern: str) -> Iterator[Path]:
            if not is_cacheable(path):
                return original_rglob(path, pattern)
            key = (path, pattern)
            if key not in rglob_cache:
                rglob_cache[key] = tuple(original_rglob(path, pattern))
            return iter(rglob_cache[key])

        def cached_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
            if not is_cacheable(path):
                return original_read_text(path, *args, **kwargs)
            key = (path, args, tuple(sorted(kwargs.items())))
            if key not in read_text_cache:
                read_text_cache[key] = original_read_text(path, *args, **kwargs)
            return read_text_cache[key]

        Path.rglob = cached_rglob
        Path.read_text = cached_read_text
        try:
            yield
        finally:
            Path.rglob = original_rglob
            Path.read_text = original_read_text


def resolve_repository_sha(root: Path) -> str:
    identity = subprocess.run(
        ("git", "rev-parse", "--show-toplevel", "HEAD"),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    status = subprocess.run(
        ("git", "status", "--porcelain", "--untracked-files=all"),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    identity_lines = identity.stdout.splitlines()
    sha = identity_lines[-1].strip() if identity_lines else ""
    try:
        top_level = (
            Path(identity_lines[0]).resolve() if len(identity_lines) == 2 else None
        )
        resolved_root = root.resolve()
    except (OSError, RuntimeError):
        top_level = None
        resolved_root = None
    if (
        identity.returncode != 0
        or status.returncode != 0
        or len(identity_lines) != 2
        or top_level != resolved_root
        or SHA_PATTERN.fullmatch(sha) is None
        or status.stdout.strip()
    ):
        raise ValueError(
            "static verification requires an exact clean repository revision"
        )
    return sha
