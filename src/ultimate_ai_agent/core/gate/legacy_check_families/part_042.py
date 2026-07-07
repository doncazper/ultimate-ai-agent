from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart042Mixin:
    """Legacy checks from m150_ultimate_ai_agent_alpha_contracts through m160_bounded_hf_gguf_search_static_safety."""
    def check_m150_ultimate_ai_agent_alpha_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/productization/ultimate_ai_agent_alpha.py",
            "docs/productization/ULTIMATE_AI_AGENT_ALPHA.md",
            "docs/productization/ULTIMATE_AI_AGENT_ALPHA_POLICY.md",
            "docs/productization/ULTIMATE_AI_AGENT_ALPHA_AUTHORITY_BOUNDARY.md",
            "docs/productization/ULTIMATE_AI_AGENT_ALPHA_RECEIPT_PLAN.md",
            "docs/productization/ULTIMATE_AI_AGENT_ALPHA_NON_GOALS.md",
            "docs/productization/M150_ALPHA_TO_BETA_BOUNDARY.md",
            "docs/release_notes/checkpoint_m150.md",
            "docs/archive/checkpoints/m150/README_IMPORT.md",
            "docs/archive/checkpoints/m150/master_plan.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m150_ultimate_ai_agent_alpha.py",
            "tests/test_m150_gate_integration.py",
        ]
        failures = [
            f"missing M150 Ultimate AI Agent Alpha file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.gate.checkpoint_builders.m150_ultimate_ai_agent_alpha import _request
            from ultimate_ai_agent.core.productization import (
                UltimateAiAgentAlphaStatus,
                build_ultimate_ai_agent_alpha_record,
                validate_ultimate_ai_agent_alpha_record,
            )

            record = build_ultimate_ai_agent_alpha_record(_request())
            if (
                record.status != UltimateAiAgentAlphaStatus.alpha_target_recorded
                or record.product_target_ref != "product-target:v1.2.0-alpha"
                or not record.contract_only
                or not record.review_only
                or not record.alpha_target_only
                or not record.deterministic
                or not record.local_only
                or not record.safe_refs_only
                or not record.disabled_by_default
                or not record.m101_m149_covered
                or not record.alpha_targets_bound
                or not record.release_candidate_freezes_bound
                or not record.alpha_readiness_bound
                or not record.evidence_indexes_bound
                or not record.blocker_summaries_bound
                or not record.signoff_reviews_bound
                or not record.beta_promotion_gates_bound
                or not record.no_release_publication
                or not record.no_release_tag
                or not record.no_tag_creation
                or not record.no_artifact_build
                or not record.no_artifact_upload
                or not record.no_artifact_export
                or not record.no_external_distribution
                or not record.no_app_store_submission
                or not record.no_testflight_submission
                or not record.no_beta_release
                or not record.no_release_automation
                or not record.no_backend_route
                or not record.no_control_center_control
                or not record.no_dependency
                or not record.no_production_authority
                or record.release_publication_started
                or record.release_tag_created
                or record.tag_creation_performed
                or record.artifact_build_performed
                or record.artifact_upload_started
                or record.artifact_export_started
                or record.external_distribution_started
                or record.app_store_submission_started
                or record.testflight_submission_started
                or record.beta_release_enabled
                or record.release_automation_started
                or record.auth_runtime_started
                or record.backend_route_added
                or record.control_center_control_added
                or record.dependency_added
                or record.production_authority_granted
                or "M150_ULTIMATE_AI_AGENT_ALPHA_REVIEW_ONLY" not in record.reason_codes
                or "M150_M101_M149_COVERED" not in record.reason_codes
                or "M150_ALPHA_TARGET_ONLY" not in record.reason_codes
                or "M150_DISABLED_BY_DEFAULT" not in record.reason_codes
                or "M150_NO_RELEASE_PUBLICATION" not in record.reason_codes
                or "M150_NO_RELEASE_TAG" not in record.reason_codes
                or "M150_NO_TAG_CREATION" not in record.reason_codes
                or "M150_NO_ARTIFACT_BUILD" not in record.reason_codes
                or "M150_NO_ARTIFACT_UPLOAD" not in record.reason_codes
                or "M150_NO_ARTIFACT_EXPORT" not in record.reason_codes
                or "M150_NO_EXTERNAL_DISTRIBUTION" not in record.reason_codes
                or "M150_NO_APP_STORE_SUBMISSION" not in record.reason_codes
                or "M150_NO_TESTFLIGHT_SUBMISSION" not in record.reason_codes
                or "M150_NO_BETA_RELEASE" not in record.reason_codes
                or "M150_NO_RELEASE_AUTOMATION" not in record.reason_codes
                or "M150_NO_BACKEND_ROUTE" not in record.reason_codes
                or "M150_NO_PRODUCTION_AUTHORITY" not in record.reason_codes
                or "BETA_REMAINS_FUTURE" not in record.reason_codes
            ):
                failures.append(
                    "M150 Ultimate AI Agent Alpha record is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"release_publication_started": True},
                    "M150_RELEASE_PUBLICATION_DENIED",
                ),
                ({"release_tag_created": True}, "M150_RELEASE_TAG_DENIED"),
                ({"tag_creation_performed": True}, "M150_TAG_CREATION_DENIED"),
                ({"artifact_build_performed": True}, "M150_ARTIFACT_BUILD_DENIED"),
                ({"artifact_upload_started": True}, "M150_ARTIFACT_UPLOAD_DENIED"),
                ({"artifact_export_started": True}, "M150_ARTIFACT_EXPORT_DENIED"),
                (
                    {"external_distribution_started": True},
                    "M150_EXTERNAL_DISTRIBUTION_DENIED",
                ),
                (
                    {"app_store_submission_started": True},
                    "M150_APP_STORE_SUBMISSION_DENIED",
                ),
                (
                    {"testflight_submission_started": True},
                    "M150_TESTFLIGHT_SUBMISSION_DENIED",
                ),
                ({"beta_release_enabled": True}, "M150_BETA_RELEASE_DENIED"),
                (
                    {"release_automation_started": True},
                    "M150_RELEASE_AUTOMATION_DENIED",
                ),
                ({"auth_runtime_started": True}, "M150_AUTH_RUNTIME_DENIED"),
                ({"backend_route_added": True}, "M150_BACKEND_ROUTE_DENIED"),
                ({"dependency_added": True}, "M150_DEPENDENCY_DENIED"),
                (
                    {"production_authority_granted": True},
                    "M150_PRODUCTION_AUTHORITY_DENIED",
                ),
            ]:
                try:
                    validate_ultimate_ai_agent_alpha_record(
                        record.model_copy(update=update)
                    )
                    failures.append(
                        f"M150 unsafe alpha mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M150 unsafe alpha mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M150 Ultimate AI Agent Alpha validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "ultimate ai agent",
            "v1.2.0-alpha",
            "contract-only",
            "review-only",
            "alpha-target-only",
            "deterministic",
            "local-only",
            "safe-ref-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "accepted m101-m149",
            "alpha target refs",
            "release candidate freeze refs",
            "alpha readiness refs",
            "evidence index refs",
            "blocker summary refs",
            "signoff review refs",
            "beta promotion gate refs",
            "audit",
            "replay",
            "revocation",
            "kill-switch",
            "no-effect receipt",
            "no release publication",
            "no release tag",
            "no tag creation",
            "no artifact build",
            "no artifact upload",
            "no artifact export",
            "no external distribution",
            "no app store submission",
            "no testflight submission",
            "no beta release",
            "no release automation",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
            "beta remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M150 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m150_ultimate_ai_agent_alpha_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "release_publication_enabled=True",
            "release_tag_enabled=True",
            "tag_creation_enabled=True",
            "artifact_build_enabled=True",
            "artifact_upload_enabled=True",
            "artifact_export_enabled=True",
            "external_distribution_enabled=True",
            "app_store_submission_enabled=True",
            "testflight_submission_enabled=True",
            "beta_release_enabled=True",
            "release_automation_enabled=True",
            "auth_runtime_enabled=True",
            "login_enabled=True",
            "connector_runtime_enabled=True",
            "plugin_marketplace_runtime_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "connector_action_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "backend_route_enabled=True",
            "dependency_added=True",
            "production_authority_granted=True",
            "release_publication_started=True",
            "release_tag_created=True",
            "tag_creation_performed=True",
            "artifact_build_performed=True",
            "artifact_upload_started=True",
            "artifact_export_started=True",
            "external_distribution_started=True",
            "app_store_submission_started=True",
            "testflight_submission_started=True",
            "release_automation_started=True",
            "auth_runtime_started=True",
            "/ultimate-ai-agent-alpha",
            "/alpha/accept",
            "/alpha/release",
            "/release/publish",
            "/release/tag",
            "/release/create-tag",
            "/release/artifact/build",
            "/release/artifact/upload",
            "/release/artifact/export",
            "/distribution/publish",
            "/external-distribution",
            "/app-store/submit",
            "/testflight/submit",
            "/beta/release",
            "/v1-alpha/release",
            "/v1.2.0-alpha/release",
            "/m150/release",
            "/release/automation",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "src/ultimate_ai_agent/core/productization/__init__.py",
            "src/ultimate_ai_agent/core/productization/ultimate_ai_agent_alpha.py",
            "src/ultimate_ai_agent/core/productization/alpha_release_candidate_freeze.py",
            "src/ultimate_ai_agent/core/productization/external_security_review.py",
            "src/ultimate_ai_agent/core/productization/public_docs_wiki_readiness.py",
            "src/ultimate_ai_agent/core/productization/billing_plan_boundary.py",
            "src/ultimate_ai_agent/core/productization/enterprise_pro_safety_modes.py",
            "src/ultimate_ai_agent/core/productization/plugin_marketplace_policy_draft.py",
            "src/ultimate_ai_agent/core/productization/alpha_ui_app_readiness.py",
            "src/ultimate_ai_agent/core/productization/alpha_privacy_review.py",
            "src/ultimate_ai_agent/core/productization/multi_user_product_boundary.py",
        }
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if ".test." in rel or _is_static_safety_scan_allowed_file(
                    rel, allowed_files
                ):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M150 forbidden alpha target fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m150_ultimate_ai_agent_alpha_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m150_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M150 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m150_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        failures = [
            f"missing M150 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "m150" not in text or "ultimate ai agent v1.2.0-alpha" not in text:
            failures.append("active docs do not identify M150 Ultimate AI Agent Alpha")
        if "m150 is implemented/released" not in text:
            failures.append("active docs do not mark M150 implemented/released")
        for version_label, product_target, milestone, title, status in [
            (
                "checkpoint m149",
                "pre-alpha checkpoint",
                "m149",
                "alpha release candidate freeze",
                "implemented/released",
            ),
            (
                "v1.2.0-alpha",
                "alpha",
                "m150",
                "ultimate ai agent v1.2.0-alpha",
                "implemented/released",
            ),
        ]:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | {status} |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing expected M149/M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "release publication is implemented",
            "release tag is implemented",
            "tag creation is implemented",
            "artifact build is implemented",
            "artifact upload is implemented",
            "artifact export is implemented",
            "external distribution is implemented",
            "app store submission is implemented",
            "testflight submission is implemented",
            "release automation is implemented",
            "beta is released",
            "production authority is implemented",
            "backend route is implemented",
            "control center control is implemented",
            "m150 dependency is added",
            "m151 is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"active docs imply forbidden M150 future/currentness claim: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m151_local_openwebui_test_shell_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/local_test_shell.py",
            "docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL.md",
            "docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/M151_LOCAL_OPENWEBUI_TEST_SHELL_RUNBOOK.md",
            "tests/test_m151_openwebui_local_test_shell.py",
            "tests/test_m151_openwebui_local_gateway_api.py",
        ]
        failures = [
            f"missing M151 local OpenWebUI test shell file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                UAA_OPENWEBUI_TEST_MODEL_ID,
                OpenWebUILocalChatCompletionRequest,
                build_default_openwebui_local_test_shell_policy,
                build_openwebui_local_chat_completion_response,
                openwebui_test_gateway_authorized,
                openwebui_test_gateway_enabled,
            )

            policy = build_default_openwebui_local_test_shell_policy()
            if (
                not policy.local_dev_only
                or not policy.disabled_by_default
                or not policy.localhost_only
                or not policy.openai_compatible_gateway
                or not policy.deterministic_response_only
                or policy.openwebui_is_agent_brain
                or policy.provider_call_enabled
                or policy.model_authority_enabled
                or policy.tool_execution_enabled
                or policy.memory_write_enabled
                or policy.context_injection_enabled
                or policy.external_network_enabled
                or policy.raw_prompt_logging_enabled
                or policy.dependency_added
                or policy.production_authority_enabled
            ):
                failures.append("M151 local OpenWebUI policy is unsafe")
            if openwebui_test_gateway_enabled({}):
                failures.append(
                    "M151 local OpenWebUI gateway is not disabled by default"
                )
            if not openwebui_test_gateway_authorized("Bearer uaa-local-test", {}):
                failures.append(
                    "M151 local OpenWebUI local bearer value was not accepted"
                )
            request = OpenWebUILocalChatCompletionRequest(
                model=UAA_OPENWEBUI_TEST_MODEL_ID,
                messages=[{"role": "user", "content": "token=do-not-echo"}],
            )
            response = build_openwebui_local_chat_completion_response(request)
            if "do-not-echo" in str(response):
                failures.append(
                    "M151 local OpenWebUI response echoes raw prompt content"
                )
            safety = response.get("uaa_safety", {})
            for key in [
                "provider_called",
                "model_authority_granted",
                "tool_executed",
                "memory_written",
                "context_injected",
                "external_network_called",
                "raw_prompt_logged",
                "production_authority_granted",
            ]:
                if safety.get(key) is not False:
                    failures.append(f"M151 safety flag is not false: {key}")
        except Exception as exc:
            failures.append(f"M151 local OpenWebUI contract validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "m151 local openwebui test shell",
            "local-dev-only",
            "disabled by default",
            "localhost-only",
            "openwebui is a shell, not the agent brain",
            "openai-compatible",
            "uaa-safe-local",
            "no provider call",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no external network",
            "no raw prompt logging",
            "no production authority",
        ]:
            if fragment not in docs_text:
                failures.append(f"M151 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m151_local_openwebui_test_shell_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.api.openapi import verify_openapi_contract

            paths = set(app.openapi().get("paths", {}))
            for route in M151_LOCAL_OPENWEBUI_TEST_ROUTES:
                if route not in paths:
                    failures.append(
                        f"M151 expected local OpenWebUI test route missing: {route}"
                    )
            forbidden_routes = {
                "/openwebui/execute",
                "/openwebui/bridge/run",
                "/openwebui/handoff",
                "/providers/call",
                "/providers/invoke",
                "/models/generate",
                "/models/complete",
                "/tools/execute",
                "/memory/write",
                "/context/inject",
                "/runtime/execute",
                "/model-runtime/execute",
            }
            present = sorted(paths.intersection(forbidden_routes))
            if present:
                failures.append(
                    f"M151 forbidden authority route(s) present: {', '.join(present)}"
                )
            contract_status = verify_openapi_contract(app)
            if contract_status.errors:
                failures.extend(contract_status.errors)
        except Exception as exc:
            failures.append(f"M151 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m151_local_openwebui_test_shell_launcher(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "scripts/dev/uaa_launcher.py",
            "scripts/dev/README.md",
            "tests/test_dev_launcher.py",
        ]
        failures = [
            f"missing M151 local OpenWebUI launcher file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        launcher = self._read(self.root / "scripts/dev/uaa_launcher.py").lower()
        for fragment in [
            "openwebui",
            'openwebui_host = "127.0.0.1"',
            "openwebui_port = 3000",
            "uaa_openwebui_test_gateway_enabled",
            "uaa-safe-local",
            "http://host.docker.internal:8000/v1",
            "openai_api_base_url",
            "openai_api_key",
            "uaa-local-test",
        ]:
            if fragment not in launcher:
                failures.append(f"M151 launcher missing safety fragment: {fragment}")
        for forbidden in [
            "0.0.0.0:3000",
            "--privileged",
            "--network=host",
            "docker compose",
            "docker-compose",
        ]:
            if forbidden in launcher:
                failures.append(
                    f"M151 launcher contains forbidden fragment: {forbidden}"
                )
        return self._result(criterion, failures, required_files)

    def check_m152_local_model_management_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/local_model_management/__init__.py",
            "src/ultimate_ai_agent/core/local_model_management/contracts.py",
            "src/ultimate_ai_agent/core/model_runtime/local_model_management.py",
            "docs/model_management/LOCAL_MODEL_MANAGEMENT_CHARTER.md",
            "docs/model_management/LOCAL_MODEL_MANAGEMENT_AUTHORITY_BOUNDARY.md",
            "docs/model_management/LOCAL_MODEL_MANAGEMENT_NON_GOALS.md",
            "docs/model_management/LOCAL_MODEL_MANAGEMENT_RECEIPT_PLAN.md",
            "docs/model_management/M152_TO_M153_BOUNDARY.md",
            "tests/test_m152_local_model_management.py",
            "tests/test_m152_gate_integration.py",
        ]
        failures = [
            f"missing M152 local model management file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.local_model_management import (
                REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                GgufArtifactRef,
                HardwareCapabilitySummary,
                HuggingFaceSearchPreviewRequest,
                LlamaCppSettingsPlan,
                LocalModelCandidateSummary,
                LocalModelManagementFreezeRequest,
                LocalModelManagementPolicy,
                LocalModelObservabilityPreview,
                LocalModelObservabilitySignal,
                LocalModelObservabilitySignalKind,
                build_local_model_management_freeze_record,
                build_model_selection_preview,
                validate_gguf_artifact_ref,
                validate_hardware_capability_summary,
                validate_llama_cpp_settings_plan,
                validate_local_model_management_policy,
                validate_local_model_observability_preview,
            )

            policy = validate_local_model_management_policy(
                LocalModelManagementPolicy()
            )
            unsafe_policy_flags = [
                "live_hf_search_enabled",
                "local_system_probe_enabled",
                "model_download_enabled",
                "model_file_read_enabled",
                "llama_cpp_import_enabled",
                "llama_cpp_server_enabled",
                "runtime_execution_enabled",
                "subprocess_execution_enabled",
                "network_access_enabled",
                "model_call_enabled",
                "backend_route_enabled",
                "control_center_control_enabled",
                "dependency_added",
                "production_authority_granted",
            ]
            if any(getattr(policy, field_name) for field_name in unsafe_policy_flags):
                failures.append(
                    "M152 local model management policy grants forbidden authority"
                )

            hardware = validate_hardware_capability_summary(
                HardwareCapabilitySummary(
                    summary_ref="hardware-summary:m152-gate",
                    source_ref="source:m152-injected",
                    observed_at_ref="observed-at:m152-review",
                    os_arch_bucket="darwin-arm64-bucket",
                    cpu_core_bucket="core-bucket-8-to-16",
                    ram_bucket="ram-bucket-32gb-to-64gb",
                    vram_bucket="vram-bucket-shared",
                    backend_device_family_bucket="backend-device-family-metal",
                    disk_budget_bucket="disk-budget-under-256gb",
                )
            )
            artifact = validate_gguf_artifact_ref(
                GgufArtifactRef(
                    artifact_ref="gguf-artifact:m152-qwopus-q4",
                    repo_ref="hf-repo:m152-qwopus",
                    revision_ref="hf-revision:m152-pinned",
                    filename_ref="gguf-file:qwopus-q4_k_m.gguf",
                    license_ref="license:declared-safe",
                    provenance_ref="provenance:reviewed",
                    size_bucket="size-bucket-under-20gb",
                    quantization_ref="quant:q4_k_m",
                )
            )
            settings_plan = validate_llama_cpp_settings_plan(
                LlamaCppSettingsPlan(
                    plan_ref="llama-cpp-settings-plan:m152-gate",
                    settings_ref="settings:m152-qwopus",
                    model_candidate_ref="candidate:m152-qwopus",
                    artifact_ref=artifact.artifact_ref,
                    preset_ref="model-preset:m152-default",
                    no_effect_receipt_plan_ref="receipt-plan:m152-settings-no-effect",
                )
            )
            if (
                settings_plan.server_started
                or settings_plan.subprocess_spawned
                or settings_plan.model_loaded
            ):
                failures.append("M152 llama.cpp settings plan performed runtime work")

            request = HuggingFaceSearchPreviewRequest(
                request_ref="hf-search-preview:m152-qwopus",
                query="qwopus",
                task_ref="task:coding",
                hardware_summary_ref=hardware.summary_ref,
                query_pool_ref="candidate-pool:m152-query",
                alternative_pool_ref="candidate-pool:m152-alternatives",
                no_effect_receipt_plan_ref="receipt-plan:m152-search-no-effect",
            )
            selection = build_model_selection_preview(
                request,
                [
                    LocalModelCandidateSummary(
                        candidate_ref="candidate:m152-qwopus",
                        repo_ref="hf-repo:m152-qwopus",
                        revision_ref="hf-revision:m152-pinned",
                        artifact_ref=artifact.artifact_ref,
                        filename_ref=artifact.filename_ref,
                        task_ref="task:coding",
                        license_ref=artifact.license_ref,
                        provenance_ref=artifact.provenance_ref,
                        hardware_fit_score=1.0,
                        task_capability_score=0.9,
                        query_name_score=1.0,
                        popularity_score=0.5,
                        recency_score=0.5,
                        license_provenance_score=1.0,
                    ),
                    LocalModelCandidateSummary(
                        candidate_ref="candidate:m152-alternative",
                        repo_ref="hf-repo:m152-alternative",
                        revision_ref="hf-revision:m152-pinned",
                        artifact_ref="gguf-artifact:m152-alt",
                        filename_ref="gguf-file:alt-q5.gguf",
                        task_ref="task:coding",
                        license_ref="license:declared-safe",
                        provenance_ref="provenance:reviewed",
                        hardware_fit_score=1.0,
                        task_capability_score=0.8,
                        query_name_score=0.0,
                        popularity_score=0.8,
                        recency_score=0.8,
                        license_provenance_score=1.0,
                    ),
                    LocalModelCandidateSummary(
                        candidate_ref="candidate:m152-rejected",
                        repo_ref="hf-repo:m152-rejected",
                        revision_ref="hf-revision:m152-pinned",
                        artifact_ref="gguf-artifact:m152-rejected",
                        filename_ref="gguf-file:rejected.gguf",
                        task_ref="task:coding",
                        license_ref="license:declared-safe",
                        provenance_ref="provenance:reviewed",
                        has_gguf=False,
                    ),
                ],
            )
            if (
                selection.live_search_performed
                or selection.download_performed
                or selection.model_loaded
            ):
                failures.append("M152 model selection preview performed live work")
            if selection.query_match_candidate_refs[:1] != ["candidate:m152-qwopus"]:
                failures.append("M152 query match ranking did not keep qwopus first")
            if "candidate:m152-alternative" not in selection.alternative_candidate_refs:
                failures.append(
                    "M152 alternatives did not include injected non-query candidate"
                )
            if "candidate:m152-rejected" not in selection.rejected_candidate_refs:
                failures.append("M152 unsafe candidate was not rejected")

            signal = LocalModelObservabilitySignal(
                signal_ref="observability-signal:m152-lag",
                kind=LocalModelObservabilitySignalKind.lag_summary,
                settings_plan_ref=settings_plan.plan_ref,
                safe_summary="Lag bucket summary; reduce context first.",
                suggested_adjustment_ref="settings-adjustment:m152-reduce-context",
            )
            observability = validate_local_model_observability_preview(
                LocalModelObservabilityPreview(
                    preview_ref="observability-preview:m152-redacted",
                    settings_plan_ref=settings_plan.plan_ref,
                    signal_refs=[signal.signal_ref],
                    signals=[signal],
                    no_effect_receipt_plan_ref="receipt-plan:m152-observability-no-effect",
                )
            )
            if observability.settings_applied or observability.model_call_performed:
                failures.append(
                    "M152 observability preview applied settings or called a model"
                )

            freeze_record = build_local_model_management_freeze_record(
                LocalModelManagementFreezeRequest(
                    request_ref="local-model-freeze-request:m152-gate",
                    freeze_ref="local-model-freeze:m159-planned",
                    baseline_ref="baseline:m151-accepted",
                    actor_ref="actor:foundation-gate",
                    accepted_checkpoint_refs=list(
                        REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
                    ),
                    checklist_refs=["checklist:m152-safe-contract-lane"],
                    authority_boundary_ref="authority-boundary:m152-local-model-management",
                    audit_ref="audit:m152-local-model-management",
                    replay_ref="replay:m152-local-model-management",
                    no_effect_receipt_plan_ref="receipt-plan:m152-freeze-no-effect",
                    safe_summary="Freeze accepted local model management contract refs only.",
                )
            )
            if (
                freeze_record.live_search_performed
                or freeze_record.download_performed
                or freeze_record.llama_cpp_server_started
                or freeze_record.backend_route_added
                or freeze_record.production_authority_granted
            ):
                failures.append("M152 freeze record grants forbidden live authority")
        except Exception as exc:
            failures.append(
                f"M152 local model management contract validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "m152 local model management",
            "post-m151",
            "contract-only",
            "review-only",
            "metadata-only",
            "local-only",
            "safe-ref-only",
            "disabled by default",
            "route-free",
            "no-effect",
            "model refs",
            "model profile refs",
            "model artifact refs",
            "no network access",
            "no subprocess",
            "no llama.cpp import",
            "no llama.cpp server",
            "no hugging face hub import",
            "no hugging face hub download",
            "no downloads",
            "no model load",
            "no model unload",
            "no model delete",
            "no model/provider call",
            "no backend route",
            "no control center execute control",
            "no dependency",
            "no memory write",
            "no context injection",
            "no tool execution",
            "no production authority",
        ]:
            if fragment not in docs_text:
                failures.append(f"M152 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m152_local_model_management_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        return self._result(
            criterion,
            m152_local_model_management_forbidden_fragment_failures(self.root),
            [],
        )

    def check_m152_local_model_management_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.api.openapi import verify_openapi_contract

            failures.extend(m152_openapi_route_failures(app.openapi().get("paths", {})))
            contract_status = verify_openapi_contract(app)
            if contract_status.errors:
                failures.extend(contract_status.errors)
        except Exception as exc:
            failures.append(f"M152 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m153_m165_local_model_management_progression(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/local_model_management/contracts.py",
            "docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md",
            "docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md",
            "tests/test_m153_m165_local_model_management_progression.py",
        ]
        failures = [
            f"missing M153-M165 local model management file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.core.local_model_management import (
                FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS,
                SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                FutureLiveContractStatus,
                LocalModelManagementLane,
                M160HuggingFaceGgufSearchPolicy,
                M162ModelAcquisitionPolicy,
                build_local_model_management_m153_m165_progression_plan,
                build_m163_m165_disabled_future_live_contracts,
                validate_m160_huggingface_gguf_search_policy,
                validate_m162_model_acquisition_policy,
                validate_future_live_local_model_contract,
                validate_local_model_management_m153_m165_progression_plan,
            )

            if REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS != tuple(
                f"checkpoint:m{index}" for index in range(153, 166)
            ):
                failures.append("M153-M165 exact checkpoint refs drifted")
            if SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != tuple(
                f"checkpoint:m{index}" for index in range(153, 160)
            ):
                failures.append("M153-M159 safe lane refs drifted")
            if LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != (
                "checkpoint:m160",
                "checkpoint:m161",
            ):
                failures.append("M160-M161 live read-only lane refs drifted")
            if FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != ():
                failures.append(
                    "M153-M165 future live lane refs should be empty after M165"
                )
            if LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != (
                "checkpoint:m162",
            ):
                failures.append("M162 live acquisition lane refs drifted")
            if LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != (
                "checkpoint:m163",
            ):
                failures.append("M163 live llama.cpp supervisor lane refs drifted")
            if LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != (
                "checkpoint:m164",
            ):
                failures.append("M164 live OpenAI gateway lane refs drifted")
            if LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS != (
                "checkpoint:m165",
            ):
                failures.append("M165 live settings tuning lane refs drifted")

            plan = validate_local_model_management_m153_m165_progression_plan(
                build_local_model_management_m153_m165_progression_plan()
            )
            if len(plan.milestone_contracts) != 13:
                failures.append(
                    "M153-M165 progression does not contain 13 milestone contracts"
                )
            safe_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane == LocalModelManagementLane.safe_contract
            ]
            future_live_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane == LocalModelManagementLane.future_live_contract_only
            ]
            live_read_only_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane == LocalModelManagementLane.live_bounded_read_only
            ]
            live_acquisition_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane
                == LocalModelManagementLane.live_exact_approved_acquisition
            ]
            live_llama_cpp_supervisor_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane == LocalModelManagementLane.live_llama_cpp_supervisor
            ]
            live_openai_gateway_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane == LocalModelManagementLane.live_openai_gateway
            ]
            live_settings_tuning_lane = [
                contract.milestone_ref
                for contract in plan.milestone_contracts
                if contract.lane == LocalModelManagementLane.live_settings_tuning
            ]
            if tuple(safe_lane) != SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
                failures.append(
                    "M153-M159 contracts are not exactly safe_contract lane"
                )
            if (
                tuple(live_read_only_lane)
                != LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
            ):
                failures.append(
                    "M160-M161 contracts are not exactly live_bounded_read_only lane"
                )
            if (
                tuple(live_acquisition_lane)
                != LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
            ):
                failures.append(
                    "M162 contract is not exactly live_exact_approved_acquisition lane"
                )
            if (
                tuple(live_llama_cpp_supervisor_lane)
                != LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
            ):
                failures.append(
                    "M163 contract is not exactly live_llama_cpp_supervisor lane"
                )
            if (
                tuple(live_openai_gateway_lane)
                != LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
            ):
                failures.append("M164 contract is not exactly live_openai_gateway lane")
            if (
                tuple(live_settings_tuning_lane)
                != LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
            ):
                failures.append(
                    "M165 contract is not exactly live_settings_tuning lane"
                )
            if (
                tuple(future_live_lane)
                != FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS
            ):
                failures.append(
                    "M153-M165 future_live_contract_only lane should be empty after M165"
                )
            unsafe_plan_flags = [
                "live_capability_authorized",
                "live_hf_search_performed",
                "local_system_probe_performed",
                "model_download_performed",
                "llama_cpp_server_started",
                "subprocess_execution_performed",
                "network_access_performed",
                "model_call_performed",
                "settings_applied",
                "backend_route_added",
                "control_center_control_added",
                "dependency_added",
                "production_authority_granted",
            ]
            if any(getattr(plan, field_name) for field_name in unsafe_plan_flags):
                failures.append(
                    "M153-M165 progression plan grants forbidden live authority"
                )

            policy = validate_m160_huggingface_gguf_search_policy(
                M160HuggingFaceGgufSearchPolicy()
            )
            if (
                not policy.bounded_read_only
                or not policy.unauthenticated_only
                or not policy.https_get_only
                or not policy.metadata_only
                or policy.download_allowed
                or policy.model_call_allowed
            ):
                failures.append("M160 Hugging Face GGUF search policy is unsafe")

            acquisition_policy = validate_m162_model_acquisition_policy(
                M162ModelAcquisitionPolicy()
            )
            if (
                not acquisition_policy.exact_user_approval_required
                or not acquisition_policy.pinned_revision_required
                or not acquisition_policy.exact_filename_required
                or not acquisition_policy.uaa_owned_cache_required
                or not acquisition_policy.unauthenticated_by_default
                or acquisition_policy.token_use_allowed
                or acquisition_policy.model_call_allowed
                or acquisition_policy.llama_cpp_process_allowed
                or acquisition_policy.subprocess_allowed
            ):
                failures.append("M162 GGUF acquisition policy is unsafe")

            future_contracts = build_m163_m165_disabled_future_live_contracts()
            if future_contracts != []:
                failures.append(
                    "M163-M165 disabled future live contracts should be empty after M165"
                )
            for future_contract in future_contracts:
                validated = validate_future_live_local_model_contract(future_contract)
                if (
                    validated.status
                    != FutureLiveContractStatus.disabled_until_runtime_milestone
                ):
                    failures.append(
                        f"{validated.contract_ref} is not disabled until runtime milestone"
                    )
                for field_name in [
                    "live_capability_authorized",
                    "network_access_performed",
                    "local_system_probe_performed",
                    "download_performed",
                    "model_file_read_performed",
                    "model_cache_write_performed",
                    "llama_cpp_import_performed",
                    "subprocess_execution_performed",
                    "server_started",
                    "prompt_processed",
                    "model_call_performed",
                    "settings_applied",
                    "runtime_restart_performed",
                    "backend_route_added",
                    "control_center_control_added",
                    "openwebui_settings_mutation_requested",
                    "openwebui_privileged_management_used",
                    "openwebui_plugin_added",
                    "openwebui_is_agent_brain",
                    "memory_write_performed",
                    "context_injection_performed",
                    "tool_execution_performed",
                    "dependency_added",
                    "production_authority_granted",
                ]:
                    if getattr(validated, field_name):
                        failures.append(
                            f"{validated.contract_ref} unsafe flag true: {field_name}"
                        )

            failures.extend(m152_openapi_route_failures(app.openapi().get("paths", {})))
            failures.extend(
                m152_local_model_management_forbidden_fragment_failures(self.root)
            )
        except Exception as exc:
            failures.append(
                f"M153-M165 local model management progression validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for index in range(153, 166):
            if f"m{index}" not in docs_text:
                failures.append(f"M153-M165 docs missing checkpoint m{index}")
        for fragment in [
            "safe_contract",
            "live_bounded_read_only",
            "live_exact_approved_acquisition",
            "live_llama_cpp_supervisor",
            "live_openai_gateway",
            "live_settings_tuning",
            "future_live_contract_only",
            "m160 live bounded read-only hf gguf search only",
            "m161 live bounded read-only local system capability probing only",
            "m162 live exact-approved gguf acquisition only",
            "m163 live loopback llama.cpp supervisor only",
            "m164 live local `/v1` gateway only",
            "m165 live approved settings tuning only",
            "no unapproved downloads",
            "no shell string",
            "no non-loopback llama.cpp server",
            "tools/functions and streaming remain disabled",
            "no raw prompt",
            "no raw response",
            "no serials",
            "no usernames",
            "no raw paths",
            "no environment dump",
            "no broad scans",
            "no control center execute controls",
            "no dependency",
            "no memory write",
            "no context injection",
            "no tool execution",
            "no production authority",
        ]:
            if fragment not in docs_text:
                failures.append(f"M153-M165 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m160_bounded_hf_gguf_search_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/local_model_management/hf_search.py",
            "docs/model_management/M160_HUGGING_FACE_GGUF_SEARCH.md",
            "tests/test_m160_hf_gguf_search.py",
        ]
        failures = [
            f"missing M160 Hugging Face GGUF search file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.local_model_management import (
                FakeM160HuggingFaceSearchTransport,
                M160HuggingFaceGgufSearchPolicy,
                M160HuggingFaceGgufSearchRequest,
                search_huggingface_gguf_models,
                validate_m160_huggingface_gguf_search_policy,
            )

            policy = validate_m160_huggingface_gguf_search_policy(
                M160HuggingFaceGgufSearchPolicy()
            )
            if (
                not policy.bounded_read_only
                or not policy.unauthenticated_only
                or not policy.https_get_only
                or not policy.metadata_only
                or not policy.gguf_candidates_only
                or policy.raw_response_storage_allowed
                or policy.token_use_allowed
                or policy.download_allowed
                or policy.model_call_allowed
                or policy.dependency_added
                or policy.production_authority_granted
            ):
                failures.append("M160 search policy is unsafe")
            result = search_huggingface_gguf_models(
                M160HuggingFaceGgufSearchRequest(
                    request_ref="hf-gguf-search-request:m160-gate",
                    query="qwopus",
                    limit=3,
                ),
                transport=FakeM160HuggingFaceSearchTransport(
                    [
                        {
                            "id": "org/qwopus",
                            "downloads": 5,
                            "likes": 1,
                            "cardData": {"license": "apache-2.0"},
                            "siblings": [
                                {"rfilename": "qwopus-q4_k_m.gguf", "size": 1234},
                                {"rfilename": "model.safetensors", "size": 100},
                            ],
                        }
                    ]
                ),
            )
            if (
                not result.live_search_performed
                or not result.network_access_performed
                or not result.unauthenticated
                or not result.metadata_only
                or result.raw_response_stored
                or result.token_used
                or result.download_performed
                or result.model_call_performed
                or result.backend_route_added
                or result.dependency_added
                or result.production_authority_granted
            ):
                failures.append("M160 search result is unsafe")
            if result.candidate_refs != ["hf-gguf-candidate:m160-org-qwopus"]:
                failures.append(
                    "M160 fake search did not return the expected GGUF candidate"
                )
        except Exception as exc:
            failures.append(f"M160 Hugging Face GGUF search validation failed: {exc}")

        source_path = (
            self.root / "src/ultimate_ai_agent/core/local_model_management/hf_search.py"
        )
        source = self._read(source_path)
        for fragment in [
            'HF_MODELS_API_URL = "https://huggingface.co/api/models"',
            "M160_MAX_RESPONSE_BYTES",
            "request.urlopen",
            "json.loads",
            'filter": "gguf"',
        ]:
            if fragment not in source:
                failures.append(
                    f"M160 search source missing required bounded-search fragment: {fragment}"
                )
        for forbidden in [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import huggingface_hub",
            "from huggingface_hub import",
            "hf_hub_download(",
            "snapshot_download(",
            "Authorization",
            "Cookie",
            "import " + "subprocess",
            "from subprocess import",
            "subprocess" + ".",
            "import llama_cpp",
            "from llama_cpp import",
            "llama_cpp.",
            "openai.OpenAI(",
            "download_performed=True",
            "model_call_performed=True",
            "raw_response_stored=True",
            "backend_route_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
        ]:
            if forbidden in source:
                failures.append(
                    f"M160 search source contains forbidden fragment: {forbidden}"
                )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "m160 bounded hugging face gguf search",
            "core-only",
            "bounded read-only",
            "unauthenticated",
            "https get",
            "metadata-only",
            "gguf",
            "no downloads",
            "no auth",
            "no token",
            "no raw response storage",
            "no model card storage",
            "no model/provider call",
            "no subprocess",
            "no llama.cpp",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
        ]:
            if fragment not in docs_text:
                failures.append(f"M160 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)
