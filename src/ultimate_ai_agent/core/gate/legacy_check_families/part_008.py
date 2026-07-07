from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart008Mixin:
    """Legacy checks from m31_m32_remains_future through m34_m35_m36_remain_future."""
    def check_m31_m32_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M31_TO_M32_BOUNDARY.md",
        ]
        failures = [
            f"missing M31 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.35.0" not in text
            or "real tool runtime adapter" not in text
            or "implemented/released" not in text
        ):
            failures.append(
                "M31 docs do not mark v0.35.0 Real Tool Runtime Adapter implemented/released"
            )
        if "v0.35.1" not in text or "hardens m31" not in text:
            failures.append("M31 docs do not mark v0.35.1 no-op tool runtime hardening")
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 36, 0):
            if (
                "m32 is implemented/released" not in text
                and "m32 safe local filesystem metadata tool" not in text
            ):
                failures.append("M31/M32 docs do not acknowledge implemented M32")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
            elif "m33-m40 remain planned/provisional" not in text:
                failures.append("M33-M40 must remain planned/provisional after M32")
        else:
            if "m32-m40 remain planned/provisional" not in text:
                failures.append("M32-M40 must remain planned/provisional after M31")
            forbidden_m32_fragments = (
                "m32 is implemented",
                "v0.36.0 implements m32",
                "file tools are implemented",
                "network tools are implemented",
                "model tools are implemented",
                "arbitrary tool execution is implemented",
            )
            failures.extend(
                f"M31 docs imply M32 implementation: {fragment}"
                for fragment in forbidden_m32_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m32_filesystem_metadata_tool_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/filesystem_metadata.py",
            "tests/test_filesystem_metadata_tool_contracts.py",
            "tests/test_filesystem_metadata_path_policy.py",
            "tests/test_filesystem_metadata_authority_boundaries.py",
            "tests/test_m32_gate_integration.py",
            "docs/tools/FILESYSTEM_METADATA_TOOL.md",
            "docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md",
            "docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md",
            "docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md",
            "docs/tools/FILESYSTEM_METADATA_NON_GOALS.md",
            "docs/tools/M32_TO_M33_BOUNDARY.md",
        ]
        failures = [
            f"missing M32 filesystem metadata file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                FILESYSTEM_METADATA_TOOL_NAME,
                FILESYSTEM_METADATA_TOOL_REF,
                NOOP_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_REF,
                FilesystemSafeRoot,
                ToolInvocationKind,
                ToolInvocationRequest,
                ToolInvocationStatus,
                build_tool_runtime_manifest,
                evaluate_tool_invocation,
            )

            manifest = build_tool_runtime_manifest(baseline_version="0.37.1")
            policy = manifest.policy
            forbidden_flags = [
                policy.arbitrary_tool_execution_enabled,
                policy.side_effecting_tools_enabled,
                policy.shell_tools_enabled,
                policy.file_tools_enabled,
                policy.file_content_read_enabled,
                policy.file_preview_enabled,
                policy.file_hash_enabled,
                policy.directory_listing_enabled,
                policy.recursive_traversal_enabled,
                policy.symlink_following_enabled,
                policy.caller_selected_root_enabled,
                policy.file_write_enabled,
                policy.file_delete_enabled,
                policy.memory_write_tools_enabled,
                policy.network_tools_enabled,
                policy.model_tools_enabled,
                policy.browser_tools_enabled,
                policy.mobile_tools_enabled,
                policy.remote_tools_enabled,
                policy.plugin_tools_enabled,
                policy.dynamic_tool_registration_enabled,
                policy.backend_execute_routes_enabled,
                policy.control_center_execute_controls_enabled,
                policy.production_authority_enabled,
            ]
            expected_allowlist = [
                NOOP_TOOL_REF,
                FILESYSTEM_METADATA_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_REF,
            ]
            if (
                manifest.allowlisted_tool_refs[: len(expected_allowlist)]
                != expected_allowlist
            ):
                failures.append(
                    "M32 manifest allowlist does not preserve no-op and filesystem metadata"
                )
            if not policy.filesystem_metadata_tool_enabled or any(forbidden_flags):
                failures.append(
                    "M32 policy enables forbidden filesystem/content/mutation/runtime authority"
                )

            with tempfile.TemporaryDirectory() as tmp:
                safe_root_path = Path(tmp) / "safe-root"
                safe_root_path.mkdir()
                notes = safe_root_path / "notes"
                notes.mkdir()
                target = notes / "report.md"
                target.write_text("gate metadata only", encoding="utf-8")
                safe_root = FilesystemSafeRoot(
                    root_ref="safe-root:gate-m32",
                    root_path=safe_root_path,
                    safe_label="Gate safe root",
                )
                safe_request = ToolInvocationRequest(
                    invocation_id="tool-runtime-invocation:gate-m32",
                    tool_ref=FILESYSTEM_METADATA_TOOL_REF,
                    tool_name=FILESYSTEM_METADATA_TOOL_NAME,
                    invocation_kind=ToolInvocationKind.filesystem_metadata,
                    replay_key="tool-runtime-replay:gate-m32",
                    safe_summary="Inspect safe filesystem metadata.",
                    metadata={
                        "root_ref": "safe-root:gate-m32",
                        "relative_path": "notes/report.md",
                    },
                )
                safe_decision = evaluate_tool_invocation(
                    safe_request, safe_roots=[safe_root]
                )
                if (
                    safe_decision.status != ToolInvocationStatus.metadata_completed
                    or not safe_decision.invocation_allowed
                ):
                    failures.append(
                        "M32 safe filesystem metadata request did not complete"
                    )
                if safe_decision.side_effects_performed or not safe_decision.result:
                    failures.append(
                        "M32 safe filesystem metadata request reported side effects or no result"
                    )
                if safe_decision.result:
                    dumped = safe_decision.model_dump()
                    output = safe_decision.result.output
                    if getattr(output, "raw_content_returned", True) or getattr(
                        output, "text_preview_returned", True
                    ):
                        failures.append(
                            "M32 filesystem metadata output returned raw content or text preview"
                        )
                    if getattr(output, "content_hash_returned", True) or getattr(
                        output, "directory_listing_returned", True
                    ):
                        failures.append(
                            "M32 filesystem metadata output returned content hash or directory listing"
                        )
                    if getattr(output, "absolute_path_returned", True) or str(
                        safe_root_path
                    ) in str(dumped):
                        failures.append(
                            "M32 filesystem metadata output leaked an absolute safe-root path"
                        )
                    if "gate metadata only" in str(dumped):
                        failures.append(
                            "M32 filesystem metadata output leaked file content"
                        )

                def require_denial(
                    decision: Any, required_reason: str, label: str
                ) -> None:
                    if (
                        decision.status == ToolInvocationStatus.metadata_completed
                        or decision.execution_performed
                    ):
                        failures.append(f"M32 denied probe was allowed: {label}")
                    if decision.side_effects_performed:
                        failures.append(
                            f"M32 denied probe reported side effects: {label}"
                        )
                    if required_reason not in decision.reason_codes:
                        failures.append(
                            f"M32 denied probe missing {required_reason}: {label}"
                        )

                for relative_path, reason in [
                    ("../outside.md", "PATH_TRAVERSAL_DENIED"),
                    ("notes/%2e%2e/outside.md", "PATH_TRAVERSAL_DENIED"),
                    ("~/notes/report.md", "HOME_PATH_DENIED"),
                    ("C:/Users/report.md", "WINDOWS_PATH_DENIED"),
                    ("notes//report.md", "UNSAFE_PATH_SEPARATOR_DENIED"),
                    (".env", "HIDDEN_PATH_DENIED"),
                    (".git/config", "HIDDEN_PATH_DENIED"),
                    ("notes/token.txt", "SECRET_LIKE_PATH_DENIED"),
                    ("keys/id_rsa", "SECRET_LIKE_PATH_DENIED"),
                    ("keys/private.key", "SECRET_LIKE_PATH_DENIED"),
                    ("notes/*.md", "GLOB_PATH_DENIED"),
                    ("notes/%2A.md", "GLOB_PATH_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m32",
                                        "relative_path": relative_path,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"path {relative_path}",
                    )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:gate-m32",
                                    "relative_path": "notes/report.md",
                                    "root_path": str(safe_root_path),
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "CALLER_SELECTED_ROOT_DENIED",
                    "caller-selected root",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:missing",
                                    "relative_path": "notes/%2e%2e/outside.md",
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "PATH_TRAVERSAL_DENIED",
                    "model_copy encoded traversal",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"tool_ref": "tool:file_content_read.v1"}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "TOOL_NOT_ALLOWLISTED_DENIED",
                    "model_copy file content tool ref",
                )
                for flag_name, reason in [
                    ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
                    ("file_preview_enabled", "TEXT_PREVIEW_DENIED"),
                    ("file_hash_enabled", "CONTENT_HASH_DENIED"),
                    ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
                    ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
                    ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
                    ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m32",
                                        "relative_path": "notes/report.md",
                                        flag_name: True,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"metadata alias flag {flag_name}",
                    )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"contains_raw_file_content": True}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "RAW_FILE_CONTENT_DENIED",
                    "raw file model_copy revalidation",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"authority_refs": ["model:gate-m32"]}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
                    "model authority ref",
                )
                try:
                    link = safe_root_path / "link.md"
                    link.symlink_to(target)
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m32",
                                        "relative_path": "link.md",
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        "SYMLINK_DENIED",
                        "symlink path",
                    )
                except (OSError, NotImplementedError):
                    pass

            runtime_source = "\n".join(
                self._read(self.root / path)
                for path in [
                    "src/ultimate_ai_agent/core/tools/runtime/filesystem_metadata.py",
                    "src/ultimate_ai_agent/core/tools/runtime/file_preview.py",
                    "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
                    "src/ultimate_ai_agent/core/tools/runtime/policy.py",
                ]
            ).lower()
            forbidden_fragments = (
                "read_text(",
                "read_bytes(",
                "hashlib",
                ".glob(",
                ".rglob(",
                "os.walk(",
                "follow_symlinks=true",
                "shutil",
                ".unlink(",
                ".remove(",
                ".rename(",
                ".replace(",
                ".chmod(",
                ".chown(",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "os.system(",
                "popen(",
            )
            failures.extend(
                f"M32 filesystem metadata module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in runtime_source
            )
        except Exception as exc:
            failures.append(f"M32 filesystem metadata validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m32_filesystem_metadata_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m32_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M32 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m32_m33_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M32_TO_M33_BOUNDARY.md",
        ]
        failures = [
            f"missing M32 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 36, 1):
            if "v0.36.1" not in text or "filesystem metadata path safety" not in text:
                failures.append(
                    "M32 docs do not mark v0.36.1 filesystem metadata path safety hardening"
                )
        if (
            "safe local filesystem metadata" not in text
            or "implemented/released" not in text
        ):
            failures.append(
                "M32 docs do not mark safe local filesystem metadata implemented/released"
            )
        if version_tuple >= (0, 37, 0):
            if (
                "m33" not in text
                or "redacted preview" not in text
                or "implemented/released" not in text
            ):
                failures.append(
                    "M32/M33 docs do not acknowledge implemented M33 redacted preview"
                )
            if version_tuple >= (0, 38, 0):
                if (
                    "m34" not in text
                    or "broader file capability review" not in text
                    or "implemented/released" not in text
                ):
                    failures.append(
                        "M32/M34 docs do not acknowledge implemented M34 broader file capability review"
                    )
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
        else:
            if "m33-m40 remain planned/provisional" not in text:
                failures.append("M33-M40 must remain planned/provisional after M32")
            forbidden_m33_fragments = (
                "m33 is implemented",
                "v0.37.0 implements m33",
                "mobile approval surface is implemented",
                "mobile sensors are implemented",
            )
            failures.extend(
                f"M32 docs imply M33 implementation: {fragment}"
                for fragment in forbidden_m33_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m33_redacted_file_preview_tool_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/file_preview.py",
            "tests/test_redacted_file_preview_tool_contracts.py",
            "tests/test_redacted_file_preview_path_policy.py",
            "tests/test_redacted_file_preview_authority_boundaries.py",
            "tests/test_m33_gate_integration.py",
            "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
            "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
            "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
            "docs/tools/M33_TO_M34_BOUNDARY.md",
        ]
        failures = [
            f"missing M33 redacted file preview file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                FILESYSTEM_METADATA_TOOL_REF,
                NOOP_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_NAME,
                REDACTED_FILE_PREVIEW_TOOL_REF,
                FilePreviewRedactionSummary,
                FilePreviewSafeRoot,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
                ToolInvocationKind,
                ToolInvocationRequest,
                ToolInvocationStatus,
                build_tool_runtime_manifest,
                evaluate_tool_invocation,
            )

            manifest = build_tool_runtime_manifest(baseline_version="0.37.1")
            policy = manifest.policy
            expected_allowlist = [
                NOOP_TOOL_REF,
                FILESYSTEM_METADATA_TOOL_REF,
                REDACTED_FILE_PREVIEW_TOOL_REF,
            ]
            if (
                manifest.allowlisted_tool_refs[: len(expected_allowlist)]
                != expected_allowlist
            ):
                failures.append(
                    "M33 manifest allowlist does not preserve no-op, filesystem metadata, and redacted preview"
                )
            forbidden_flags = [
                policy.arbitrary_tool_execution_enabled,
                policy.side_effecting_tools_enabled,
                policy.shell_tools_enabled,
                policy.file_tools_enabled,
                policy.file_content_read_enabled,
                policy.file_preview_enabled,
                policy.file_hash_enabled,
                policy.directory_listing_enabled,
                policy.recursive_traversal_enabled,
                policy.symlink_following_enabled,
                policy.caller_selected_root_enabled,
                policy.file_write_enabled,
                policy.file_delete_enabled,
                policy.memory_write_tools_enabled,
                policy.network_tools_enabled,
                policy.model_tools_enabled,
                policy.browser_tools_enabled,
                policy.mobile_tools_enabled,
                policy.remote_tools_enabled,
                policy.plugin_tools_enabled,
                policy.dynamic_tool_registration_enabled,
                policy.backend_execute_routes_enabled,
                policy.control_center_execute_controls_enabled,
                policy.production_authority_enabled,
            ]
            if not policy.redacted_file_preview_tool_enabled or any(forbidden_flags):
                failures.append(
                    "M33 policy enables forbidden filesystem/runtime authority"
                )

            with tempfile.TemporaryDirectory() as tmp:
                safe_root_path = Path(tmp) / "safe-root"
                safe_root_path.mkdir()
                notes = safe_root_path / "notes"
                notes.mkdir()
                target = notes / "report.md"
                target.write_text(
                    "Title\nAPI_KEY=gate-secret-value\nPublic summary.\n",
                    encoding="utf-8",
                )
                safe_root = FilePreviewSafeRoot(
                    root_ref="safe-root:gate-m33",
                    root_path=safe_root_path,
                    safe_label="Gate safe root",
                )
                safe_request = ToolInvocationRequest(
                    invocation_id="tool-runtime-invocation:gate-m33",
                    tool_ref=REDACTED_FILE_PREVIEW_TOOL_REF,
                    tool_name=REDACTED_FILE_PREVIEW_TOOL_NAME,
                    invocation_kind=ToolInvocationKind.redacted_file_preview,
                    replay_key="tool-runtime-replay:gate-m33",
                    safe_summary="Generate a redacted file preview proposal.",
                    metadata={
                        "root_ref": "safe-root:gate-m33",
                        "relative_path": "notes/report.md",
                    },
                )
                safe_decision = evaluate_tool_invocation(
                    safe_request, safe_roots=[safe_root]
                )
                if (
                    safe_decision.status != ToolInvocationStatus.preview_completed
                    or not safe_decision.invocation_allowed
                ):
                    failures.append(
                        "M33 safe redacted file preview request did not complete"
                    )
                if safe_decision.side_effects_performed or not safe_decision.result:
                    failures.append(
                        "M33 safe redacted file preview request reported side effects or no result"
                    )
                if safe_decision.result:
                    dumped = safe_decision.model_dump()
                    output = safe_decision.result.output
                    if (
                        getattr(output, "status", None)
                        != RedactedFilePreviewStatus.preview_generated
                    ):
                        failures.append("M33 redacted preview output status is invalid")
                    if not getattr(
                        output, "redacted_preview_returned", False
                    ) or not getattr(output, "redacted_preview", ""):
                        failures.append(
                            "M33 redacted preview output did not return a redacted preview"
                        )
                    if "gate-secret-value" in str(dumped):
                        failures.append(
                            "M33 redacted preview leaked a secret-like value"
                        )
                    if str(safe_root_path) in str(dumped):
                        failures.append(
                            "M33 redacted preview leaked an absolute safe-root path"
                        )
                    unsafe_output_flags = [
                        getattr(output, "raw_content_returned", True),
                        getattr(output, "raw_content_stored", True),
                        getattr(output, "full_file_returned", True),
                        getattr(output, "content_hash_returned", True),
                        getattr(output, "directory_listing_returned", True),
                        getattr(output, "absolute_path_returned", True),
                        getattr(output, "symlink_followed", True),
                        getattr(output, "mutation_performed", True),
                        getattr(output, "context_injection_performed", True),
                    ]
                    if any(unsafe_output_flags):
                        failures.append(
                            "M33 redacted preview output returned raw/full/hash/list/mutation/context data"
                        )
                    try:
                        RedactedFilePreviewOutput(
                            output_ref="redacted-file-preview-output:gate-unsafe",
                            status=RedactedFilePreviewStatus.preview_generated,
                            root_ref="safe-root:gate-m33",
                            safe_path_ref="filesystem-preview-path:safe-root_gate-m33/notes/report.md",
                            redacted_preview="API_KEY=gate-secret-value",
                            redaction_summary=FilePreviewRedactionSummary(),
                            file_size_bytes=25,
                        )
                        failures.append(
                            "M33 redacted preview output accepted unredacted secret-like content"
                        )
                    except ValueError as exc:
                        if (
                            "REDACTED_FILE_PREVIEW_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT"
                            not in str(exc)
                        ):
                            failures.append(
                                "M33 redacted preview output rejected unsafe content with unexpected reason"
                            )

                def require_denial(
                    decision: Any, required_reason: str, label: str
                ) -> None:
                    if (
                        decision.status == ToolInvocationStatus.preview_completed
                        or decision.execution_performed
                    ):
                        failures.append(f"M33 denied probe was allowed: {label}")
                    if decision.side_effects_performed:
                        failures.append(
                            f"M33 denied probe reported side effects: {label}"
                        )
                    if required_reason not in decision.reason_codes:
                        failures.append(
                            f"M33 denied probe missing {required_reason}: {label}"
                        )

                for relative_path, reason in [
                    ("/etc/passwd", "ABSOLUTE_PATH_DENIED"),
                    ("../outside.md", "PATH_TRAVERSAL_DENIED"),
                    ("notes/%2e%2e/outside.md", "PATH_TRAVERSAL_DENIED"),
                    (".env", "HIDDEN_PATH_DENIED"),
                    ("notes/token.txt", "SECRET_LIKE_PATH_DENIED"),
                    ("keys/id_rsa", "SECRET_LIKE_PATH_DENIED"),
                    ("notes/*.md", "GLOB_PATH_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m33",
                                        "relative_path": relative_path,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"path {relative_path}",
                    )
                directory = safe_root_path / "docs"
                directory.mkdir()
                (directory / "child.md").write_text("child content", encoding="utf-8")
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:gate-m33",
                                    "relative_path": "docs",
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "DIRECTORY_PATH_DENIED",
                    "directory path",
                )
                binary = notes / "binary.txt"
                binary.write_bytes(b"hello\x00world")
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:gate-m33",
                                    "relative_path": "notes/binary.txt",
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "BINARY_FILE_DENIED",
                    "binary file",
                )
                try:
                    symlink_root_path = Path(tmp) / "safe-root-link"
                    symlink_root_path.symlink_to(
                        safe_root_path, target_is_directory=True
                    )
                    symlink_root = FilePreviewSafeRoot(
                        root_ref="safe-root:gate-m33-link",
                        root_path=symlink_root_path,
                        safe_label="Gate symlink safe root",
                    )
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m33-link",
                                        "relative_path": "notes/report.md",
                                    }
                                }
                            ),
                            safe_roots=[symlink_root],
                        ),
                        "SAFE_ROOT_SYMLINK_DENIED",
                        "symlink safe root",
                    )
                except (OSError, NotImplementedError):
                    pass
                large = notes / "large.md"
                large.write_bytes(b"a" * 70000)
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={
                                "metadata": {
                                    "root_ref": "safe-root:gate-m33",
                                    "relative_path": "notes/large.md",
                                }
                            }
                        ),
                        safe_roots=[safe_root],
                    ),
                    "FILE_TOO_LARGE_DENIED",
                    "oversized file",
                )
                for flag_name, reason in [
                    ("raw_content_enabled", "RAW_FILE_CONTENT_DENIED"),
                    ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
                    ("content_hash_enabled", "CONTENT_HASH_DENIED"),
                    ("directory_listing_enabled", "DIRECTORY_LISTING_DENIED"),
                    ("recursive_traversal_enabled", "RECURSIVE_TRAVERSAL_DENIED"),
                    ("symlink_following_enabled", "SYMLINK_FOLLOWING_DENIED"),
                    ("file_write_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("file_delete_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
                    ("caller_selected_root_enabled", "CALLER_SELECTED_ROOT_DENIED"),
                    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
                ]:
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m33",
                                        "relative_path": "notes/report.md",
                                        flag_name: True,
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        reason,
                        f"metadata alias flag {flag_name}",
                    )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"contains_raw_file_content": True}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "RAW_FILE_CONTENT_DENIED",
                    "raw file model_copy revalidation",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"tool_ref": "tool:filesystem.raw_read.v1"}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "TOOL_NOT_ALLOWLISTED_DENIED",
                    "model_copy raw read tool ref",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"authority_refs": ["model:gate-m33"]}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
                    "model authority ref",
                )
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"approval_ref": "approval_test_m33"}
                        ),
                        safe_roots=[safe_root],
                    ),
                    "APPROVAL_TEST_REF_DENIED",
                    "approval_test ref",
                )
                try:
                    link = safe_root_path / "link.md"
                    link.symlink_to(target)
                    require_denial(
                        evaluate_tool_invocation(
                            safe_request.model_copy(
                                update={
                                    "metadata": {
                                        "root_ref": "safe-root:gate-m33",
                                        "relative_path": "link.md",
                                    }
                                }
                            ),
                            safe_roots=[safe_root],
                        ),
                        "SYMLINK_DENIED",
                        "symlink path",
                    )
                except (OSError, NotImplementedError):
                    pass

            runtime_root = (
                self.root / "src" / "ultimate_ai_agent" / "core" / "tools" / "runtime"
            )
            preview_source = self._read(runtime_root / "file_preview.py").lower()
            forbidden_preview_fragments = (
                "read_text(",
                "read_bytes(",
                "hashlib",
                ".glob(",
                ".rglob(",
                "os.walk(",
                "follow_symlinks=true",
                "shutil",
                ".unlink(",
                ".remove(",
                ".rename(",
                ".replace(",
                ".chmod(",
                ".chown(",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "os.system(",
                "popen(",
                "shell=true",
            )
            failures.extend(
                f"M33 redacted preview module contains forbidden fragment: {fragment}"
                for fragment in forbidden_preview_fragments
                if fragment in preview_source
            )
        except Exception as exc:
            failures.append(f"M33 redacted preview validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m33_redacted_file_preview_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m33_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M33 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m33_m34_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M33_TO_M34_BOUNDARY.md",
            "docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
            "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
            "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
        ]
        failures = [
            f"missing M33 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "first safe local file read proposal" not in text
            or "redacted preview" not in text
        ):
            failures.append(
                "M33 docs do not mark redacted file preview proposal implemented/released"
            )
        if "implemented/released" not in text:
            failures.append("M33 docs do not mark M33 implemented/released")
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 38, 0):
            if (
                "m34" not in text
                or "broader file capability review" not in text
                or "implemented/released" not in text
            ):
                failures.append(
                    "M34 broader file capability review must be implemented/released at v0.38.0+"
                )
            if "m36-m60 remain planned/provisional" not in text:
                failures.append("M36-M60 must remain planned/provisional after M34")
            active_currentness_docs = {
                path: self._read(self.root / path)
                for path in ["README.md", *required_docs]
                if (self.root / path).exists()
            }
            failures.extend(m34_active_currentness_failures(active_currentness_docs))
        elif "m34" not in text or "planned/provisional" not in text:
            failures.append("M34 must remain planned/provisional after M33")
        forbidden_m34_fragments = (
            "full file read is implemented",
            "file write tool is implemented",
            "safe file review workflow is implemented",
            "file review ui is implemented",
            "approval persistence is implemented",
            "context injection is implemented",
        )
        failures.extend(
            f"M33 docs imply M34 implementation: {fragment}"
            for fragment in forbidden_m34_fragments
            if fragment in text
        )
        return self._result(criterion, failures, required_docs)

    def check_m34_broader_file_capability_review_docs_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md",
            "docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md",
            "docs/files/FILE_CAPABILITY_RISK_REGISTER.md",
            "docs/files/FILE_CAPABILITY_DECISION_RECORD.md",
            "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md",
            "docs/files/M34_TO_M35_BOUNDARY.md",
            "docs/control_center/FILE_REVIEW_SURFACE_READINESS.md",
            "docs/tools/FILE_TOOL_CAPABILITY_MATRIX.md",
            "docs/release_notes/v0_38_2.md",
            "docs/archive/releases/v0_38_2/README_IMPORT.md",
            "docs/archive/releases/v0_38_2/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_38_2.md",
            "tests/test_m34_gate_integration.py",
        ]
        failures = [
            f"missing M34 broader file capability review file: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        version_tuple = self._active_version_tuple()
        required_fragments = {
            "M34 docs must say planning/review only": "planning/review only",
            "M34 docs must say no runtime file capability": "no runtime file capability",
            "M34 docs must say no raw file reads": "no raw file reads",
            "M34 docs must say no file review UI": "no file review ui",
            "M34 docs must say no approval persistence": "no approval persistence",
            "M34 docs must say no context proposal": "no context proposal",
            "M34 docs must say no context injection": "no context injection",
            "M34 docs must say no memory writes": "no memory writes",
            "M34 docs must say no export": "no export",
            "M34 docs must say no execution": "no execution",
            "M34 docs must say no backend routes": "no backend routes",
        }
        if version_tuple < (0, 40, 0):
            required_fragments["M36 must remain planned/provisional"] = (
                "m36 remains planned/provisional"
            )
        if version_tuple >= (0, 39, 0):
            required_fragments["M34 docs must acknowledge M35 implementation"] = (
                "v0.39.0 implements m35"
            )
        else:
            required_fragments["M35 must remain planned/provisional"] = (
                "m35 remains planned/provisional"
            )
        for failure, fragment in required_fragments.items():
            if fragment not in text:
                failures.append(failure)
        forbidden_fragments = (
            "m34 implements safe file review workflow contracts",
            "approval persistence is implemented",
            "review approval capture is implemented",
            "context proposal is implemented",
            "context injection is implemented",
            "memory writes are implemented",
            "raw file export is implemented",
            "execution is implemented",
            "backend file route is implemented",
        )
        if version_tuple < (0, 40, 0):
            forbidden_fragments += (
                "file review ui is implemented",
                "ccc file review surface is implemented",
            )
        failures.extend(
            f"M34 docs imply forbidden implementation: {fragment}"
            for fragment in forbidden_fragments
            if fragment in text
        )
        if version_tuple < (0, 39, 0):
            failures.extend(
                f"M34 docs imply forbidden implementation: {fragment}"
                for fragment in ("safe file review workflow is implemented",)
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m34_file_capability_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m34_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M34 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m34_m35_m36_remain_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/files/M34_TO_M35_BOUNDARY.md",
            "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md",
            "docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md",
            "docs/tools/REDACTED_FILE_PREVIEW_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md",
            "docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md",
            "docs/tools/REDACTED_FILE_PREVIEW_TOOL.md",
        ]
        failures = [
            f"missing M34/M35 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.38.0" not in text
            or "m34" not in text
            or "broader file capability review" not in text
        ):
            failures.append(
                "M34 roadmap docs do not identify v0.38.0 Broader File Capability Review"
            )
        if (
            "m34 is implemented/released" not in text
            and "m34 is implemented/released by v0.38.0" not in text
        ):
            failures.append("M34 roadmap docs do not mark M34 implemented/released")
        if (
            "planning/docs/verifier" not in text
            and "planning, architecture review" not in text
        ):
            failures.append(
                "M34 roadmap docs do not constrain M34 to planning/docs/verifier work"
            )
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 45, 0):
            if (
                "m41 is implemented/released" not in text
                and "v0.45.0 implements m41" not in text
            ):
                failures.append("M41 roadmap docs do not mark M41 implemented/released")
            if (
                "m42-m60 remain planned/provisional" not in text
                and "m44-m60 remain planned/provisional" not in text
                and "m45-m60 remain planned/provisional" not in text
                and "m46-m60 remain planned/provisional" not in text
                and "m47-m60 remain planned/provisional" not in text
                and "m48-m60 remain planned/provisional" not in text
                and "m49-m60 remain planned/provisional" not in text
                and "m50-m60 remain planned/provisional" not in text
                and "m51-m60 remain planned/provisional" not in text
                and "m52-m60 remain planned/provisional" not in text
                and "m53-m60 remain planned/provisional" not in text
                and "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append(
                    "M42-M60 through M49-M60 planned/provisional marker missing after M41"
                )
        elif current_tuple >= (0, 44, 0):
            if (
                "m40 is implemented/released" not in text
                and "v0.44.0 implements m40" not in text
            ):
                failures.append("M40 roadmap docs do not mark M40 implemented/released")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif current_tuple >= (0, 43, 0):
            if (
                "m39 is implemented/released" not in text
                and "v0.43.0 implements m39" not in text
            ):
                failures.append("M39 roadmap docs do not mark M39 implemented/released")
            if "m40-m60 remain planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif current_tuple >= (0, 42, 0):
            if (
                "m38 is implemented/released" not in text
                and "v0.42.0 implements m38" not in text
            ):
                failures.append("M38 roadmap docs do not mark M38 implemented/released")
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif current_tuple >= (0, 41, 0):
            if (
                "m37 is implemented/released" not in text
                and "v0.41.0 implements m37" not in text
            ):
                failures.append("M37 roadmap docs do not mark M37 implemented/released")
            if "m38-m60 remain planned/provisional" not in text:
                failures.append("M38-M60 must remain planned/provisional after M37")
        elif current_tuple >= (0, 40, 0):
            if (
                "m36 is implemented/released" not in text
                and "v0.40.0 implements m36" not in text
            ):
                failures.append("M36 roadmap docs do not mark M36 implemented/released")
            if "m37-m60 remain planned/provisional" not in text:
                failures.append("M37-M60 must remain planned/provisional after M36")
        elif current_tuple >= (0, 39, 0):
            if (
                "m35 is implemented/released" not in text
                and "v0.39.0 implements m35" not in text
            ):
                failures.append("M35 roadmap docs do not mark M35 implemented/released")
            if "m36-m60 remain planned/provisional" not in text:
                failures.append("M36-M60 must remain planned/provisional after M35")
        elif "m36-m60 remain planned/provisional" not in text:
            failures.append("M36-M60 must remain planned/provisional after M34")
        future_fragments = [
            "approval persistence is implemented",
            "context injection is implemented",
        ]
        if current_tuple < (0, 42, 0):
            future_fragments.append("context proposal is implemented")
        if current_tuple < (0, 40, 0):
            future_fragments.extend(
                [
                    "ccc file review surface is implemented",
                    "m36 is implemented",
                    "v0.40.0 implements m36",
                    "file review ui is implemented",
                ]
            )
        if current_tuple < (0, 41, 0):
            future_fragments.extend(
                [
                    "approval persistence is implemented",
                    "review approval capture is implemented",
                    "m37 is implemented",
                    "v0.41.0 implements m37",
                ]
            )
        if current_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        for fragment in future_fragments:
            if fragment in text:
                failures.append(
                    f"M34 docs imply future milestone implementation: {fragment}"
                )
        if current_tuple < (0, 39, 0):
            for fragment in (
                "safe file review workflow is implemented",
                "m35 is implemented",
                "v0.39.0 implements m35",
            ):
                if fragment in text:
                    failures.append(
                        f"M34 docs imply future milestone implementation: {fragment}"
                    )
        failures.extend(
            m34_active_currentness_failures(
                {
                    path: self._read(self.root / path)
                    for path in required_docs
                    if (self.root / path).exists()
                }
            )
        )
        return self._result(criterion, failures, required_docs)
