#!/usr/bin/env python3
"""Generate ignored local-web-service secrets without displaying them."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import secrets
import sys


SECRET_BYTES = 48
PLACEHOLDER = "__UAA_SEARXNG_SECRET__"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_once(path: Path, value: str) -> bool:
    if path.exists():
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("local state target must be a regular file")
        os.chmod(path, 0o600)
        return False
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(value)
        handle.write("\n")
    return True


def setup_local_state(*, state_dir: Path, template: Path) -> tuple[int, int]:
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state_dir, 0o700)
    generated = 0
    preserved = 0
    for filename in ("firecrawl_postgres_password", "firecrawl_bull_auth_key"):
        created = _write_once(state_dir / filename, secrets.token_urlsafe(SECRET_BYTES))
        generated += int(created)
        preserved += int(not created)

    settings_dir = state_dir / "searxng"
    settings_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(settings_dir, 0o700)
    settings_path = settings_dir / "settings.yml"
    if settings_path.exists():
        if not settings_path.is_file() or settings_path.is_symlink():
            raise RuntimeError("SearXNG settings target must be a regular file")
        os.chmod(settings_path, 0o600)
        preserved += 1
    else:
        rendered = template.read_text(encoding="utf-8")
        if rendered.count(PLACEHOLDER) != 1:
            raise RuntimeError("SearXNG template must contain one secret placeholder")
        rendered = rendered.replace(PLACEHOLDER, secrets.token_urlsafe(SECRET_BYTES))
        _write_once(settings_path, rendered.rstrip("\n"))
        generated += 1
    return generated, preserved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args(argv)
    root = _repo_root()
    state_dir = args.state_dir or root / ".uaa" / "local-web-services"
    template = (
        root / "packaging" / "local-web-services" / "searxng" / "settings.yml.template"
    )
    try:
        generated, preserved = setup_local_state(state_dir=state_dir, template=template)
    except (OSError, RuntimeError) as exc:
        print(f"local web service setup blocked: {type(exc).__name__}", file=sys.stderr)
        return 1
    print(
        "local web service state ready: "
        f"generated={generated} preserved={preserved} credential_values_displayed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
