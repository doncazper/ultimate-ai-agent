from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_ROOT = ROOT / "integrations" / "matrix-client-adapter"
LOCK_PATH = ADAPTER_ROOT / "package-lock.json"
OUTPUT_PATH = ADAPTER_ROOT / "runtime-integrity.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError("MATRIX_ADAPTER_INTEGRITY_TREE_EMPTY")
    for path in files:
        metadata = os.lstat(path)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise RuntimeError("MATRIX_ADAPTER_INTEGRITY_FILE_UNSAFE")
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(metadata.st_size).encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(_sha256(path)))
    return digest.hexdigest()


def build_manifest() -> dict[str, object]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    package_roots = sorted(
        key
        for key in lock.get("packages", {})
        if key.startswith("node_modules/") and "/node_modules/" not in key
    )
    roots = ["src", *package_roots]
    return {
        "schema_version": "uaa-matrix-client-adapter-integrity.v1",
        "package_lock_sha256": _sha256(LOCK_PATH),
        "trees": [
            {"root": root, "sha256": _tree_sha256(ADAPTER_ROOT / root)}
            for root in roots
        ],
        "raw_paths_included": False,
        "credential_material_included": False,
        "execution_authority_granted": False,
    }


def main() -> int:
    payload = json.dumps(build_manifest(), sort_keys=True, indent=2) + "\n"
    OUTPUT_PATH.write_text(payload, encoding="utf-8")
    print("Matrix adapter runtime integrity manifest refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
