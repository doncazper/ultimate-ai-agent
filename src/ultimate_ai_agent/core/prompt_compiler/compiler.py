"""Fail-closed deterministic compiler for repository-owned prompt modules."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
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
MAX_MANIFEST_BYTES = 1_048_576
_READ_CHUNK_BYTES = 65_536
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
_MODULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9._-]{0,79}$")


class PromptCompilationError(RuntimeError):
    """A safe, stable compilation failure."""

    def __init__(self, reason_code: str, safe_message: str) -> None:
        super().__init__(safe_message)
        self.reason_code = reason_code
        self.safe_message = safe_message


class PromptModuleCompiler:
    """Compile a strict prompt-module graph without executing tools or models."""

    def __init__(self, repository_root: Path) -> None:
        try:
            self._root = repository_root.resolve(strict=True)
            root_info = os.stat(self._root, follow_symlinks=False)
        except OSError as exc:
            raise PromptCompilationError(
                "PROMPT_COMPILER_ROOT_INVALID",
                "Prompt compiler repository root is unavailable.",
            ) from exc
        if not stat.S_ISDIR(root_info.st_mode):
            raise PromptCompilationError(
                "PROMPT_COMPILER_ROOT_INVALID",
                "Prompt compiler repository root is unavailable.",
            )
        self._root_identity = (root_info.st_dev, root_info.st_ino)

    def load_manifest(self, manifest_path: Path) -> PromptModuleManifest:
        try:
            encoded = self._read_repository_file(
                manifest_path,
                max_bytes=MAX_MANIFEST_BYTES,
                unsafe_code="PROMPT_MANIFEST_PATH_UNSAFE",
                unavailable_code="PROMPT_MANIFEST_UNAVAILABLE",
                budget_code="PROMPT_MANIFEST_BUDGET_EXCEEDED",
            )
            return PromptModuleManifest.model_validate_json(encoded, strict=True)
        except (
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
        manifest = self._revalidate_manifest(manifest)
        module_by_id, _source_bytes_by_id = self._validated_graph(manifest)
        entries = self._entry_ids(manifest, entry_module_ids, module_by_id)
        ordered = self._topological_closure(entries, module_by_id)
        reverse = self._reverse_dependencies(module_by_id)
        if isinstance(changed_module_ids, str):
            raise PromptCompilationError(
                "PROMPT_CHANGED_MODULE_INVALID",
                "Blast-radius inspection requires valid prompt module ids.",
            )
        requested_changed = list(changed_module_ids)
        if any(
            not isinstance(module_id, str)
            or _MODULE_ID_PATTERN.fullmatch(module_id) is None
            for module_id in requested_changed
        ):
            raise PromptCompilationError(
                "PROMPT_CHANGED_MODULE_INVALID",
                "Blast-radius inspection requires valid prompt module ids.",
            )
        if len(requested_changed) != len(set(requested_changed)):
            raise PromptCompilationError(
                "PROMPT_CHANGED_MODULE_DUPLICATE",
                "Blast-radius inspection module ids must be unique.",
            )
        changed = sorted(requested_changed)
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
        manifest = self._revalidate_manifest(manifest)
        supplied = dict(variables or {})
        module_by_id, source_bytes_by_id = self._validated_graph(manifest)
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
        compiled_chunks: list[str] = []
        compiled_size = 0

        def append_chunk(chunk: str) -> None:
            nonlocal compiled_size
            encoded_size = len(chunk.encode("utf-8"))
            # The final formatting step removes at most one trailing newline.
            if compiled_size + encoded_size > manifest.max_compiled_bytes + 1:
                raise PromptCompilationError(
                    "PROMPT_COMPILED_BUDGET_EXCEEDED",
                    "Compiled prompt exceeds its configured byte budget.",
                )
            compiled_chunks.append(chunk)
            compiled_size += encoded_size

        for header_chunk in (
            "# Compiled UAA Prompt Module Bundle\n\n",
            f"Bundle id: `{manifest.bundle_id}`\n",
            f"Bundle version: `{manifest.version}`\n\n",
            "Generated deterministically from repository-owned modules.\n\n",
        ):
            append_chunk(header_chunk)
        for module_id in ordered_ids:
            module = module_by_id[module_id]
            source_bytes = source_bytes_by_id[module_id]
            source_text = self._decode_source(source_bytes)
            begin_marker = f"<!-- BEGIN {module_id} {module.source_ref} -->\n"
            append_chunk(begin_marker)
            rendered = self._render(
                source_text,
                manifest.variables,
                bindings,
                max_bytes=manifest.max_compiled_bytes + 1 - compiled_size,
            )
            source_receipts.append(
                PromptModuleSourceReceipt(
                    module_id=module_id,
                    source_ref=module.source_ref,
                    source_hash=_sha256(source_bytes),
                    source_bytes=len(source_bytes),
                )
            )
            append_chunk(rendered)
            if not rendered.endswith("\n"):
                append_chunk("\n")
            append_chunk(f"<!-- END {module_id} -->\n\n")

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
            entry_module_ids=tuple(entries),
            ordered_module_ids=tuple(ordered_ids),
            source_receipts=tuple(source_receipts),
            manifest_contract_hash=_canonical_hash(
                manifest.model_dump(mode="json", by_alias=True)
            ),
            dependency_graph_hash=self._graph_hash(manifest, module_by_id),
            declared_source_contract_hash=self._declared_source_contract_hash(
                module_by_id,
                source_bytes_by_id,
            ),
            variable_contract_hash=self._variable_contract_hash(manifest.variables),
            supplied_variable_names=tuple(sorted(supplied)),
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

    @staticmethod
    def _revalidate_manifest(manifest: PromptModuleManifest) -> PromptModuleManifest:
        """Detach and revalidate mutable nested values before each operation."""

        try:
            payload = manifest.model_dump(mode="python", by_alias=True)
            return PromptModuleManifest.model_validate(payload, strict=True)
        except (AttributeError, TypeError, ValueError, ValidationError) as exc:
            raise PromptCompilationError(
                "PROMPT_MANIFEST_MUTATED",
                "Prompt module manifest changed after validation.",
            ) from exc

    def _validated_graph(
        self,
        manifest: PromptModuleManifest,
    ) -> tuple[
        dict[str, PromptModuleDefinition],
        dict[str, bytes],
    ]:
        module_ids = [module.module_id for module in manifest.modules]
        if len(module_ids) != len(set(module_ids)):
            raise PromptCompilationError(
                "PROMPT_MODULE_ID_DUPLICATE",
                "Prompt module ids must remain unique during compilation.",
            )
        module_by_id = {module.module_id: module for module in manifest.modules}
        source_bytes_by_id: dict[str, bytes] = {}
        known_variables = set(manifest.variables)
        for module in manifest.modules:
            raw_source_parts = module.source_ref.split("/")
            if any(part in {"", ".", ".."} for part in raw_source_parts):
                raise PromptCompilationError(
                    "PROMPT_SOURCE_PATH_UNSAFE",
                    "Prompt source must be a repository-relative file.",
                )
            source_ref = Path(module.source_ref)
            if not source_ref.parts or source_ref.is_absolute() or any(
                part in {"", ".", ".."} for part in source_ref.parts
            ):
                raise PromptCompilationError(
                    "PROMPT_SOURCE_PATH_UNSAFE",
                    "Prompt source must be a repository-relative file.",
                )
            source_bytes = self._read_repository_file(
                source_ref,
                max_bytes=manifest.max_module_bytes,
                unsafe_code="PROMPT_SOURCE_PATH_UNSAFE",
                unavailable_code="PROMPT_SOURCE_UNAVAILABLE",
                budget_code="PROMPT_MODULE_BUDGET_EXCEEDED",
            )
            source_text = self._decode_source(source_bytes)
            self._validate_template_contract(source_text, manifest.variables)
            source_bytes_by_id[module.module_id] = source_bytes
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
        return module_by_id, source_bytes_by_id

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
        if isinstance(requested, str):
            raise PromptCompilationError(
                "PROMPT_ENTRY_MODULE_INVALID",
                "Prompt compilation requires valid prompt entry module ids.",
            )
        requested_entries = list(
            requested if requested is not None else manifest.entry_module_ids
        )
        if any(
            not isinstance(entry, str) or _MODULE_ID_PATTERN.fullmatch(entry) is None
            for entry in requested_entries
        ):
            raise PromptCompilationError(
                "PROMPT_ENTRY_MODULE_INVALID",
                "Prompt compilation requires valid prompt entry module ids.",
            )
        if len(requested_entries) != len(set(requested_entries)):
            raise PromptCompilationError(
                "PROMPT_ENTRY_MODULE_DUPLICATE",
                "Prompt compilation entry modules must be unique.",
            )
        entries = sorted(requested_entries)
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

    @staticmethod
    def _decode_source(source_bytes: bytes) -> str:
        try:
            source_text = source_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PromptCompilationError(
                "PROMPT_MODULE_ENCODING_INVALID",
                "A prompt module is not valid UTF-8.",
            ) from exc
        if "\x00" in source_text:
            raise PromptCompilationError(
                "PROMPT_MODULE_CONTENT_INVALID",
                "A prompt module contains an unsupported control character.",
            )
        return source_text

    @staticmethod
    def _validate_template_contract(
        source: str,
        definitions: dict[str, PromptVariableDefinition],
    ) -> None:
        variable_refs = set(_VARIABLE_PATTERN.findall(source))
        conditional_matches = list(_CONDITIONAL_PATTERN.finditer(source))
        conditional_refs = {match.group(1) for match in conditional_matches}
        if any(name not in definitions for name in variable_refs | conditional_refs):
            raise PromptCompilationError(
                "PROMPT_TEMPLATE_VARIABLE_UNDECLARED",
                "Prompt template references an undeclared variable.",
            )
        for match in conditional_matches:
            if definitions[match.group(1)].type is not PromptVariableType.boolean:
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
        branch_content = _CONDITIONAL_PATTERN.sub(
            lambda match: match.group(2) + (match.group(3) or ""),
            source,
        )
        if _CONTROL_TOKEN_PATTERN.search(branch_content):
            raise PromptCompilationError(
                "PROMPT_TEMPLATE_CONTROL_INVALID",
                "Prompt template contains an invalid control token.",
            )
        if _VARIABLE_TOKEN_PATTERN.search(
            _VARIABLE_PATTERN.sub("", branch_content)
        ):
            raise PromptCompilationError(
                "PROMPT_TEMPLATE_VARIABLE_INVALID",
                "Prompt template contains an invalid variable token.",
            )

    def _read_repository_file(
        self,
        path: Path,
        *,
        max_bytes: int,
        unsafe_code: str,
        unavailable_code: str,
        budget_code: str,
    ) -> bytes:
        try:
            relative = path.relative_to(self._root) if path.is_absolute() else path
        except ValueError as exc:
            raise PromptCompilationError(
                unsafe_code,
                "Prompt input must be a repository-contained file.",
            ) from exc
        parts = relative.parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise PromptCompilationError(
                unsafe_code,
                "Prompt input must be a non-symlink repository-contained file.",
            )
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            raise PromptCompilationError(
                "PROMPT_PATH_GUARD_UNAVAILABLE",
                "Prompt path safety guards are unavailable on this platform.",
            )

        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory_flags |= getattr(os, "O_CLOEXEC", 0)
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        file_flags |= getattr(os, "O_NONBLOCK", 0)
        directory_fd = -1
        file_fd = -1
        validation_fd = -1
        directory_identities = [self._root_identity]
        try:
            directory_fd = os.open(self._root, directory_flags)
            root_info = os.fstat(directory_fd)
            if (
                not stat.S_ISDIR(root_info.st_mode)
                or (root_info.st_dev, root_info.st_ino) != self._root_identity
            ):
                raise PromptCompilationError(
                    unsafe_code,
                    "Prompt compiler repository root changed during access.",
                )
            for component in parts[:-1]:
                next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
                next_info = os.fstat(next_fd)
                if not stat.S_ISDIR(next_info.st_mode):
                    os.close(next_fd)
                    raise PromptCompilationError(
                        unsafe_code,
                        "Prompt input parent must be a repository directory.",
                    )
                directory_identities.append((next_info.st_dev, next_info.st_ino))
                os.close(directory_fd)
                directory_fd = next_fd
            file_fd = os.open(parts[-1], file_flags, dir_fd=directory_fd)
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode):
                raise PromptCompilationError(
                    unsafe_code,
                    "Prompt input must be a regular repository file.",
                )
            if before.st_size > max_bytes:
                raise PromptCompilationError(
                    budget_code,
                    "Prompt input exceeds its configured byte budget.",
                )
            payload = bytearray()
            while len(payload) <= max_bytes:
                chunk = os.read(
                    file_fd,
                    min(_READ_CHUNK_BYTES, max_bytes + 1 - len(payload)),
                )
                if not chunk:
                    break
                payload.extend(chunk)
            if len(payload) > max_bytes:
                raise PromptCompilationError(
                    budget_code,
                    "Prompt input exceeds its configured byte budget.",
                )
            after = os.fstat(file_fd)
            validation_fd = os.open(self._root, directory_flags)
            validation_root = os.fstat(validation_fd)
            if (
                not stat.S_ISDIR(validation_root.st_mode)
                or (validation_root.st_dev, validation_root.st_ino)
                != directory_identities[0]
            ):
                raise PromptCompilationError(
                    unavailable_code,
                    "Prompt input path changed during its bounded read.",
                )
            for component, expected_identity in zip(
                parts[:-1],
                directory_identities[1:],
                strict=True,
            ):
                next_validation_fd = os.open(
                    component,
                    directory_flags,
                    dir_fd=validation_fd,
                )
                validation_info = os.fstat(next_validation_fd)
                if (
                    not stat.S_ISDIR(validation_info.st_mode)
                    or (validation_info.st_dev, validation_info.st_ino)
                    != expected_identity
                ):
                    os.close(next_validation_fd)
                    raise PromptCompilationError(
                        unavailable_code,
                        "Prompt input path changed during its bounded read.",
                    )
                os.close(validation_fd)
                validation_fd = next_validation_fd
            path_after = os.stat(
                parts[-1],
                dir_fd=validation_fd,
                follow_symlinks=False,
            )
            root_after = os.stat(self._root, follow_symlinks=False)
            if (
                (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
                or after.st_size != before.st_size
                or after.st_mtime_ns != before.st_mtime_ns
                or after.st_ctime_ns != before.st_ctime_ns
                or len(payload) != after.st_size
                or not stat.S_ISREG(path_after.st_mode)
                or (path_after.st_dev, path_after.st_ino)
                != (before.st_dev, before.st_ino)
                or path_after.st_size != before.st_size
                or path_after.st_mtime_ns != before.st_mtime_ns
                or path_after.st_ctime_ns != before.st_ctime_ns
                or not stat.S_ISDIR(root_after.st_mode)
                or (root_after.st_dev, root_after.st_ino) != self._root_identity
            ):
                raise PromptCompilationError(
                    unavailable_code,
                    "Prompt input changed during its bounded read.",
                )
            return bytes(payload)
        except PromptCompilationError:
            raise
        except OSError as exc:
            availability_errnos = {
                errno.ENOENT,
                getattr(errno, "ESTALE", -1),
            }
            reason_code = (
                unavailable_code if exc.errno in availability_errnos else unsafe_code
            )
            safe_message = (
                "Prompt input is unavailable through its repository path."
                if reason_code == unavailable_code
                else "Prompt input could not be opened through repository path guards."
            )
            raise PromptCompilationError(
                reason_code,
                safe_message,
            ) from exc
        finally:
            if file_fd >= 0:
                os.close(file_fd)
            if directory_fd >= 0:
                os.close(directory_fd)
            if validation_fd >= 0:
                os.close(validation_fd)

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
            if name in supplied:
                value = supplied[name]
                if value is None:
                    raise PromptCompilationError(
                        "PROMPT_VARIABLE_TYPE_INVALID",
                        "Prompt variable does not match its declared type.",
                    )
            else:
                value = definition.default
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
                "\x00" in value
                or _VARIABLE_TOKEN_PATTERN.search(value)
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
        *,
        max_bytes: int,
    ) -> str:
        PromptModuleCompiler._validate_template_contract(source, definitions)
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

        chunks: list[str] = []
        rendered_size = 0
        cursor = 0
        for match in _VARIABLE_PATTERN.finditer(rendered):
            for chunk in (rendered[cursor : match.start()], render_variable(match)):
                rendered_size += len(chunk.encode("utf-8"))
                if rendered_size > max_bytes:
                    raise PromptCompilationError(
                        "PROMPT_COMPILED_BUDGET_EXCEEDED",
                        "Compiled prompt exceeds its configured byte budget.",
                    )
                chunks.append(chunk)
            cursor = match.end()
        tail = rendered[cursor:]
        rendered_size += len(tail.encode("utf-8"))
        if rendered_size > max_bytes:
            raise PromptCompilationError(
                "PROMPT_COMPILED_BUDGET_EXCEEDED",
                "Compiled prompt exceeds its configured byte budget.",
            )
        chunks.append(tail)
        rendered = "".join(chunks)
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

    @staticmethod
    def _declared_source_contract_hash(
        module_by_id: dict[str, PromptModuleDefinition],
        source_bytes_by_id: dict[str, bytes],
    ) -> str:
        payload = [
            {
                "module_id": module_id,
                "source_ref": module_by_id[module_id].source_ref,
                "source_hash": _sha256(source_bytes_by_id[module_id]),
                "source_bytes": len(source_bytes_by_id[module_id]),
            }
            for module_id in sorted(module_by_id)
        ]
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
