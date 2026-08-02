"""Bounded static inventory for supported frontend test declarations."""

from __future__ import annotations

import re


TEST_API_NAME = r"[A-Za-z_$][\w$]*"
TEST_MODIFIERS = r"(?:\s*\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
RUNNER_MODULES = {"vitest", "@playwright/test"}
IMPORT_PATTERN = re.compile(
    r"\bimport\s*\{(?P<members>[^}]*)\}\s*from\s*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)"
)
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


def _is_regex_start(
    text: str,
    start: int,
    regex_closures: set[int],
) -> bool:
    index = start - 1
    while index >= 0 and text[index].isspace():
        index -= 1
    if index < 0 or text[index] in "([{:;,=!?&|+-*%^~\n":
        return True
    if text[index] == "/":
        return index not in regex_closures
    if text[max(0, index - 1) : index + 1] == "=>":
        return True
    prefix = text[: index + 1]
    match = re.search(r"([A-Za-z_$][\w$]*)$", prefix)
    return bool(
        match
        and match.group(1) in {"case", "delete", "return", "throw", "typeof", "void"}
    )


def _skip_regex(text: str, start: int) -> tuple[int, int]:
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
            closing = index
            index += 1
            while index < len(text) and (text[index].isalpha() or text[index] == "_"):
                index += 1
            return index, closing
        index += 1
    raise FrontendInventoryError(
        "frontend test inventory has an unterminated regex literal"
    )


def _is_regex_literal_at(
    text: str,
    index: int,
    regex_closures: set[int],
) -> bool:
    return (
        text[index] == "/"
        and not text.startswith(("//", "/*"), index)
        and _is_regex_start(text, index, regex_closures)
    )


def _code_mask(text: str) -> bytearray:
    mask = bytearray(b"\x01" * len(text))
    regex_closures: set[int] = set()
    index = 0
    while index < len(text):
        if text[index] in "\"'`":
            end = _skip_string(text, index)
            mask[index:end] = b"\x00" * (end - index)
            index = end
            continue
        if _is_regex_literal_at(text, index, regex_closures):
            end, closing = _skip_regex(text, index)
            regex_closures.add(closing)
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
    regex_closures: set[int] = set()
    index = start + 1
    while index < len(text):
        character = text[index]
        if character in "\"'`":
            index = _skip_string(text, index)
            continue
        if _is_regex_literal_at(text, index, regex_closures):
            index, closing = _skip_regex(text, index)
            regex_closures.add(closing)
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


def _test_api_names(text: str, scan_text: str) -> set[str]:
    names = {"it", "test"}
    approved_import_bindings: set[str] = set()
    for match in IMPORT_PATTERN.finditer(text):
        if scan_text[match.start() : match.start() + len("import")] != "import":
            continue
        for member in match.group("members").split(","):
            binding = re.fullmatch(
                rf"\s*(?P<imported>{TEST_API_NAME})"
                rf"(?:\s+as\s+(?P<local>{TEST_API_NAME}))?\s*",
                member,
            )
            if binding is None:
                continue
            imported = binding.group("imported")
            local = binding.group("local") or imported
            if imported in {"it", "test"} and match.group("module") in RUNNER_MODULES:
                names.add(local)
                approved_import_bindings.add(local)
            elif local in {"it", "test"}:
                raise FrontendInventoryError(
                    "frontend test API name is shadowed by a non-runner import"
                )

    declaration_pattern = re.compile(
        r"\b(?:const|let|var|function|class)\s+(?P<name>it|test)\b"
    )
    if declaration_pattern.search(scan_text):
        raise FrontendInventoryError(
            "frontend test API name is shadowed by a local declaration"
        )
    destructuring_pattern = re.compile(
        r"\b(?:const|let|var)\s*\{(?P<bindings>[^{}]*)\}"
    )
    for match in destructuring_pattern.finditer(scan_text):
        for member in match.group("bindings").split(","):
            local = member.split(":", 1)[-1].split("=", 1)[0].strip()
            local = local.removeprefix("...").strip()
            if local in {"it", "test"}:
                raise FrontendInventoryError(
                    "frontend test API name is shadowed by a local declaration"
                )
    parameter_pattern = re.compile(r"\((?P<parameters>[^()]*)\)\s*(?:=>|\{)")
    if any(
        re.search(r"\b(?:it|test)\b", match.group("parameters"))
        for match in parameter_pattern.finditer(scan_text)
    ) or re.search(r"\b(?:it|test)\s*=>", scan_text):
        raise FrontendInventoryError(
            "frontend test API name is shadowed by a local declaration"
        )
    non_named_import_pattern = re.compile(
        r"\bimport\s+(?:type\s+)?(?:\*\s+as\s+)?(?P<name>it|test)\b"
    )
    for match in non_named_import_pattern.finditer(scan_text):
        if match.group("name") not in approved_import_bindings:
            raise FrontendInventoryError(
                "frontend test API name is shadowed by a non-runner import"
            )

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


def _parameterized_declarations(
    text: str,
    scan_text: str,
    pattern: re.Pattern[str],
) -> tuple[tuple[str, str], ...]:
    declarations: list[tuple[str, str]] = []
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
        declaration_end = _skip_balanced(text, index)
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            raise FrontendInventoryError("frontend parameterized test title is invalid")
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        declarations.append(
            (text[title_start:title_end], text[match.start() : declaration_end])
        )
    return tuple(declarations)


def _conditional_declarations(
    text: str,
    scan_text: str,
    pattern: re.Pattern[str],
) -> tuple[tuple[str, str], ...]:
    declarations: list[tuple[str, str]] = []
    for match in pattern.finditer(scan_text):
        index = _skip_balanced(text, match.end() - 1)
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != "(":
            raise FrontendInventoryError("frontend conditional test title is missing")
        declaration_end = _skip_balanced(text, index)
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            raise FrontendInventoryError("frontend conditional test title is invalid")
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        declarations.append(
            (text[title_start:title_end], text[match.start() : declaration_end])
        )
    return tuple(declarations)


def _frontend_inventory_entries(path: str, text: str) -> tuple[tuple[str, str], ...]:
    raw_entries: list[tuple[str, str]] = []
    code_mask = _code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    direct_pattern, each_pattern, conditional_pattern = _patterns(
        _test_api_names(text, scan_text)
    )
    for match in direct_pattern.finditer(scan_text):
        declaration_end = _skip_balanced(text, match.end() - 1)
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
        raw_entries.append((f"{path}::{title}", text[match.start() : declaration_end]))
    for raw_title, declaration_source in (
        *_parameterized_declarations(text, scan_text, each_pattern),
        *_conditional_declarations(text, scan_text, conditional_pattern),
    ):
        title = _normalized_title(raw_title)
        if not title or len(title) > 500:
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        raw_entries.append((f"{path}::{title}", declaration_source))

    counts: dict[str, int] = {}
    entries: list[tuple[str, str]] = []
    for raw_ref, declaration_source in raw_entries:
        occurrence = counts.get(raw_ref, 0) + 1
        counts[raw_ref] = occurrence
        ref = raw_ref if occurrence == 1 else f"{raw_ref}#{occurrence}"
        entries.append((ref, declaration_source))
    return tuple(entries)


def parse_frontend_refs(path: str, text: str) -> tuple[str, ...]:
    return tuple(ref for ref, _source in _frontend_inventory_entries(path, text))


def frontend_source_for_ref(path: str, text: str, test_ref: str) -> str | None:
    return dict(_frontend_inventory_entries(path, text)).get(test_ref)
