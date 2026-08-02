"""Bounded static inventory for supported frontend test declarations."""

from __future__ import annotations

import re


TEST_API_NAME = r"[A-Za-z_$][\w$]*"
TEST_MODIFIERS = r"(?:\s*\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
IMPORT_PATTERN = re.compile(r"\bimport\s*\{(?P<members>[^}]*)\}")
EXTENSION_PATTERN = re.compile(
    rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*=\s*"
    rf"(?P<base>{TEST_API_NAME}){TEST_MODIFIERS}\s*\.extend\s*\("
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


def _is_regex_start(text: str, start: int) -> bool:
    index = start - 1
    while index >= 0 and text[index].isspace():
        index -= 1
    if index < 0 or text[index] in "([{:;,=!?&|+-*%^~\n":
        return True
    if text[max(0, index - 1) : index + 1] == "=>":
        return True
    prefix = text[: index + 1]
    match = re.search(r"([A-Za-z_$][\w$]*)$", prefix)
    return bool(
        match
        and match.group(1) in {"case", "delete", "return", "throw", "typeof", "void"}
    )


def _skip_regex(text: str, start: int) -> int:
    index = start + 1
    in_character_class = False
    while index < len(text):
        character = text[index]
        if character in "\r\n":
            raise FrontendInventoryError(
                "frontend test inventory has an unterminated regex literal"
            )
        if character == "\\":
            index += 2
            continue
        if character == "[":
            in_character_class = True
        elif character == "]":
            in_character_class = False
        elif character == "/" and not in_character_class:
            index += 1
            while index < len(text) and (text[index].isalpha() or text[index] == "_"):
                index += 1
            return index
        index += 1
    raise FrontendInventoryError(
        "frontend test inventory has an unterminated regex literal"
    )


def _code_mask(text: str) -> bytearray:
    mask = bytearray(b"\x01" * len(text))
    index = 0
    while index < len(text):
        if text[index] in "\"'`":
            end = _skip_string(text, index)
            mask[index:end] = b"\x00" * (end - index)
            index = end
            continue
        if (
            text[index] == "/"
            and not text.startswith(("//", "/*"), index)
            and _is_regex_start(text, index)
        ):
            end = _skip_regex(text, index)
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
        if (
            character == "/"
            and not text.startswith(("//", "/*"), index)
            and _is_regex_start(text, index)
        ):
            index = _skip_regex(text, index)
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


def _patterns(
    api_names: set[str],
) -> tuple[re.Pattern[str], re.Pattern[str], re.Pattern[str]]:
    names = "(?:" + "|".join(re.escape(name) for name in sorted(api_names)) + ")"
    direct = re.compile(rf"(?<![.\w$]){names}{TEST_MODIFIERS}\s*\(")
    each = re.compile(rf"(?<![.\w$]){names}{TEST_MODIFIERS}\.(?:each|for)\b")
    conditional = re.compile(
        rf"(?<![.\w$]){names}{TEST_MODIFIERS}\.(?:runIf|skipIf)\s*\("
    )
    return direct, each, conditional


def _test_api_names(scan_text: str) -> set[str]:
    names = {"it", "test"}
    for match in IMPORT_PATTERN.finditer(scan_text):
        for member in match.group("members").split(","):
            alias = re.fullmatch(
                rf"\s*(?:it|test)\s+as\s+({TEST_API_NAME})\s*",
                member,
            )
            if alias:
                names.add(alias.group(1))

    recognized_extensions: set[int] = set()
    while True:
        added = False
        for match in EXTENSION_PATTERN.finditer(scan_text):
            if match.group("base") in names:
                recognized_extensions.add(match.start("base"))
                if match.group("alias") not in names:
                    names.add(match.group("alias"))
                    added = True
        if not added:
            break

    api_pattern = "(?:" + "|".join(re.escape(name) for name in sorted(names)) + ")"
    for match in re.finditer(
        rf"(?<![.\w$]){api_pattern}{TEST_MODIFIERS}\s*\.extend\b",
        scan_text,
    ):
        if match.start() not in recognized_extensions:
            raise FrontendInventoryError(
                "frontend extended test API cannot be inventoried safely"
            )
    return names


def _parameterized_titles(
    text: str,
    scan_text: str,
    pattern: re.Pattern[str],
) -> tuple[str, ...]:
    titles: list[str] = []
    for match in pattern.finditer(scan_text):
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


def _conditional_titles(
    text: str,
    scan_text: str,
    pattern: re.Pattern[str],
) -> tuple[str, ...]:
    titles: list[str] = []
    for match in pattern.finditer(scan_text):
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
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    direct_pattern, each_pattern, conditional_pattern = _patterns(
        _test_api_names(scan_text)
    )
    for match in direct_pattern.finditer(scan_text):
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
        *_parameterized_titles(text, scan_text, each_pattern),
        *_conditional_titles(text, scan_text, conditional_pattern),
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
