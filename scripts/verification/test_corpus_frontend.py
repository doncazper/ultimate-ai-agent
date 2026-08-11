"""Bounded static inventory for supported frontend test declarations."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass


TEST_API_NAME = r"[A-Za-z_$][\w$]*"
TEST_MODIFIERS = r"(?:\s*\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
EXECUTION_DISABLING_TEST_MODIFIERS = frozenset({"fixme", "skip", "todo"})
CONDITIONAL_TEST_MODIFIERS = frozenset({"runIf", "skipIf"})
RUNNER_MODULES = {"vitest", "@playwright/test"}
IMPORT_PATTERN = re.compile(
    r"\bimport\s*\{(?P<members>[^}]*)\}\s*from\s*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)"
)
SIDE_EFFECT_IMPORT_PATTERN = re.compile(
    r"\bimport(?:\s+|/\*.*?\*/|//[^\r\n]*(?:\r?\n|$))*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)",
    re.DOTALL,
)
EMPTY_NAMED_IMPORT_PATTERN = re.compile(
    r"\bimport(?:\s+|/\*.*?\*/|//[^\r\n]*(?:\r?\n|$))*"
    r"\{(?:\s+|/\*.*?\*/|//[^\r\n]*(?:\r?\n|$))*\}"
    r"(?:\s+|/\*.*?\*/|//[^\r\n]*(?:\r?\n|$))*from"
    r"(?:\s+|/\*.*?\*/|//[^\r\n]*(?:\r?\n|$))*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)",
    re.DOTALL,
)
DEFAULT_IMPORT_PATTERN = re.compile(
    rf"\bimport\s+(?:type\s+)?(?P<name>{TEST_API_NAME})"
    rf"(?:\s*,\s*(?:\{{[^}}]*\}}|\*\s+as\s+{TEST_API_NAME}))?\s+from\s*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)"
)
EXPORT_FROM_PATTERN = re.compile(
    r"\bexport\s+(?:type\s+)?(?:\*|\{[^}]*\})\s+from\s*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)"
)
NAMESPACE_IMPORT_PATTERN = re.compile(
    r"\bimport\s+\*\s+as\s+(?P<name>[A-Za-z_$][\w$]*)\s+from\s*"
    r"(?P<quote>['\"])(?P<module>[^'\"]+)(?P=quote)"
)
EXTENSION_PATTERN = re.compile(
    rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*=\s*"
    rf"(?P<base>{TEST_API_NAME}){TEST_MODIFIERS}\s*\.extend\s*\("
)


class FrontendInventoryError(RuntimeError):
    """Raised when a frontend declaration cannot be inventoried safely."""


ImportBindingResolver = Callable[[str, str], str | None]


StaticValue = (
    str
    | bool
    | int
    | float
    | None
    | tuple["StaticValue", ...]
    | dict[str, "StaticValue"]
)


@dataclass(frozen=True)
class _RegistrationContext:
    title: str
    evidence_source: str
    execution_postures: tuple[str, ...] = ()


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
            if text[index] == "`":
                template_index = index + 1
                while template_index < end - 1:
                    if text[template_index] == "\\":
                        template_index += 2
                        continue
                    if text.startswith("${", template_index):
                        interpolation_end = _skip_balanced(text, template_index + 1)
                        body_start = template_index + 2
                        body_end = interpolation_end - 1
                        mask[body_start:body_end] = _code_mask(
                            text[body_start:body_end]
                        )
                        template_index = interpolation_end
                        continue
                    template_index += 1
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


def _javascript_tokens(source: str) -> tuple[str, ...]:
    """Return a bounded lexical token stream with comments and trivia removed."""

    tokens: list[str] = []
    regex_closures: set[int] = set()
    identifier = re.compile(r"[A-Za-z_$][\w$]*")
    number = re.compile(
        r"(?:0[xX][0-9A-Fa-f](?:_?[0-9A-Fa-f])*n?"
        r"|0[bB][01](?:_?[01])*n?"
        r"|0[oO][0-7](?:_?[0-7])*n?"
        r"|(?:\d(?:_?\d)*)?(?:\.\d(?:_?\d)*)"
        r"(?:[eE][+-]?\d(?:_?\d)*)?"
        r"|\d(?:_?\d)*(?:[eE][+-]?\d(?:_?\d)*)?n?)"
    )
    punctuators = (
        ">>>=",
        "**=",
        "&&=",
        "||=",
        "??=",
        "===",
        "!==",
        ">>>",
        "...",
        "=>",
        "++",
        "--",
        "&&",
        "||",
        "??",
        "==",
        "!=",
        "<=",
        ">=",
        "<<",
        ">>",
        "**",
        "?.",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "&=",
        "|=",
        "^=",
    )
    index = 0
    while index < len(source):
        character = source[index]
        if character.isspace():
            index += 1
            continue
        comment_end = _skip_comment(source, index)
        if comment_end != index:
            index = comment_end
            continue
        if character in "\"'`":
            end = _skip_string(source, index)
            tokens.append(source[index:end])
            index = end
            continue
        if _is_regex_literal_at(source, index, regex_closures):
            end, closing = _skip_regex(source, index)
            regex_closures.add(closing)
            tokens.append(source[index:end])
            index = end
            continue
        match = identifier.match(source, index) or number.match(source, index)
        if match is not None:
            tokens.append(match.group(0))
            index = match.end()
            continue
        punctuator = next(
            (
                candidate
                for candidate in punctuators
                if source.startswith(candidate, index)
            ),
            None,
        )
        if punctuator is not None:
            tokens.append(punctuator)
            index += len(punctuator)
            continue
        tokens.append(character)
        index += 1
    return tuple(tokens)


def _normalized_javascript_expression(source: str) -> str:
    """Canonicalize executable tokens without collapsing operator boundaries."""

    return json.dumps(
        _javascript_tokens(source),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _named_imports(
    text: str,
    scan_text: str,
) -> tuple[tuple[tuple[tuple[str, str], ...], str], ...]:
    """Parse runtime named imports while treating comments as static trivia."""

    imports: list[tuple[tuple[tuple[str, str], ...], str]] = []
    pattern = re.compile(r"\bimport\s*(?P<body>\{)")
    for match in pattern.finditer(scan_text):
        body_start = match.start("body")
        body_end = _skip_balanced(text, body_start)
        index = _skip_static_trivia(text, body_end)
        if not text.startswith("from", index):
            continue
        index = _skip_static_trivia(text, index + len("from"))
        if index >= len(text) or text[index] not in "\"'":
            raise FrontendInventoryError(
                "frontend named import cannot be inventoried safely"
            )
        module_end = _skip_string(text, index)
        module = text[index + 1 : module_end - 1]
        member_source = text[body_start + 1 : body_end - 1]
        member_mask = _code_mask(member_source)
        cleaned = "".join(
            character if member_mask[offset] else " "
            for offset, character in enumerate(member_source)
        )
        bindings: list[tuple[str, str]] = []
        for member in cleaned.split(","):
            if re.fullmatch(
                rf"\s*type\s+{TEST_API_NAME}"
                rf"(?:\s+as\s+{TEST_API_NAME})?\s*",
                member,
            ):
                continue
            binding = re.fullmatch(
                rf"\s*(?P<imported>{TEST_API_NAME})"
                rf"(?:\s+as\s+(?P<local>{TEST_API_NAME}))?\s*",
                member,
            )
            if binding is None:
                if member.strip():
                    raise FrontendInventoryError(
                        "frontend named import cannot be inventoried safely"
                    )
                continue
            imported = binding.group("imported")
            bindings.append((imported, binding.group("local") or imported))
        imports.append((tuple(bindings), module))
    return tuple(imports)


def _execution_posture_parts(declaration_source: str) -> tuple[str, ...]:
    """Return statically visible non-running Vitest posture components."""

    code_mask = _code_mask(declaration_source)
    scan_text = "".join(
        character if code_mask[index] else " "
        for index, character in enumerate(declaration_source)
    )
    arguments_start = scan_text.find("(")
    if arguments_start < 0:
        raise FrontendInventoryError(
            "frontend test declaration arguments cannot be inventoried safely"
        )
    call_chain = scan_text[:arguments_start]
    modifiers = tuple(
        match.group(1)
        for match in re.finditer(r"\.\s*([A-Za-z_$][\w$]*)\b", call_chain)
    )
    disabling = tuple(
        modifier
        for modifier in modifiers
        if modifier in EXECUTION_DISABLING_TEST_MODIFIERS
    )
    conditional = next(
        (
            modifier
            for modifier in reversed(modifiers)
            if modifier in CONDITIONAL_TEST_MODIFIERS
        ),
        None,
    )
    parts = [f"disabled:{modifier}" for modifier in disabling]
    if conditional is not None:
        condition_end = _skip_balanced(declaration_source, arguments_start)
        normalized_condition = _normalized_javascript_expression(
            declaration_source[arguments_start:condition_end]
        )
        digest = hashlib.sha256(normalized_condition.encode("utf-8")).hexdigest()
        parts.append(f"conditional:{conditional}:sha256:{digest}")
    return tuple(parts)


def _frontend_ref(
    path: str,
    title: str,
    *,
    parameter_digest: str | None = None,
    execution_postures: tuple[str, ...] = (),
) -> str:
    """Encode user titles and execution metadata as one collision-bound identity."""

    ref = f"{path}::{title}"
    if parameter_digest is not None:
        ref += f"::parameters-sha256:{parameter_digest}"
    posture = "+".join(execution_postures)
    if posture:
        ref += f"::execution-{posture}"
    reserved_title = any(
        marker in title
        for marker in (
            "::execution-",
            "::parameters-sha256:",
            "::identity-sha256:",
        )
    )
    if parameter_digest is not None or posture or reserved_title:
        structured = json.dumps(
            {
                "execution_postures": list(execution_postures),
                "parameter_digest": parameter_digest,
                "title": title,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = hashlib.sha256(structured.encode("utf-8")).hexdigest()
        ref += f"::identity-sha256:{digest}"
    return ref


def _has_indirect_runner_invocation(
    text: str,
    scan_text: str,
    *,
    names: set[str],
) -> bool:
    name_pattern = "(?:" + "|".join(re.escape(name) for name in sorted(names)) + ")"
    if re.search(
        rf"(?<![.\w$]){name_pattern}\s*\.\s*(?:apply|bind|call)\s*\(",
        scan_text,
    ):
        return True
    if re.search(
        rf"\(\s*[^(),;\r\n]+\s*,\s*{name_pattern}{TEST_MODIFIERS}\s*\)\s*\(",
        scan_text,
    ):
        return True
    if re.search(
        rf"\(\s*[^();\r\n]*?(?<![.\w$]){name_pattern}{TEST_MODIFIERS}"
        rf"\s*[^();\r\n]*\)\s*\(",
        scan_text,
    ):
        return True
    global_object = r"(?:globalThis|\(\s*globalThis(?:\s+as\s+[^()]*)?\s*\))"
    dot_property = rf"{global_object}\s*\.\s*{name_pattern}\b"
    if re.search(rf"{dot_property}\s*\(", scan_text):
        return True
    quoted_names = (
        "(?:"
        + "|".join(quoted for name in names for quoted in (f'"{name}"', f"'{name}'"))
        + ")"
    )
    computed_property = rf"{global_object}\s*\[\s*{quoted_names}\s*\]"
    return any(
        scan_text[match.start()] == text[match.start()]
        for match in re.finditer(rf"{computed_property}\s*\(", text)
    )


def _has_dynamic_runner_import(text: str, scan_text: str) -> bool:
    modules = "|".join(re.escape(module) for module in sorted(RUNNER_MODULES))
    pattern = re.compile(
        rf"\bimport\s*\(\s*(?P<quote>['\"])(?:{modules})(?P=quote)\s*\)"
    )
    for match in pattern.finditer(text):
        if scan_text[match.start() : match.start() + len("import")] != "import":
            continue
        prefix = scan_text[: match.start()]
        significant = prefix.rstrip()
        type_query = re.search(r"\btypeof\s*$", significant)
        type_start = type_query.start() if type_query is not None else match.start()
        type_prefix = scan_text[:type_start].rstrip()
        statement_start = max(
            type_prefix.rfind(";"),
            type_prefix.rfind("\n"),
            type_prefix.rfind("}"),
        )
        statement = type_prefix[statement_start + 1 :]
        if re.match(
            rf"\s*(?:export\s+)?type\s+{TEST_API_NAME}\b",
            statement,
        ):
            continue
        delimiter_stack: list[tuple[str, int]] = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        for index, character in enumerate(scan_text[:type_start]):
            if character in pairs:
                delimiter_stack.append((pairs[character], index))
            elif delimiter_stack and character == delimiter_stack[-1][0]:
                delimiter_stack.pop()
        if delimiter_stack and delimiter_stack[-1][0] == ")":
            parameters_start = delimiter_stack[-1][1]
            parameter = scan_text[parameters_start + 1 : type_start]
            comma = parameter.rfind(",")
            parameter = parameter[comma + 1 :]
            if re.fullmatch(
                rf"\s*(?:\.\.\.)?{TEST_API_NAME}\s*\??\s*:\s*",
                parameter,
            ):
                continue
        return True
    return False


def _has_global_api_mutation(
    text: str,
    scan_text: str,
    *,
    names: tuple[str, ...],
) -> bool:
    global_object = r"(?:globalThis|\(\s*globalThis(?:\s+as\s+[^()]*)?\s*\))"
    name_pattern = "(?:" + "|".join(re.escape(name) for name in names) + ")"
    operator_pattern = r"(?:=(?!=|>)|\+=|-=|\*=|/=|%=|&&=|\|\|=|\?\?=|\+\+|--)"
    dot_property = rf"{global_object}\s*\.\s*{name_pattern}\b"
    if re.search(rf"\bdelete\s+{dot_property}", scan_text) or re.search(
        rf"{dot_property}\s*{operator_pattern}",
        scan_text,
    ):
        return True
    quoted_names = (
        "(?:"
        + "|".join(quoted for name in names for quoted in (f'"{name}"', f"'{name}'"))
        + ")"
    )
    computed_property = rf"{global_object}\s*\[\s*{quoted_names}\s*\]"
    for pattern in (
        rf"\bdelete\s+{computed_property}",
        rf"{computed_property}\s*{operator_pattern}",
    ):
        if any(
            scan_text[match.start()] == text[match.start()]
            for match in re.finditer(pattern, text)
        ):
            return True
    property_key = rf"(?:{name_pattern}|{quoted_names})"
    property_mutators = (
        rf"\b(?:Object|Reflect)\s*\.\s*defineProperty\s*\(\s*{global_object}\s*,"
        rf"\s*{quoted_names}\s*,",
        rf"\bReflect\s*\.\s*set\s*\(\s*{global_object}\s*,"
        rf"\s*{quoted_names}\s*,",
        rf"\bObject\s*\.\s*assign\s*\(\s*{global_object}\s*,"
        rf"\s*\{{[^{{}}\r\n]*{property_key}\s*:",
    )
    if any(
        scan_text[match.start()] == text[match.start()]
        for pattern in property_mutators
        for match in re.finditer(pattern, text)
    ):
        return True
    return False


def _test_api_names(text: str, scan_text: str) -> set[str]:
    names = {"it", "test"}
    approved_import_bindings: set[str] = set()
    for bindings, module in _named_imports(text, scan_text):
        for imported, local in bindings:
            if imported in {"it", "test"} and module in RUNNER_MODULES:
                names.add(local)
                approved_import_bindings.add(local)
            elif local in {"it", "test"}:
                raise FrontendInventoryError(
                    "frontend test API name is shadowed by a non-runner import"
                )
    for match in NAMESPACE_IMPORT_PATTERN.finditer(text):
        if scan_text[match.start() : match.start() + len("import")] != "import":
            continue
        if match.group("module") not in RUNNER_MODULES:
            continue
        namespace = re.escape(match.group("name"))
        if re.search(
            rf"\b(?:const|let|var)\s*(?:\{{[^}}]*\b(?:it|test)\b[^}}]*\}}|"
            rf"\[[^\]]*\])\s*=\s*{namespace}\b|"
            rf"\b{namespace}\s*\[\s*['\"](?:it|test)['\"]\s*\]",
            scan_text,
        ):
            raise FrontendInventoryError(
                "frontend namespace-derived test API cannot be inventoried safely"
            )
        if re.search(rf"\b{namespace}\s*\.\s*(?:it|test)\b", scan_text):
            raise FrontendInventoryError(
                "frontend namespace test API cannot be inventoried safely"
            )

    recognized_extensions: set[int] = set()
    while True:
        added = False
        for match in EXTENSION_PATTERN.finditer(scan_text):
            if match.group("base") in names:
                recognized_extensions.add(match.start("alias"))
                if match.group("alias") not in names:
                    names.add(match.group("alias"))
                    added = True
        if not added:
            break

    api_names_pattern = (
        "(?:" + "|".join(re.escape(name) for name in sorted(names)) + ")"
    )
    if re.search(
        rf"(?<![.\w$]){api_names_pattern}{TEST_MODIFIERS}\s*\?\.",
        scan_text,
    ):
        raise FrontendInventoryError(
            "frontend optional test API call cannot be inventoried safely"
        )
    if _has_global_api_mutation(text, scan_text, names=("it", "test")):
        raise FrontendInventoryError(
            "frontend global test API mutation cannot be inventoried safely"
        )
    ordinary_alias_pattern = re.compile(
        rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*"
        rf"(?:\:\s*[^=;\r\n]+)?"
        rf"(?P<assignment>=)\s*"
        rf"(?P<assertion><\s*[^;\r\n]+>\s*)?"
        rf"(?P<wrapper>\(*\s*)"
        rf"(?P<base>{api_names_pattern})\b"
        rf"(?P<closers>\s*\)*)"
    )
    angle_alias_pattern = re.compile(
        rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*"
        rf"(?:\:\s*[^=;\r\n]+)?(?P<assignment>=)"
    )

    def angle_assertion_end(start: int) -> int | None:
        if start >= len(scan_text) or scan_text[start] != "<":
            return None
        index = start + 1
        angle_depth = 1
        delimiter_stack: list[str] = []
        delimiter_pairs = {"(": ")", "[": "]", "{": "}"}
        while index < len(scan_text) and angle_depth:
            character = scan_text[index]
            if character in delimiter_pairs:
                delimiter_stack.append(delimiter_pairs[character])
            elif delimiter_stack and character == delimiter_stack[-1]:
                delimiter_stack.pop()
            elif not delimiter_stack:
                if character == "<":
                    angle_depth += 1
                elif character == ">" and scan_text[index - 1] != "=":
                    angle_depth -= 1
            index += 1
        return index if angle_depth == 0 else None

    def angle_asserted_alias(match: re.Match[str]) -> bool:
        index = _skip_static_trivia(text, match.end("assignment"))
        outer_wrapper_count = 0
        while index < len(scan_text) and scan_text[index] == "(":
            outer_wrapper_count += 1
            index = _skip_static_trivia(text, index + 1)
        assertion_end = angle_assertion_end(index)
        if assertion_end is None:
            return False
        index = _skip_static_trivia(text, assertion_end)
        inner_wrapper_count = 0
        while index < len(scan_text) and scan_text[index] == "(":
            inner_wrapper_count += 1
            index = _skip_static_trivia(text, index + 1)
        base_match = re.match(api_names_pattern, scan_text[index:])
        if base_match is None:
            return False
        base = base_match.group(0)
        index += len(base)
        for _ in range(outer_wrapper_count + inner_wrapper_count):
            index = _skip_static_trivia(text, index)
            if index >= len(scan_text) or scan_text[index] != ")":
                raise FrontendInventoryError(
                    "frontend test API alias cannot be inventoried safely"
                )
            index += 1
        suffix_start = _skip_static_trivia(text, index)
        return (
            match.group("alias") != base
            and match.start("alias") not in recognized_extensions
            and not text.startswith(("=>", ".extend"), suffix_start)
        )

    def is_ordinary_alias(match: re.Match[str]) -> bool:
        initializer_start = _skip_static_trivia(text, match.end("assignment"))
        if match.group("assertion"):
            if initializer_start != match.start("assertion"):
                return False
            initializer_start = _skip_static_trivia(text, match.end("assertion"))
        if match.group("wrapper"):
            if (
                initializer_start >= match.start("base")
                or text[initializer_start] != "("
                or match.group("closers").count(")") < match.group("wrapper").count("(")
            ):
                return False
            suffix_start = _skip_static_trivia(text, match.end("closers"))
            return not text.startswith("=>", suffix_start)
        if initializer_start != match.start("base"):
            return False
        suffix_start = _skip_static_trivia(text, match.end("base"))
        return not text.startswith(".extend", suffix_start)

    def has_unproven_runner_reference(
        initializer_start: int,
        initializer_end: int,
    ) -> bool:
        for runner_match in re.finditer(
            rf"(?<![.\w$]){api_names_pattern}(?![\w$])",
            scan_text[initializer_start:initializer_end],
        ):
            index = _skip_static_trivia(
                text,
                initializer_start + runner_match.end(),
            )
            if index >= initializer_end:
                return True
            if scan_text[index] == "(":
                continue
            if scan_text[index] != ".":
                return True
            member_match = re.match(
                rf"(?:\s*\.\s*{TEST_API_NAME})+",
                scan_text[index:initializer_end],
            )
            if member_match is None:
                return True
            member_source = member_match.group(0)
            member_names = re.findall(TEST_API_NAME, member_source)
            index = _skip_static_trivia(text, index + member_match.end())
            if index >= initializer_end or scan_text[index] != "(":
                return True
            call_end = _skip_balanced(text, index)
            if member_names[-1] in {"each", "for", "runIf", "skipIf"}:
                next_call = _skip_static_trivia(text, call_end)
                if next_call >= initializer_end or scan_text[next_call] != "(":
                    return True
                continue
            if all(
                member
                in {
                    "concurrent",
                    "fail",
                    "fails",
                    "fixme",
                    "only",
                    "sequential",
                    "skip",
                    "todo",
                }
                for member in member_names
            ):
                continue
            return True
        return False

    if any(
        match.group("alias") != match.group("base")
        and match.start("alias") not in recognized_extensions
        and is_ordinary_alias(match)
        for match in ordinary_alias_pattern.finditer(scan_text)
    ) or any(
        angle_asserted_alias(match) for match in angle_alias_pattern.finditer(scan_text)
    ):
        raise FrontendInventoryError(
            "frontend test API alias cannot be inventoried safely"
        )
    unproven_runner_alias = False
    for match in angle_alias_pattern.finditer(scan_text):
        initializer_start = _skip_static_trivia(text, match.end("assignment"))
        initializer_end = _unbraced_expression_end(
            text,
            scan_text,
            initializer_start,
        )
        for assertion_start in range(initializer_start, initializer_end):
            if scan_text[assertion_start] != "<":
                continue
            assertion_end = angle_assertion_end(assertion_start)
            if assertion_end is None or assertion_end > initializer_end:
                continue
            base_start = _skip_static_trivia(text, assertion_end)
            if re.match(api_names_pattern, scan_text[base_start:initializer_end]):
                raise FrontendInventoryError(
                    "frontend test API alias cannot be inventoried safely"
                )
        initializer = scan_text[initializer_start:initializer_end]
        if re.search(r"(?:\?|&&|\|\|)", initializer) and re.search(
            rf"(?<![.\w$]){api_names_pattern}(?![\w$])",
            initializer,
        ):
            raise FrontendInventoryError(
                "frontend test API alias cannot be inventoried safely"
            )
        unproven_runner_alias = unproven_runner_alias or (
            match.start("alias") not in recognized_extensions
            and has_unproven_runner_reference(initializer_start, initializer_end)
        )

    declaration_pattern = re.compile(
        rf"\b(?:const|let|var|function|class)\s+(?P<name>{api_names_pattern})\b"
    )
    for match in declaration_pattern.finditer(scan_text):
        if match.start("name") not in recognized_extensions:
            raise FrontendInventoryError(
                "frontend test API name is shadowed by a local declaration"
            )
    destructuring_pattern = re.compile(
        r"\b(?:const|let|var)\s*\{(?P<bindings>[^{}]*)\}"
    )
    if re.search(r"\b(?:const|let|var)\s*\{[^{}]*\{", scan_text):
        raise FrontendInventoryError(
            "frontend nested destructuring cannot be inventoried safely"
        )
    for match in destructuring_pattern.finditer(scan_text):
        for member in match.group("bindings").split(","):
            local = member.split(":", 1)[-1].split("=", 1)[0].strip()
            local = local.removeprefix("...").strip()
            if local in names:
                raise FrontendInventoryError(
                    "frontend test API name is shadowed by a local declaration"
                )
    array_destructuring_pattern = re.compile(
        r"\b(?:const|let|var)\s*\[(?P<bindings>[^\[\]]*)\]"
    )
    if re.search(r"\b(?:const|let|var)\s*\[[^\[\]]*\[", scan_text):
        raise FrontendInventoryError(
            "frontend nested destructuring cannot be inventoried safely"
        )
    for match in array_destructuring_pattern.finditer(scan_text):
        if re.search(rf"\b{api_names_pattern}\b", match.group("bindings")):
            raise FrontendInventoryError(
                "frontend test API name is shadowed by a local declaration"
            )
    parameter_pattern = re.compile(r"\((?P<parameters>[^()]*)\)\s*(?:=>|\{)")
    if any(
        re.search(rf"\b{api_names_pattern}\b", match.group("parameters"))
        for match in parameter_pattern.finditer(scan_text)
    ) or re.search(rf"\b{api_names_pattern}\s*=>", scan_text):
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

    api_pattern = "(?:" + "|".join(re.escape(name) for name in sorted(names)) + ")"
    for match in re.finditer(
        rf"(?<![.\w$]){api_pattern}{TEST_MODIFIERS}\s*\.extend\b",
        scan_text,
    ):
        extension_base_starts = {
            extension.start("base")
            for extension in EXTENSION_PATTERN.finditer(scan_text)
            if extension.group("alias") in names
        }
        if match.start() not in extension_base_starts:
            raise FrontendInventoryError(
                "frontend extended test API cannot be inventoried safely"
            )
    if unproven_runner_alias:
        raise FrontendInventoryError(
            "frontend test API alias cannot be inventoried safely"
        )
    return names


def _suite_api_names(text: str, scan_text: str) -> set[str]:
    names = {"describe", "suite"}
    for bindings, module in _named_imports(text, scan_text):
        for imported, local in bindings:
            if imported in {"describe", "suite"}:
                if module not in RUNNER_MODULES:
                    raise FrontendInventoryError(
                        "frontend suite API name is shadowed by a non-runner import"
                    )
                names.add(local)
            elif local in {"describe", "suite"}:
                raise FrontendInventoryError(
                    "frontend suite API name is shadowed by a non-runner import"
                )
    names_pattern = "(?:" + "|".join(re.escape(name) for name in sorted(names)) + ")"
    if re.search(
        rf"(?<![.\w$]){names_pattern}{TEST_MODIFIERS}\s*\?\.",
        scan_text,
    ):
        raise FrontendInventoryError(
            "frontend optional suite API call cannot be inventoried safely"
        )
    if _has_global_api_mutation(text, scan_text, names=("describe", "suite")):
        raise FrontendInventoryError(
            "frontend global suite API mutation cannot be inventoried safely"
        )
    ordinary_alias_pattern = re.compile(
        rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*"
        rf"(?:\:\s*[^=;\r\n]+)?"
        rf"(?P<assignment>=)\s*"
        rf"(?P<assertion><\s*[^;\r\n]+>\s*)?"
        rf"(?P<wrapper>\(*\s*)"
        rf"(?P<base>{names_pattern})\b"
        rf"(?P<closers>\s*\)*)"
    )

    def is_ordinary_alias(match: re.Match[str]) -> bool:
        initializer_start = _skip_static_trivia(text, match.end("assignment"))
        if match.group("assertion"):
            if initializer_start != match.start("assertion"):
                return False
            initializer_start = _skip_static_trivia(text, match.end("assertion"))
        if match.group("wrapper"):
            if (
                initializer_start >= match.start("base")
                or text[initializer_start] != "("
                or match.group("closers").count(")") < match.group("wrapper").count("(")
            ):
                return False
            suffix_start = _skip_static_trivia(text, match.end("closers"))
            return not text.startswith("=>", suffix_start)
        return initializer_start == match.start("base")

    if any(
        match.group("alias") != match.group("base") and is_ordinary_alias(match)
        for match in ordinary_alias_pattern.finditer(scan_text)
    ):
        raise FrontendInventoryError(
            "frontend suite API alias cannot be inventoried safely"
        )
    if re.search(rf"\b(?:const|let|var|function|class)\s+{names_pattern}\b", scan_text):
        raise FrontendInventoryError(
            "frontend suite API name is shadowed by a local declaration"
        )
    destructuring_pattern = re.compile(
        r"\b(?:const|let|var)\s*\{(?P<bindings>[^{}]*)\}"
    )
    if re.search(r"\b(?:const|let|var)\s*\{[^{}]*\{", scan_text):
        raise FrontendInventoryError(
            "frontend nested destructuring cannot be inventoried safely"
        )
    for match in destructuring_pattern.finditer(scan_text):
        for member in match.group("bindings").split(","):
            local = member.split(":", 1)[-1].split("=", 1)[0].strip()
            local = local.removeprefix("...").strip()
            if local in names:
                raise FrontendInventoryError(
                    "frontend suite API name is shadowed by a local declaration"
                )
    array_destructuring_pattern = re.compile(
        r"\b(?:const|let|var)\s*\[(?P<bindings>[^\[\]]*)\]"
    )
    if re.search(r"\b(?:const|let|var)\s*\[[^\[\]]*\[", scan_text):
        raise FrontendInventoryError(
            "frontend nested destructuring cannot be inventoried safely"
        )
    for match in array_destructuring_pattern.finditer(scan_text):
        if re.search(rf"\b{names_pattern}\b", match.group("bindings")):
            raise FrontendInventoryError(
                "frontend suite API name is shadowed by a local declaration"
            )
    parameter_pattern = re.compile(r"\((?P<parameters>[^()]*)\)\s*(?:=>|\{)")
    if any(
        re.search(rf"\b{names_pattern}\b", match.group("parameters"))
        for match in parameter_pattern.finditer(scan_text)
    ) or re.search(rf"\b{names_pattern}\s*=>", scan_text):
        raise FrontendInventoryError(
            "frontend suite API name is shadowed by a local declaration"
        )
    return names


def _parameterized_declarations(
    text: str,
    scan_text: str,
    pattern: re.Pattern[str],
) -> tuple[tuple[int, str, str, str], ...]:
    declarations: list[tuple[int, str, str, str]] = []
    for match in pattern.finditer(scan_text):
        index = match.end()
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            raise FrontendInventoryError("frontend parameterized test data is missing")
        data_start = index
        if text[index] == "(":
            index = _skip_balanced(text, index)
        elif text[index] == "`":
            index = _skip_string(text, index)
        else:
            raise FrontendInventoryError("frontend parameterized test data is invalid")
        data_end = index
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
        title_end = _skip_string(text, index) - 1
        declarations.append(
            (
                match.start(),
                text[index : title_end + 1],
                text[match.start() : declaration_end],
                text[data_start:data_end],
            )
        )
    return tuple(declarations)


def _const_initializer_source(
    text: str,
    scan_text: str,
    name: str,
    before_offset: int,
    proven_parameter_call_ranges: frozenset[tuple[int, int]] | None = None,
    *,
    _seen_names: frozenset[str] = frozenset(),
    _validate_references: bool = True,
) -> str | None:
    if name in _seen_names:
        raise FrontendInventoryError(
            "frontend parameterized test binding dependencies are circular"
        )
    pattern = re.compile(rf"\bconst\s+{re.escape(name)}\b")
    matches = [match for match in pattern.finditer(scan_text, 0, before_offset)]
    if not matches:
        return None
    if len(matches) != 1:
        raise FrontendInventoryError("frontend parameterized test binding is ambiguous")
    match = matches[0]
    equals = -1
    for index in range(match.end(), before_offset):
        if scan_text[index] == ";":
            break
        if scan_text[index] != "=":
            continue
        previous = scan_text[index - 1] if index else ""
        following = scan_text[index + 1] if index + 1 < len(text) else ""
        if previous not in "=!<>" and following not in "=>":
            equals = index
            break
    if equals < 0:
        raise FrontendInventoryError("frontend parameterized test binding is invalid")
    value_start = equals + 1
    while value_start < before_offset and text[value_start].isspace():
        value_start += 1
    if value_start >= before_offset or text[value_start] not in "[{'\"`(":
        raise FrontendInventoryError("frontend parameterized test binding is dynamic")
    if text[value_start] in "[({":
        value_end = _skip_balanced(text, value_start)
    else:
        value_end = _skip_string(text, value_start)
    semicolon = scan_text.find(";", value_end, before_offset)
    newline = scan_text.find("\n", value_end, before_offset)
    boundaries = [boundary for boundary in (semicolon, newline) if boundary >= 0]
    if not boundaries:
        raise FrontendInventoryError("frontend parameterized test binding is invalid")
    semicolon = min(boundaries)
    if semicolon == newline:
        continuation = semicolon + 1
        while continuation < before_offset and text[continuation] in " \t\r":
            continuation += 1
        if text.startswith((".", "?."), continuation):
            raise FrontendInventoryError(
                "frontend parameterized test ASI continuation cannot be inventoried safely"
            )
    suffix = text[value_end:semicolon].strip()
    if _validate_references and suffix and re.fullmatch(r"as\s+const", suffix) is None:
        raise FrontendInventoryError("frontend parameterized test binding is dynamic")
    initializer_scan = scan_text[value_start:value_end]
    allowed_identifiers = {
        "Date",
        "false",
        "Infinity",
        "NaN",
        "new",
        "null",
        "true",
        "undefined",
    }
    dependencies: set[str] = set()
    for dependency in re.finditer(TEST_API_NAME, initializer_scan):
        identifier = dependency.group(0)
        if identifier in allowed_identifiers:
            continue
        absolute_start = value_start + dependency.start()
        absolute_end = value_start + dependency.end()
        prefix = scan_text[max(value_start, absolute_start - 3) : absolute_start]
        following = scan_text[absolute_end:value_end]
        if (prefix.endswith(".") and not prefix.endswith("...")) or re.match(
            r"\s*:", following
        ):
            continue
        dependencies.add(identifier)

    intervening = scan_text[semicolon + 1 : before_offset]
    escaped_name = re.escape(name)
    function_pattern = re.compile(
        rf"\b(?:async\s+)?function\s+(?P<name>{TEST_API_NAME})\s*\("
    )
    for helper in function_pattern.finditer(scan_text, 0, match.start()):
        arguments_end = _skip_balanced(text, helper.end() - 1)
        body_start = arguments_end
        while body_start < match.start() and text[body_start].isspace():
            body_start += 1
        if body_start >= match.start() or text[body_start] != "{":
            continue
        body_end = _skip_balanced(text, body_start)
        if re.search(
            rf"\b{escaped_name}\b", scan_text[body_start:body_end]
        ) and re.search(rf"\b{re.escape(helper.group('name'))}\s*\(", intervening):
            raise FrontendInventoryError(
                "frontend parameterized test binding is used by an unproven helper"
            )
    mutation_patterns = (
        rf"\b{escaped_name}\s*(?:\[[^;\n]*\]|\.[A-Za-z_$][\w$]*)?\s*(?:[+\-*/%]=|&&=|\|\|=|\?\?=|=(?!=|>)|\+\+|--)",
        rf"\b{escaped_name}\s*\.\s*(?:add|clear|copyWithin|delete|fill|pop|push|reverse|set|shift|sort|splice|unshift)\s*\(",
        rf"\bObject\s*\.\s*assign\s*\(\s*{escaped_name}\b",
    )
    if any(re.search(candidate, intervening) for candidate in mutation_patterns):
        raise FrontendInventoryError(
            "frontend parameterized test binding is mutated before collection"
        )
    if _validate_references:
        call_pattern = re.compile(
            rf"(?P<callee>\b{TEST_API_NAME}(?:\s*(?:\.|\?\.)\s*{TEST_API_NAME})*|(?:\]|\)))"
            r"\s*(?:\?\.)?\s*(?P<opening>\()"
        )
        proven_ranges = list(proven_parameter_call_ranges or frozenset())
        proven_offsets = {start for start, _end in proven_ranges}
        for call in call_pattern.finditer(scan_text, semicolon + 1, before_offset):
            opening = call.start("opening")
            call_end = _skip_balanced(text, opening)
            if call_end > before_offset:
                continue
            if call.start() in proven_offsets or any(
                start <= call.start() < end for start, end in proven_ranges
            ):
                continue
            arguments = scan_text[opening + 1 : call_end - 1]
            if re.search(rf"\b{escaped_name}\b", arguments):
                raise FrontendInventoryError(
                    "frontend parameterized test binding is passed to an "
                    "unproven call before collection"
                )
        use_pattern = re.compile(rf"\b{escaped_name}\b")
        for use in use_pattern.finditer(scan_text, semicolon + 1, before_offset):
            if any(start <= use.start() < end for start, end in proven_ranges):
                continue
            line_start = scan_text.rfind("\n", semicolon + 1, use.start()) + 1
            line_prefix = scan_text[line_start : use.start()]
            if re.search(
                r"(?:\b(?:export\s+)?type\b[^=]*=|:\s*|\bas\s+|\bsatisfies\s+)"
                r"[^=;\n]*\btypeof\s*$",
                line_prefix,
            ):
                continue
            raise FrontendInventoryError(
                "frontend parameterized test binding has an unproven use before collection"
            )
    sources = [text[match.start() : semicolon + 1]]
    for dependency in sorted(dependencies):
        dependency_source = _const_initializer_source(
            text,
            scan_text,
            dependency,
            match.start(),
            _seen_names=frozenset((*_seen_names, name)),
            _validate_references=False,
        )
        if dependency_source is None:
            function_pattern = re.compile(
                rf"\b(?:async\s+)?function\s+{re.escape(dependency)}\s*\("
            )
            function_matches = list(
                function_pattern.finditer(scan_text, 0, match.start())
            )
            if len(function_matches) != 1:
                raise FrontendInventoryError(
                    "frontend parameterized test binding initializer has unproven dependencies"
                )
            function_match = function_matches[0]
            arguments_end = _skip_balanced(text, function_match.end() - 1)
            body_start = arguments_end
            while body_start < match.start() and text[body_start].isspace():
                body_start += 1
            if body_start >= match.start() or text[body_start] != "{":
                raise FrontendInventoryError(
                    "frontend parameterized test binding initializer has unproven dependencies"
                )
            body_end = _skip_balanced(text, body_start)
            dependency_source = text[function_match.start() : body_end]
            all_helper_pattern = re.compile(
                rf"\b(?:async\s+)?function\s+(?P<name>{TEST_API_NAME})\s*\("
            )
            declared_helpers = {
                candidate.group("name")
                for candidate in all_helper_pattern.finditer(scan_text)
            }
            called_helpers = {
                candidate.group("name")
                for candidate in re.finditer(
                    rf"\b(?P<name>{TEST_API_NAME})\s*\(",
                    scan_text[body_start:body_end],
                )
                if candidate.group("name") in declared_helpers
            }
            if called_helpers:
                raise FrontendInventoryError(
                    "frontend parameterized test binding initializer has "
                    "unproven transitive helper dependencies"
                )
            prior_const_pattern = re.compile(rf"\bconst\s+(?P<name>{TEST_API_NAME})\b")
            prior_const_names = {
                candidate.group("name")
                for candidate in prior_const_pattern.finditer(
                    scan_text, 0, function_match.start()
                )
            }
            for referenced_name in sorted(prior_const_names):
                if re.search(
                    rf"\b{re.escape(referenced_name)}\b",
                    scan_text[body_start:body_end],
                ):
                    referenced_source = _const_initializer_source(
                        text,
                        scan_text,
                        referenced_name,
                        function_match.start(),
                        _seen_names=frozenset((*_seen_names, name, dependency)),
                        _validate_references=False,
                    )
                    if referenced_source is not None:
                        dependency_source += "\n" + referenced_source
        sources.append(dependency_source)
    return "\n".join(sources)


def _import_binding(
    text: str,
    scan_text: str,
    name: str,
    before_offset: int,
) -> tuple[str, str] | None:
    bindings: list[tuple[str, str]] = []
    for match in IMPORT_PATTERN.finditer(text, 0, before_offset):
        if scan_text[match.start() : match.start() + len("import")] != "import":
            continue
        for member in match.group("members").split(","):
            binding = re.fullmatch(
                rf"\s*(?:type\s+)?(?P<imported>{TEST_API_NAME})"
                rf"(?:\s+as\s+(?P<local>{TEST_API_NAME}))?\s*",
                member,
            )
            if binding is None:
                continue
            local = binding.group("local") or binding.group("imported")
            if local == name:
                bindings.append((match.group("module"), binding.group("imported")))
    if len(bindings) > 1:
        raise FrontendInventoryError(
            "frontend parameterized test import binding is ambiguous"
        )
    return bindings[0] if bindings else None


def _bound_parameter_data(
    text: str,
    scan_text: str,
    parameter_data: str,
    before_offset: int,
    import_binding_resolver: ImportBindingResolver | None,
    proven_parameter_call_ranges: frozenset[tuple[int, int]],
) -> str:
    if not (parameter_data.startswith("(") and parameter_data.endswith(")")):
        return parameter_data
    expression = parameter_data[1:-1].strip()
    while expression.startswith("(") and expression.endswith(")"):
        if _skip_balanced(expression, 0) != len(expression):
            break
        expression = expression[1:-1].strip()
    if re.fullmatch(TEST_API_NAME, expression) is None:
        expression_mask = _code_mask(expression)
        expression_scan = "".join(
            character if expression_mask[index] else " "
            for index, character in enumerate(expression)
        )
        literal_collection = False
        if expression.startswith(("[", "{")):
            literal_end = _skip_balanced(expression, 0)
            literal_suffix = expression[literal_end:].strip()
            literal_collection = not literal_suffix or bool(
                re.fullmatch(r"as\s+const", literal_suffix)
            )
        dependencies: set[str] = set()
        allowed_identifiers = {
            "Array",
            "Object",
            "Date",
            "Infinity",
            "NaN",
            "as",
            "async",
            "await",
            "break",
            "case",
            "catch",
            "class",
            "const",
            "continue",
            "default",
            "delete",
            "do",
            "else",
            "export",
            "extends",
            "false",
            "finally",
            "for",
            "from",
            "function",
            "if",
            "import",
            "in",
            "instanceof",
            "let",
            "new",
            "null",
            "of",
            "return",
            "satisfies",
            "switch",
            "throw",
            "true",
            "try",
            "typeof",
            "undefined",
            "var",
            "void",
            "while",
            "with",
            "yield",
        }
        dependency_scan = (
            expression_scan[:literal_end] if literal_collection else expression_scan
        )
        local_binding_names = {
            candidate.group("name")
            for candidate in re.finditer(
                rf"\b(?:const|let|var)\s+(?P<name>{TEST_API_NAME})\b",
                dependency_scan,
            )
        }
        for candidate in re.finditer(
            rf"(?:\((?P<parameters>[^()]*)\)|(?P<single>{TEST_API_NAME}))\s*=>",
            dependency_scan,
        ):
            parameters = candidate.group("parameters")
            if parameters is None:
                parameters = candidate.group("single") or ""
            local_binding_names.update(re.findall(TEST_API_NAME, parameters))
        for match in re.finditer(TEST_API_NAME, dependency_scan):
            name = match.group(0)
            prefix = dependency_scan[max(0, match.start() - 3) : match.start()]
            following = dependency_scan[match.end() :]
            if (
                name in allowed_identifiers
                or name in local_binding_names
                or (match.start() > 0 and dependency_scan[match.start() - 1].isdigit())
                or (prefix.endswith(".") and not prefix.endswith("..."))
                or re.match(r"\s*:", following)
                or re.match(r"\s*=>", following)
                or re.match(r"\s*\(", following)
                or re.match(r"\s*\.", following)
            ):
                continue
            dependencies.add(name)
        if literal_collection and not dependencies:
            return parameter_data
        if not dependencies:
            raise FrontendInventoryError(
                "frontend parameterized test data expression cannot be resolved safely"
            )
        sources = [parameter_data]
        for dependency in sorted(dependencies):
            local_source = _const_initializer_source(
                text,
                scan_text,
                dependency,
                before_offset,
                proven_parameter_call_ranges,
                _validate_references=False,
            )
            if local_source is not None:
                sources.append(local_source)
                continue
            imported = _import_binding(text, scan_text, dependency, before_offset)
            if imported is None or import_binding_resolver is None:
                raise FrontendInventoryError(
                    "frontend parameterized test binding cannot be resolved safely"
                )
            module, imported_name = imported
            imported_source = import_binding_resolver(module, imported_name)
            if imported_source is None:
                raise FrontendInventoryError(
                    "frontend parameterized test import cannot be resolved safely"
                )
            sources.append(
                f"module={module}\nimported={imported_name}\n{imported_source}"
            )
        return "\n".join(sources)

    local_source = _const_initializer_source(
        text,
        scan_text,
        expression,
        before_offset,
        proven_parameter_call_ranges,
    )
    if local_source is not None:
        return local_source
    imported = _import_binding(text, scan_text, expression, before_offset)
    if imported is None or import_binding_resolver is None:
        raise FrontendInventoryError(
            "frontend parameterized test binding cannot be resolved safely"
        )
    module, imported_name = imported
    imported_source = import_binding_resolver(module, imported_name)
    if imported_source is None:
        raise FrontendInventoryError(
            "frontend parameterized test import cannot be resolved safely"
        )
    return f"module={module}\nimported={imported_name}\n{imported_source}"


def frontend_export_binding_source(text: str, name: str) -> str | None:
    """Return a bounded static exported-const initializer for parameter data."""

    code_mask = _code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    export_pattern = re.compile(rf"\bexport\s+const\s+{re.escape(name)}\b")
    if export_pattern.search(scan_text) is None:
        return None
    return _const_initializer_source(text, scan_text, name, len(text))


def frontend_relative_import_modules(text: str) -> tuple[str, ...]:
    """Return relative static module specifiers from executable code."""

    code_mask = _code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    matches = sorted(
        (
            match.start(),
            match.group("module"),
            "export" if match.re is EXPORT_FROM_PATTERN else "import",
        )
        for pattern in (
            IMPORT_PATTERN,
            NAMESPACE_IMPORT_PATTERN,
            DEFAULT_IMPORT_PATTERN,
            SIDE_EFFECT_IMPORT_PATTERN,
            EMPTY_NAMED_IMPORT_PATTERN,
            EXPORT_FROM_PATTERN,
        )
        for match in pattern.finditer(text)
        if match.group("module").startswith(".")
    )
    modules: list[str] = []
    for offset, module, keyword in matches:
        if scan_text[offset : offset + len(keyword)] != keyword:
            continue
        if module not in modules:
            modules.append(module)
    return tuple(modules)


def frontend_collection_setup_modules(text: str) -> tuple[str, ...]:
    """Return statically configured Vitest setup-file module specifiers."""

    code_mask = _code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    modules: list[str] = []

    def append_literal(start: int) -> int:
        if text[start] not in "\"'":
            raise FrontendInventoryError(
                "frontend setup-file configuration cannot be inventoried safely"
            )
        end = _skip_string(text, start)
        value = text[start + 1 : end - 1]
        if not value or "\\" in value or "\0" in value or value.startswith("/"):
            raise FrontendInventoryError(
                "frontend setup-file configuration cannot be inventoried safely"
            )
        module = value if value.startswith(".") else f"./{value}"
        if module not in modules:
            modules.append(module)
        return end

    for match in re.finditer(r"\bsetupFiles?\s*:", scan_text):
        start = _skip_static_trivia(text, match.end())
        if start >= len(text):
            raise FrontendInventoryError(
                "frontend setup-file configuration cannot be inventoried safely"
            )
        if text[start] in "\"'":
            append_literal(start)
            continue
        if text[start] != "[":
            raise FrontendInventoryError(
                "frontend setup-file configuration cannot be inventoried safely"
            )
        end = _skip_balanced(text, start)
        index = _skip_static_trivia(text, start + 1)
        while index < end - 1:
            index = append_literal(index)
            index = _skip_static_trivia(text, index)
            if index >= end - 1:
                break
            if text[index] != ",":
                raise FrontendInventoryError(
                    "frontend setup-file configuration cannot be inventoried safely"
                )
            index = _skip_static_trivia(text, index + 1)
    return tuple(modules)


def _relative_imported_call_names(text: str, scan_text: str) -> set[str]:
    names: set[str] = set()
    for match in IMPORT_PATTERN.finditer(text):
        if (
            not match.group("module").startswith(".")
            or scan_text[match.start() : match.start() + len("import")] != "import"
        ):
            continue
        for member in match.group("members").split(","):
            binding = re.fullmatch(
                rf"\s*(?:type\s+)?(?P<imported>{TEST_API_NAME})"
                rf"(?:\s+as\s+(?P<local>{TEST_API_NAME}))?\s*",
                member,
            )
            if binding is not None:
                names.add(binding.group("local") or binding.group("imported"))
    for match in DEFAULT_IMPORT_PATTERN.finditer(text):
        if (
            match.group("module").startswith(".")
            and scan_text[match.start() : match.start() + len("import")] == "import"
        ):
            names.add(match.group("name"))
    return names


def _has_unproven_imported_registration_call(
    text: str,
    scan_text: str,
    block_regions: tuple[tuple[int, int], ...],
    expression_regions: tuple[tuple[int, int], ...],
) -> bool:
    for name in sorted(_relative_imported_call_names(text, scan_text)):
        for match in re.finditer(rf"(?<![.\w$]){re.escape(name)}\s*\(", scan_text):
            if any(start < match.start() < end for start, end in block_regions):
                continue
            if any(start <= match.start() < end for start, end in expression_regions):
                continue
            return True
    return False


def _conditional_declarations(
    text: str,
    scan_text: str,
    pattern: re.Pattern[str],
) -> tuple[tuple[int, str, str], ...]:
    declarations: list[tuple[int, str, str]] = []
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
        title_end = _skip_string(text, index) - 1
        declarations.append(
            (
                match.start(),
                text[index : title_end + 1],
                text[match.start() : declaration_end],
            )
        )
    return tuple(declarations)


def _static_collection_source(
    text: str,
    scan_text: str,
    name: str,
    before_offset: int,
    import_binding_resolver: ImportBindingResolver | None,
    *,
    _seen_names: frozenset[str] = frozenset(),
) -> str:
    if name in _seen_names:
        raise FrontendInventoryError("frontend registration loop bindings are circular")
    try:
        local_source = _const_initializer_source(
            text,
            scan_text,
            name,
            before_offset,
        )
    except FrontendInventoryError as exc:
        if "binding is dynamic" not in str(exc):
            raise
        local_source = None
    if local_source is not None:
        return local_source

    pattern = re.compile(rf"\bconst\s+{re.escape(name)}\b")
    matches = list(pattern.finditer(scan_text, 0, before_offset))
    if len(matches) == 1:
        match = matches[0]
        statement_end = scan_text.find(";", match.end(), before_offset)
        if statement_end < 0:
            statement_end = scan_text.find("\n", match.end(), before_offset)
        if statement_end < 0:
            raise FrontendInventoryError(
                "frontend registration loop binding is invalid"
            )
        alias = re.fullmatch(
            rf"\s*=\s*(?P<name>{TEST_API_NAME})(?:\s+as\s+const)?\s*",
            scan_text[match.end() : statement_end],
        )
        if alias is None:
            raise FrontendInventoryError(
                "frontend registration loop binding is dynamic"
            )
        escaped_name = re.escape(name)
        intervening = scan_text[statement_end + 1 : before_offset]
        if re.search(
            rf"\b{escaped_name}\s*(?:\[[^;\n]*\]|\.[A-Za-z_$][\w$]*)*\s*"
            r"(?:[+\-*/%]=|&&=|\|\|=|\?\?=|=(?!=|>)|\+\+|--)",
            intervening,
        ):
            raise FrontendInventoryError(
                "frontend registration loop binding is mutated before collection"
            )
        if re.search(rf"\b{escaped_name}\b", intervening):
            raise FrontendInventoryError(
                "frontend registration loop alias has an unproven use before collection"
            )
        dependency_source = _static_collection_source(
            text,
            scan_text,
            alias.group("name"),
            match.start(),
            import_binding_resolver,
            _seen_names=frozenset((*_seen_names, name)),
        )
        return f"{text[match.start() : statement_end + 1]}\n{dependency_source}"

    imported = _import_binding(text, scan_text, name, before_offset)
    if imported is None or import_binding_resolver is None:
        raise FrontendInventoryError(
            "frontend registration loop binding cannot be resolved safely"
        )
    module, imported_name = imported
    imported_source = import_binding_resolver(module, imported_name)
    if imported_source is None:
        raise FrontendInventoryError(
            "frontend registration loop import cannot be resolved safely"
        )
    return f"module={module}\nimported={imported_name}\n{imported_source}"


def _static_collection_items(collection_source: str) -> tuple[str, ...]:
    scan_text = "".join(
        character if visible else " "
        for character, visible in zip(
            collection_source,
            _code_mask(collection_source),
            strict=True,
        )
    )
    initializer_start = -1
    initializer_end = -1
    for match in re.finditer(rf"\bconst\s+{TEST_API_NAME}\s*=", scan_text):
        candidate = match.end()
        while (
            candidate < len(collection_source)
            and collection_source[candidate].isspace()
        ):
            candidate += 1
        if candidate < len(collection_source) and collection_source[candidate] == "[":
            initializer_start = candidate
            initializer_end = _skip_balanced(collection_source, candidate)
            break
    if initializer_start < 0:
        raise FrontendInventoryError(
            "frontend registration loop collection is not a static array"
        )
    items: list[str] = []
    item_start = initializer_start + 1
    depth = 0
    for index in range(item_start, initializer_end - 1):
        if not scan_text[index].strip():
            continue
        character = scan_text[index]
        if character in "[({":
            depth += 1
        elif character in "])}":
            depth -= 1
        elif character == "," and depth == 0:
            item = collection_source[item_start:index].strip()
            if not item:
                raise FrontendInventoryError(
                    "frontend registration loop collection cannot be sparse"
                )
            items.append(item)
            item_start = index + 1
    final_item = collection_source[item_start : initializer_end - 1].strip()
    if final_item:
        items.append(final_item)
    if not items or any(item.startswith("...") for item in items):
        raise FrontendInventoryError(
            "frontend registration loop collection items cannot be proven"
        )
    return tuple(items)


def _skip_static_trivia(source: str, start: int) -> int:
    index = start
    while True:
        while index < len(source) and source[index].isspace():
            index += 1
        comment_end = _skip_comment(source, index)
        if comment_end == index:
            return index
        index = comment_end


def _combine_utf16_surrogates(value: str) -> str:
    combined: list[str] = []
    index = 0
    while index < len(value):
        codepoint = ord(value[index])
        if 0xD800 <= codepoint <= 0xDBFF:
            if index + 1 >= len(value):
                raise FrontendInventoryError(
                    "frontend registration loop string has an unpaired surrogate"
                )
            low = ord(value[index + 1])
            if not 0xDC00 <= low <= 0xDFFF:
                raise FrontendInventoryError(
                    "frontend registration loop string has an unpaired surrogate"
                )
            combined.append(chr(0x10000 + ((codepoint - 0xD800) << 10) + low - 0xDC00))
            index += 2
            continue
        if 0xDC00 <= codepoint <= 0xDFFF:
            raise FrontendInventoryError(
                "frontend registration loop string has an unpaired surrogate"
            )
        combined.append(value[index])
        index += 1
    return "".join(combined)


def _static_string_value(source: str, start: int) -> tuple[str, int]:
    quote = source[start]
    if quote not in "\"'`":
        raise FrontendInventoryError("frontend registration loop value is not static")
    value: list[str] = []
    index = start + 1
    escapes = {
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
        "0": "\0",
    }
    while index < len(source):
        character = source[index]
        if character == quote:
            return _combine_utf16_surrogates("".join(value)), index + 1
        if quote == "`" and source.startswith("${", index):
            raise FrontendInventoryError(
                "frontend registration loop value is not a static literal"
            )
        if character != "\\":
            value.append(character)
            index += 1
            continue
        index += 1
        if index >= len(source):
            break
        escaped = source[index]
        if escaped in escapes:
            value.append(escapes[escaped])
            index += 1
            continue
        if escaped in "\"'`\\":
            value.append(escaped)
            index += 1
            continue
        if escaped in "xu":
            digits = 2 if escaped == "x" else 4
            encoded = source[index + 1 : index + 1 + digits]
            if len(encoded) != digits or re.fullmatch(r"[0-9A-Fa-f]+", encoded) is None:
                raise FrontendInventoryError(
                    "frontend registration loop string escape is invalid"
                )
            value.append(chr(int(encoded, 16)))
            index += digits + 1
            continue
        if escaped in "\r\n":
            if (
                escaped == "\r"
                and index + 1 < len(source)
                and source[index + 1] == "\n"
            ):
                index += 1
            index += 1
            continue
        value.append(escaped)
        index += 1
    raise FrontendInventoryError("frontend registration loop string is unterminated")


def _static_value(source: str, start: int = 0) -> tuple[StaticValue, int]:
    index = _skip_static_trivia(source, start)
    if index >= len(source):
        raise FrontendInventoryError("frontend registration loop item is empty")
    if source[index] in "\"'`":
        return _static_string_value(source, index)
    if source[index] == "[":
        values: list[StaticValue] = []
        index += 1
        while True:
            index = _skip_static_trivia(source, index)
            if index < len(source) and source[index] == "]":
                return tuple(values), index + 1
            value, index = _static_value(source, index)
            values.append(value)
            index = _skip_static_trivia(source, index)
            if index >= len(source) or source[index] not in ",]":
                raise FrontendInventoryError(
                    "frontend registration loop array item is invalid"
                )
            if source[index] == "]":
                return tuple(values), index + 1
            index += 1
    if source[index] == "{":
        values: dict[str, StaticValue] = {}
        index += 1
        while True:
            index = _skip_static_trivia(source, index)
            if index < len(source) and source[index] == "}":
                return values, index + 1
            if index >= len(source):
                break
            if source[index] in "\"'`":
                key, index = _static_string_value(source, index)
            else:
                key_match = re.match(TEST_API_NAME, source[index:])
                if key_match is None:
                    break
                key = key_match.group(0)
                index += len(key)
            index = _skip_static_trivia(source, index)
            if index >= len(source) or source[index] != ":":
                break
            value, index = _static_value(source, index + 1)
            if key in values:
                raise FrontendInventoryError(
                    "frontend registration loop object keys are ambiguous"
                )
            values[key] = value
            index = _skip_static_trivia(source, index)
            if index >= len(source) or source[index] not in ",}":
                break
            if source[index] == "}":
                return values, index + 1
            index += 1
        raise FrontendInventoryError(
            "frontend registration loop object item is invalid"
        )
    literal_match = re.match(
        r"(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)\b",
        source[index:],
    )
    if literal_match is None:
        raise FrontendInventoryError("frontend registration loop item is not static")
    literal = literal_match.group(0)
    index += len(literal)
    if literal == "true":
        return True, index
    if literal == "false":
        return False, index
    if literal == "null":
        return None, index
    return (
        float(literal) if any(marker in literal for marker in ".eE") else int(literal)
    ), index


def _static_item_value(source: str) -> StaticValue:
    value, index = _static_value(source)
    index = _skip_static_trivia(source, index)
    suffix = source[index:].strip()
    if suffix and re.fullmatch(r"as\s+const", suffix) is None:
        raise FrontendInventoryError(
            "frontend registration loop item is not a bounded static literal"
        )
    return value


def _destructured_item_bindings(
    binding: str, value: StaticValue
) -> dict[str, StaticValue]:
    if re.fullmatch(TEST_API_NAME, binding):
        return {binding: value}
    if not (binding.startswith("[") and binding.endswith("]")) or not isinstance(
        value, tuple
    ):
        raise FrontendInventoryError(
            "frontend registration loop binding cannot be resolved safely"
        )
    names = [name.strip() for name in binding[1:-1].split(",")]
    if len(names) > len(value) or any(
        name and re.fullmatch(TEST_API_NAME, name) is None for name in names
    ):
        raise FrontendInventoryError(
            "frontend registration loop destructuring cannot be resolved safely"
        )
    return {name: value[index] for index, name in enumerate(names) if name}


def _static_expression_value(
    expression: str, bindings: dict[str, StaticValue]
) -> StaticValue:
    expression = expression.strip()
    conditional = re.fullmatch(
        rf"(?P<condition>{TEST_API_NAME}(?:\.{TEST_API_NAME})*)\s*\?\s*"
        r"(?P<yes>(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'))\s*:\s*"
        r"(?P<no>(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'))",
        expression,
    )
    if conditional is not None:
        condition = _static_expression_value(conditional.group("condition"), bindings)
        if not isinstance(condition, bool):
            raise FrontendInventoryError(
                "frontend registration loop title condition is not boolean"
            )
        branch = conditional.group("yes" if condition else "no")
        value, end = _static_string_value(branch, 0)
        if end != len(branch):
            raise FrontendInventoryError(
                "frontend registration loop title condition is invalid"
            )
        return value
    parts = expression.split(".")
    if (
        not parts
        or re.fullmatch(TEST_API_NAME, parts[0]) is None
        or parts[0] not in bindings
    ):
        raise FrontendInventoryError(
            "frontend registration loop title expression cannot be resolved safely"
        )
    value = bindings[parts[0]]
    for part in parts[1:]:
        if (
            re.fullmatch(TEST_API_NAME, part) is None
            or not isinstance(value, dict)
            or part not in value
        ):
            raise FrontendInventoryError(
                "frontend registration loop title property cannot be resolved safely"
            )
        value = value[part]
    if isinstance(value, (tuple, dict)):
        raise FrontendInventoryError(
            "frontend registration loop title value is not scalar"
        )
    return value


def _title_scalar(value: StaticValue) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        raise FrontendInventoryError(
            "frontend registration loop numeric titles cannot be resolved safely"
        )
    return str(value)


def _resolved_loop_title(title_literal: str, bindings: dict[str, StaticValue]) -> str:
    if not title_literal or title_literal[0] not in "\"'`":
        raise FrontendInventoryError("frontend registration loop title is invalid")
    if title_literal[0] != "`":
        value, end = _static_string_value(title_literal, 0)
        if end != len(title_literal):
            raise FrontendInventoryError("frontend registration loop title is invalid")
        return value
    value: list[str] = []
    index = 1
    segment_start = index
    while index < len(title_literal) - 1:
        if title_literal.startswith("${", index):
            fragment, fragment_end = _static_string_value(
                f"`{title_literal[segment_start:index]}`",
                0,
            )
            if fragment_end != index - segment_start + 2:
                raise FrontendInventoryError(
                    "frontend registration loop title is invalid"
                )
            value.append(fragment)
            end = _skip_balanced(title_literal, index + 1)
            expression = title_literal[index + 2 : end - 1]
            value.append(_title_scalar(_static_expression_value(expression, bindings)))
            index = end
            segment_start = index
            continue
        if title_literal[index] == "\\":
            index += 2
            continue
        index += 1
    fragment, fragment_end = _static_string_value(
        f"`{title_literal[segment_start:-1]}`",
        0,
    )
    if fragment_end != len(title_literal[segment_start:-1]) + 2:
        raise FrontendInventoryError("frontend registration loop title is invalid")
    value.append(fragment)
    return "".join(value)


def _unbraced_statement_contains_offset(
    text: str,
    start: int,
    offset: int,
) -> bool:
    index = _skip_static_trivia(text, start)
    while index <= offset and index < len(text):
        index = _skip_static_trivia(text, index)
        if index == offset:
            return True
        if index > offset or index >= len(text) or text[index] == ";":
            return False
        if text[index] in "([{":
            end = _skip_balanced(text, index)
            if index < offset < end:
                return True
            index = end
            continue
        if text[index] in "\"'`":
            index = _skip_string(text, index)
            continue
        comment_end = _skip_comment(text, index)
        if comment_end != index:
            index = comment_end
            continue
        index += 1
    return False


def _unbraced_expression_end(text: str, scan_text: str, start: int) -> int:
    index = start
    while index < len(text):
        while index < len(text) and scan_text[index].isspace():
            index += 1
        if index >= len(text) or scan_text[index] in ",;)]}":
            return index
        if scan_text[index] in "([{":
            index = _skip_balanced(text, index)
            continue
        index += 1
    return len(text)


def _function_body_after_parameters(
    text: str,
    scan_text: str,
    parameters_end: int,
) -> int | None:
    """Locate a function body after an optional bounded TypeScript return type."""

    index = _skip_static_trivia(text, parameters_end)
    if index >= len(text):
        return None
    if text[index] == "{":
        return index
    if text[index] != ":":
        return None

    index = _skip_static_trivia(text, index + 1)
    return_type_start = index
    angle_depth = 0
    while index < len(text):
        character = scan_text[index]
        if character.isspace():
            index += 1
            continue
        if character in "([":
            index = _skip_balanced(text, index)
            continue
        if character == "<":
            angle_depth += 1
            index += 1
            continue
        if character == ">" and angle_depth:
            angle_depth -= 1
            index += 1
            continue
        if character == "{":
            prefix = scan_text[return_type_start:index].rstrip()
            trailing_word = re.search(r"([A-Za-z_$][\w$]*)$", prefix)
            if (
                angle_depth
                or index == return_type_start
                or prefix.endswith(("=>", "?", ":", "|", "&"))
                or (
                    trailing_word is not None
                    and trailing_word.group(1)
                    in {"extends", "infer", "is", "keyof", "readonly", "typeof"}
                )
            ):
                index = _skip_balanced(text, index)
                continue
            return index
        if not angle_depth and scan_text.startswith("=>", index):
            index += 2
            continue
        if not angle_depth and character in ";=":
            return None
        index += 1
    return None


def _suite_callback_body(
    text: str,
    start: int,
    call_end: int,
) -> tuple[int, int] | None:
    index = _skip_static_trivia(text, start)
    if re.match(r"async\b", text[index:]):
        index = _skip_static_trivia(text, index + len("async"))
    if re.match(r"function\b", text[index:]):
        index = _skip_static_trivia(text, index + len("function"))
        name = re.match(TEST_API_NAME, text[index:])
        if name is not None:
            index = _skip_static_trivia(text, index + name.end())
        if index >= call_end or text[index] != "(":
            return None
        index = _skip_static_trivia(text, _skip_balanced(text, index))
    else:
        if index < call_end and text[index] == "(":
            index = _skip_static_trivia(text, _skip_balanced(text, index))
        else:
            parameter = re.match(TEST_API_NAME, text[index:])
            if parameter is None:
                return None
            index = _skip_static_trivia(text, index + parameter.end())
        if not text.startswith("=>", index):
            return None
        index = _skip_static_trivia(text, index + 2)
    if index >= call_end or text[index] != "{":
        return None
    body_end = _skip_balanced(text, index)
    return (index, body_end) if body_end <= call_end else None


def _suite_context_regions(
    text: str,
    scan_text: str,
    suite_api_names: set[str],
) -> tuple[tuple[int, int, str, str, tuple[str, ...]], ...]:
    names = "(?:" + "|".join(re.escape(name) for name in sorted(suite_api_names)) + ")"
    pattern = re.compile(rf"(?<![.\w$]){names}{TEST_MODIFIERS}\s*(?P<arguments>\()")
    contexts: list[tuple[int, int, str, str, tuple[str, ...]]] = []
    for match in pattern.finditer(scan_text):
        call_end = _skip_balanced(text, match.start("arguments"))
        title_start = _skip_static_trivia(text, match.start("arguments") + 1)
        if title_start >= call_end or text[title_start] not in "\"'`":
            raise FrontendInventoryError(
                "frontend suite title cannot be inventoried safely"
            )
        title_end = _skip_string(text, title_start)
        separator = _skip_static_trivia(text, title_end)
        if separator >= call_end or text[separator] != ",":
            raise FrontendInventoryError(
                "frontend suite callback cannot be inventoried safely"
            )
        callback = _suite_callback_body(text, separator + 1, call_end)
        if callback is None:
            raise FrontendInventoryError(
                "frontend suite callback cannot be inventoried safely"
            )
        contexts.append(
            (
                callback[0],
                callback[1],
                text[title_start:title_end],
                text[match.start() : callback[0]],
                _execution_posture_parts(text[match.start() : callback[0]]),
            )
        )
    return tuple(sorted(contexts))


def _unproven_registration_regions(
    text: str,
    scan_text: str,
    suite_context_regions: tuple[tuple[int, int, str, str, tuple[str, ...]], ...],
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    suite_bodies = {
        (start, end) for start, end, _title, _source, _posture in suite_context_regions
    }
    block_regions: set[tuple[int, int]] = set()
    expression_regions: set[tuple[int, int]] = set()

    def record_body(body_start: int) -> None:
        body_end = _skip_balanced(text, body_start)
        if (body_start, body_end) not in suite_bodies:
            block_regions.add((body_start, body_end))

    function_pattern = re.compile(
        rf"\b(?:async\s+)?function\s*\*?(?:\s+{TEST_API_NAME})?\s*(?P<parameters>\()"
    )
    for match in function_pattern.finditer(scan_text):
        parameters_end = _skip_balanced(text, match.start("parameters"))
        body_start = _function_body_after_parameters(
            text,
            scan_text,
            parameters_end,
        )
        if body_start is not None:
            record_body(body_start)

    def record_arrow_body(body_start: int) -> None:
        if body_start < len(text) and text[body_start] == "{":
            record_body(body_start)
        else:
            expression_regions.add(
                (body_start, _unbraced_expression_end(text, scan_text, body_start))
            )

    for match in re.compile(r"=>").finditer(scan_text):
        record_arrow_body(_skip_static_trivia(text, match.end()))

    method_pattern = re.compile(rf"\b(?P<name>{TEST_API_NAME})\s*(?P<parameters>\()")
    for match in method_pattern.finditer(scan_text):
        if match.group("name") in {"catch", "for", "if", "switch", "while", "with"}:
            continue
        parameters_end = _skip_balanced(text, match.start("parameters"))
        body_start = _function_body_after_parameters(
            text,
            scan_text,
            parameters_end,
        )
        if body_start is not None:
            record_body(body_start)

    generic_method_pattern = re.compile(
        rf"\b(?P<name>{TEST_API_NAME})\s*(?P<type_parameters><)"
    )
    for match in generic_method_pattern.finditer(scan_text):
        if match.group("name") in {"catch", "for", "if", "switch", "while", "with"}:
            continue
        index = match.start("type_parameters") + 1
        angle_depth = 1
        delimiter_stack: list[str] = []
        delimiter_pairs = {"(": ")", "[": "]", "{": "}"}
        while index < len(scan_text) and angle_depth:
            character = scan_text[index]
            if character in delimiter_pairs:
                delimiter_stack.append(delimiter_pairs[character])
            elif delimiter_stack and character == delimiter_stack[-1]:
                delimiter_stack.pop()
            elif not delimiter_stack:
                if character == "<":
                    angle_depth += 1
                elif character == ">" and scan_text[index - 1] != "=":
                    angle_depth -= 1
            index += 1
        if angle_depth:
            continue
        parameters_start = _skip_static_trivia(text, index)
        if parameters_start >= len(text) or text[parameters_start] != "(":
            continue
        parameters_end = _skip_balanced(text, parameters_start)
        body_start = _function_body_after_parameters(
            text,
            scan_text,
            parameters_end,
        )
        if body_start is not None:
            record_body(body_start)

    field_pattern = re.compile(
        rf"(?:^|[;\r\n}}])\s*"
        rf"(?P<modifiers>(?:(?:public|private|protected|readonly|declare|"
        rf"abstract|override|accessor|static)\s+)*)"
        rf"(?:#{TEST_API_NAME}|{TEST_API_NAME}|\[[^\]\r\n]+\])(?:[!?])?"
        rf"(?:\s*:\s*[^=;\r\n]+)?\s*=\s*"
    )
    class_bodies: list[int] = []
    for class_match in re.finditer(r"\bclass\b", scan_text):
        index = class_match.end()
        angle_depth = 0
        delimiter_stack: list[str] = []
        while index < len(scan_text):
            character = scan_text[index]
            if character == "<" and not delimiter_stack:
                angle_depth += 1
            elif character == ">" and angle_depth and not delimiter_stack:
                angle_depth -= 1
            elif character in "([":
                delimiter_stack.append(")" if character == "(" else "]")
            elif delimiter_stack and character == delimiter_stack[-1]:
                delimiter_stack.pop()
            elif character == "{" and (angle_depth or delimiter_stack):
                index = _skip_balanced(text, index)
                continue
            elif character == "{" and angle_depth == 0 and not delimiter_stack:
                class_bodies.append(index)
                break
            elif character == ";" and angle_depth == 0 and not delimiter_stack:
                break
            index += 1
    for body_start in class_bodies:
        body_end = _skip_balanced(text, body_start)
        body_scan = scan_text[body_start + 1 : body_end - 1]
        for field_match in field_pattern.finditer(body_scan):
            if "static" in field_match.group("modifiers").split():
                continue
            initializer_start = body_start + 1 + field_match.end()
            expression_regions.add(
                (
                    initializer_start,
                    _unbraced_expression_end(
                        text,
                        scan_text,
                        initializer_start,
                    ),
                )
            )

    nested_suite_bodies = tuple(suite_bodies)
    conditional_pattern = re.compile(r"\b(?P<keyword>if|switch)\s*(?P<condition>\()")
    for suite_start, suite_end in suite_bodies:
        for conditional_match in conditional_pattern.finditer(
            scan_text,
            suite_start + 1,
            suite_end - 1,
        ):
            conditional_start = conditional_match.start()
            if any(
                start < conditional_start < end
                for start, end in (*block_regions, *expression_regions)
            ) or any(
                start < conditional_start < end
                for start, end in nested_suite_bodies
                if (start, end) != (suite_start, suite_end)
            ):
                continue
            condition_end = _skip_balanced(
                text,
                conditional_match.start("condition"),
            )
            statement_start = _skip_static_trivia(text, condition_end)
            if statement_start >= suite_end:
                continue
            statement_end = (
                _skip_balanced(text, statement_start)
                if text[statement_start] == "{"
                else _unbraced_expression_end(
                    text,
                    scan_text,
                    statement_start,
                )
            )
            if re.search(
                r"\b(?:return|throw)\b",
                scan_text[statement_start:statement_end],
            ):
                expression_regions.add((statement_end, suite_end))

    return tuple(sorted(block_regions)), tuple(sorted(expression_regions))


def _registration_contexts(
    text: str,
    scan_text: str,
    offset: int,
    title_literal: str,
    import_binding_resolver: ImportBindingResolver | None,
    suite_context_regions: tuple[tuple[int, int, str, str, tuple[str, ...]], ...],
    unproven_block_regions: tuple[tuple[int, int], ...],
    unproven_expression_regions: tuple[tuple[int, int], ...],
) -> tuple[_RegistrationContext, ...]:
    if any(start < offset < end for start, end in unproven_block_regions) or any(
        start <= offset < end for start, end in unproven_expression_regions
    ):
        raise FrontendInventoryError(
            "frontend test registration context cannot be inventoried safely"
        )

    statement_start = -1
    delimiter_stack: list[list[object]] = []
    delimiter_pairs = {"(": ")", "[": "]", "{": "}"}

    def inside_expression() -> bool:
        nearest_block = max(
            (
                index
                for index, (opener, is_block, _previous, _closed_block) in enumerate(
                    delimiter_stack
                )
                if opener == "{" and is_block
            ),
            default=-1,
        )
        return any(
            opener in "(["
            for opener, _is_block, _previous, _closed_block in delimiter_stack[
                nearest_block + 1 :
            ]
        )

    for index, character in enumerate(scan_text[:offset]):
        if character in delimiter_pairs:
            prefix = scan_text[:index].rstrip()
            is_block = character == "{" and (
                prefix.endswith(("=>", ")")) or not inside_expression()
            )
            previous_statement_start = statement_start
            if is_block:
                statement_start = index
            delimiter_stack.append(
                [character, is_block, previous_statement_start, False]
            )
            continue
        if character in ")]}" and delimiter_stack:
            opener, is_block, previous_statement_start, contains_closed_block = (
                delimiter_stack[-1]
            )
            if delimiter_pairs[opener] == character:
                delimiter_stack.pop()
                if character == "}" and is_block:
                    statement_start = int(previous_statement_start)
                    if delimiter_stack:
                        delimiter_stack[-1][3] = True
                    if not inside_expression():
                        statement_start = index
                elif contains_closed_block and not inside_expression():
                    statement_start = index
            continue
        if character == ";" and not inside_expression():
            statement_start = index
    statement_prefix = scan_text[statement_start + 1 : offset]
    if re.search(r"&&|\|\||\?\?", statement_prefix) or re.search(
        r"\?(?![.?])", statement_prefix
    ):
        raise FrontendInventoryError(
            "frontend conditional test registration cannot be inventoried safely"
        )

    def reject_enclosing_body(body_start: int) -> None:
        if body_start < offset < _skip_balanced(text, body_start):
            raise FrontendInventoryError(
                "frontend test registration context cannot be inventoried safely"
            )

    control_pattern = re.compile(r"\b(?:while|if|switch|catch)\s*(?P<header>\()")
    for match in control_pattern.finditer(scan_text, 0, offset):
        header_end = _skip_balanced(text, match.start("header"))
        body_start = _skip_static_trivia(text, header_end)
        if body_start < len(text) and text[body_start] == "{":
            reject_enclosing_body(body_start)
        elif _unbraced_statement_contains_offset(text, body_start, offset):
            raise FrontendInventoryError(
                "frontend test registration context cannot be inventoried safely"
            )

    for match in re.compile(r"\belse\b").finditer(scan_text, 0, offset):
        body_start = _skip_static_trivia(text, match.end())
        if body_start < len(text) and text[body_start] == "{":
            reject_enclosing_body(body_start)
        elif _unbraced_statement_contains_offset(text, body_start, offset):
            raise FrontendInventoryError(
                "frontend test registration context cannot be inventoried safely"
            )

    for match in re.compile(r"\b(?:do|try|finally)\s*(?P<body>\{)").finditer(
        scan_text, 0, offset
    ):
        reject_enclosing_body(match.start("body"))

    for match in re.compile(r"\bfor\s+await\s*(?P<header>\()").finditer(
        scan_text, 0, offset
    ):
        header_end = _skip_balanced(text, match.start("header"))
        body_start = _skip_static_trivia(text, header_end)
        if body_start < len(text) and text[body_start] == "{":
            reject_enclosing_body(body_start)
        elif _unbraced_statement_contains_offset(text, body_start, offset):
            raise FrontendInventoryError(
                "frontend test registration context cannot be inventoried safely"
            )

    context_bindings: list[tuple[dict[str, StaticValue], str]] = [({}, "")]
    for match in re.compile(r"\bfor\s*\(").finditer(scan_text, 0, offset):
        header_end = _skip_balanced(text, match.end() - 1)
        body_start = _skip_static_trivia(text, header_end)
        if body_start >= len(text) or text[body_start] != "{":
            if _unbraced_statement_contains_offset(text, body_start, offset):
                raise FrontendInventoryError(
                    "frontend test registration loop cannot be inventoried safely"
                )
            continue
        body_end = _skip_balanced(text, body_start)
        if not (body_start < offset < body_end):
            continue
        header = scan_text[match.start() : header_end]
        binding = re.fullmatch(
            rf"for\s*\(\s*const\s+(?P<binding>{TEST_API_NAME}|\[[^\[\]]+\])\s+of\s+"
            rf"(?P<collection>{TEST_API_NAME})\s*\)",
            header,
        )
        if binding is None:
            raise FrontendInventoryError(
                "frontend test registration loop cannot be inventoried safely"
            )
        collection_source = _static_collection_source(
            text,
            scan_text,
            binding.group("collection"),
            match.start(),
            import_binding_resolver,
        )
        items = _static_collection_items(collection_source)
        next_bindings: list[tuple[dict[str, StaticValue], str]] = []
        for existing_bindings, existing_source in context_bindings:
            for item in items:
                item_bindings = _destructured_item_bindings(
                    binding.group("binding"),
                    _static_item_value(item),
                )
                if set(existing_bindings) & set(item_bindings):
                    raise FrontendInventoryError(
                        "frontend registration loop bindings shadow one another"
                    )
                next_bindings.append(
                    (
                        {**existing_bindings, **item_bindings},
                        f"{existing_source}\n{text[match.start() : header_end]}\nitem={item}".strip(),
                    )
                )
        context_bindings = next_bindings
    suite_contexts = tuple(
        (suite_title, suite_source, suite_posture)
        for (
            body_start,
            body_end,
            suite_title,
            suite_source,
            suite_posture,
        ) in suite_context_regions
        if body_start < offset < body_end
    )
    registrations: list[_RegistrationContext] = []
    for bindings, evidence_source in context_bindings:
        suite_titles = tuple(
            _resolved_loop_title(suite_title, bindings)
            for suite_title, _suite_source, _suite_posture in suite_contexts
        )
        title = _resolved_loop_title(title_literal, bindings)
        if suite_titles:
            title = (
                "".join(
                    f"suite[{len(suite_title)}]:{suite_title}::"
                    for suite_title in suite_titles
                )
                + title
            )
        suite_source = "\n".join(source for _title, source, _posture in suite_contexts)
        registrations.append(
            _RegistrationContext(
                title=title,
                evidence_source="\n".join(
                    part for part in (evidence_source, suite_source) if part
                ),
                execution_postures=tuple(
                    posture_part
                    for _title, _source, posture in suite_contexts
                    for posture_part in posture
                ),
            )
        )
    return tuple(registrations)


def _frontend_inventory_entries(
    path: str,
    text: str,
    import_binding_resolver: ImportBindingResolver | None = None,
) -> tuple[tuple[str, str], ...]:
    raw_entries: list[tuple[int, str, str]] = []
    code_mask = _code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    if any(
        match.group("module").startswith(".")
        and scan_text[match.start() : match.start() + len("import")] == "import"
        for match in SIDE_EFFECT_IMPORT_PATTERN.finditer(text)
    ) or any(
        match.group("module").startswith(".")
        and scan_text[match.start() : match.start() + len("import")] == "import"
        for match in EMPTY_NAMED_IMPORT_PATTERN.finditer(text)
    ):
        raise FrontendInventoryError(
            "frontend side-effect import cannot be inventoried safely"
        )
    if _has_dynamic_runner_import(text, scan_text):
        raise FrontendInventoryError(
            "dynamic frontend runner import cannot be inventoried safely"
        )
    if re.search(r"\bimport\s*\.\s*meta\s*\.\s*glob\s*\(", scan_text):
        raise FrontendInventoryError(
            "frontend glob registration import cannot be inventoried safely"
        )
    test_api_names = _test_api_names(text, scan_text)
    if _has_indirect_runner_invocation(
        text,
        scan_text,
        names=test_api_names,
    ):
        raise FrontendInventoryError(
            "indirect frontend test registration cannot be inventoried safely"
        )
    direct_pattern, each_pattern, conditional_pattern = _patterns(test_api_names)
    suite_api_names = _suite_api_names(text, scan_text)
    suite_api_pattern = (
        "(?:" + "|".join(re.escape(name) for name in sorted(suite_api_names)) + ")"
    )
    if re.search(
        rf"(?<![.\w$]){suite_api_pattern}{TEST_MODIFIERS}\.(?:each|for)\b",
        scan_text,
    ):
        raise FrontendInventoryError(
            "frontend parameterized suites cannot be inventoried safely"
        )
    suite_context_regions = _suite_context_regions(
        text,
        scan_text,
        suite_api_names,
    )
    (
        unproven_block_regions,
        unproven_expression_regions,
    ) = _unproven_registration_regions(
        text,
        scan_text,
        suite_context_regions,
    )
    if _has_unproven_imported_registration_call(
        text,
        scan_text,
        unproven_block_regions,
        unproven_expression_regions,
    ):
        raise FrontendInventoryError(
            "imported frontend registration helper cannot be inventoried safely"
        )

    for match in direct_pattern.finditer(scan_text):
        declaration_end = _skip_balanced(text, match.end() - 1)
        index = match.end()
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] not in "\"'`":
            arguments = scan_text[match.end() : declaration_end - 1]
            if (
                any(
                    modifier in match.group(0)
                    for modifier in (".skip", ".fail", ".fixme")
                )
                and re.search(r"=>|\bfunction\b", arguments) is None
            ):
                continue
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        title_end = _skip_string(text, index) - 1
        title_literal = text[index : title_end + 1]
        contexts = _registration_contexts(
            text,
            scan_text,
            match.start(),
            title_literal,
            import_binding_resolver,
            suite_context_regions,
            unproven_block_regions,
            unproven_expression_regions,
        )
        declaration_source = text[match.start() : declaration_end]
        for context in contexts:
            title = context.title
            if not title or len(title) > 500 or re.search(r"#\d+$", title):
                raise FrontendInventoryError(f"frontend test title is invalid: {path}")
            bound_source = declaration_source
            if context.evidence_source:
                bound_source = f"{bound_source}\n{context.evidence_source}"
            raw_entries.append(
                (
                    match.start(),
                    _frontend_ref(
                        path,
                        title,
                        execution_postures=(
                            *context.execution_postures,
                            *_execution_posture_parts(declaration_source),
                        ),
                    ),
                    bound_source,
                )
            )
    parameterized_declarations = _parameterized_declarations(
        text,
        scan_text,
        each_pattern,
    )
    parameter_call_ranges = frozenset(
        (declaration[0], declaration[0] + len(declaration[2]))
        for declaration in parameterized_declarations
    )
    for (
        offset,
        raw_title,
        declaration_source,
        parameter_data,
    ) in parameterized_declarations:
        contexts = _registration_contexts(
            text,
            scan_text,
            offset,
            raw_title,
            import_binding_resolver,
            suite_context_regions,
            unproven_block_regions,
            unproven_expression_regions,
        )
        bound_data = _bound_parameter_data(
            text,
            scan_text,
            parameter_data,
            offset,
            import_binding_resolver,
            parameter_call_ranges,
        )
        digest = hashlib.sha256(bound_data.encode("utf-8")).hexdigest()
        for context in contexts:
            title = context.title
            if not title or len(title) > 500 or re.search(r"#\d+$", title):
                raise FrontendInventoryError(f"frontend test title is invalid: {path}")
            bound_source = declaration_source
            if context.evidence_source:
                bound_source = f"{bound_source}\n{context.evidence_source}"
            raw_entries.append(
                (
                    offset,
                    _frontend_ref(
                        path,
                        title,
                        parameter_digest=digest,
                        execution_postures=(
                            *context.execution_postures,
                            *_execution_posture_parts(declaration_source),
                        ),
                    ),
                    bound_source,
                )
            )
    for offset, raw_title, declaration_source in _conditional_declarations(
        text, scan_text, conditional_pattern
    ):
        contexts = _registration_contexts(
            text,
            scan_text,
            offset,
            raw_title,
            import_binding_resolver,
            suite_context_regions,
            unproven_block_regions,
            unproven_expression_regions,
        )
        for context in contexts:
            title = context.title
            if not title or len(title) > 500 or re.search(r"#\d+$", title):
                raise FrontendInventoryError(f"frontend test title is invalid: {path}")
            bound_source = declaration_source
            if context.evidence_source:
                bound_source = f"{bound_source}\n{context.evidence_source}"
            raw_entries.append(
                (
                    offset,
                    _frontend_ref(
                        path,
                        title,
                        execution_postures=(
                            *context.execution_postures,
                            *_execution_posture_parts(declaration_source),
                        ),
                    ),
                    bound_source,
                )
            )

    counts: dict[str, int] = {}
    used_refs: set[str] = set()
    entries: list[tuple[str, str]] = []
    for _offset, raw_ref, declaration_source in sorted(
        raw_entries, key=lambda entry: entry[0]
    ):
        occurrence = counts.get(raw_ref, 0) + 1
        ref = raw_ref if occurrence == 1 else f"{raw_ref}#{occurrence}"
        while ref in used_refs:
            occurrence += 1
            ref = f"{raw_ref}#{occurrence}"
        counts[raw_ref] = occurrence
        used_refs.add(ref)
        entries.append((ref, declaration_source))
    return tuple(entries)


def parse_frontend_refs(
    path: str,
    text: str,
    import_binding_resolver: ImportBindingResolver | None = None,
) -> tuple[str, ...]:
    return tuple(
        ref
        for ref, _source in _frontend_inventory_entries(
            path,
            text,
            import_binding_resolver,
        )
    )


def frontend_source_for_ref(
    path: str,
    text: str,
    test_ref: str,
    import_binding_resolver: ImportBindingResolver | None = None,
) -> str | None:
    return dict(_frontend_inventory_entries(path, text, import_binding_resolver)).get(
        test_ref
    )
