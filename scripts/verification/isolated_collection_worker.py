"""Fixed collection-only worker. Its observations are NOT acceptance authority.

Started only by isolated_collection_observation, under an OS sandbox with
Python -I -B -S. Do not add an unsandboxed entry point or test execution here.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


MAX_ITEMS = 100_000
PROTOCOL = "uaa-isolated-collection-worker.v1"


def inactive_skipif_marker(mark: object) -> dict[str, object] | None:
    """Recognize only already-materialized false booleans; never eval a mark."""
    if mark.name != "skipif" or set(mark.kwargs) - {"condition", "reason"}:
        return None
    conditions = (
        (mark.kwargs["condition"],) if "condition" in mark.kwargs else mark.args
    )
    reason = mark.kwargs.get("reason")
    if (
        not conditions
        or any(type(value) is not bool or value for value in conditions)
        or type(reason) is not str
        or len(reason) > 4096
    ):
        return None
    return {"conditions": list(conditions), "reason": reason}


def main() -> int:
    import resource

    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (150, 150))
    root, dependencies, scratch, request_file, output_file = map(Path, sys.argv[1:])
    # The parent already created this exact directory. Avoid tempfile's
    # write-probe merely to compute gettempdir(). Existing import caches may
    # write only within this run-owned cache, never the host temporary area.
    tempfile.tempdir = str(scratch / "cache")
    request = json.loads(request_file.read_bytes())
    # -S prevents .pth/sitecustomize execution. Only the separately bound
    # dependency directory and frozen source are added, not ambient sys.path.
    sys.path[:0] = [str(dependencies), str(root / "src"), str(root)]
    retained = tuple(
        (name, getattr(builtins, name))
        for name in (
            "list",
            "dict",
            "set",
            "tuple",
            "str",
            "int",
            "bool",
            "type",
            "object",
            "__import__",
            "open",
            "compile",
            "eval",
            "exec",
        )
    )
    import pytest

    class Observer:
        def __init__(self) -> None:
            self.errors = 0
            self.skips = 0
            self.deselected = 0
            self.disabled = 0
            self.items: list[str] | None = None
            self.postures: list[str] | None = None

        def pytest_collectreport(self, report: object) -> None:
            self.errors += int(report.failed)
            self.skips += int(report.skipped)

        def pytest_deselected(self, items: list[object]) -> None:
            self.deselected += len(items)

        def pytest_sessionfinish(self, session: object, exitstatus: int) -> None:
            if len(session.items) > MAX_ITEMS:
                self.errors += 1
                return
            self.items = [
                hashlib.sha256(item.nodeid.encode("utf-8")).hexdigest()
                for item in session.items
            ]
            self.postures = []
            for item in session.items:
                postures = []
                for mark in item.iter_markers():
                    if mark.name not in {"skip", "skipif", "xfail"}:
                        continue
                    posture = inactive_skipif_marker(mark)
                    if posture is None:
                        self.disabled += 1
                    else:
                        postures.append(posture)
                encoded = json.dumps(
                    postures, sort_keys=True, separators=(",", ":")
                ).encode()
                self.postures.append(hashlib.sha256(encoded).hexdigest())

    observer = Observer()
    result = pytest.main(
        [
            "--collect-only",
            "-s",
            "-p",
            "no:terminal",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(scratch / "pytest"),
            "--rootdir",
            str(root),
            "-c",
            str(root / "pyproject.toml"),
            *(str(root / name) for name in request["tests"]),
        ],
        plugins=[observer],
    )
    model_counts = []
    for name in request["model_modules"]:
        module = sys.modules.get(name)
        count = 0
        if module is not None:
            for value in vars(module).values():
                if isinstance(value, type):
                    namespace = vars(value)
                    count += int(
                        namespace.get("__module__") == name
                        and namespace.get("__pydantic_complete__") is True
                        and "__pydantic_validator__" in namespace
                    )
        model_counts.append(count)
    payload = {
        "schema_version": PROTOCOL,
        "nonce": request["nonce"],
        "exit_code": int(result),
        "item_refs": observer.items,
        "posture_refs": observer.postures,
        "collection_errors": observer.errors,
        "collection_skips": observer.skips,
        "deselected": observer.deselected,
        "disabled_items": observer.disabled,
        "model_counts": model_counts,
        "builtin_bindings_preserved": all(
            getattr(builtins, name, None) is value for name, value in retained
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    # Output is private scratch, untrusted, bounded and revalidated by the
    # parent. A well-shaped payload is never a corpus-retirement attestation.
    descriptor = os.open(output_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
