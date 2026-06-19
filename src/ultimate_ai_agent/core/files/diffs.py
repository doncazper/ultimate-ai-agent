import difflib
from pathlib import Path


def build_unified_diff(path: str, old_content: str, new_content: str) -> str:
    return "".join(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=path,
            tofile=path,
            lineterm="",
        )
    )


def build_redacted_diff_summary(path: str, old_content: str, new_content: str) -> str:
    added_lines = 0
    removed_lines = 0
    hunk_count = 0
    for line in difflib.unified_diff(
        old_content.splitlines(),
        new_content.splitlines(),
        fromfile=path,
        tofile=path,
        lineterm="",
    ):
        if line.startswith("@@"):
            hunk_count += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines += 1
    return (
        "Redacted file diff summary: "
        f"hunks={hunk_count}, added_lines={added_lines}, removed_lines={removed_lines}, raw_diff_omitted=True."
    )


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
