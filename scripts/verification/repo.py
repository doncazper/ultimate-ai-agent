from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]


def repo_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def read_text(path: str | Path) -> str:
    return repo_path(path).read_text(encoding="utf-8")


def load_json(path: str | Path) -> Any:
    return json.loads(read_text(path))


def compact_text(path: str | Path) -> str:
    return normalize_snippet(read_text(path))


def normalize_snippet(text: str) -> str:
    return " ".join(text.lower().split())


def append_missing_doc_snippets(
    failures: list[str],
    required_doc_snippets: dict[str, Iterable[str]],
) -> None:
    for doc_path, snippets in required_doc_snippets.items():
        path = repo_path(doc_path)
        if not path.exists():
            failures.append(f"missing doc: {doc_path}")
            continue
        compact = compact_text(path)
        for snippet in snippets:
            if normalize_snippet(snippet) not in compact:
                failures.append(f"{doc_path} missing '{snippet}'")


def append_forbidden_claims(
    failures: list[str],
    scan_paths: Iterable[str],
    forbidden_claims: Iterable[str],
) -> None:
    for scan_path in scan_paths:
        path = repo_path(scan_path)
        if not path.exists():
            continue
        compact = compact_text(path)
        for forbidden in forbidden_claims:
            if normalize_snippet(forbidden) in compact:
                failures.append(f"{scan_path} contains forbidden claim '{forbidden}'")


def print_failures_or_success(failures: list[str], success_message: str) -> int:
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print(success_message)
    return 0
