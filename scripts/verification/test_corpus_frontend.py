"""Bounded static inventory for supported frontend test declarations."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache


TEST_API_NAME = r"[A-Za-z_$][\w$]*"
MAX_CONTEXT_FORWARDING_HELPERS = 64
MAX_CONTEXT_HELPER_IDENTITY_BYTES = 200_000
TEST_MODIFIERS = r"(?:\s*\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
EXECUTION_DISABLING_TEST_MODIFIERS = frozenset({"fixme", "skip", "todo"})
EXPECTED_FAILURE_TEST_MODIFIERS = frozenset({"fail", "fails"})
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
    rf"\bexport\s+(?:type\s+)?(?:\*\s*(?:as\s+{TEST_API_NAME}\s*)?|\{{[^}}]*\}})\s+from\s*"
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
MODULE_INITIALIZER_BINDING = "__uaa_module_initializer__"
MODULE_INITIALIZER_INERT = "__uaa_module_initializer_inert__"


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
    if start >= len(text) or text[start] != "/":
        return start
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
    token_start = index
    while token_start >= 0 and (
        text[token_start].isalnum() or text[token_start] in "_$"
    ):
        token_start -= 1
    return text[token_start + 1 : index + 1] in {
        "case",
        "delete",
        "return",
        "throw",
        "typeof",
        "void",
    }


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
        comment_end = _skip_comment(text, index) if text[index] == "/" else index
        if comment_end != index:
            mask[index:comment_end] = b"\x00" * (comment_end - index)
            index = comment_end
            continue
        index += 1
    return mask


@lru_cache(maxsize=16384)
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
        comment_end = _skip_comment(text, index) if character == "/" else index
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
        comment_end = _skip_comment(source, index) if character == "/" else index
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


def frontend_runtime_identity_source(source: str) -> str:
    """Canonicalize initializer tokens while preserving executable literals."""

    try:
        mask = _module_initializer_code_mask(source, preserve_literals=True)
        initializer_source = "".join(
            character if mask[index] else " " for index, character in enumerate(source)
        )
        return _normalized_javascript_expression(initializer_source)
    except FrontendInventoryError:
        return source


def _call_argument_ranges(
    text: str,
    arguments_start: int,
) -> tuple[tuple[int, int], ...]:
    """Return the top-level argument spans for one balanced call."""

    arguments_end = _skip_balanced(text, arguments_start)
    ranges: list[tuple[int, int]] = []
    argument_start = arguments_start + 1
    index = argument_start
    while index < arguments_end - 1:
        character = text[index]
        if character in "\"'`":
            index = _skip_string(text, index)
            continue
        comment_end = _skip_comment(text, index) if character == "/" else index
        if comment_end != index:
            index = comment_end
            continue
        if character in "([{":
            index = _skip_balanced(text, index)
            continue
        if character == ",":
            ranges.append((argument_start, index))
            argument_start = index + 1
        index += 1
    if text[argument_start : arguments_end - 1].strip() or ranges:
        ranges.append((argument_start, arguments_end - 1))
    return tuple(ranges)


def _registration_argument_ranges(text: str) -> tuple[tuple[int, int], ...]:
    """Return arguments from the final top-level call in a registration."""

    code_mask = _code_mask(text)
    calls: list[int] = []
    index = 0
    while index < len(text):
        if code_mask[index] and text[index] == "(":
            calls.append(index)
            index = _skip_balanced(text, index)
            continue
        index += 1
    if not calls:
        raise FrontendInventoryError(
            "frontend test declaration arguments cannot be inventoried safely"
        )
    return _call_argument_ranges(text, calls[-1])


def _looks_like_frontend_callback(source: str) -> bool:
    scan = "".join(
        character if enabled else " "
        for character, enabled in zip(source, _code_mask(source), strict=True)
    ).strip()
    return bool(
        re.fullmatch(TEST_API_NAME, scan)
        or re.match(r"(?:async\s+)?function\b", scan)
        or re.search(r"=>", scan)
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


_JAVASCRIPT_NON_BINDING_NAMES = frozenset(
    {
        "as",
        "await",
        "false",
        "globalThis",
        "import",
        "instanceof",
        "new",
        "null",
        "process",
        "this",
        "true",
        "typeof",
        "undefined",
        "void",
    }
)


def _javascript_binding_names(
    source: str,
    *,
    ignore_object_keys: bool = False,
) -> tuple[str, ...]:
    """Return value-bearing identifiers from a bounded JavaScript expression."""

    mask = _code_mask(source)
    scan_text = "".join(
        character if mask[index] else " " for index, character in enumerate(source)
    )
    names: list[str] = []
    for match in re.finditer(TEST_API_NAME, scan_text):
        name = match.group(0)
        if name in _JAVASCRIPT_NON_BINDING_NAMES:
            continue
        before = match.start() - 1
        while before >= 0 and scan_text[before].isspace():
            before -= 1
        if before >= 0 and scan_text[before] == ".":
            continue
        after = match.end()
        while after < len(scan_text) and scan_text[after].isspace():
            after += 1
        if ignore_object_keys and after < len(scan_text) and scan_text[after] == ":":
            continue
        if name not in names:
            names.append(name)
    return tuple(names)


def _resolved_javascript_bindings(
    source: str,
    resolver: Callable[[str], str | None] | None,
    *,
    ignore_object_keys: bool = False,
) -> tuple[str, ...]:
    names = _javascript_binding_names(
        source,
        ignore_object_keys=ignore_object_keys,
    )
    if not names:
        return ()
    if resolver is None:
        raise FrontendInventoryError(
            "frontend conditional binding cannot be resolved safely"
        )
    bindings: list[str] = []
    for name in names:
        binding_source = resolver(name)
        if binding_source is None:
            raise FrontendInventoryError(
                "frontend conditional binding cannot be resolved safely"
            )
        bindings.append(f"binding:{name}={binding_source}")
    return tuple(bindings)


def _frontend_callback_parameters(callback: str) -> tuple[str, ...]:
    """Return bounded formal parameters for an inline frontend callback."""

    callback_mask = _code_mask(callback)
    callback_scan = "".join(
        character if callback_mask[index] else " "
        for index, character in enumerate(callback)
    )
    parenthesized = re.match(
        rf"\s*(?:async\s+)?(?:function(?:\s+{TEST_API_NAME})?\s*)?"
        r"(?P<parameters>\()",
        callback_scan,
    )
    if parenthesized is not None:
        start = parenthesized.start("parameters")
        end = _skip_balanced(callback, start)
        return tuple(
            callback[item_start:item_end].strip()
            for item_start, item_end in _call_argument_ranges(
                callback[:end],
                start,
            )
        )
    bare = re.match(
        rf"\s*(?:async\s+)?(?P<parameter>{TEST_API_NAME})\b\s*=>",
        callback_scan,
    )
    return (bare.group("parameter"),) if bare is not None else ()


def _has_runtime_callback_skip(
    declaration_source: str,
    arguments: tuple[tuple[int, int], ...],
) -> bool:
    if len(arguments) < 2:
        return False
    callback_index = (
        2
        if len(arguments) >= 3
        and _looks_like_frontend_callback(
            declaration_source[arguments[2][0] : arguments[2][1]]
        )
        else 1
    )
    callback = declaration_source[
        arguments[callback_index][0] : arguments[callback_index][1]
    ]
    callback_mask = _code_mask(callback)
    callback_scan = "".join(
        character if callback_mask[index] else " "
        for index, character in enumerate(callback)
    )
    callback_scan_characters = list(callback_scan)
    for computed_skip in re.finditer(
        r"\[\s*(?P<quote>['\"])skip(?P=quote)\s*\]",
        callback,
    ):
        if not (
            callback_mask[computed_skip.start()]
            and callback_mask[computed_skip.end() - 1]
        ):
            continue
        replacement = ".skip".ljust(computed_skip.end() - computed_skip.start())
        callback_scan_characters[computed_skip.start() : computed_skip.end()] = (
            replacement
        )
    callback_scan = "".join(callback_scan_characters)
    final_call_prefix = declaration_source[: arguments[0][0]]
    context_parameter_index = (
        None
        if re.search(r"\.\s*each\b", final_call_prefix)
        else 1
        if re.search(r"\.\s*for\b", final_call_prefix)
        else 0
    )
    parameter = None
    destructured_parameter = None
    skip_aliases: set[str] = set()
    parameters = _frontend_callback_parameters(callback)
    if context_parameter_index is not None:
        indexed_context_sources = [rf"arguments\s*\[\s*{context_parameter_index}\s*\]"]
        for candidate in parameters:
            rest_parameter = re.match(
                rf"\.\.\.\s*(?P<name>{TEST_API_NAME})\b",
                candidate,
            )
            if rest_parameter is not None:
                indexed_context_sources.append(
                    rf"{re.escape(rest_parameter.group('name'))}\s*"
                    rf"\[\s*{context_parameter_index}\s*\]"
                )
        indexed_context_aliases: set[str] = set()
        rest_array_names = {
            rest.group("name")
            for candidate in parameters
            if (
                rest := re.match(
                    rf"\.\.\.\s*(?P<name>{TEST_API_NAME})\b",
                    candidate,
                )
            )
            is not None
        }
        indexed_array_roots = {"arguments", *rest_array_names}
        for match in re.finditer(
            rf"\b(?:const|let|var)\s*\[(?P<items>[^\]]*)\]\s*=\s*"
            rf"(?P<source>{TEST_API_NAME})\b",
            callback_scan,
        ):
            if match.group("source") not in indexed_array_roots:
                continue
            items = [item.strip() for item in match.group("items").split(",")]
            if context_parameter_index >= len(items):
                continue
            context_item = re.match(
                rf"(?:\.\.\.\s*)?(?P<name>{TEST_API_NAME})\b",
                items[context_parameter_index],
            )
            if context_item is not None:
                indexed_context_aliases.add(context_item.group("name"))
        for context_source in indexed_context_sources:
            if re.search(
                rf"\b{context_source}\s*(?:(?:\?\.|\.)\s*skip\b|"
                r"(?:\?\.)?\[)",
                callback_scan,
            ):
                return True
            if re.search(
                rf"\b(?:Reflect\s*\.\s*get|"
                rf"Object\s*\.\s*getOwnPropertyDescriptor)\s*\(\s*"
                rf"{context_source}\s*,\s*['\"]skip['\"]",
                callback,
            ):
                return True
            if re.search(
                rf"\b(?:const|let|var)\s*\{{[^}}]*"
                rf"(?:\.\.\.|(?:\.\s*)?skip\b)[^}}]*\}}\s*=\s*"
                rf"{context_source}",
                callback_scan,
            ):
                return True
            for match in re.finditer(
                rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*=\s*"
                rf"{context_source}",
                callback_scan,
            ):
                indexed_context_aliases.add(match.group("alias"))
        changed = True
        while changed:
            changed = False
            for match in re.finditer(
                rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*=\s*"
                rf"(?P<source>{TEST_API_NAME})\b",
                callback_scan,
            ):
                if (
                    match.group("source") in indexed_context_aliases
                    and match.group("alias") not in indexed_context_aliases
                ):
                    indexed_context_aliases.add(match.group("alias"))
                    changed = True
        for context_alias in indexed_context_aliases:
            context_pattern = re.escape(context_alias)
            if re.search(
                rf"\b{context_pattern}\s*(?:(?:\?\.|\.)\s*skip\b|"
                r"(?:\?\.)?\[)",
                callback_scan,
            ) or re.search(
                rf"\b(?:Reflect\s*\.\s*get|"
                rf"Object\s*\.\s*getOwnPropertyDescriptor)\s*\(\s*"
                rf"{context_pattern}\s*,\s*['\"]skip['\"]",
                callback,
            ):
                return True
            if re.search(
                rf"\b(?:const|let|var)\s*\{{[^}}]*"
                rf"(?:\.\.\.|(?:\.\s*)?skip\b)[^}}]*\}}\s*=\s*"
                rf"{context_pattern}\b",
                callback_scan,
            ):
                return True
    if context_parameter_index is not None and context_parameter_index < len(
        parameters
    ):
        selected = parameters[context_parameter_index]
        simple_parameter = re.match(rf"(?P<name>{TEST_API_NAME})\b", selected)
        if simple_parameter is not None:
            parameter = simple_parameter.group("name")
        elif selected.startswith("{"):
            destructured_parameter = selected
    if destructured_parameter is not None:
        if "[" in destructured_parameter or re.search(
            r"(?:^|[,{}])\s*(?:\.\.\.|skip\b)",
            destructured_parameter,
        ):
            return True
    if parameter is not None:
        parameter_pattern = re.escape(parameter)
        if re.search(rf"\b{parameter_pattern}\s*(?:\?\.)?\[", callback_scan):
            return True
        if re.search(
            rf"\b{parameter_pattern}\s*(?:\?\.|\.)\s*skip\b",
            callback_scan,
        ):
            return True
    destructured = (
        re.match(
            rf"\s*(?:async\s+)?(?:function(?:\s+{TEST_API_NAME})?\s*)?"
            r"\(\s*\{(?P<body>[^}]*)\}\s*\)\s*(?:=>)?",
            callback_scan,
        )
        if context_parameter_index == 0
        else None
    )
    if destructured is not None:
        if "[" in destructured.group("body"):
            return True
        if re.search(
            r"(?:^|,)\s*(?:\.\.\.|(?:\.\s*)?skip\b)", destructured.group("body")
        ):
            return True
        for item in destructured.group("body").split(","):
            binding = re.fullmatch(
                rf"\s*skip(?:\s*:\s*(?P<alias>{TEST_API_NAME}))?\s*",
                item,
            )
            if binding is not None:
                skip_aliases.add(binding.group("alias") or "skip")
    if parameter is not None:
        parameter_pattern = re.escape(parameter)
        if re.search(
            rf"\b(?:const|let|var)\s*\{{[^}}]*(?:\.\.\.|(?:\.\s*)?skip\b)"
            rf"[^}}]*\}}\s*=\s*{parameter_pattern}\b",
            callback_scan,
        ):
            return True
        for match in re.finditer(
            rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*=\s*"
            rf"{parameter_pattern}\s*(?:(?:\?\.|\.)\s*skip|"
            r"(?:\?\.)?\[\s*['\"]skip['\"]\s*\])",
            callback_scan,
        ):
            skip_aliases.add(match.group("alias"))
        for match in re.finditer(
            rf"\b(?:const|let|var)\s*\{{\s*skip"
            rf"(?:\s*:\s*(?P<alias>{TEST_API_NAME}))?\s*\}}\s*=\s*"
            rf"{parameter_pattern}\b",
            callback_scan,
        ):
            skip_aliases.add(match.group("alias") or "skip")
        context_aliases = {parameter}
        changed = True
        while changed:
            changed = False
            for match in re.finditer(
                rf"(?:\b(?:const|let|var)\s+|(?<![.\w$]))"
                rf"(?P<alias>{TEST_API_NAME})\s*=\s*\(*\s*"
                rf"(?P<source>{TEST_API_NAME})\s*\)*",
                callback_scan,
            ):
                if (
                    match.group("source") in context_aliases
                    and match.group("alias") not in context_aliases
                ):
                    context_aliases.add(match.group("alias"))
                    changed = True
        for context_alias in context_aliases:
            context_pattern = re.escape(context_alias)
            if re.search(
                rf"\b{context_pattern}\s*(?:\?\.)?\[",
                callback_scan,
            ) or re.search(
                rf"\b{context_pattern}\s*(?:\?\.|\.)\s*skip\b",
                callback_scan,
            ):
                return True
            reflective_patterns = (
                re.compile(
                    rf"\bReflect\s*\.\s*get\s*\(\s*{context_pattern}\s*,\s*"
                    r"['\"]skip['\"]"
                ),
                re.compile(
                    rf"\bObject\s*\.\s*getOwnPropertyDescriptor\s*\(\s*"
                    rf"{context_pattern}\s*,\s*['\"]skip['\"]"
                ),
            )
            if any(
                callback_mask[match.start()]
                for pattern in reflective_patterns
                for match in pattern.finditer(callback)
            ):
                return True
            if re.search(
                rf"\{{[^}}]*\.\.\.\s*{context_pattern}\b[^}}]*\}}",
                callback_scan,
            ) or re.search(
                rf"\bObject\s*\.\s*assign\s*\([^)]*\b{context_pattern}\b",
                callback_scan,
            ):
                return True
            if re.search(
                rf"\(?\s*\{{[^}}]*(?:\.\.\.|(?:\.\s*)?skip\b)[^}}]*\}}\s*"
                rf"=\s*\(*\s*{context_pattern}\s*\)*",
                callback_scan,
            ):
                return True
    changed = True
    while changed:
        changed = False
        for match in re.finditer(
            rf"\b(?:const|let|var)\s+(?P<alias>{TEST_API_NAME})\s*=\s*"
            rf"(?P<source>{TEST_API_NAME})\b",
            callback_scan,
        ):
            if (
                match.group("source") in skip_aliases
                and match.group("alias") not in skip_aliases
            ):
                skip_aliases.add(match.group("alias"))
                changed = True
    return any(
        re.search(rf"\b{re.escape(alias)}\s*(?:\?\.)?\s*\(", callback_scan) is not None
        for alias in skip_aliases
    )


def _runtime_callback_context_helpers(
    declaration_source: str,
    arguments: tuple[tuple[int, int], ...],
) -> tuple[str, ...]:
    if len(arguments) < 2:
        return ()
    final_call_prefix = declaration_source[: arguments[0][0]]
    if re.search(r"\.\s*each\b", final_call_prefix):
        return ()
    context_parameter_index = 1 if re.search(r"\.\s*for\b", final_call_prefix) else 0
    callback_index = (
        2
        if len(arguments) >= 3
        and _looks_like_frontend_callback(
            declaration_source[arguments[2][0] : arguments[2][1]]
        )
        else 1
    )
    callback = declaration_source[
        arguments[callback_index][0] : arguments[callback_index][1]
    ]
    callback_mask = _code_mask(callback)
    callback_scan = "".join(
        character if callback_mask[index] else " "
        for index, character in enumerate(callback)
    )
    parameters = _frontend_callback_parameters(callback)
    if context_parameter_index >= len(parameters):
        return ()
    parameter = parameters[context_parameter_index]
    simple_parameter = re.match(rf"(?P<name>{TEST_API_NAME})\b", parameter)
    if simple_parameter is None:
        return ()
    parameter = simple_parameter.group("name")
    parameter_pattern = re.escape(parameter)
    helpers: set[str] = set()
    helper_call_pattern = re.compile(
        rf"(?<![.\w$])(?P<callee>{TEST_API_NAME})\s*(?P<arguments>\()"
    )
    for helper_call in helper_call_pattern.finditer(callback_scan):
        if helper_call.group("callee") in {
            "Boolean",
            "Date",
            "Error",
            "Map",
            "Number",
            "RegExp",
            "Set",
            "URL",
            "async",
            "catch",
            "for",
            "function",
            "if",
            "switch",
            "while",
            "with",
        }:
            continue
        arguments_end = _skip_balanced(
            callback,
            helper_call.start("arguments"),
        )
        arguments_source = callback_scan[
            helper_call.start("arguments") + 1 : arguments_end - 1
        ]
        if re.search(rf"\b{parameter_pattern}\b", arguments_source):
            helpers.add(helper_call.group("callee"))
    return tuple(sorted(helpers))


def _context_helper_identity_source(binding_source: str) -> str:
    """Mask uncalled nested helpers from a callback-helper identity."""

    mask = _code_mask(binding_source)
    scan_text = "".join(
        character if mask[index] else " "
        for index, character in enumerate(binding_source)
    )
    outer = re.match(
        rf"\s*(?:export\s+)?(?:async\s+)?function\s*\*?\s*"
        rf"{TEST_API_NAME}\s*(?P<parameters>\()",
        scan_text,
    )
    if outer is None:
        return binding_source
    parameters_end = _skip_balanced(binding_source, outer.start("parameters"))
    body_start = _function_body_after_parameters(
        binding_source,
        scan_text,
        parameters_end,
    )
    if body_start is None:
        return binding_source
    body_end = _skip_balanced(binding_source, body_start)
    body_scan = scan_text[body_start + 1 : body_end - 1]
    dormant_ranges: list[tuple[int, int]] = []
    for nested in re.finditer(
        rf"\bfunction\s+(?P<name>{TEST_API_NAME})\s*(?P<parameters>\()",
        body_scan,
    ):
        nested_start = body_start + 1 + nested.start()
        nested_parameters = body_start + 1 + nested.start("parameters")
        nested_parameters_end = _skip_balanced(binding_source, nested_parameters)
        nested_body_start = _function_body_after_parameters(
            binding_source,
            scan_text,
            nested_parameters_end,
        )
        if nested_body_start is None:
            continue
        nested_body_end = _skip_balanced(binding_source, nested_body_start)
        outside = (
            scan_text[body_start + 1 : nested_start]
            + " " * (nested_body_end - nested_start)
            + scan_text[nested_body_end : body_end - 1]
        )
        if (
            re.search(rf"(?<![.\w$]){re.escape(nested.group('name'))}\b", outside)
            is None
        ):
            dormant_ranges.append((nested_start, nested_body_end))
    if not dormant_ranges:
        return binding_source
    parts: list[str] = []
    cursor = 0
    for start, end in dormant_ranges:
        parts.extend((binding_source[cursor:start], "/*uaa-dormant-helper*/"))
        cursor = end
    parts.append(binding_source[cursor:])
    return "".join(parts)


def _context_forwarded_helper_names(binding_source: str) -> tuple[str, ...]:
    """Return named helpers that receive a binding's callback-context argument."""

    binding_source = _context_helper_identity_source(binding_source)
    mask = _code_mask(binding_source)
    full_scan_text = "".join(
        character if mask[index] else " "
        for index, character in enumerate(binding_source)
    )
    function_match = re.match(
        rf"\s*(?:export\s+)?(?:async\s+)?function\s*\*?\s*"
        rf"(?P<function_name>{TEST_API_NAME})\s*"
        rf"(?P<parameters>\()\s*{TEST_API_NAME}\b",
        full_scan_text,
    )
    arrow_match = None
    if function_match is None:
        arrow_match = re.match(
            rf"\s*(?:export\s+)?(?:const|let|var)\s+"
            rf"(?P<arrow_name>{TEST_API_NAME})\s*=\s*"
            rf"(?:async\s+)?(?:(?P<parameters>\()\s*{TEST_API_NAME}\b[^)]*\)"
            rf"|(?P<bare>{TEST_API_NAME})\b)\s*(?:\:\s*[^=]+)?=>",
            full_scan_text,
        )
    if function_match is None and arrow_match is None:
        return ()
    parameter_match = function_match or arrow_match
    parameters_start = parameter_match.start("parameters")
    if parameters_start >= 0:
        parameters_end = _skip_balanced(binding_source, parameters_start)
        parameters_source = full_scan_text[parameters_start + 1 : parameters_end - 1]
        parameters = tuple(
            match.group("name")
            for match in re.finditer(
                rf"(?:^|,)\s*(?:\.\.\.\s*)?(?P<name>{TEST_API_NAME})\b",
                parameters_source,
            )
        )
    else:
        parameters = (arrow_match.group("bare"),)
    if not parameters:
        return ()
    if function_match is not None:
        body_start = _function_body_after_parameters(
            binding_source,
            full_scan_text,
            parameters_end,
        )
        if body_start is None:
            return ()
        body_end = _skip_balanced(binding_source, body_start)
        body_source = binding_source[body_start + 1 : body_end - 1]
    else:
        arrow = full_scan_text.find("=>", arrow_match.start(), arrow_match.end())
        body_start = _skip_static_trivia(binding_source, arrow + 2)
        if body_start < len(binding_source) and binding_source[body_start] == "{":
            body_end = _skip_balanced(binding_source, body_start)
            body_source = binding_source[body_start + 1 : body_end - 1]
        else:
            body_source = binding_source[body_start:]
    body_mask = bytearray(_runtime_import_code_mask_bytes(body_source))
    body_scan = "".join(
        character if body_mask[index] else " "
        for index, character in enumerate(body_source)
    )
    nested_function = re.compile(
        rf"\bfunction\s+(?P<name>{TEST_API_NAME})\s*(?P<parameters>\()"
    )
    for nested in nested_function.finditer(body_scan):
        nested_parameters_end = _skip_balanced(
            body_source,
            nested.start("parameters"),
        )
        nested_body_start = _function_body_after_parameters(
            body_source,
            body_scan,
            nested_parameters_end,
        )
        if nested_body_start is None:
            continue
        nested_body_end = _skip_balanced(body_source, nested_body_start)
        outside = (
            body_scan[: nested.start()]
            + " " * (nested_body_end - nested.start())
            + body_scan[nested_body_end:]
        )
        if (
            re.search(
                rf"(?<![.\w$]){re.escape(nested.group('name'))}\b",
                outside,
            )
            is None
        ):
            body_mask[nested.start() : nested_body_end] = b"\x00" * (
                nested_body_end - nested.start()
            )
    scan_text = "".join(
        character if body_mask[index] else " "
        for index, character in enumerate(body_source)
    )
    binding_name = (
        function_match.group("function_name")
        if function_match is not None
        else arrow_match.group("arrow_name")
    )
    context_aliases = set(parameters)
    changed = True
    while changed:
        changed = False
        alias_pattern = "(?:" + "|".join(map(re.escape, context_aliases)) + ")"
        for alias in re.finditer(
            rf"(?<![.\w$])(?:\b(?:const|let|var)\s+)?"
            rf"(?P<target>{TEST_API_NAME})\s*=(?!=|>)\s*"
            rf"(?P<source>{alias_pattern})\b",
            scan_text,
        ):
            if alias.group("target") not in context_aliases:
                context_aliases.add(alias.group("target"))
                changed = True
    parameter_pattern = "(?:" + "|".join(map(re.escape, context_aliases)) + ")"
    member_helper_roots: set[str] = set()
    callable_argument_helpers: set[str] = set()
    escaped_context = False
    for member_call in re.finditer(
        rf"\b(?P<root>{TEST_API_NAME})\s*(?:\.\s*{TEST_API_NAME}|\[[^\]]+\])"
        rf"\s*(?P<arguments>\()",
        scan_text,
    ):
        arguments_end = _skip_balanced(body_source, member_call.start("arguments"))
        arguments_source = scan_text[
            member_call.start("arguments") + 1 : arguments_end - 1
        ]
        if not re.search(rf"\b{parameter_pattern}\b", arguments_source):
            continue
        escaped_context = True
        if re.search(r"\)\s*(?:\?\.|\.)", scan_text[arguments_end - 1 :]):
            raise FrontendInventoryError(
                "frontend callback context escape cannot be inventoried safely"
            )
        if "=>" in arguments_source:
            raise FrontendInventoryError(
                "frontend callback context escape cannot be inventoried safely"
            )
        if re.search(rf"\b{TEST_API_NAME}\s*\(", arguments_source):
            raise FrontendInventoryError(
                "frontend callback context escape cannot be inventoried safely"
            )
        for candidate in re.finditer(TEST_API_NAME, arguments_source):
            candidate_name = candidate.group(0)
            if candidate_name in context_aliases or candidate_name in {
                "false",
                "null",
                "true",
                "undefined",
            }:
                continue
            callable_argument_helpers.add(candidate_name)
        root = member_call.group("root")
        if root not in context_aliases and root not in {
            "Array",
            "Boolean",
            "Date",
            "Error",
            "JSON",
            "Map",
            "Math",
            "Number",
            "Object",
            "Promise",
            "RegExp",
            "Reflect",
            "Set",
            "String",
            "URL",
            "console",
        }:
            member_helper_roots.add(root)
    if re.search(
        rf"[\[{{][^;]*\b(?:{parameter_pattern})\b[^;]*[\]}}]\s*"
        rf"(?:(?:\?\.|\.)\s*{TEST_API_NAME}|"
        r"(?:\?\.)?\[[^\]]+\])\s*\(",
        scan_text,
    ):
        raise FrontendInventoryError(
            "frontend callback context escape cannot be inventoried safely"
        )
    for constructor in re.finditer(
        rf"\bnew\s+{TEST_API_NAME}\s*(?P<arguments>\()",
        scan_text,
    ):
        arguments_end = _skip_balanced(
            body_source,
            constructor.start("arguments"),
        )
        arguments_source = scan_text[
            constructor.start("arguments") + 1 : arguments_end - 1
        ]
        if re.search(
            rf"\b{parameter_pattern}\b",
            arguments_source,
        ) and re.match(
            rf"\s*(?:\?\.|\.)\s*{TEST_API_NAME}\s*\(",
            scan_text[arguments_end:],
        ):
            raise FrontendInventoryError(
                "frontend callback context escape cannot be inventoried safely"
            )
    for assignment in re.finditer(
        rf"(?P<statement>[^;\n]*(?:=|\|\|=|&&=|\?\?=)[^;\n]*"
        rf"\b(?:{parameter_pattern})\b[^;\n]*)",
        scan_text,
    ):
        line_start = max(0, scan_text.rfind("\n", 0, assignment.start()) + 1)
        prefix = scan_text[line_start : assignment.start()]
        statement = assignment.group("statement")
        if not re.match(
            rf"\s*(?:const|let|var)\s+{TEST_API_NAME}\s*=\s*"
            rf"(?:{parameter_pattern})\s*$",
            statement,
        ) and not re.search(r"(?:const|let|var)\s*$", prefix):
            escaped_context = True
            break
    if escaped_context:
        for member_call in re.finditer(
            rf"\b{TEST_API_NAME}\s*(?:\.\s*{TEST_API_NAME}|\[[^\]]+\])"
            rf"\s*(?P<arguments>\()",
            scan_text,
        ):
            arguments_end = _skip_balanced(
                body_source,
                member_call.start("arguments"),
            )
            arguments_source = scan_text[
                member_call.start("arguments") + 1 : arguments_end - 1
            ]
            if re.search(rf"\b{TEST_API_NAME}\s*\(", arguments_source):
                raise FrontendInventoryError(
                    "frontend callback context escape cannot be inventoried safely"
                )
            for candidate in re.finditer(TEST_API_NAME, arguments_source):
                candidate_name = candidate.group(0)
                if candidate_name not in context_aliases and candidate_name not in {
                    "false",
                    "null",
                    "true",
                    "undefined",
                }:
                    callable_argument_helpers.add(candidate_name)
    helpers: set[str] = {*member_helper_roots, *callable_argument_helpers}
    for helper_call in re.finditer(
        rf"(?<![.\w$])(?P<callee>{TEST_API_NAME})\s*(?P<arguments>\()",
        scan_text,
    ):
        if (
            helper_call.group("callee")
            in {
                "Boolean",
                "Date",
                "Error",
                "Map",
                "Number",
                "RegExp",
                "Set",
                "URL",
                "async",
                "catch",
                "for",
                "function",
                "if",
                "switch",
                "while",
                "with",
            }
            or helper_call.group("callee") == binding_name
        ):
            continue
        arguments_end = _skip_balanced(body_source, helper_call.start("arguments"))
        arguments_source = scan_text[
            helper_call.start("arguments") + 1 : arguments_end - 1
        ]
        receives_context = re.search(
            rf"\b{parameter_pattern}\b",
            arguments_source,
        )
        if escaped_context or receives_context:
            helpers.add(helper_call.group("callee"))
        if receives_context:
            escaped_context = True
    return tuple(sorted(helpers))


def _resolved_callback_source(binding_source: str, name: str) -> str:
    """Extract one bounded callback expression from a resolved local binding."""

    mask = _code_mask(binding_source)
    scan_text = "".join(
        character if mask[index] else " "
        for index, character in enumerate(binding_source)
    )
    declaration = re.match(
        rf"\s*(?:export\s+)?(?:const|let|var)\s+{re.escape(name)}"
        rf"(?:\s*[?!])?",
        scan_text,
    )
    if declaration is None:
        return binding_source
    assignment_end: int | None = None
    cursor = declaration.end()
    while cursor < len(binding_source):
        if binding_source[cursor] in "\"'`":
            cursor = _skip_string(binding_source, cursor)
            continue
        if binding_source[cursor] in "([{":
            cursor = _skip_balanced(binding_source, cursor)
            continue
        if binding_source[cursor] in ";\n":
            break
        if binding_source[cursor] == "=" and (
            cursor + 1 >= len(binding_source) or binding_source[cursor + 1] != ">"
        ):
            assignment_end = cursor + 1
            break
        cursor += 1
    if assignment_end is None:
        return binding_source
    start = _skip_static_trivia(binding_source, assignment_end)
    cursor = start
    while cursor < len(binding_source):
        if binding_source[cursor] in "\"'`":
            cursor = _skip_string(binding_source, cursor)
            continue
        if binding_source[cursor] in "([{":
            cursor = _skip_balanced(binding_source, cursor)
            continue
        if binding_source[cursor] == ";":
            callback_source = binding_source[start:cursor].strip()
            while callback_source.startswith("("):
                end = _skip_balanced(callback_source, 0)
                suffix = callback_source[end:].strip()
                if not suffix or re.match(r"(?:as|satisfies)\b", suffix):
                    callback_source = callback_source[1 : end - 1].strip()
                    continue
                break
            alias = re.fullmatch(TEST_API_NAME, callback_source)
            if alias is not None:
                remainder = binding_source[cursor + 1 :].lstrip()
                if remainder:
                    return _resolved_callback_source(remainder, alias.group(0))
                raise FrontendInventoryError(
                    "frontend runtime callback cannot be resolved safely"
                )
            return callback_source
        cursor += 1
    raise FrontendInventoryError("frontend runtime callback cannot be resolved safely")


def _execution_posture_parts(
    declaration_source: str,
    *,
    condition_binding_resolver: Callable[[str], str | None] | None = None,
) -> tuple[str, ...]:
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
    expected_failure = tuple(
        modifier
        for modifier in modifiers
        if modifier in EXPECTED_FAILURE_TEST_MODIFIERS
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
    parts.extend(f"expected-failure:{modifier}" for modifier in expected_failure)
    if conditional is not None:
        condition_end = _skip_balanced(declaration_source, arguments_start)
        normalized_condition = _normalized_javascript_expression(
            declaration_source[arguments_start:condition_end]
        )
        condition_source = declaration_source[arguments_start + 1 : condition_end - 1]
        condition_mask = _code_mask(condition_source)
        condition_scan = "".join(
            character if condition_mask[index] else " "
            for index, character in enumerate(condition_source)
        )
        binding_parts = _resolved_javascript_bindings(
            condition_scan,
            condition_binding_resolver,
        )
        if binding_parts:
            normalized_condition = "\n".join((normalized_condition, *binding_parts))
        digest = hashlib.sha256(normalized_condition.encode("utf-8")).hexdigest()
        parts.append(f"conditional:{conditional}:sha256:{digest}")
    arguments = _registration_argument_ranges(declaration_source)
    if len(arguments) >= 3:
        option_source = declaration_source[arguments[1][0] : arguments[1][1]].strip()
        callback_source = declaration_source[arguments[2][0] : arguments[2][1]]
        has_option_slot = option_source.startswith("{") or (
            _looks_like_frontend_callback(callback_source)
        )
        if has_option_slot:
            if option_source.startswith("{"):
                if _skip_balanced(option_source, 0) != len(option_source):
                    raise FrontendInventoryError(
                        "frontend test option object cannot be inventoried safely"
                    )
                normalized_option = _normalized_javascript_expression(option_source)
                option_bindings = _resolved_javascript_bindings(
                    option_source,
                    condition_binding_resolver,
                    ignore_object_keys=True,
                )
                if option_bindings:
                    normalized_option = "\n".join((normalized_option, *option_bindings))
            elif re.fullmatch(TEST_API_NAME, option_source):
                if condition_binding_resolver is None:
                    raise FrontendInventoryError(
                        "frontend test option binding cannot be resolved safely"
                    )
                normalized_option = (
                    _normalized_javascript_expression(option_source)
                    + "\nbinding="
                    + condition_binding_resolver(option_source)
                )
            else:
                raise FrontendInventoryError(
                    "frontend test option object cannot be inventoried safely"
                )
            digest = hashlib.sha256(normalized_option.encode("utf-8")).hexdigest()
            parts.append(f"options:sha256:{digest}")
    if len(arguments) >= 2:
        callback_index = (
            2
            if len(arguments) >= 3
            and _looks_like_frontend_callback(
                declaration_source[arguments[2][0] : arguments[2][1]]
            )
            else 1
        )
        callback_source = declaration_source[
            arguments[callback_index][0] : arguments[callback_index][1]
        ].strip()
        if condition_binding_resolver is not None:
            for helper_name in _runtime_callback_context_helpers(
                declaration_source,
                arguments,
            ):
                helper_source = condition_binding_resolver(helper_name)
                if helper_source is None:
                    raise FrontendInventoryError(
                        "frontend callback helper cannot be resolved safely"
                    )
                digest = hashlib.sha256(helper_source.encode("utf-8")).hexdigest()
                parts.append(f"callback-helper:{helper_name}:sha256:{digest}")
        if re.fullmatch(TEST_API_NAME, callback_source):
            if condition_binding_resolver is None:
                raise FrontendInventoryError(
                    "frontend runtime callback cannot be resolved safely"
                )
            resolved_callback = condition_binding_resolver(callback_source)
            if resolved_callback is None:
                raise FrontendInventoryError(
                    "frontend runtime callback cannot be resolved safely"
                )
            inline_callback = _resolved_callback_source(
                resolved_callback,
                callback_source,
            )
            callback_start, callback_end = arguments[callback_index]
            synthetic_declaration = (
                declaration_source[:callback_start]
                + inline_callback
                + declaration_source[callback_end:]
            )
            if _has_runtime_callback_skip(
                synthetic_declaration,
                _registration_argument_ranges(synthetic_declaration),
            ):
                raise FrontendInventoryError(
                    "frontend runtime callback skip cannot be inventoried safely"
                )
            digest = hashlib.sha256(resolved_callback.encode("utf-8")).hexdigest()
            parts.append(f"callback:sha256:{digest}")
        elif not _looks_like_frontend_callback(callback_source):
            raise FrontendInventoryError(
                "frontend runtime callback cannot be resolved safely"
            )
        elif re.search(
            r"\.\s*each\b", declaration_source[: arguments[0][0]]
        ) is None and (
            (
                "=>" in callback_source
                and re.search(r"\bskip\b", callback_source.split("=>", 1)[0])
            )
            or (
                re.match(
                    r"\s*(?:async\s+)?(?:function\s*)?\(\s*\.\.\.",
                    callback_source,
                )
                and re.search(r"\[\s*0\s*\]\s*\.\s*skip\b", callback_source)
            )
            or (
                re.match(r"\s*function\s*\(\s*\)", callback_source)
                and re.search(
                    r"\barguments\s*\[\s*0\s*\]\s*\.\s*skip\b",
                    callback_source,
                )
            )
        ):
            raise FrontendInventoryError(
                "frontend runtime callback skip cannot be inventoried safely"
            )
    if _has_runtime_callback_skip(declaration_source, arguments):
        raise FrontendInventoryError(
            "frontend runtime callback skip cannot be inventoried safely"
        )
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
    dot_property = rf"{global_object}\s*(?:\?\.\s*|\.\s*){name_pattern}\b"
    modifier_names = r"(?:concurrent|fail|fails|fixme|only|sequential|skip|todo)"
    quoted_modifier_names = (
        r'(?:"(?:concurrent|fail|fails|fixme|only|sequential|skip|todo)"'
        r"|'(?:concurrent|fail|fails|fixme|only|sequential|skip|todo)')"
    )
    modifier_access = (
        rf"(?:\s*(?:(?:\?\.\s*|\.\s*){modifier_names}\b"
        rf"|(?:\?\.\s*)?\[\s*{quoted_modifier_names}\s*\]))*"
    )
    parameterizer_names = r"(?:each|for|runIf|skipIf)"
    quoted_parameterizer_names = (
        r'(?:"(?:each|for|runIf|skipIf)"|\'(?:each|for|runIf|skipIf)\')'
    )
    parameterizer_access = (
        rf"(?:(?:\?\.\s*|\.\s*){parameterizer_names}\b"
        rf"|(?:\?\.\s*)?\[\s*{quoted_parameterizer_names}\s*\])"
    )
    invocation_suffix = (
        rf"{modifier_access}\s*(?:(?:\?\.\s*)?\(|{parameterizer_access})"
    )
    dot_invocation = rf"{dot_property}{invocation_suffix}"
    if re.search(dot_invocation, scan_text) or any(
        scan_text[match.start()] == text[match.start()]
        for match in re.finditer(dot_invocation, text)
    ):
        return True
    quoted_names = (
        "(?:"
        + "|".join(quoted for name in names for quoted in (f'"{name}"', f"'{name}'"))
        + ")"
    )
    computed_property = rf"{global_object}\s*(?:\?\.\s*)?\[\s*{quoted_names}\s*\]"
    return any(
        scan_text[match.start()] == text[match.start()]
        for match in re.finditer(rf"{computed_property}{invocation_suffix}", text)
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


def _extended_test_api_postures(
    text: str,
    scan_text: str,
    api_names: set[str],
    import_binding_resolver: ImportBindingResolver | None,
) -> dict[str, tuple[str, ...]]:
    """Bind each extended runner API to its complete extension initializer."""

    javascript_keywords = {
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
        "finally",
        "for",
        "function",
        "if",
        "in",
        "let",
        "of",
        "return",
        "static",
        "super",
        "switch",
        "throw",
        "try",
        "var",
        "while",
        "yield",
    }
    host_globals = {
        "Array",
        "Boolean",
        "Date",
        "Error",
        "JSON",
        "Map",
        "Math",
        "Number",
        "Object",
        "Promise",
        "RegExp",
        "Set",
        "String",
        "URL",
        "console",
        "queueMicrotask",
        "setInterval",
        "setTimeout",
    }
    postures: dict[str, tuple[str, ...]] = {}
    for match in EXTENSION_PATTERN.finditer(scan_text):
        alias = match.group("alias")
        base = match.group("base")
        if alias not in api_names or base not in api_names:
            continue
        call_start = match.end() - 1
        call_end = _skip_balanced(text, call_start)
        initializer = text[call_start + 1 : call_end - 1]
        source = _normalized_javascript_expression(
            text[match.start("base") : call_end]
        )
        initializer_mask = _code_mask(initializer)
        initializer_scan = "".join(
            character if initializer_mask[index] else " "
            for index, character in enumerate(initializer)
        )
        callback_bindings: set[str] = set()
        for callback in re.finditer(
            rf"(?:async\s+)?(?:\((?P<parameters>[^()]*)\)|"
            rf"(?P<bare>{TEST_API_NAME}))\s*=>",
            initializer_scan,
        ):
            parameters = callback.group("parameters") or callback.group("bare")
            if "=" in parameters:
                raise FrontendInventoryError(
                    "frontend extended test API callback defaults cannot be "
                    "inventoried safely"
                )
            callback_bindings.update(re.findall(TEST_API_NAME, parameters))
        local_bindings = set(
            re.findall(
                rf"\b(?:const|let|var|function|class)\s+(?P<name>{TEST_API_NAME})",
                initializer_scan,
            )
        )
        binding_parts: list[str] = []
        for name in _javascript_binding_names(
            initializer,
            ignore_object_keys=True,
        ):
            if (
                name == base
                or name in callback_bindings
                or name in local_bindings
                or name in javascript_keywords
                or name in host_globals
            ):
                continue
            binding_source = _static_collection_source(
                text,
                scan_text,
                name,
                match.start(),
                import_binding_resolver,
            )
            binding_parts.append(f"binding:{name}={binding_source}")
        parent_postures = postures.get(base, ())
        identity_source = "\n".join(
            (*parent_postures, source, *binding_parts)
        )
        digest = hashlib.sha256(identity_source.encode("utf-8")).hexdigest()
        postures[alias] = (f"test-extension:sha256:{digest}",)
    return postures


def _applicable_extended_test_api_postures(
    postures: dict[str, tuple[str, ...]],
    scan_text: str,
    offset: int,
) -> tuple[str, ...]:
    match = re.match(TEST_API_NAME, scan_text[offset:])
    return postures.get(match.group(0), ()) if match is not None else ()


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
    pattern = re.compile(rf"\b(?:const|let|var)\s+{re.escape(name)}\b")
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
    primitive = re.match(
        r"(?:false|true|null|undefined)\b",
        scan_text[value_start:before_offset],
    )
    if (
        value_start >= before_offset
        or text[value_start] not in "[{'\"`("
        and primitive is None
    ):
        raise FrontendInventoryError("frontend parameterized test binding is dynamic")
    if primitive is not None:
        value_end = value_start + primitive.end()
    elif text[value_start] in "[({":
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
    if export_pattern.search(scan_text) is not None:
        return _const_initializer_source(text, scan_text, name, len(text))
    function_pattern = re.compile(
        rf"\bexport\s+(?:async\s+)?function\s*\*?\s*{re.escape(name)}\s*"
        r"(?P<parameters>\()"
    )
    function = function_pattern.search(scan_text)
    if function is None:
        return None
    parameters_end = _skip_balanced(text, function.start("parameters"))
    body_start = _function_body_after_parameters(text, scan_text, parameters_end)
    if body_start is None:
        return None
    function_source = text[function.start() : _skip_balanced(text, body_start)]
    dependency_sources = tuple(
        _static_collection_source(
            text,
            scan_text,
            helper_name,
            len(text),
            None,
            _seen_names=frozenset((name,)),
        )
        for helper_name in _context_forwarded_helper_names(function_source)
    )
    return "\n".join((function_source, *dependency_sources))


def _relative_commonjs_require_modules(text: str, scan_text: str) -> tuple[str, ...]:
    return tuple(
        module
        for module in _commonjs_require_modules(text, scan_text)
        if module.startswith(".")
    )


def _commonjs_require_modules(text: str, scan_text: str) -> tuple[str, ...]:
    if re.search(
        rf"\b(?:const|let|var)\s+{TEST_API_NAME}\s*=\s*require\b"
        r"(?!\s*(?:\?\.\s*)?\()",
        scan_text,
    ):
        raise FrontendInventoryError(
            "dynamic CommonJS dependency cannot be inventoried safely"
        )
    require_callee = r"(?:\brequire\b|\(\s*(?P<wrapped_require>require)\s*\))"
    call_pattern = re.compile(rf"{require_callee}\s*(?:\?\.\s*)?\(")
    call_offsets = {
        match.start("wrapped_require")
        if match.group("wrapped_require") is not None
        else match.start()
        for match in call_pattern.finditer(scan_text)
    }
    require_pattern = re.compile(
        rf"{require_callee}\s*(?:\?\.\s*)?\(\s*(?:"
        r"(?P<quote>['\"])(?P<quoted_module>[^'\"]+)(?P=quote)"
        r"|`(?P<template_module>[^`$]+)`"
        r")\s*\)"
    )
    literal_offsets: set[int] = set()
    modules: list[str] = []
    for match in require_pattern.finditer(text):
        offset = (
            match.start("wrapped_require")
            if match.group("wrapped_require") is not None
            else match.start()
        )
        if offset not in call_offsets:
            continue
        literal_offsets.add(offset)
        module = match.group("quoted_module") or match.group("template_module")
        if module not in modules:
            modules.append(module)
    if call_offsets != literal_offsets:
        raise FrontendInventoryError(
            "dynamic CommonJS dependency cannot be inventoried safely"
        )
    return tuple(modules)


def _typescript_type_import(text: str, offset: int) -> bool:
    line_start = max(text.rfind("\n", 0, offset), text.rfind(";", 0, offset)) + 1
    prefix = text[line_start:offset]
    stripped = prefix.lstrip()
    if re.match(r"(?:export\s+)?(?:type|interface)\b", stripped):
        return True
    if re.search(r"\b(?:if|while|for|switch)\s*\([^)]*\btype\b[^)]*\)", prefix):
        return False
    colon = prefix.rfind(":")
    if colon >= 0 and not prefix[colon + 1 :].strip():
        context = prefix[:colon]
        last_assignment = context.rfind("=")
        last_brace = context.rfind("{")
        if last_assignment >= 0 and last_brace > last_assignment:
            return False
        if "?" in context[max(0, last_assignment) :]:
            return False
        return "=>" not in context
    if colon >= 0 and "=>" in prefix[colon + 1 :]:
        return False
    return re.search(r":\s*[A-Za-z_$][\w$]*(?:\s*<[^{};]*)?\s*$", prefix) is not None


def _dynamic_import_modules(text: str, scan_text: str) -> tuple[str, ...]:
    call_offsets = {
        match.start()
        for match in re.finditer(r"\bimport\s*\(", scan_text)
        if not _typescript_type_import(text, match.start())
    }
    pattern = re.compile(
        r"\bimport\s*\(\s*(?:"
        r"(?P<quote>['\"])(?P<quoted_module>[^'\"]+)(?P=quote)"
        r"|`(?P<template_module>[^`$]+)`"
        r")\s*\)"
    )
    literal_offsets: set[int] = set()
    modules: list[str] = []
    for match in pattern.finditer(text):
        if match.start() not in call_offsets:
            continue
        literal_offsets.add(match.start())
        module = match.group("quoted_module") or match.group("template_module")
        if module not in modules:
            modules.append(module)
    if call_offsets != literal_offsets:
        raise FrontendInventoryError(
            "dynamic frontend dependency cannot be inventoried safely"
        )
    return tuple(modules)


def _runtime_named_members(members: str) -> tuple[str, ...]:
    member_mask = _code_mask(members)
    visible = "".join(
        character if member_mask[index] else " "
        for index, character in enumerate(members)
    )
    return tuple(
        member
        for member in visible.split(",")
        if member.strip()
        and not (
            re.match(r"\s*type\s+[A-Za-z_$]", member) is not None
            and re.match(r"\s*type\s+as\b", member) is None
        )
    )


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
    for module in _relative_commonjs_require_modules(text, scan_text):
        if module not in modules:
            modules.append(module)
    return tuple(modules)


def frontend_runtime_import_modules(text: str) -> tuple[str, ...]:
    """Return relative imports whose module initializers execute at runtime."""

    code_mask = _module_initializer_code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    matches: list[tuple[int, str]] = []
    for match in IMPORT_PATTERN.finditer(text):
        if (
            not match.group("module").startswith(".")
            or scan_text[match.start() : match.start() + len("import")] != "import"
        ):
            continue
        runtime_members = _runtime_named_members(match.group("members"))
        if runtime_members:
            matches.append((match.start(), match.group("module")))
    for pattern in (DEFAULT_IMPORT_PATTERN, NAMESPACE_IMPORT_PATTERN):
        for match in pattern.finditer(text):
            statement = scan_text[match.start() : match.end()]
            if (
                match.group("module").startswith(".")
                and statement.startswith("import")
                and re.match(r"import\s+type\b", statement) is None
            ):
                matches.append((match.start(), match.group("module")))
    for pattern in (
        SIDE_EFFECT_IMPORT_PATTERN,
        EMPTY_NAMED_IMPORT_PATTERN,
        EXPORT_FROM_PATTERN,
    ):
        for match in pattern.finditer(text):
            keyword = "export" if pattern is EXPORT_FROM_PATTERN else "import"
            statement = scan_text[match.start() : match.end()]
            type_only_named_export = (
                pattern is EXPORT_FROM_PATTERN
                and statement.startswith("export")
                and "{" in statement
                and not _runtime_named_members(
                    text[match.start() : match.end()].split("{", 1)[1].rsplit("}", 1)[0]
                )
            )
            if (
                match.group("module").startswith(".")
                and statement.startswith(keyword)
                and re.match(rf"{keyword}\s+type\b", statement) is None
                and not type_only_named_export
            ):
                matches.append((match.start(), match.group("module")))
    for module in (
        *_commonjs_require_modules(text, scan_text),
        *_dynamic_import_modules(text, scan_text),
    ):
        if module.startswith("."):
            matches.append((len(text), module))
    modules: list[str] = []
    for _offset, module in sorted(matches):
        if module not in modules:
            modules.append(module)
    return tuple(modules)


def frontend_runtime_test_posture(text: str) -> bool:
    """Return whether module initialization can affect test execution posture."""

    code_mask = _module_initializer_code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    for match in IMPORT_PATTERN.finditer(text):
        if (
            match.group("module") not in RUNNER_MODULES
            or scan_text[match.start() : match.start() + len("import")] != "import"
        ):
            continue
        if _runtime_named_members(match.group("members")):
            return True
    for pattern in (
        DEFAULT_IMPORT_PATTERN,
        NAMESPACE_IMPORT_PATTERN,
        SIDE_EFFECT_IMPORT_PATTERN,
        EMPTY_NAMED_IMPORT_PATTERN,
        EXPORT_FROM_PATTERN,
    ):
        for match in pattern.finditer(text):
            keyword = "export" if pattern is EXPORT_FROM_PATTERN else "import"
            statement = scan_text[match.start() : match.end()]
            type_only_named_export = (
                pattern is EXPORT_FROM_PATTERN
                and statement.startswith("export")
                and "{" in statement
                and not _runtime_named_members(
                    text[match.start() : match.end()].split("{", 1)[1].rsplit("}", 1)[0]
                )
            )
            if (
                match.group("module") in RUNNER_MODULES
                and statement.startswith(keyword)
                and re.match(rf"{keyword}\s+type\b", statement) is None
                and not type_only_named_export
            ):
                return True
    if RUNNER_MODULES.intersection(
        (
            *_commonjs_require_modules(text, scan_text),
            *_dynamic_import_modules(text, scan_text),
        )
    ):
        return True
    posture_apis = (
        "afterAll",
        "afterEach",
        "beforeAll",
        "beforeEach",
        "describe",
        "it",
        "suite",
        "test",
    )
    posture_pattern = "(?:" + "|".join(posture_apis) + ")"
    if re.search(
        r"(?<![.\w$])(?:afterAll|afterEach|beforeAll|beforeEach)\b", scan_text
    ):
        return True
    direct_call_pattern = re.compile(rf"(?<![.\w$]){posture_pattern}\s*\(")
    for match in direct_call_pattern.finditer(scan_text):
        prefix = scan_text[max(0, match.start() - 32) : match.start()]
        if re.search(r"\bfunction\s*$", prefix) is None:
            return True
    if re.search(
        rf"(?<![.\w$]){posture_pattern}\s*(?:\?\.|\.)",
        scan_text,
    ):
        return True
    if re.search(
        rf"\(\s*{posture_pattern}\s*\)\s*(?:\?\.)?\s*\(",
        scan_text,
    ):
        return True
    if (
        re.search(
            rf"\b(?:const|let|var)\s+{TEST_API_NAME}\s*=\s*\(*\s*{posture_pattern}\b",
            scan_text,
        )
        is not None
    ):
        return True
    if (
        re.search(
            rf"\b{TEST_API_NAME}\s*=\s*\(*\s*{posture_pattern}\b",
            scan_text,
        )
        is not None
    ):
        return True
    global_object = r"(?:globalThis|window|self)"
    if re.search(rf"\b{global_object}\s*(?:\?\.)?\[", scan_text):
        return True
    if re.search(rf"\b{global_object}\s*(?:\?\.|\.)\s*{posture_pattern}\b", scan_text):
        return True
    if re.search(
        rf"\b(?:const|let|var)\s*\{{[^}}]*\b{posture_pattern}\b[^}}]*\}}\s*=\s*{global_object}\b",
        scan_text,
    ):
        return True
    return any(
        scan_text[match.start()] == text[match.start()]
        for match in re.finditer(
            rf"\b{global_object}\s*(?:\?\.)?\[\s*['\"]{posture_pattern}['\"]\s*\]",
            text,
        )
    )


@lru_cache(maxsize=256)
def _runtime_import_code_mask_bytes(text: str) -> bytes:
    """Mask import-irrelevant syntax without rejecting ordinary JSX text."""

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
                        mask[body_start:body_end] = _runtime_import_code_mask_bytes(
                            text[body_start:body_end]
                        )
                        template_index = interpolation_end
                        continue
                    template_index += 1
            index = end
            continue
        if _is_regex_literal_at(text, index, regex_closures):
            try:
                end, closing = _skip_regex(text, index)
            except FrontendInventoryError:
                # Production JSX may contain unquoted text such as
                # ``delete/export``. It cannot contain a static import
                # declaration, so keep the slash visible and continue.
                index += 1
                continue
            regex_closures.add(closing)
            mask[index:end] = b"\x00" * (end - index)
            index = end
            continue
        comment_end = _skip_comment(text, index) if text[index] == "/" else index
        if comment_end != index:
            mask[index:comment_end] = b"\x00" * (comment_end - index)
            index = comment_end
            continue
        index += 1
    return bytes(mask)


def _runtime_import_code_mask(text: str) -> bytearray:
    """Return an isolated mutable view of the exact-source lexical mask."""

    return bytearray(_runtime_import_code_mask_bytes(text))


@lru_cache(maxsize=256)
def _module_initializer_code_mask_bytes(
    text: str,
    *,
    preserve_literals: bool = False,
) -> bytes:
    """Mask function bodies that cannot execute during module initialization."""

    scan_mask = bytearray(_runtime_import_code_mask_bytes(text))
    mask = bytearray(b"\x01" * len(text)) if preserve_literals else bytearray(scan_mask)
    scan_text = "".join(
        character if scan_mask[index] else " " for index, character in enumerate(text)
    )
    identifier_positions: dict[str, list[int]] = {}
    for identifier in re.finditer(
        rf"(?<![\w$])(?P<name>{TEST_API_NAME})\b",
        scan_text,
    ):
        identifier_positions.setdefault(identifier.group("name"), []).append(
            identifier.start()
        )
    function_pattern = re.compile(
        rf"\b(?:async\s+)?function\s*\*?\s*(?P<name>{TEST_API_NAME})\s*"
        r"(?P<parameters>\()"
    )
    for match in function_pattern.finditer(scan_text):
        try:
            parameters_end = _skip_balanced(text, match.start("parameters"))
            body_start = _function_body_after_parameters(
                text,
                scan_text,
                parameters_end,
            )
            if body_start is None:
                continue
            body_end = _skip_balanced(text, body_start)
        except FrontendInventoryError:
            continue
        referenced_outside_declaration = any(
            position < match.start() or position >= body_end
            for position in identifier_positions.get(match.group("name"), ())
        )
        if referenced_outside_declaration:
            continue
        mask[body_start:body_end] = b"\x00" * (body_end - body_start)
    arrow_pattern = re.compile(
        rf"\b(?:const|let|var)\s+(?P<name>{TEST_API_NAME})\s*=\s*"
        r"(?:async\s*)?(?:<[^;{}\n]+>\s*)?"
        r"(?:\([^;\n]*?\)|[A-Za-z_$][\w$]*)"
        r"(?:\s*:\s*[^=;\n]+)?\s*=>"
    )
    for match in arrow_pattern.finditer(scan_text):
        body_start = _skip_static_trivia(text, match.end())
        try:
            if body_start < len(text) and text[body_start] == "{":
                body_end = _skip_balanced(text, body_start)
            else:
                semicolon = scan_text.find(";", body_start)
                newline = scan_text.find("\n", body_start)
                endings = [end for end in (semicolon, newline) if end >= 0]
                body_end = min(endings) if endings else len(text)
        except FrontendInventoryError:
            continue
        if any(
            position < match.start() or position >= body_end
            for position in identifier_positions.get(match.group("name"), ())
        ):
            continue
        mask[body_start:body_end] = b"\x00" * (body_end - body_start)
    class_pattern = re.compile(rf"\bclass\s+(?P<name>{TEST_API_NAME})[^{{]*\{{")
    method_pattern = re.compile(
        rf"\s*(?!static\s*\{{)(?P<static>static\s+)?(?:async\s+)?"
        rf"(?P<kind>get\s+|set\s+)?(?P<name>{TEST_API_NAME})"
        r"\s*\([^)]*\)\s*\{"
    )
    field_arrow_pattern = re.compile(
        rf"\s*(?P<static>static\s+)?(?:readonly\s+)?"
        rf"(?P<name>{TEST_API_NAME})(?:\s*[?!])?"
        r"(?:\s*:\s*[^=;\n]+)?\s*=\s*(?:async\s+)?"
        r"(?:<[^;{}\n]+>\s*)?"
        rf"(?:\([^;\n]*?\)|{TEST_API_NAME})"
        r"(?:\s*:\s*[^=;\n]+)?\s*=>"
    )

    def direct_class_member(class_start: int, offset: int) -> bool:
        depth = 1
        for character in scan_text[class_start + 1 : offset]:
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
        return depth == 1

    def member_used(
        source: str,
        receivers: tuple[str, ...],
        member: str,
        *,
        require_call: bool,
        raw_source: str | None = None,
    ) -> bool:
        receiver_pattern = "(?:" + "|".join(receivers) + ")"
        member_pattern = re.escape(member)
        dot_access = rf"(?:{receiver_pattern})\s*(?:\?\.|\.)\s*{member_pattern}\b"
        suffix = r"\s*(?:\?\.)?\s*\(" if require_call else ""
        if re.search(rf"(?:{dot_access}){suffix}", source) is not None:
            return True
        if raw_source is None:
            return False
        computed_access = re.compile(
            rf"(?:{receiver_pattern})\s*(?:\?\.)?\[\s*(['\"])"
            rf"{member_pattern}\1\s*\]"
        )
        for match in computed_access.finditer(raw_source):
            if not source[match.start()] or source[match.start()].isspace():
                continue
            if not require_call or re.match(suffix, source[match.end() :]):
                return True
        computed_member = re.compile(
            rf"(?:{receiver_pattern})\s*(?:\?\.)?(?P<bracket>\[)"
        )
        for match in computed_member.finditer(raw_source):
            if not source[match.start()] or source[match.start()].isspace():
                continue
            try:
                access_end = _skip_balanced(
                    raw_source,
                    match.start("bracket"),
                )
                key_start = _skip_static_trivia(
                    raw_source,
                    match.start("bracket") + 1,
                )
                computed_name, key_end = _static_string_value(
                    raw_source,
                    key_start,
                )
                if _skip_static_trivia(raw_source, key_end) != access_end - 1:
                    return True
            except FrontendInventoryError:
                # A dynamic key on a proven receiver can select any method.
                return True
            if computed_name != member:
                continue
            if not require_call or re.match(suffix, source[access_end:]):
                return True
        reflect_get = re.compile(
            rf"\bReflect\s*\.\s*get\s*\(\s*(?:{receiver_pattern})\s*,"
        )
        for match in reflect_get.finditer(raw_source):
            if not source[match.start()] or source[match.start()].isspace():
                continue
            argument_start = _skip_static_trivia(raw_source, match.end())
            try:
                reflected_member, argument_end = _static_string_value(
                    raw_source,
                    argument_start,
                )
            except FrontendInventoryError:
                # A dynamic key on a proven receiver can select any method.
                return True
            if reflected_member != member:
                continue
            closing = _skip_static_trivia(raw_source, argument_end)
            if closing >= len(raw_source) or raw_source[closing] != ")":
                return True
            if not require_call or re.match(suffix, source[closing + 1 :]):
                return True
        destructuring = re.compile(
            rf"(?<![.\w$])(?:(?:const|let|var)\s+)?\(?\s*"
            rf"\{{(?P<members>[^}}]*)\}}\s*\)?\s*=\s*"
            rf"(?:{receiver_pattern})\b"
        )
        for match in destructuring.finditer(source):
            member_binding = re.search(
                rf"(?:^|,)\s*{member_pattern}\b"
                rf"(?:\s*:\s*(?P<alias>{TEST_API_NAME}))?",
                match.group("members"),
            )
            if member_binding is None:
                continue
            alias = member_binding.group("alias") or member
            if not require_call or re.search(
                rf"(?<![.\w$]){re.escape(alias)}\s*\(",
                source[match.end() :],
            ):
                return True
        descriptor_get = re.compile(
            rf"\bObject\s*\.\s*getOwnPropertyDescriptor\s*\(\s*"
            rf"(?:{receiver_pattern})\s*,"
        )
        for match in descriptor_get.finditer(raw_source):
            if not source[match.start()] or source[match.start()].isspace():
                continue
            key_start = _skip_static_trivia(raw_source, match.end())
            try:
                descriptor_name, _key_end = _static_string_value(
                    raw_source,
                    key_start,
                )
            except FrontendInventoryError:
                return True
            if descriptor_name == member:
                return True
        receiver_argument = re.compile(
            rf"(?<![.\w$])(?P<callee>{TEST_API_NAME})\s*\("
            rf"(?P<arguments>[^)]*(?:{receiver_pattern})[^)]*)\)"
        )
        if any(
            match.group("callee")
            not in {"Object", "Reflect", "String", "Boolean", "Number"}
            for match in receiver_argument.finditer(source)
        ):
            # Passing a proven receiver to an opaque initializer helper may
            # invoke any member; bind all methods conservatively.
            return True
        return False

    for class_match in class_pattern.finditer(scan_text):
        class_start = scan_text.find("{", class_match.start(), class_match.end())
        try:
            class_end = _skip_balanced(text, class_start)
        except FrontendInventoryError:
            continue
        class_name = class_match.group("name")
        initializer_source = "".join(
            character if mask[index] else " " for index, character in enumerate(text)
        )
        external_source = (
            initializer_source[: class_match.start()]
            + " " * (class_end - class_match.start())
            + initializer_source[class_end:]
        )
        external_text = (
            text[: class_match.start()]
            + " " * (class_end - class_match.start())
            + text[class_end:]
        )
        class_pattern_text = re.escape(class_name)
        instance_receiver_names = {
            match.group("name")
            for match in re.finditer(
                rf"\b(?:const|let|var)\s+(?P<name>{TEST_API_NAME})\s*=\s*"
                rf"new\s+{class_pattern_text}\b",
                external_source,
            )
        }
        class_receiver_names = {class_name}
        class_expression_target: str | None = None
        class_expression_binding_range: tuple[int, int] | None = None
        binding_prefix = scan_text[: class_match.start()]
        statement_start = binding_prefix.rfind(";") + 1
        statement_prefix = binding_prefix[statement_start:]
        outer_bindings = tuple(
            re.finditer(
                rf"\b(?:const|let|var)\s+(?P<root>{TEST_API_NAME})"
                rf"(?:\s*[?!])?(?:\s*:\s*[^=;\n]+)?\s*=",
                statement_prefix,
            )
        )
        direct_binding = re.search(
            rf"(?P<root>{TEST_API_NAME})"
            rf"(?:\s*(?:\.\s*{TEST_API_NAME}|\[[^\]]+\]))*\s*=\s*"
            rf"[^;]*$",
            statement_prefix,
        )
        class_expression_binding = (
            outer_bindings[-1] if outer_bindings else direct_binding
        )
        if class_expression_binding is not None:
            class_expression_target = class_expression_binding.group("root")
            class_receiver_names.add(class_expression_target)
            class_expression_binding_range = (
                statement_start + class_expression_binding.start("root"),
                statement_start + class_expression_binding.end("root"),
            )
        changed = True
        while changed:
            changed = False
            for match in re.finditer(
                rf"(?<![.\w$])(?:\b(?:const|let|var)\s+)?"
                rf"(?P<name>{TEST_API_NAME})\s*=(?!=|>)\s*"
                rf"(?P<source>{TEST_API_NAME})\b",
                external_source,
            ):
                source_name = match.group("source")
                target_name = match.group("name")
                target_set = (
                    instance_receiver_names
                    if source_name in instance_receiver_names
                    else class_receiver_names
                    if source_name in class_receiver_names
                    else None
                )
                if target_set is not None and target_name not in target_set:
                    target_set.add(target_name)
                    changed = True
        instance_receivers = tuple(
            re.escape(name) for name in sorted(instance_receiver_names)
        )
        class_receivers = [re.escape(name) for name in sorted(class_receiver_names)]
        class_expression_receiver: str | None = None
        if class_expression_target is not None and "." in class_expression_target:
            class_expression_receiver = r"\s*\.\s*".join(
                re.escape(part) for part in class_expression_target.split(".")
            )
            class_receivers.append(class_expression_receiver)
        class_receivers_tuple = tuple(class_receivers)
        immediate_class_construction = bool(
            re.search(r"\bnew\s*(?:\(\s*)?$", binding_prefix)
            and re.match(r"\s*\)?\s*\(", external_source[class_end:])
        )
        instantiated = immediate_class_construction or any(
            re.search(rf"\bnew\s+{receiver}\b", external_source) is not None
            for receiver in class_receivers_tuple
        )
        class_reference_source = external_source
        if class_expression_binding_range is not None:
            binding_start, binding_end = class_expression_binding_range
            class_reference_source = (
                external_source[:binding_start]
                + " " * (binding_end - binding_start)
                + external_source[binding_end:]
            )
        immediate_class_member_access = (
            re.match(
                rf"\s*\)*\s*(?:(?:\?\.|\.)\s*{TEST_API_NAME}\b|"
                r"(?:\?\.)?\[)",
                external_source[class_end:],
            )
            is not None
        )
        class_object_referenced = immediate_class_member_access or any(
            re.search(rf"(?<![.\w$]){receiver}\b", class_reference_source) is not None
            for receiver in class_receivers_tuple
        )
        prototype_receivers = tuple(
            rf"{receiver}\s*\.\s*prototype" for receiver in class_receivers_tuple
        )
        direct_instance_receivers = tuple(
            rf"new\s+{receiver}\s*\([^)]*\)" for receiver in class_receivers_tuple
        )
        instance_call_receivers = (
            *instance_receivers,
            *prototype_receivers,
            *direct_instance_receivers,
        )
        class_source = scan_text[class_start + 1 : class_end - 1]
        for method in method_pattern.finditer(
            scan_text,
            class_start + 1,
            class_end - 1,
        ):
            if not direct_class_member(class_start, method.start()):
                continue
            body_start = scan_text.find("{", method.start(), method.end())
            try:
                body_end = _skip_balanced(text, body_start)
            except FrontendInventoryError:
                continue
            method_name = method.group("name")
            class_execution_source = (
                scan_text[class_start + 1 : body_start]
                + " " * (body_end - body_start)
                + scan_text[body_end : class_end - 1]
            )
            class_execution_text = (
                text[class_start + 1 : body_start]
                + " " * (body_end - body_start)
                + text[body_end : class_end - 1]
            )
            if method_name == "constructor" and instantiated:
                continue
            if instantiated and not method.group("static"):
                # Once an instance escapes the exact local binding shape, any
                # method may be reached through a factory or container. Keep
                # instance method identity conservatively rather than masking it.
                continue
            if method.group("static"):
                if class_object_referenced:
                    # A class object can escape through aliases, containers, or
                    # opaque calls. Retain every static method once referenced.
                    continue
                if member_used(
                    external_source,
                    class_receivers_tuple,
                    method_name,
                    require_call=False,
                    raw_source=external_text,
                ) or member_used(
                    class_execution_source,
                    (r"this", class_pattern_text),
                    method_name,
                    require_call=False,
                    raw_source=class_execution_text,
                ):
                    continue
            elif instance_call_receivers and member_used(
                external_source,
                instance_call_receivers,
                method_name,
                require_call=False,
                raw_source=external_text,
            ):
                continue
            elif instantiated and member_used(
                class_execution_source,
                (r"this",),
                method_name,
                require_call=False,
                raw_source=class_execution_text,
            ):
                continue
            mask[body_start:body_end] = b"\x00" * (body_end - body_start)
        for field in field_arrow_pattern.finditer(
            scan_text,
            class_start + 1,
            class_end - 1,
        ):
            if not direct_class_member(class_start, field.start()):
                continue
            body_start = _skip_static_trivia(text, field.end())
            try:
                if body_start < len(text) and text[body_start] == "{":
                    body_end = _skip_balanced(text, body_start)
                else:
                    semicolon = scan_text.find(";", body_start, class_end)
                    newline = scan_text.find("\n", body_start, class_end)
                    endings = [end for end in (semicolon, newline) if end >= 0]
                    body_end = min(endings) if endings else class_end - 1
            except FrontendInventoryError:
                continue
            field_name = field.group("name")
            if field.group("static"):
                if class_object_referenced:
                    continue
                if member_used(
                    external_source,
                    (class_pattern_text,),
                    field_name,
                    require_call=True,
                    raw_source=external_text,
                ) or member_used(
                    class_source,
                    (r"this", class_pattern_text),
                    field_name,
                    require_call=True,
                    raw_source=text[class_start + 1 : class_end - 1],
                ):
                    continue
            elif instance_call_receivers and member_used(
                external_source,
                instance_call_receivers,
                field_name,
                require_call=True,
                raw_source=external_text,
            ):
                continue
            elif instantiated and member_used(
                class_source,
                (r"this",),
                field_name,
                require_call=True,
                raw_source=text[class_start + 1 : class_end - 1],
            ):
                continue
            mask[body_start:body_end] = b"\x00" * (body_end - body_start)
    return bytes(mask)


def _module_initializer_code_mask(
    text: str,
    *,
    preserve_literals: bool = False,
) -> bytearray:
    """Return an isolated mutable view of cached exact-source initializer analysis."""

    return bytearray(
        _module_initializer_code_mask_bytes(
            text,
            preserve_literals=preserve_literals,
        )
    )


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
    _memo: dict[tuple[str, int], str] | None = None,
) -> str:
    if _memo is None:
        _memo = {}
    memo_key = (name, before_offset)
    if memo_key in _memo:
        return _memo[memo_key]

    def finish(source: str) -> str:
        if len(source.encode("utf-8")) > MAX_CONTEXT_HELPER_IDENTITY_BYTES:
            raise FrontendInventoryError(
                "frontend callback helper identity exceeds byte budget"
            )
        _memo[memo_key] = source
        return source

    def dependency_source(helper_name: str) -> str:
        return _static_collection_source(
            text,
            scan_text,
            helper_name,
            before_offset,
            import_binding_resolver,
            _seen_names=frozenset((*_seen_names, name)),
            _memo=_memo,
        )

    if name in _seen_names:
        raise FrontendInventoryError("frontend registration loop bindings are circular")
    if len(_seen_names) >= MAX_CONTEXT_FORWARDING_HELPERS:
        raise FrontendInventoryError(
            "frontend callback helper closure exceeds helper budget"
        )
    try:
        local_source = _const_initializer_source(
            text,
            scan_text,
            name,
            before_offset,
        )
    except FrontendInventoryError as exc:
        if not any(
            marker in str(exc)
            for marker in (
                "binding is dynamic",
                "unproven use before collection",
            )
        ):
            raise
        local_source = None
    if local_source is not None:
        return finish(local_source)

    function_pattern = re.compile(
        rf"\b(?:async\s+)?function\s*\*?\s*{re.escape(name)}\s*"
        r"(?P<parameters>\()"
    )
    functions = list(function_pattern.finditer(scan_text))
    if len(functions) == 1:
        function = functions[0]
        parameters_end = _skip_balanced(text, function.start("parameters"))
        body_start = _function_body_after_parameters(text, scan_text, parameters_end)
        if body_start is None:
            raise FrontendInventoryError(
                "frontend registration loop binding is invalid"
            )
        body_end = _skip_balanced(text, body_start)
        intervening = (
            scan_text[body_end:before_offset]
            if body_end <= before_offset
            else scan_text[:before_offset]
        )
        if re.search(
            rf"(?<![.\w$]){re.escape(name)}\s*=(?!=|>)",
            intervening,
        ):
            raise FrontendInventoryError(
                "frontend registration loop binding is mutated before collection"
            )
        function_source = _context_helper_identity_source(
            text[function.start() : body_end]
        )
        dependency_sources = tuple(
            dependency_source(helper_name)
            for helper_name in _context_forwarded_helper_names(function_source)
        )
        return finish("\n".join((function_source, *dependency_sources)))

    pattern = re.compile(rf"\bconst\s+{re.escape(name)}\b")
    matches = list(pattern.finditer(scan_text, 0, before_offset))
    if len(matches) == 1:
        match = matches[0]
        statement_end = -1
        cursor = match.end()
        while cursor < before_offset:
            if not scan_text[cursor] or scan_text[cursor].isspace():
                cursor += 1
                continue
            if text[cursor] in "\"'`":
                cursor = _skip_string(text, cursor)
                continue
            if text[cursor] in "([{":
                cursor = _skip_balanced(text, cursor)
                continue
            if text[cursor] == ";":
                statement_end = cursor
                break
            cursor += 1
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
        initializer = scan_text[match.end() : statement_end]
        equals = initializer.find("=")
        initializer_start = (
            _skip_static_trivia(
                text,
                match.end() + equals + 1,
            )
            if equals >= 0
            else statement_end
        )
        static_object = (
            alias is None
            and initializer_start < statement_end
            and text[initializer_start] == "{"
            and _skip_balanced(text, initializer_start) == statement_end
        )
        dynamic_callback = alias is None and _looks_like_frontend_callback(
            initializer.partition("=")[2].strip()
        )
        if alias is None and not dynamic_callback and not static_object:
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
        if (
            not static_object
            and not dynamic_callback
            and alias is None
            and re.search(rf"\b{escaped_name}\b", intervening)
        ):
            raise FrontendInventoryError(
                "frontend registration loop alias has an unproven use before collection"
            )
        if static_object:
            return finish(text[match.start() : statement_end + 1])
        if dynamic_callback:
            callback_source = text[match.start() : statement_end + 1]
            dependency_sources = tuple(
                dependency_source(helper_name)
                for helper_name in _context_forwarded_helper_names(callback_source)
            )
            return finish("\n".join((callback_source, *dependency_sources)))
        dependency_source = _static_collection_source(
            text,
            scan_text,
            alias.group("name"),
            match.start(),
            import_binding_resolver,
            _seen_names=frozenset((*_seen_names, name)),
            _memo=_memo,
        )
        return finish(f"{text[match.start() : statement_end + 1]}\n{dependency_source}")

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
    return finish(f"module={module}\nimported={imported_name}\n{imported_source}")


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
        comment_end = (
            _skip_comment(source, index)
            if index < len(source) and source[index] == "/"
            else index
        )
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
        comment_end = _skip_comment(text, index) if text[index] == "/" else index
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
    import_binding_resolver: ImportBindingResolver | None,
) -> tuple[tuple[int, int, str, str, tuple[str, ...]], ...]:
    names = "(?:" + "|".join(re.escape(name) for name in sorted(suite_api_names)) + ")"
    pattern = re.compile(rf"(?<![.\w$]){names}{TEST_MODIFIERS}\s*(?P<arguments>\()")
    contexts: list[tuple[int, int, str, str, tuple[str, ...]]] = []
    for match in pattern.finditer(scan_text):
        call_end = _skip_balanced(text, match.start("arguments"))
        arguments = _call_argument_ranges(text, match.start("arguments"))
        if len(arguments) not in {2, 3}:
            raise FrontendInventoryError(
                "frontend suite callback cannot be inventoried safely"
            )
        title_start = _skip_static_trivia(text, arguments[0][0])
        if title_start >= call_end or text[title_start] not in "\"'`":
            raise FrontendInventoryError(
                "frontend suite title cannot be inventoried safely"
            )
        title_end = _skip_string(text, title_start)
        if _skip_static_trivia(text, title_end) != arguments[0][1]:
            raise FrontendInventoryError(
                "frontend suite callback cannot be inventoried safely"
            )
        callback_index = 2 if len(arguments) == 3 else 1
        callback = _suite_callback_body(text, arguments[callback_index][0], call_end)
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
                _execution_posture_parts(
                    text[match.start() : call_end],
                    condition_binding_resolver=lambda name, offset=match.start(): (
                        _static_collection_source(
                            text,
                            scan_text,
                            name,
                            offset,
                            import_binding_resolver,
                        )
                    ),
                ),
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


def _local_setup_hook_postures(
    text: str,
    scan_text: str,
    suite_context_regions: tuple[tuple[int, int, str, str, tuple[str, ...]], ...],
    unproven_block_regions: tuple[tuple[int, int], ...],
    unproven_expression_regions: tuple[tuple[int, int], ...],
    import_binding_resolver: ImportBindingResolver | None,
) -> tuple[tuple[int, int, str], ...]:
    """Bind reachable Vitest setup hooks to the suite region they affect."""

    def local_declaration_source(name: str, before_offset: int) -> str | None:
        pattern = re.compile(
            rf"\b(?P<kind>const|let|var)\s+{re.escape(name)}\b"
        )
        matches = list(pattern.finditer(scan_text, 0, before_offset))
        if not matches:
            return None
        if len(matches) != 1:
            raise FrontendInventoryError(
                "frontend setup hook binding is ambiguous"
            )
        match = matches[0]
        cursor = match.end()
        while cursor < before_offset:
            if text[cursor] in "\"'`":
                cursor = _skip_string(text, cursor)
                continue
            if text[cursor] in "([{":
                cursor = _skip_balanced(text, cursor)
                continue
            if scan_text[cursor] == ";":
                return text[match.start() : cursor + 1]
            if scan_text[cursor] in "\r\n":
                return text[match.start() : cursor]
            cursor += 1
        raise FrontendInventoryError(
            "frontend setup hook binding cannot be resolved safely"
        )

    def local_function_source(name: str, before_offset: int) -> str | None:
        pattern = re.compile(
            rf"\b(?:async\s+)?function\s*\*?\s*{re.escape(name)}\s*"
            r"(?P<parameters>\()"
        )
        matches = list(pattern.finditer(scan_text, 0, before_offset))
        if not matches:
            return None
        if len(matches) != 1:
            raise FrontendInventoryError(
                "frontend setup hook binding is ambiguous"
            )
        match = matches[0]
        parameters_end = _skip_balanced(text, match.start("parameters"))
        body_start = _function_body_after_parameters(
            text,
            scan_text,
            parameters_end,
        )
        if body_start is None or body_start >= before_offset:
            raise FrontendInventoryError(
                "frontend setup hook binding cannot be resolved safely"
            )
        return text[match.start() : _skip_balanced(text, body_start)]

    def setup_binding_source(name: str, before_offset: int) -> str:
        imported = _import_binding(text, scan_text, name, before_offset)
        if imported is not None:
            module, imported_name = imported
            resolved = (
                import_binding_resolver(module, imported_name)
                if module.startswith(".") and import_binding_resolver is not None
                else None
            )
            return "\n".join(
                part
                for part in (
                    f"module={module}",
                    f"imported={imported_name}",
                    resolved,
                )
                if part
            )
        declaration = local_declaration_source(name, before_offset)
        if declaration is not None:
            return declaration
        function = local_function_source(name, before_offset)
        if function is not None:
            return function
        if name in {
            "Array",
            "Blob",
            "BodyInit",
            "Boolean",
            "Date",
            "Error",
            "FormData",
            "Headers",
            "JSON",
            "Map",
            "Math",
            "Number",
            "Object",
            "Promise",
            "RegExp",
            "Request",
            "Response",
            "ResponseInit",
            "Set",
            "String",
            "URL",
            "URLSearchParams",
            "clearInterval",
            "clearTimeout",
            "console",
            "crypto",
            "document",
            "fetch",
            "localStorage",
            "navigator",
            "queueMicrotask",
            "sessionStorage",
            "setInterval",
            "setTimeout",
            "structuredClone",
            "window",
        }:
            return f"host-global={name}"
        raise FrontendInventoryError(
            "frontend setup hook binding cannot be resolved safely"
        )

    hook_names = {
        "afterAll",
        "afterEach",
        "aroundEach",
        "beforeAll",
        "beforeEach",
    }
    for bindings, module in _named_imports(text, scan_text):
        for imported, local in bindings:
            if imported in hook_names:
                if module not in RUNNER_MODULES:
                    raise FrontendInventoryError(
                        "frontend setup hook is shadowed by a non-runner import"
                    )
                hook_names.add(local)
            elif local in hook_names:
                raise FrontendInventoryError(
                    "frontend setup hook is shadowed by a non-runner import"
                )
    changed = True
    while changed:
        changed = False
        source_pattern = (
            "(?:" + "|".join(re.escape(name) for name in sorted(hook_names)) + ")"
        )
        for alias_match in re.finditer(
            rf"(?<![.\w$])(?:const|let|var)\s+"
            rf"(?P<alias>{TEST_API_NAME})(?:\s*:\s*[^=;\r\n]+)?\s*=\s*"
            rf"\(*\s*(?P<source>{source_pattern})\s*\)*[ \t]*"
            rf"(?:;|(?=\r?\n|$))",
            scan_text,
        ):
            alias = alias_match.group("alias")
            if alias not in hook_names:
                hook_names.add(alias)
                changed = True
        for alias_match in re.finditer(
            rf"(?<![.\w$])(?P<alias>{TEST_API_NAME})\s*=\s*(?!=)"
            rf"\(*\s*(?P<source>{source_pattern})\s*\)*[ \t]*"
            rf"(?:;|(?=\r?\n|$))",
            scan_text,
        ):
            alias = alias_match.group("alias")
            if alias not in hook_names:
                hook_names.add(alias)
                changed = True
    source_pattern = (
        "(?:" + "|".join(re.escape(name) for name in sorted(hook_names)) + ")"
    )
    for binding_match in re.finditer(
        rf"(?<![.\w$])(?P<alias>{TEST_API_NAME})"
        rf"(?:\s*:\s*[^=;\r\n]+)?\s*=\s*(?!=)"
        rf"(?P<value>[^;\r\n]+?)[ \t]*(?:;|(?=\r?\n|$))",
        scan_text,
    ):
        if binding_match.group("alias") not in hook_names:
            continue
        if re.fullmatch(
            rf"\s*\(*\s*{source_pattern}\s*\)*\s*",
            binding_match.group("value"),
        ) is None:
            raise FrontendInventoryError(
                "frontend setup hook alias shadowing cannot be inventoried safely"
            )
    hook_pattern = (
        "(?:" + "|".join(re.escape(name) for name in sorted(hook_names)) + ")"
    )
    posture_regions: list[tuple[int, int, str]] = []
    for match in re.finditer(
        rf"(?<![.\w$]){hook_pattern}\s*(?P<arguments>\()",
        scan_text,
    ):
        prefix = scan_text[max(0, match.start() - 32) : match.start()]
        if re.search(r"\bfunction\s*$", prefix) is not None:
            continue
        if any(
            start < match.start() < end for start, end in unproven_block_regions
        ) or any(
            start <= match.start() < end
            for start, end in unproven_expression_regions
        ):
            continue
        call_end = _skip_balanced(text, match.start("arguments"))
        source = _normalized_javascript_expression(text[match.start() : call_end])
        arguments = _call_argument_ranges(text, match.start("arguments"))
        if not arguments:
            raise FrontendInventoryError(
                "frontend setup hook callback cannot be inventoried safely"
            )
        callback_source = text[arguments[0][0] : arguments[0][1]]
        callback_parameters = set(_frontend_callback_parameters(callback_source))
        local_bindings = set(
            re.findall(
                rf"\b(?:const|let|var|function|class)\s+(?P<name>{TEST_API_NAME})",
                callback_source,
            )
        )
        local_bindings.update(
            re.findall(
                rf"\bcatch\s*\(\s*(?P<name>{TEST_API_NAME})",
                callback_source,
            )
        )
        for parameters in re.findall(
            r"\(([^()]*)\)\s*(?:=>|(?::\s*[^{}]+)?\{)",
            callback_source,
        ):
            for parameter in parameters.split(","):
                parameter_name = re.match(
                    rf"\s*\.\.\.\s*(?P<rest>{TEST_API_NAME})"
                    rf"|\s*(?P<plain>{TEST_API_NAME})",
                    parameter,
                )
                if parameter_name is not None:
                    local_bindings.add(
                        parameter_name.group("rest")
                        or parameter_name.group("plain")
                    )
        local_bindings.update(
            re.findall(
                rf"\b(?P<name>{TEST_API_NAME})\s*\([^()]*(?:\([^()]*\)[^()]*)*\)"
                r"\s*(?::\s*[^{}]+)?\{",
                callback_source,
            )
        )
        javascript_keywords = {
            "async",
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
            "finally",
            "for",
            "function",
            "if",
            "in",
            "let",
            "of",
            "return",
            "static",
            "super",
            "switch",
            "throw",
            "try",
            "var",
            "while",
            "yield",
        }
        binding_parts: list[str] = []
        for name in _javascript_binding_names(
            callback_source,
            ignore_object_keys=True,
        ):
            if (
                name in callback_parameters
                or name in local_bindings
                or name in javascript_keywords
            ):
                continue
            binding_source = setup_binding_source(name, match.start())
            binding_parts.append(f"binding:{name}={binding_source}")
        if binding_parts:
            source = "\n".join((source, *binding_parts))
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        posture = f"local-hook:sha256:{digest}"
        containing_suites = tuple(
            (start, end)
            for start, end, _title, _source, _posture in suite_context_regions
            if start < match.start() < end
        )
        scope_start, scope_end = (
            min(containing_suites, key=lambda region: region[1] - region[0])
            if containing_suites
            else (0, len(text) + 1)
        )
        region = (scope_start, scope_end, posture)
        if region not in posture_regions:
            posture_regions.append(region)
    return tuple(posture_regions)


def _applicable_setup_hook_postures(
    posture_regions: tuple[tuple[int, int, str], ...],
    offset: int,
) -> tuple[str, ...]:
    return tuple(
        posture for start, end, posture in posture_regions if start < offset < end
    )


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
            prefix_end = index
            while prefix_end > 0 and scan_text[prefix_end - 1].isspace():
                prefix_end -= 1
            follows_callback_or_call = scan_text[
                max(0, prefix_end - 2) : prefix_end
            ] == "=>" or (prefix_end > 0 and scan_text[prefix_end - 1] == ")")
            is_block = character == "{" and (
                follows_callback_or_call or not inside_expression()
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
    if re.search(r"\bimport\s*\.\s*meta\s*\.\s*glob\b", scan_text):
        raise FrontendInventoryError(
            "frontend glob registration import cannot be inventoried safely"
        )
    global_object = r"(?:globalThis|\(\s*globalThis(?:\s+as\s+[^()]*)?\s*\))"
    computed_dynamic_code = re.compile(
        rf"{global_object}\s*(?:\?\.\s*)?\[\s*"
        r"['\"](?:eval|Function)['\"]\s*\]"
    )
    if re.search(r"\b(?:eval|Function)\b", scan_text) or any(
        scan_text[match.start()] == text[match.start()]
        for match in computed_dynamic_code.finditer(text)
    ):
        raise FrontendInventoryError(
            "dynamic frontend test registration cannot be inventoried safely"
        )
    if re.search(r"\brequire\b", scan_text):
        raise FrontendInventoryError(
            "frontend CommonJS registration dependency cannot be inventoried safely"
        )
    test_api_names = _test_api_names(text, scan_text)
    extended_test_api_postures = _extended_test_api_postures(
        text,
        scan_text,
        test_api_names,
        import_binding_resolver,
    )
    if _has_indirect_runner_invocation(
        text,
        scan_text,
        names=test_api_names,
    ):
        raise FrontendInventoryError(
            "indirect frontend test registration cannot be inventoried safely"
        )
    direct_pattern, each_pattern, conditional_pattern = _patterns(test_api_names)
    test_api_pattern = (
        "(?:" + "|".join(re.escape(name) for name in sorted(test_api_names)) + ")"
    )
    if re.search(
        rf"(?<![.\w$]){test_api_pattern}{TEST_MODIFIERS}\s*<",
        scan_text,
    ):
        raise FrontendInventoryError(
            "generic frontend test registration cannot be inventoried safely"
        )
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
        import_binding_resolver,
    )
    (
        unproven_block_regions,
        unproven_expression_regions,
    ) = _unproven_registration_regions(
        text,
        scan_text,
        suite_context_regions,
    )
    local_setup_postures = _local_setup_hook_postures(
        text,
        scan_text,
        suite_context_regions,
        unproven_block_regions,
        unproven_expression_regions,
        import_binding_resolver,
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
    runtime_imports = frontend_runtime_import_modules(text)
    if runtime_imports and import_binding_resolver is None:
        raise FrontendInventoryError(
            "frontend runtime import initialization cannot be inventoried safely"
        )
    module_initialization_postures: list[str] = []
    for module in runtime_imports:
        assert import_binding_resolver is not None
        initialization_source = import_binding_resolver(
            module,
            MODULE_INITIALIZER_BINDING,
        )
        if initialization_source is None:
            raise FrontendInventoryError(
                "frontend runtime import initialization cannot be inventoried safely"
            )
        if initialization_source == MODULE_INITIALIZER_INERT:
            continue
        digest = hashlib.sha256(initialization_source.encode("utf-8")).hexdigest()
        module_initialization_postures.append(f"module-initializer:sha256:{digest}")

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
                            *module_initialization_postures,
                            *_applicable_extended_test_api_postures(
                                extended_test_api_postures,
                                scan_text,
                                match.start(),
                            ),
                            *_applicable_setup_hook_postures(
                                local_setup_postures,
                                match.start(),
                            ),
                            *context.execution_postures,
                            *_execution_posture_parts(
                                declaration_source,
                                condition_binding_resolver=lambda name, offset=match.start(): (
                                    _static_collection_source(
                                        text,
                                        scan_text,
                                        name,
                                        offset,
                                        import_binding_resolver,
                                    )
                                ),
                            ),
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
                            *module_initialization_postures,
                            *_applicable_extended_test_api_postures(
                                extended_test_api_postures,
                                scan_text,
                                offset,
                            ),
                            *_applicable_setup_hook_postures(
                                local_setup_postures,
                                offset,
                            ),
                            *context.execution_postures,
                            *_execution_posture_parts(
                                declaration_source,
                                condition_binding_resolver=lambda name, declaration_offset=offset: (
                                    _static_collection_source(
                                        text,
                                        scan_text,
                                        name,
                                        declaration_offset,
                                        import_binding_resolver,
                                    )
                                ),
                            ),
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
                            *module_initialization_postures,
                            *_applicable_extended_test_api_postures(
                                extended_test_api_postures,
                                scan_text,
                                offset,
                            ),
                            *_applicable_setup_hook_postures(
                                local_setup_postures,
                                offset,
                            ),
                            *context.execution_postures,
                            *_execution_posture_parts(
                                declaration_source,
                                condition_binding_resolver=lambda name, declaration_offset=offset: (
                                    _static_collection_source(
                                        text,
                                        scan_text,
                                        name,
                                        declaration_offset,
                                        import_binding_resolver,
                                    )
                                ),
                            ),
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
