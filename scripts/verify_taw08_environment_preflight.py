from __future__ import annotations

import base64
import csv
import hashlib
import importlib.machinery
import io
import os
import re
import runpy
import sys
import urllib.parse
import zipfile
from pathlib import Path


_ENVIRONMENT_ROOT = "UAA_TAW08_ENVIRONMENT_ROOT"
_LOCKED_WHEELHOUSE = "UAA_TAW08_LOCKED_WHEELHOUSE"
_PREFLIGHT_COMPLETE = "UAA_TAW08_PREFLIGHT_COMPLETE"
_PREFLIGHT_DIGEST = "UAA_TAW08_PREFLIGHT_DIGEST"
_MAX_WHEELS = 2_048
_MAX_FILES = 200_000


def _site_packages(environment_root: Path) -> Path:
    if os.name == "nt":
        return environment_root / "Lib" / "site-packages"
    return (
        environment_root
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )


def _locked_wheel_artifacts(uv_lock: bytes) -> dict[str, tuple[int, str]]:
    if len(uv_lock) > 64 * 1024 * 1024:
        raise RuntimeError("TAW-08 preflight lock bound exceeded")
    try:
        lock_text = uv_lock.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("TAW-08 preflight lock is invalid") from exc
    wheel_pattern = re.compile(
        r'\{\s*url = "([^"\r\n]+\.whl)",\s*hash = "sha256:([0-9a-f]{64})",'
        r"\s*size = ([1-9][0-9]*)(?:, [^{}\r\n]{1,256})?\s*\}"
    )
    matches = tuple(wheel_pattern.finditer(lock_text))
    if (
        not matches
        or len(matches) > 100_000
        or len(re.findall(r'url = "[^"\r\n]+\.whl"', lock_text)) != len(matches)
    ):
        raise RuntimeError("TAW-08 preflight locked wheel census is invalid")
    artifacts: dict[str, tuple[int, str]] = {}
    for match in matches:
        url, digest, size_value = match.groups()
        parsed = urllib.parse.urlsplit(url)
        filename = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
        if (
            parsed.scheme != "https"
            or parsed.netloc != "files.pythonhosted.org"
            or parsed.query
            or parsed.fragment
            or not filename.endswith(".whl")
            or len(filename) > 512
        ):
            raise RuntimeError("TAW-08 preflight locked wheel URL is invalid")
        identity = (int(size_value), digest)
        existing = artifacts.get(filename)
        if existing is not None and existing != identity:
            raise RuntimeError("TAW-08 preflight locked wheel is ambiguous")
        artifacts[filename] = identity
    return artifacts


def _authenticated_wheel_files(
    *, wheelhouse: Path, uv_lock: bytes
) -> dict[str, tuple[int, str]]:
    artifacts = _locked_wheel_artifacts(uv_lock)
    wheel_paths = tuple(sorted(wheelhouse.glob("*.whl")))
    if not wheel_paths or len(wheel_paths) > _MAX_WHEELS:
        raise RuntimeError("TAW-08 preflight wheelhouse census is invalid")
    authenticated: dict[str, tuple[int, str]] = {}
    member_count = 0
    total_bytes = 0
    for wheel_path in wheel_paths:
        if (
            wheel_path.is_symlink()
            or not wheel_path.is_file()
            or wheel_path.name not in artifacts
            or wheel_path.parent.resolve() != wheelhouse
        ):
            raise RuntimeError("TAW-08 preflight wheel is not locked")
        wheel_content = wheel_path.read_bytes()
        expected_size, expected_hash = artifacts[wheel_path.name]
        if (
            len(wheel_content) != expected_size
            or hashlib.sha256(wheel_content).hexdigest() != expected_hash
        ):
            raise RuntimeError("TAW-08 preflight wheel differs from uv.lock")
        try:
            with zipfile.ZipFile(io.BytesIO(wheel_content)) as wheel:
                members = tuple(item for item in wheel.infolist() if not item.is_dir())
                names = tuple(item.filename for item in members)
                record_names = tuple(
                    name for name in names if name.endswith(".dist-info/RECORD")
                )
                if (
                    not members
                    or len(names) != len(set(names))
                    or len(record_names) != 1
                ):
                    raise RuntimeError("TAW-08 preflight wheel RECORD is invalid")
                rows = tuple(
                    csv.reader(
                        io.StringIO(
                            wheel.read(record_names[0]).decode("utf-8"), newline=""
                        )
                    )
                )
                if any(len(row) != 3 for row in rows):
                    raise RuntimeError("TAW-08 preflight wheel RECORD is invalid")
                record_by_ref = {row[0]: (row[1], row[2]) for row in rows}
                if len(record_by_ref) != len(rows) or set(record_by_ref) != set(names):
                    raise RuntimeError("TAW-08 preflight wheel RECORD is invalid")
                for member in members:
                    member_count += 1
                    total_bytes += member.file_size
                    member_name = member.filename
                    if (
                        member_count > _MAX_FILES
                        or member.file_size > 64 * 1024 * 1024
                        or total_bytes > 1024 * 1024 * 1024
                        or not member_name
                        or len(member_name) > 1_024
                        or member_name.startswith("/")
                        or ".." in Path(member_name).parts
                    ):
                        raise RuntimeError("TAW-08 preflight wheel bound exceeded")
                    content = wheel.read(member_name)
                    hash_value, size_value = record_by_ref[member_name]
                    if member_name == record_names[0]:
                        if hash_value or size_value:
                            raise RuntimeError(
                                "TAW-08 preflight wheel RECORD is invalid"
                            )
                        continue
                    actual_hash = (
                        base64.urlsafe_b64encode(hashlib.sha256(content).digest())
                        .rstrip(b"=")
                        .decode("ascii")
                    )
                    if hash_value != f"sha256={actual_hash}" or size_value != str(
                        len(content)
                    ):
                        raise RuntimeError("TAW-08 preflight wheel member is invalid")
                    installed_ref = member_name
                    data_match = re.match(
                        r"^[^/]+\.data/(?:purelib|platlib)/(.*)$", member_name
                    )
                    if data_match:
                        installed_ref = data_match.group(1)
                    elif re.match(
                        r"^[^/]+\.data/(?:scripts|headers|data)/", member_name
                    ):
                        continue
                    identity = (len(content), hashlib.sha256(content).hexdigest())
                    existing = authenticated.get(installed_ref)
                    if existing is not None and existing != identity:
                        raise RuntimeError("TAW-08 preflight wheel path is ambiguous")
                    authenticated[installed_ref] = identity
        except (OSError, UnicodeDecodeError, csv.Error, zipfile.BadZipFile) as exc:
            raise RuntimeError("TAW-08 preflight wheel is invalid") from exc
    return authenticated


def _verify_environment_census(
    *,
    environment_root: Path,
    site_packages: Path,
    authenticated_files: dict[str, tuple[int, str]],
) -> None:
    if not site_packages.is_dir() or not site_packages.is_relative_to(environment_root):
        raise RuntimeError("TAW-08 preflight site-packages is unavailable")
    importable_suffixes = {
        ".py",
        ".pyw",
        ".pth",
        ".egg-link",
        *importlib.machinery.EXTENSION_SUFFIXES,
    }
    observed = 0
    for path in site_packages.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("TAW-08 preflight found a symlink")
        resolved = path.resolve()
        if not resolved.is_relative_to(environment_root):
            raise RuntimeError("TAW-08 preflight path escapes environment")
        if path.is_dir():
            continue
        if not path.is_file():
            raise RuntimeError("TAW-08 preflight found a special file")
        observed += 1
        if observed > _MAX_FILES:
            raise RuntimeError("TAW-08 preflight file census bound exceeded")
        name = path.name
        relative_ref = path.relative_to(site_packages).as_posix()
        if any(name.endswith(suffix) for suffix in importable_suffixes):
            content = path.read_bytes()
            actual = (len(content), hashlib.sha256(content).hexdigest())
            if authenticated_files.get(relative_ref) != actual:
                raise RuntimeError(
                    "TAW-08 preflight found an unauthenticated importable file"
                )
        if name.endswith((".pyc", ".pyo")):
            raise RuntimeError("TAW-08 preflight found generated bytecode")
    for relative_ref, expected in authenticated_files.items():
        if not any(relative_ref.endswith(suffix) for suffix in importable_suffixes):
            continue
        path = site_packages / relative_ref
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise RuntimeError(
                "TAW-08 preflight importable file is unavailable"
            ) from exc
        if (len(content), hashlib.sha256(content).hexdigest()) != expected:
            raise RuntimeError("TAW-08 preflight importable file differs from wheel")


def verify_environment(verifier: Path) -> Path:
    if not sys.flags.isolated or not sys.flags.no_site:
        raise RuntimeError("TAW-08 preflight requires isolated no-site mode")
    root_value = os.environ.get(_ENVIRONMENT_ROOT)
    wheelhouse_value = os.environ.get(_LOCKED_WHEELHOUSE)
    if not root_value or not wheelhouse_value:
        raise RuntimeError("TAW-08 preflight environment inputs are unavailable")
    environment_root = Path(root_value).resolve()
    site_packages = _site_packages(environment_root).resolve()
    wheelhouse = Path(wheelhouse_value).resolve()
    authenticated_files = _authenticated_wheel_files(
        wheelhouse=wheelhouse,
        uv_lock=(verifier.parents[1] / "uv.lock").read_bytes(),
    )
    _verify_environment_census(
        environment_root=environment_root,
        site_packages=site_packages,
        authenticated_files=authenticated_files,
    )
    return site_packages


def main() -> int:
    if len(sys.argv) != 2:
        raise RuntimeError("TAW-08 preflight requires one verifier path")
    verifier = Path(sys.argv[1]).resolve()
    if not verifier.is_file():
        raise RuntimeError("TAW-08 preflight verifier is unavailable")
    site_packages = verify_environment(verifier)
    sys.path.insert(0, str(site_packages))
    os.environ[_PREFLIGHT_COMPLETE] = "1"
    os.environ[_PREFLIGHT_DIGEST] = (
        "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    )
    sys.argv = [str(verifier)]
    runpy.run_path(str(verifier), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
