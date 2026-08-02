"""Bounded static inventory for supported frontend test declarations."""

from __future__ import annotations

import re


FRONTEND_TEST_PATTERN = re.compile(
    r"(?<![.\w$])(?:it|test)"
    r"(?:\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*\s*\("
)
FRONTEND_EACH_PATTERN = re.compile(
    r"(?<![.\w$])(?:it|test)"
    r"(?:\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
    r"\.(?:each|for)\b"
)
FRONTEND_CONDITIONAL_PATTERN = re.compile(
    r"(?<![.\w$])(?:it|test)"
    r"(?:\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
    r"\.(?:runIf|skipIf)\s*\("
)


class FrontendInventoryError(RuntimeError):
    """Raised when a frontend declaration cannot be inventoried safely."""


def _normalized_title(value: str) -> str:
    return " ".join(value.split())


def _skip_string(text: str, start: int) -> int:
    quote = text[start]
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if quote == "`" and text.startswith("${", index):
            index = _skip_balanced(text, index + 1)
            continue
        if character == quote:
            return index + 1
        index += 1
    raise FrontendInventoryError("frontend test inventory has an unterminated string")


def _skip_comment(text: str, start: int) -> int:
    if text.startswith("//", start):
        newline = text.find("\n", start + 2)
        return len(text) if newline < 0 else newline + 1
    if text.startswith("/*", start):
        end = text.find("*/", start + 2)
        if end < 0:
            raise FrontendInventoryError(
                "frontend test inventory has an unterminated comment"
            )
        return end + 2
    return start


def _code_mask(text: str) -> bytearray:
    mask = bytearray(b"\x01" * len(text))
    index = 0
    while index < len(text):
        if text[index] in "\"'`":
            end = _skip_string(text, index)
            mask[index:end] = b"\x00" * (end - index)
            index = end
            continue
        comment_end = _skip_comment(text, index)
        if comment_end != index:
            mask[index:comment_end] = b"\x00" * (comment_end - index)
            index = comment_end
            continue
        index += 1
    return mask


def _skip_balanced(text: str, start: int) -> int:
    pairs = {"(": ")", "[": "]", "{": "}"}
    opening = text[start]
    if opening not in pairs:
        raise FrontendInventoryError("frontend parameterized test data is invalid")
    stack = [pairs[opening]]
    index = start + 1
    while index < len(text):
        character = text[index]
        if character in "\"'`":
            index = _skip_string(text, index)
            continue
        comment_end = _skip_comment(text, index)
        if comment_end != index:
            index = comment_end
            continue
        if character in pairs:
            stack.append(pairs[character])
        elif character == stack[-1]:
            stack.pop()
            if not stack:
                return index + 1
        index += 1
    raise FrontendInventoryError(
        "frontend parameterized test data has unbalanced delimiters"
    )


def _parameterized_titles(text: str, code_mask: bytearray) -> tuple[str, ...]:
    titles: list[str] = []
    for match in FRONTEND_EACH_PATTERN.finditer(text):
        if not code_mask[match.start()]:
            continue
        index = match.end()
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            raise FrontendInventoryError("frontend parameterized test data is missing")
        if text[index] == "(":
            index = _skip_balanced(text, index)
        elif text[index] == "`":
            index = _skip_string(text, index)
        else:
            raise FrontendInventoryError("frontend parameterized test data is invalid")
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != "(":
            raise FrontendInventoryError("frontend parameterized test title is missing")
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            raise FrontendInventoryError("frontend parameterized test title is invalid")
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        titles.append(text[title_start:title_end])
    return tuple(titles)


def _conditional_titles(text: str, code_mask: bytearray) -> tuple[str, ...]:
    titles: list[str] = []
    for match in FRONTEND_CONDITIONAL_PATTERN.finditer(text):
        if not code_mask[match.start()]:
            continue
        index = _skip_balanced(text, match.end() - 1)
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != "(":
            raise FrontendInventoryError("frontend conditional test title is missing")
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            raise FrontendInventoryError("frontend conditional test title is invalid")
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        titles.append(text[title_start:title_end])
    return tuple(titles)


def parse_frontend_refs(path: str, text: str) -> tuple[str, ...]:
    raw_refs: list[str] = []
    code_mask = _code_mask(text)
    for match in FRONTEND_TEST_PATTERN.finditer(text):
        if not code_mask[match.start()]:
            continue
        index = match.end()
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            if any(
                modifier in match.group(0) for modifier in (".skip", ".fail", ".fixme")
            ):
                continue
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        title = _normalized_title(text[title_start:title_end])
        if not title or len(title) > 500:
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        raw_refs.append(f"{path}::{title}")
    for raw_title in (
        *_parameterized_titles(text, code_mask),
        *_conditional_titles(text, code_mask),
    ):
        title = _normalized_title(raw_title)
        if not title or len(title) > 500:
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        raw_refs.append(f"{path}::{title}")

    counts: dict[str, int] = {}
    refs: list[str] = []
    for raw_ref in raw_refs:
        occurrence = counts.get(raw_ref, 0) + 1
        counts[raw_ref] = occurrence
        refs.append(raw_ref if occurrence == 1 else f"{raw_ref}#{occurrence}")
    return tuple(refs)
