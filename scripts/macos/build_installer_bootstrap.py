#!/usr/bin/env python3
"""Build the long-lived, self-contained macOS installer bootstrap."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_TAG = "uaa-installer-v1"
BOOTSTRAP_SCHEMA = "uaa.macos.installer-bootstrap.v1"


def build_bootstrap(
    *,
    source_root: Path,
    python_runtime: Path,
    output_dir: Path,
    architecture: str,
    signing_identity: str | None,
) -> dict[str, object]:
    if architecture not in {"arm64", "x86_64"}:
        raise ValueError("unsupported installer bootstrap architecture")
    if not (python_runtime / "bin" / "python3").is_file():
        raise ValueError("relocatable Python runtime is missing")
    source_package = source_root / "src" / "ultimate_ai_agent"
    if not (source_package / "distribution" / "macos" / "runtime.py").is_file():
        raise ValueError("macOS distribution package is missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"uaa-installer-macos-{architecture}.tar.gz"
    checksum = archive.with_name(archive.name + ".sha256")
    archive.unlink(missing_ok=True)
    checksum.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="uaa-installer-bootstrap-") as temporary:
        payload = Path(temporary) / "bootstrap"
        runtime = payload / "python"
        shutil.copytree(python_runtime, runtime, symlinks=False)
        purelib = _purelib(runtime / "bin" / "python3")
        target_package = purelib / "ultimate_ai_agent"
        target_package.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_package / "__init__.py", target_package / "__init__.py")
        shutil.copytree(
            source_package / "distribution",
            target_package / "distribution",
        )
        for cache in sorted(runtime.rglob("__pycache__"), reverse=True):
            if cache.is_dir():
                shutil.rmtree(cache)
        _sign_macho_tree(runtime, signing_identity=signing_identity)
        marker = {
            "schema_version": BOOTSTRAP_SCHEMA,
            "bootstrap_tag": BOOTSTRAP_TAG,
            "architecture": architecture,
            "signing_kind": "developer-id" if signing_identity else "ad-hoc",
            "scope": "exact UAA GitHub Release discovery and installation only",
            "agent_web_authority_added": False,
            "raw_paths_included": False,
            "credentials_included": False,
        }
        (payload / "bootstrap.json").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _archive(payload, archive)
    digest = _sha256(archive)
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    receipt = {
        "schema_version": BOOTSTRAP_SCHEMA,
        "status": "built",
        "bootstrap_tag": BOOTSTRAP_TAG,
        "architecture": architecture,
        "artifact_ref": f"github-release-asset:{archive.name}",
        "checksum_ref": f"sha256:{digest}",
        "signing_kind": "developer-id" if signing_identity else "ad-hoc",
        "raw_paths_included": False,
        "credentials_included": False,
    }
    (output_dir / "installer-bootstrap-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def _purelib(python: Path) -> Path:
    completed = subprocess.run(
        [
            str(python),
            "-c",
            "import sysconfig; print(sysconfig.get_paths()['purelib'])",
        ],
        text=True,
        capture_output=True,
        timeout=30.0,
        check=True,
    )
    return Path(completed.stdout.strip())


def _sign_macho_tree(root: Path, *, signing_identity: str | None) -> None:
    identity = signing_identity or "-"
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file() and _is_macho(item)),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        command = ["/usr/bin/codesign", "--force", "--sign", identity]
        if signing_identity:
            command.extend(["--options", "runtime", "--timestamp"])
        else:
            command.append("--timestamp=none")
        command.append(str(path))
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60.0,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("installer bootstrap code signing failed")


def _is_macho(path: Path) -> bool:
    completed = subprocess.run(
        ["/usr/bin/file", "-b", str(path)],
        text=True,
        capture_output=True,
        timeout=10.0,
        check=False,
    )
    return completed.returncode == 0 and "Mach-O" in completed.stdout


def _archive(payload: Path, target: Path) -> None:
    with tarfile.open(target, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        tar.dereference = True
        for path in sorted(payload.rglob("*")):
            info_name = path.relative_to(payload.parent).as_posix()
            tar.add(
                path,
                arcname=info_name,
                recursive=False,
                filter=_normalize_tar_info,
            )


def _normalize_tar_info(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    if info.isdir():
        info.mode = 0o755
    elif info.isfile():
        info.mode = 0o755 if info.mode & stat.S_IXUSR else 0o644
    return info


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the long-lived UAA macOS installer bootstrap"
    )
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--python-runtime", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--architecture", choices=["arm64", "x86_64"], required=True)
    parser.add_argument("--signing-identity", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = build_bootstrap(
        source_root=args.source_root.resolve(),
        python_runtime=args.python_runtime.resolve(),
        output_dir=args.output_dir.resolve(),
        architecture=args.architecture,
        signing_identity=args.signing_identity,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
