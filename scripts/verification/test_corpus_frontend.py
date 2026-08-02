"""Bounded static inventory for supported frontend test declarations."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable


TEST_API_NAME = r"[A-Za-z_$][\w$]*"
TEST_MODIFIERS = r"(?:\s*\.(?:concurrent|fail|fails|fixme|only|sequential|skip|todo))*"
RUNNER_MODULES = {"vitest", "@playwright/test"}
IMPORT_PATTERN = re.compile(
    r"\bimport\s*\{(?P<members>[^}]*)\}\s*from\s*"
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

    declaration_pattern = re.compile(
        r"\b(?:const|let|var|function|class)\s+(?P<name>it|test)\b"
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
            if local in {"it", "test"}:
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
        if re.search(r"\b(?:it|test)\b", match.group("bindings")):
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
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        declarations.append(
            (
                match.start(),
                text[title_start:title_end],
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
        dependencies = {
            match.group("name")
            for pattern in (
                re.compile(rf"\.\.\.\s*(?P<name>{TEST_API_NAME})\s*(?=[,\]}}])"),
                re.compile(
                    rf"(?<![.\w$])(?P<name>{TEST_API_NAME})\s*\."
                    r"(?:concat|filter|flatMap|map|slice)\b"
                ),
            )
            for match in pattern.finditer(expression_scan)
        }
        if not dependencies:
            return parameter_data
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
    """Return relative named-import module specifiers from executable code."""

    code_mask = _code_mask(text)
    scan_text = "".join(
        character if code_mask[index] else " " for index, character in enumerate(text)
    )
    return tuple(
        match.group("module")
        for match in IMPORT_PATTERN.finditer(text)
        if match.group("module").startswith(".")
        and scan_text[match.start() : match.start() + len("import")] == "import"
    )


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
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        declarations.append(
            (
                match.start(),
                text[title_start:title_end],
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
            rf"\b{escaped_name}\s*(?:\[[^;\n]*\]|\.[A-Za-z_$][\w$]*)?\s*"
            r"(?:[+\-*/%]=|&&=|\|\|=|\?\?=|=(?!=|>)|\+\+|--)",
            intervening,
        ):
            raise FrontendInventoryError(
                "frontend registration loop binding is mutated before collection"
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
        while candidate < len(collection_source) and collection_source[
            candidate
        ].isspace():
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
            if item:
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


def _registration_context_source(
    text: str,
    scan_text: str,
    offset: int,
    import_binding_resolver: ImportBindingResolver | None,
) -> tuple[str, ...]:
    range_patterns = (
        re.compile(rf"\b(?:async\s+)?function\s+{TEST_API_NAME}\s*\([^)]*\)\s*\{{"),
        re.compile(
            rf"\b(?:const|let|var)\s+{TEST_API_NAME}\s*=\s*"
            r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*\{"
        ),
        re.compile(r"\b(?:while|if|switch|catch)\s*\([^)]*\)\s*\{"),
        re.compile(r"\b(?:do|try|finally)\s*\{"),
    )
    for pattern in range_patterns:
        for match in pattern.finditer(scan_text, 0, offset):
            opening = scan_text.find("{", match.start(), match.end())
            if opening < 0:
                continue
            if offset < _skip_balanced(text, opening):
                raise FrontendInventoryError(
                    "frontend test registration context cannot be inventoried safely"
                )

    context_sources = [""]
    for match in re.compile(r"\bfor\s*\(").finditer(scan_text, 0, offset):
        header_end = _skip_balanced(text, match.end() - 1)
        body_start = header_end
        while body_start < len(text) and text[body_start].isspace():
            body_start += 1
        if body_start >= len(text) or text[body_start] != "{":
            continue
        body_end = _skip_balanced(text, body_start)
        if not (body_start < offset < body_end):
            continue
        header = scan_text[match.start() : header_end]
        binding = re.fullmatch(
            rf"for\s*\(\s*const\s+(?:{TEST_API_NAME}|\[[^\[\]]+\])\s+of\s+"
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
        context_sources = [
            f"{existing}\n{text[match.start() : header_end]}\nitem={item}".strip()
            for existing in context_sources
            for item in items
        ]
    return tuple(context_sources)


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
    direct_pattern, each_pattern, conditional_pattern = _patterns(
        _test_api_names(text, scan_text)
    )
    if re.search(
        rf"(?<![.\w$])(?:describe|suite){TEST_MODIFIERS}\.(?:each|for)\b",
        scan_text,
    ):
        raise FrontendInventoryError(
            "frontend parameterized suites cannot be inventoried safely"
        )

    def context_bound_ref(raw_ref: str, context_source: str) -> str:
        if not context_source:
            return raw_ref
        digest = hashlib.sha256(context_source.encode("utf-8")).hexdigest()
        return f"{raw_ref}::registration-context-sha256:{digest}"

    for match in direct_pattern.finditer(scan_text):
        context_sources = _registration_context_source(
            text,
            scan_text,
            match.start(),
            import_binding_resolver,
        )
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
        title_start = index + 1
        title_end = _skip_string(text, index) - 1
        title = _normalized_title(text[title_start:title_end])
        if not title or len(title) > 500 or re.search(r"#\d+$", title):
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        declaration_source = text[match.start() : declaration_end]
        for context_source in context_sources:
            bound_source = declaration_source
            if context_source:
                bound_source = f"{bound_source}\n{context_source}"
            raw_entries.append(
                (
                    match.start(),
                    context_bound_ref(f"{path}::{title}", context_source),
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
        context_sources = _registration_context_source(
            text,
            scan_text,
            offset,
            import_binding_resolver,
        )
        title = _normalized_title(raw_title)
        if not title or len(title) > 500 or re.search(r"#\d+$", title):
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        bound_data = _bound_parameter_data(
            text,
            scan_text,
            parameter_data,
            offset,
            import_binding_resolver,
            parameter_call_ranges,
        )
        digest = hashlib.sha256(bound_data.encode("utf-8")).hexdigest()
        for context_source in context_sources:
            bound_source = declaration_source
            if context_source:
                bound_source = f"{bound_source}\n{context_source}"
            raw_entries.append(
                (
                    offset,
                    context_bound_ref(
                        f"{path}::{title}::parameters-sha256:{digest}",
                        context_source,
                    ),
                    bound_source,
                )
            )
    for offset, raw_title, declaration_source in _conditional_declarations(
        text, scan_text, conditional_pattern
    ):
        context_sources = _registration_context_source(
            text,
            scan_text,
            offset,
            import_binding_resolver,
        )
        title = _normalized_title(raw_title)
        if not title or len(title) > 500 or re.search(r"#\d+$", title):
            raise FrontendInventoryError(f"frontend test title is invalid: {path}")
        for context_source in context_sources:
            bound_source = declaration_source
            if context_source:
                bound_source = f"{bound_source}\n{context_source}"
            raw_entries.append(
                (
                    offset,
                    context_bound_ref(f"{path}::{title}", context_source),
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
