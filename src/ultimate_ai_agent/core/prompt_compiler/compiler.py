"""Fail-closed deterministic compiler for repository-owned prompt modules."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from pydantic import ValidationError

from ultimate_ai_agent.core.prompt_compiler.contracts import (
    PromptCompilationArtifact,
    PromptCompilationReceipt,
    PromptGraphInspection,
    PromptModuleDefinition,
    PromptModuleManifest,
    PromptModuleSourceReceipt,
    PromptVariableDefinition,
    PromptVariableType,
    variable_value_matches_type,
)

HASH_PREFIX = "sha256:"
_VARIABLE_PATTERN = re.compile(r"{{\s*([a-z][a-z0-9_]{0,79})\s*}}")
_VARIABLE_TOKEN_PATTERN = re.compile(r"{{|}}")
_CONDITIONAL_PATTERN = re.compile(
    r"{%\s*if\s+([a-z][a-z0-9_]{0,79})\s*%}"
    r"(.*?)"
    r"(?:{%\s*else\s*%}(.*?))?"
    r"{%\s*endif\s*%}",
    flags=re.DOTALL,
)
_CONTROL_TOKEN_PATTERN = re.compile(r"{%|%}")


class PromptCompilationError(RuntimeError):
    """A safe, stable compilation failure."""

    def __init__(self, reason_code: str, safe_message: str) -> None:
        super().__init__(safe_message)
        self.reason_code = reason_code
        self.safe_message = safe_message


class PromptModuleCompiler:
    """Compile a strict prompt-module graph without executing tools or models."""

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root.resolve()
        if not self._root.is_dir():
            raise PromptCompilationError(
                "PROMPT_COMPILER_ROOT_INVALID",
                "Prompt compiler repository root is unavailable.",
            )

    def load_manifest(self, manifest_path: Path) -> PromptModuleManifest:
        path = self._resolve_manifest_path(manifest_path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return PromptModuleManifest.model_validate(payload)
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            raise PromptCompilationError(
                "PROMPT_MANIFEST_INVALID",
                "Prompt module manifest validation failed safely.",
            ) from exc

    def inspect(
        self,
        manifest: PromptModuleManifest,
        *,
        entry_module_ids: Iterable[str] | None = None,
        changed_module_ids: Iterable[str] = (),
    ) -> PromptGraphInspection:
        module_by_id = self._validated_graph(manifest)
        entries = self._entry_ids(manifest, entry_module_ids, module_by_id)
        ordered = self._topological_closure(entries, module_by_id)
        reverse = self._reverse_dependencies(module_by_id)
        changed = sorted(set(changed_module_ids))
        unknown_changed = [
            module_id for module_id in changed if module_id not in module_by_id
        ]
        if unknown_changed:
            raise PromptCompilationError(
                "PROMPT_CHANGED_MODULE_UNKNOWN",
                "Blast-radius inspection references an unknown prompt module.",
            )
        impacted = self._reverse_closure(changed, reverse)
        return PromptGraphInspection(
            bundle_id=manifest.bundle_id,
            entry_module_ids=entries,
            resolved_module_ids=ordered,
            manifest_contract_hash=_canonical_hash(
                manifest.model_dump(mode="json", by_alias=True)
            ),
            dependency_graph_hash=self._graph_hash(manifest, module_by_id),
            dependencies={
                module_id: sorted(module.dependencies)
                for module_id, module in sorted(module_by_id.items())
            },
            reverse_dependencies=reverse,
            impacted_module_ids=impacted,
        )

    def compile(
        self,
        manifest: PromptModuleManifest,
        *,
        variables: dict[str, Any] | None = None,
        entry_module_ids: Iterable[str] | None = None,
    ) -> PromptCompilationArtifact:
        supplied = dict(variables or {})
        module_by_id = self._validated_graph(manifest)
        entries = self._entry_ids(manifest, entry_module_ids, module_by_id)
        ordered_ids = self._topological_closure(entries, module_by_id)
        bindings = self._validate_bindings(manifest.variables, supplied)
        self._validate_selected_variables(
            manifest=manifest,
            ordered_ids=ordered_ids,
            module_by_id=module_by_id,
            bindings=bindings,
        )

        source_receipts: list[PromptModuleSourceReceipt] = []
        compiled_chunks = [
            "# Compiled UAA Prompt Module Bundle\n\n",
            f"Bundle id: `{manifest.bundle_id}`\n",
            f"Bundle version: `{manifest.version}`\n\n",
            "Generated deterministically from repository-owned modules.\n\n",
        ]
        for module_id in ordered_ids:
            module = module_by_id[module_id]
            source_bytes = self._read_source(module, manifest.max_module_bytes)
            try:
                source_text = source_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise PromptCompilationError(
                    "PROMPT_MODULE_ENCODING_INVALID",
                    "A prompt module is not valid UTF-8.",
                ) from exc
            rendered = self._render(source_text, manifest.variables, bindings)
            source_receipts.append(
                PromptModuleSourceReceipt(
                    module_id=module_id,
                    source_ref=module.source_ref,
                    source_hash=_sha256(source_bytes),
                    source_bytes=len(source_bytes),
                )
            )
            compiled_chunks.append(f"<!-- BEGIN {module_id} {module.source_ref} -->\n")
            compiled_chunks.append(rendered)
            if not rendered.endswith("\n"):
                compiled_chunks.append("\n")
            compiled_chunks.append(f"<!-- END {module_id} -->\n\n")

        content = "".join(compiled_chunks).removesuffix("\n")
        compiled_bytes = content.encode("utf-8")
        if len(compiled_bytes) > manifest.max_compiled_bytes:
            raise PromptCompilationError(
                "PROMPT_COMPILED_BUDGET_EXCEEDED",
                "Compiled prompt exceeds its configured byte budget.",
            )

        receipt = PromptCompilationReceipt(
            receipt_version="uaa.prompt_compilation_receipt.v1",
            bundle_id=manifest.bundle_id,
            bundle_version=manifest.version,
            entry_module_ids=entries,
            ordered_module_ids=ordered_ids,
            source_receipts=source_receipts,
            manifest_contract_hash=_canonical_hash(
                manifest.model_dump(mode="json", by_alias=True)
            ),
            dependency_graph_hash=self._graph_hash(manifest, module_by_id),
            variable_contract_hash=self._variable_contract_hash(manifest.variables),
            supplied_variable_names=sorted(supplied),
            compiled_artifact_hash=_sha256(compiled_bytes),
            compiled_bytes=len(compiled_bytes),
            raw_prompt_included=False,
            variable_values_included=False,
            runtime_model_calls=False,
            automatic_skill_loading=False,
            automatic_pr_creation=False,
            execution_authority="none",
        )
        return PromptCompilationArtifact(content=content, receipt=receipt)

    def compile_file(
        self,
        manifest_path: Path,
        *,
        variables: dict[str, Any] | None = None,
        entry_module_ids: Iterable[str] | None = None,
    ) -> PromptCompilationArtifact:
        return self.compile(
            self.load_manifest(manifest_path),
            variables=variables,
            entry_module_ids=entry_module_ids,
        )

    def _resolve_manifest_path(self, manifest_path: Path) -> Path:
        candidate = manifest_path
        if not candidate.is_absolute():
            candidate = self._root / candidate
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(self._root)
        except (OSError, ValueError) as exc:
            raise PromptCompilationError(
                "PROMPT_MANIFEST_PATH_UNSAFE",
                "Prompt manifest must be a repository-contained file.",
            ) from exc
        if not resolved.is_file() or self._contains_symlink(candidate):
            raise PromptCompilationError(
                "PROMPT_MANIFEST_PATH_UNSAFE",
                "Prompt manifest must be a non-symlink repository-contained file.",
            )
        return resolved

    def _validated_graph(
        self,
        manifest: PromptModuleManifest,
    ) -> dict[str, PromptModuleDefinition]:
        module_by_id = {module.module_id: module for module in manifest.modules}
        known_variables = set(manifest.variables)
        for module in manifest.modules:
            if any(
                dependency not in module_by_id for dependency in module.dependencies
            ):
                raise PromptCompilationError(
                    "PROMPT_DEPENDENCY_MISSING",
                    "Prompt module dependency graph references an unknown module.",
                )
            if any(
                variable not in known_variables
                for variable in module.required_variables
            ):
                raise PromptCompilationError(
                    "PROMPT_REQUIRED_VARIABLE_UNDECLARED",
                    "Prompt module requires an undeclared variable.",
                )
        if any(entry not in module_by_id for entry in manifest.entry_module_ids):
            raise PromptCompilationError(
                "PROMPT_ENTRY_MODULE_MISSING",
                "Prompt manifest references an unknown entry module.",
            )
        self._assert_acyclic(module_by_id)
        return module_by_id

    @staticmethod
    def _assert_acyclic(module_by_id: dict[str, PromptModuleDefinition]) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in visiting:
                raise PromptCompilationError(
                    "PROMPT_DEPENDENCY_CYCLE",
                    "Prompt module dependency graph contains a cycle.",
                )
            if module_id in visited:
                return
            visiting.add(module_id)
            for dependency in sorted(module_by_id[module_id].dependencies):
                visit(dependency)
            visiting.remove(module_id)
            visited.add(module_id)

        for module_id in sorted(module_by_id):
            visit(module_id)

    @staticmethod
    def _entry_ids(
        manifest: PromptModuleManifest,
        requested: Iterable[str] | None,
        module_by_id: dict[str, PromptModuleDefinition],
    ) -> list[str]:
        entries = sorted(
            set(requested if requested is not None else manifest.entry_module_ids)
        )
        if not entries:
            raise PromptCompilationError(
                "PROMPT_ENTRY_MODULE_EMPTY",
                "At least one prompt entry module is required.",
            )
        if any(entry not in module_by_id for entry in entries):
            raise PromptCompilationError(
                "PROMPT_ENTRY_MODULE_MISSING",
                "Prompt compilation references an unknown entry module.",
            )
        return entries

    @staticmethod
    def _topological_closure(
        entries: list[str],
        module_by_id: dict[str, PromptModuleDefinition],
    ) -> list[str]:
        ordered: list[str] = []
        visited: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in visited:
                return
            for dependency in sorted(module_by_id[module_id].dependencies):
                visit(dependency)
            visited.add(module_id)
            ordered.append(module_id)

        for entry in entries:
            visit(entry)
        return ordered

    @staticmethod
    def _reverse_dependencies(
        module_by_id: dict[str, PromptModuleDefinition],
    ) -> dict[str, list[str]]:
        reverse: dict[str, list[str]] = defaultdict(list)
        for module_id, module in module_by_id.items():
            reverse.setdefault(module_id, [])
            for dependency in module.dependencies:
                reverse[dependency].append(module_id)
        return {
            module_id: sorted(dependents)
            for module_id, dependents in sorted(reverse.items())
        }

    @staticmethod
    def _reverse_closure(
        changed: Iterable[str],
        reverse: dict[str, list[str]],
    ) -> list[str]:
        impacted: set[str] = set()
        pending = list(changed)
        while pending:
            module_id = pending.pop()
            if module_id in impacted:
                continue
            impacted.add(module_id)
            pending.extend(reverse[module_id])
        return sorted(impacted)

    def _read_source(self, module: PromptModuleDefinition, max_bytes: int) -> bytes:
        ref = Path(module.source_ref)
        if ref.is_absolute() or ".." in ref.parts:
            raise PromptCompilationError(
                "PROMPT_SOURCE_PATH_UNSAFE",
                "Prompt source must be a repository-relative file.",
            )
        candidate = self._root / ref
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(self._root)
        except (OSError, ValueError) as exc:
            raise PromptCompilationError(
                "PROMPT_SOURCE_PATH_UNSAFE",
                "Prompt source must be a repository-contained file.",
            ) from exc
        if not resolved.is_file() or self._contains_symlink(candidate):
            raise PromptCompilationError(
                "PROMPT_SOURCE_PATH_UNSAFE",
                "Prompt source must be a non-symlink repository file.",
            )
        try:
            size = resolved.stat().st_size
            if size > max_bytes:
                raise PromptCompilationError(
                    "PROMPT_MODULE_BUDGET_EXCEEDED",
                    "A prompt module exceeds its configured byte budget.",
                )
            content = resolved.read_bytes()
            if len(content) > max_bytes:
                raise PromptCompilationError(
                    "PROMPT_MODULE_BUDGET_EXCEEDED",
                    "A prompt module exceeds its configured byte budget.",
                )
            return content
        except PromptCompilationError:
            raise
        except OSError as exc:
            raise PromptCompilationError(
                "PROMPT_SOURCE_UNAVAILABLE",
                "Prompt source could not be read safely.",
            ) from exc

    def _contains_symlink(self, candidate: Path) -> bool:
        try:
            relative = candidate.relative_to(self._root)
        except ValueError:
            return True
        current = self._root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return True
        return False

    @staticmethod
    def _validate_bindings(
        definitions: dict[str, PromptVariableDefinition],
        supplied: dict[str, Any],
    ) -> dict[str, str | int | bool | None]:
        if any(name not in definitions for name in supplied):
            raise PromptCompilationError(
                "PROMPT_VARIABLE_UNKNOWN",
                "Prompt compilation received an undeclared variable.",
            )
        bindings: dict[str, str | int | bool | None] = {}
        for name, definition in definitions.items():
            value = supplied.get(name, definition.default)
            if value is None:
                bindings[name] = None
                continue
            if not variable_value_matches_type(value, definition.type):
                raise PromptCompilationError(
                    "PROMPT_VARIABLE_TYPE_INVALID",
                    "Prompt variable does not match its declared type.",
                )
            if isinstance(value, str) and len(value) > definition.max_length:
                raise PromptCompilationError(
                    "PROMPT_VARIABLE_BUDGET_EXCEEDED",
                    "Prompt variable exceeds its declared length budget.",
                )
            if isinstance(value, str) and (
                _VARIABLE_TOKEN_PATTERN.search(value)
                or _CONTROL_TOKEN_PATTERN.search(value)
            ):
                raise PromptCompilationError(
                    "PROMPT_VARIABLE_CONTROL_TOKEN",
                    "Prompt variable contains a reserved template control token.",
                )
            if definition.allowed_values and value not in definition.allowed_values:
                raise PromptCompilationError(
                    "PROMPT_VARIABLE_VALUE_INVALID",
                    "Prompt variable is outside its declared allowed values.",
                )
            bindings[name] = value
        return bindings

    @staticmethod
    def _validate_selected_variables(
        *,
        manifest: PromptModuleManifest,
        ordered_ids: list[str],
        module_by_id: dict[str, PromptModuleDefinition],
        bindings: dict[str, str | int | bool | None],
    ) -> None:
        for module_id in ordered_ids:
            for name in module_by_id[module_id].required_variables:
                if bindings.get(name) is None:
                    raise PromptCompilationError(
                        "PROMPT_MODULE_VARIABLE_REQUIRED",
                        "Selected prompt module is missing a required variable.",
                    )
        if any(name not in manifest.variables for name in bindings):
            raise PromptCompilationError(
                "PROMPT_VARIABLE_UNKNOWN",
                "Prompt compilation received an undeclared variable.",
            )

    @staticmethod
    def _render(
        source: str,
        definitions: dict[str, PromptVariableDefinition],
        bindings: dict[str, str | int | bool | None],
    ) -> str:
        variable_refs = set(_VARIABLE_PATTERN.findall(source))
        conditional_refs = {
            match.group(1) for match in _CONDITIONAL_PATTERN.finditer(source)
        }
        if any(name not in definitions for name in variable_refs | conditional_refs):
            raise PromptCompilationError(
                "PROMPT_TEMPLATE_VARIABLE_UNDECLARED",
                "Prompt template references an undeclared variable.",
            )
        if any(
            definitions[name].required and bindings.get(name) is None
            for name in conditional_refs
        ):
            raise PromptCompilationError(
                "PROMPT_VARIABLE_REQUIRED",
                "Selected prompt template is missing a required variable.",
            )

        def render_conditional(match: re.Match[str]) -> str:
            name = match.group(1)
            definition = definitions[name]
            if definition.type is not PromptVariableType.boolean:
                raise PromptCompilationError(
                    "PROMPT_CONDITION_TYPE_INVALID",
                    "Prompt condition must reference a boolean variable.",
                )
            if _CONTROL_TOKEN_PATTERN.search(match.group(2)) or (
                match.group(3) and _CONTROL_TOKEN_PATTERN.search(match.group(3))
            ):
                raise PromptCompilationError(
                    "PROMPT_TEMPLATE_NESTING_UNSUPPORTED",
                    "Nested prompt template conditions are not supported.",
                )
            return (
                match.group(2) if bindings.get(name) is True else (match.group(3) or "")
            )

        rendered = _CONDITIONAL_PATTERN.sub(render_conditional, source)
        if _CONTROL_TOKEN_PATTERN.search(rendered):
            raise PromptCompilationError(
                "PROMPT_TEMPLATE_CONTROL_INVALID",
                "Prompt template contains an invalid control token.",
            )
        rendered_variable_refs = set(_VARIABLE_PATTERN.findall(rendered))
        if any(
            definitions[name].required and bindings.get(name) is None
            for name in rendered_variable_refs
        ):
            raise PromptCompilationError(
                "PROMPT_VARIABLE_REQUIRED",
                "Selected prompt template is missing a required variable.",
            )

        def render_variable(match: re.Match[str]) -> str:
            value = bindings.get(match.group(1))
            if value is None:
                return ""
            if isinstance(value, bool):
                return "true" if value else "false"
            return str(value)

        rendered = _VARIABLE_PATTERN.sub(render_variable, rendered)
        if _VARIABLE_TOKEN_PATTERN.search(rendered):
            raise PromptCompilationError(
                "PROMPT_TEMPLATE_VARIABLE_INVALID",
                "Prompt template contains an invalid variable token.",
            )
        return rendered

    @staticmethod
    def _graph_hash(
        manifest: PromptModuleManifest,
        module_by_id: dict[str, PromptModuleDefinition],
    ) -> str:
        payload = {
            "schema_version": manifest.schema_version,
            "bundle_id": manifest.bundle_id,
            "bundle_version": manifest.version,
            "entry_module_ids": sorted(manifest.entry_module_ids),
            "modules": [
                {
                    "module_id": module_id,
                    "source_ref": module.source_ref,
                    "kind": module.kind.value,
                    "stability_tier": module.stability_tier.value,
                    "dependencies": sorted(module.dependencies),
                    "required_variables": sorted(module.required_variables),
                }
                for module_id, module in sorted(module_by_id.items())
            ],
        }
        return _canonical_hash(payload)

    @staticmethod
    def _variable_contract_hash(
        definitions: dict[str, PromptVariableDefinition],
    ) -> str:
        payload = {
            name: definition.model_dump(mode="json")
            for name, definition in sorted(definitions.items())
        }
        return _canonical_hash(payload)


def _sha256(value: bytes) -> str:
    return f"{HASH_PREFIX}{hashlib.sha256(value).hexdigest()}"


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(encoded)
