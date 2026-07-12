from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403
from ultimate_ai_agent.core.sandbox_calculation.static_safety import is_exact_sealed_calculation_subprocess_site


class FoundationGateLegacyChecksPart001Mixin:
    """Legacy checks from versioning_consistent through m85_expired_revoked_approval_denies."""
    def check_versioning_consistent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        version = self._active_version()
        if not version:
            failures.append("VERSION.md active baseline missing")
        else:
            pyproject_version = self._regex_first(
                self.root / "pyproject.toml", r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]"
            )
            init_version = self._regex_first(
                self.root / "src/ultimate_ai_agent/__init__.py",
                r"(?m)^__version__\s*=\s*['\"]([^'\"]+)['\"]",
            )
            readme = self._read(self.root / "README.md")
            expected_underscored = self._version_key(version)
            expected_package_version = self._package_version(version)
            expected_import = (
                f"docs/archive/releases/v{expected_underscored}/README_IMPORT.md"
            )
            expected_master = (
                f"docs/archive/releases/v{expected_underscored}/master_plan.md"
            )
            if pyproject_version != expected_package_version:
                failures.append("pyproject.toml version mismatch")
            if init_version != expected_package_version:
                failures.append("package __version__ mismatch")
            if f"v{version}" not in readme:
                failures.append("README.md missing active version")
            if expected_import not in readme:
                failures.append("README.md missing active archived import README")
            if expected_master not in readme:
                failures.append("README.md missing active archived master plan")
        return self._result(
            criterion, failures, ["VERSION.md", "pyproject.toml", "README.md"]
        )

    def check_release_docs_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        version = self._active_version()
        version_key = self._version_key(version or "0.0.0")
        required = [
            f"docs/archive/releases/v{version_key}/README_IMPORT.md",
            f"docs/archive/releases/v{version_key}/master_plan.md",
            f"docs/release_notes/v{version_key}.md",
            f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_foundation_modules_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/contracts/execution_contract.py",
            "src/ultimate_ai_agent/core/contracts/context_pack.py",
            "src/ultimate_ai_agent/core/ledger/events.py",
            "src/ultimate_ai_agent/core/world_state/models.py",
            "src/ultimate_ai_agent/core/context_budget/models.py",
            "src/ultimate_ai_agent/core/runtime/local_runtime.py",
            "src/ultimate_ai_agent/core/adapters/sdk_manifest.py",
            "src/ultimate_ai_agent/core/consent/grants.py",
            "src/ultimate_ai_agent/core/tools/broker.py",
            "src/ultimate_ai_agent/core/secrets/broker.py",
            "src/ultimate_ai_agent/core/providers/registry.py",
            "src/ultimate_ai_agent/core/memory/store.py",
            "src/ultimate_ai_agent/core/files/manager.py",
            "src/ultimate_ai_agent/core/truth/evidence.py",
            "src/ultimate_ai_agent/core/kernel/runner.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/gate/shadow_replay.py",
            "scripts/run_foundation_gate.py",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m7_modules_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_router/__init__.py",
            "src/ultimate_ai_agent/core/model_router/enums.py",
            "src/ultimate_ai_agent/core/model_router/profiles.py",
            "src/ultimate_ai_agent/core/model_router/policies.py",
            "src/ultimate_ai_agent/core/model_router/requests.py",
            "src/ultimate_ai_agent/core/model_router/decisions.py",
            "src/ultimate_ai_agent/core/model_router/router.py",
            "src/ultimate_ai_agent/core/model_router/validation.py",
            "src/ultimate_ai_agent/core/costs/__init__.py",
            "src/ultimate_ai_agent/core/costs/enums.py",
            "src/ultimate_ai_agent/core/costs/budgets.py",
            "src/ultimate_ai_agent/core/costs/estimates.py",
            "src/ultimate_ai_agent/core/costs/decisions.py",
            "src/ultimate_ai_agent/core/costs/governor.py",
            "src/ultimate_ai_agent/core/costs/validation.py",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_blocked_modules_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        blocked_paths = [
            "src/ultimate_ai_agent/core/scanners",
            "src/ultimate_ai_agent/core/companion",
            "src/ultimate_ai_agent/core/skill_factory",
            "src/ultimate_ai_agent/core/self_improvement",
            "src/ultimate_ai_agent/core/autopilot",
            "src/ultimate_ai_agent/core/browser_automation",
            "src/ultimate_ai_agent/core/sdk_runtime_delegation",
            "src/ultimate_ai_agent/core/a2a_runtime_delegation",
        ]
        failures = [
            f"blocked module exists: {path}"
            for path in blocked_paths
            if (self.root / path).exists()
        ]
        return self._result(criterion, failures, blocked_paths)

    def check_forbidden_runtime_integrations_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib.request",
            "from " + "urllib import request",
            "import " + "boto3",
            "import " + "ollama",
            "import " + "vllm",
            "import " + "llama_cpp",
            "import " + "sglang",
            "import " + "openai",
            "import " + "anthropic",
            "import " + "google.generativeai",
            "import " + "chromadb",
            "import " + "faiss",
            "import " + "pgvector",
            "import " + "pinecone",
            "import " + "psycopg",
            "import " + "sentence_transformers",
            "import " + "weaviate",
        ]
        forbidden_contains = [
            "from " + "openai import",
            "from " + "anthropic import",
            "http" + "://",
            "https" + "://",
        ]
        failures = []
        allowed_manual_smoke_network_files = {
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
        }
        allowed_m160_hf_search_file = (
            "src/ultimate_ai_agent/core/local_model_management/hf_search.py"
        )
        allowed_m162_acquisition_file = (
            "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py"
        )
        allowed_m164_gateway_file = (
            "src/ultimate_ai_agent/core/local_model_management/gateway.py"
        )
        allowed_provider_catalog_file = (
            "src/ultimate_ai_agent/core/providers/catalog.py"
        )
        allowed_provider_credential_validation_file = (
            "src/ultimate_ai_agent/core/providers/credential_validation.py"
        )
        allowed_tiny_provider_invocation_file = (
            "src/ultimate_ai_agent/core/providers/invocation.py"
        )
        allowed_tiny_provider_live_adapter_file = (
            "src/ultimate_ai_agent/core/providers/live_invocation_adapter.py"
        )
        allowed_m72_fixture_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
        }
        provider_catalog_https_prefix = "https" + "://"
        provider_catalog_url_markers = (
            'setup_link="' + provider_catalog_https_prefix,
            'api_docs_link="' + provider_catalog_https_prefix,
            'pricing_link="' + provider_catalog_https_prefix,
            "(ProviderSourceKind.",
        )
        provider_catalog_runtime_markers = (
            "requests.",
            "httpx.",
            "urllib.request.",
            "urlopen(",
            ".get(",
            ".post(",
            ".request(",
        )
        provider_credential_validation_endpoint_marker = (
            provider_catalog_https_prefix + "api.openai.com/v1/models"
        )
        tiny_provider_invocation_endpoint_markers = (
            provider_catalog_https_prefix + "api.openai.com/v1/responses",
            provider_catalog_https_prefix + "api.anthropic.com/v1/messages",
        )
        allowed_web_hybrid_endpoint_lines = {
            "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py": (
                'FIRECRAWL_CLOUD_BASE_URL = "https://api.firecrawl.dev"'
            ),
            "src/ultimate_ai_agent/core/web_access/firecrawl_markdown.py": (
                'FIRECRAWL_SELF_HOSTED_DEFAULT_ENDPOINT = "http://127.0.0.1:3002"'
            ),
            "src/ultimate_ai_agent/core/web_access/searxng_search.py": (
                'SEARXNG_SEARCH_DEFAULT_ENDPOINT = "http://127.0.0.1:8888"'
            ),
        }
        for path, line_no, stripped in self._runtime_lines():
            if self._is_static_scanner_text(stripped):
                continue
            if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                if path in allowed_manual_smoke_network_files and stripped.startswith(
                    (
                        "import urllib.request",
                        "from urllib import request",
                        "from urllib import error",
                    )
                ):
                    continue
                if (
                    path == allowed_provider_credential_validation_file
                    and stripped.startswith(
                        ("from urllib import request", "from urllib import error")
                    )
                ):
                    continue
                if (
                    path == allowed_tiny_provider_live_adapter_file
                    and stripped.startswith(
                        ("from urllib import request", "from urllib import error")
                    )
                ):
                    continue
                failures.append(f"{path}:{line_no} forbidden import")
            if path in allowed_m72_fixture_files and (
                "docs.example.test" in stripped or "evil.example" in stripped
            ):
                continue
            if (
                path == allowed_m160_hf_search_file
                and "huggingface.co/api/models" in stripped
            ):
                continue
            if (
                path == "src/ultimate_ai_agent/core/gate/evaluators.py"
                and "https://huggingface.co" in stripped
            ):
                continue
            if (
                path == "src/ultimate_ai_agent/core/gate/evaluators.py"
                and "http://127.0.0.1:8080" in stripped
            ):
                continue
            if (
                path == allowed_m162_acquisition_file
                and "https://huggingface.co" in stripped
            ):
                continue
            if (
                path == allowed_m164_gateway_file
                and "http://127.0.0.1:8080" in stripped
            ):
                continue
            if (
                path == allowed_provider_catalog_file
                and provider_catalog_https_prefix in stripped
                and any(marker in stripped for marker in provider_catalog_url_markers)
                and not any(
                    marker in stripped for marker in provider_catalog_runtime_markers
                )
            ):
                continue
            if (
                path == allowed_provider_credential_validation_file
                and provider_credential_validation_endpoint_marker in stripped
            ):
                continue
            if (
                path == allowed_tiny_provider_invocation_file
                and any(
                    marker in stripped
                    for marker in tiny_provider_invocation_endpoint_markers
                )
            ):
                continue
            if stripped == allowed_web_hybrid_endpoint_lines.get(path):
                continue
            if any(pattern in stripped for pattern in forbidden_contains):
                failures.append(f"{path}:{line_no} forbidden integration reference")
            if ".get(" in stripped and any(
                marker in stripped for marker in forbidden_contains[-2:]
            ):
                failures.append(f"{path}:{line_no} possible network call")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_shell_execution_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        forbidden = [
            "import " + "subprocess",
            "from " + "subprocess import",
            "os." + "system(",
            "po" + "pen(",
            "sub" + "process.",
        ]
        allowed_m163_supervisor_file = (
            "src/ultimate_ai_agent/core/local_model_management/llama_cpp_supervisor.py"
        )
        allowed_phase04_command_adapter_file = (
            "src/ultimate_ai_agent/core/runtime_gateway/command.py"
        )
        allowed_sealed_arithmetic_adapter_file = (
            "src/ultimate_ai_agent/core/sandbox_calculation/backend.py"
        )
        sealed_source = self._read(self.root / allowed_sealed_arithmetic_adapter_file)
        sealed_adapter_exact = all(
            is_exact_sealed_calculation_subprocess_site(
                rel_path=allowed_sealed_arithmetic_adapter_file,
                source=sealed_source,
                fragment=fragment,
            )
            for fragment in ("subprocess" + ".run(", "subprocess" + ".Popen(")
        )
        failures = []
        for path, line_no, stripped in self._runtime_lines():
            if self._is_static_scanner_text(stripped):
                continue
            exact_allowed_path = path in {
                allowed_m163_supervisor_file,
                allowed_phase04_command_adapter_file,
            } or (path == allowed_sealed_arithmetic_adapter_file and sealed_adapter_exact)
            if exact_allowed_path and any(fragment in stripped for fragment in forbidden):
                continue
            if any(fragment in stripped for fragment in forbidden):
                failures.append(f"{path}:{line_no} shell execution")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_broad_filesystem_scanning_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        forbidden = [
            ".rglob(" + '"*"' + ")",
            ".rglob(" + "'*'" + ")",
            "os." + "walk(",
            "Path." + "home(",
        ]
        failures = [
            f"{path}:{line_no} broad filesystem scan"
            for path, line_no, stripped in self._runtime_lines()
            if not self._is_static_scanner_text(stripped)
            and any(fragment in stripped for fragment in forbidden)
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_secret_hygiene_clean(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        secret_assignment = re.compile(
            r"(?i)(api_key|password|client_secret|private_key|token|auth_token)\s*=\s*['\"][A-Za-z0-9_\-.:/]{16,}['\"]"
        )
        failures = []
        private_key_begin = "-----" + "BEGIN"
        private_key_end = "PRIVATE" + " KEY-----"
        for rel_path in self._tracked_runtime_files():
            content = self._read(self.root / rel_path)
            if private_key_begin in content and private_key_end in content:
                failures.append(f"{rel_path}: private key header")
            for match in secret_assignment.finditer(content):
                value = match.group(0).lower()
                if any(
                    marker in value
                    for marker in [
                        "mock",
                        "dummy",
                        "example",
                        "placeholder",
                        "oauth_refresh_token",
                        "token_secret",
                    ]
                ):
                    continue
                failures.append(f"{rel_path}: secret-like assignment")
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_tool_broker_blocks_advanced_adapters(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        for category in (
            ToolCategory.mcp,
            ToolCategory.a2a,
            ToolCategory.sdk_adapter,
            ToolCategory.skill,
        ):
            registry = ToolRegistry()
            tool_id = f"{category.value}.gate_check"
            registry.register_tool(
                ToolManifest(
                    tool_id=tool_id,
                    display_name="Gate Check",
                    category=category,
                    description="Foundation Gate category block check.",
                    execution_mode=ToolExecutionMode.mock,
                    risk_level=ToolRiskLevel.low,
                    capability_flag=f"{category.value}_gate_check",
                    owner="core.gate",
                    source="local",
                    version="0.0.0",
                )
            )
            decision = ToolBroker(
                registry, CapabilityFirewallPolicy()
            ).evaluate_request(
                ToolRequest(
                    request_id=f"req_{category.value}_gate",
                    run_id="run_foundation_gate",
                    tool_id=tool_id,
                    actor_context=self._actor(),
                    requested_action="execute",
                    purpose="foundation_gate_check",
                    data_classification=DataBoundary.project_private,
                ),
                ConsentLedger(),
            )
            if decision.status != ToolDecisionStatus.blocked_by_foundation_gate:
                failures.append(f"{category.value} was not blocked")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/tools/broker.py"]
        )

    def check_truth_evidence_contracts_valid(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        try:
            source = TruthSourceManifest(
                source_id="truth_gate",
                source_type=TruthSourceType.canonical_file,
                authority_level=TruthAuthorityLevel.authoritative,
                display_name="Gate Truth Source",
                owner="core.gate",
                data_classification="project_private",
            )
            item = EvidenceItem(
                evidence_id="evidence_gate",
                source_id=source.source_id,
                source_type=TruthSourceType.canonical_file,
                summary="Gate evidence contract check.",
                freshness_status=SourceFreshnessStatus.current,
            )
            claim = ClaimEvidence(
                claim_id="claim_gate",
                claim_text="Foundation Gate is verification only.",
                verification_status=ClaimVerificationStatus.supported,
                evidence_refs=[item.evidence_id],
                source_ids=[source.source_id],
                freshness_status=SourceFreshnessStatus.current,
            )
            EvidenceManifest(
                manifest_id="evm_gate",
                run_id="run_foundation_gate",
                claims=[claim],
                evidence_items=[item],
            )
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/truth"])

    def check_governed_web_evidence_intake_no_live_fetch(
        self,
        criterion: FoundationGateCriterion,
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/truth/web_evidence.py",
            "docs/truth/GOVERNED_WEB_EVIDENCE.md",
            "docs/canonical/59_truth_grounding_and_evidence_governance.md",
            "tests/test_governed_web_evidence.py",
        ]
        failures = [
            f"missing governed web evidence file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        source_path = self.root / "src/ultimate_ai_agent/core/truth/web_evidence.py"
        if source_path.exists():
            source = self._read(source_path)
            for fragment in [
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "selenium",
                "playwright",
                "openai.",
                "anthropic.",
            ]:
                if fragment in source:
                    failures.append(
                        f"governed web evidence source contains live integration: {fragment}"
                    )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "web evidence intake, no live fetch",
            "operator-supplied metadata only",
            "live fetch denied",
            "browser automation denied",
            "openwebui web search denied",
            "model/provider calls denied",
            "raw body storage denied",
            "downloads denied",
            "auth denied",
            "cookies denied",
            "redirects denied",
            "allowlisted https get lane",
            "openwebui web search is outside uaa governance unless routed through the future allowlisted https get lane",
        ]:
            if fragment not in docs_text:
                failures.append(
                    f"governed web evidence docs missing fragment: {fragment}"
                )

        try:
            from ultimate_ai_agent.core.truth import (
                FutureAllowlistedHttpsGetLanePlan,
                GovernedWebEvidenceIntakePolicy,
                build_fixture_governed_web_evidence_intake_bundle,
                build_fixture_governed_web_evidence_intake_record,
                validate_future_allowlisted_https_get_lane_plan,
                validate_governed_web_evidence_intake_bundle,
                validate_governed_web_evidence_intake_policy,
                validate_governed_web_evidence_intake_record,
            )

            policy = validate_governed_web_evidence_intake_policy(
                GovernedWebEvidenceIntakePolicy()
            )
            if (
                not policy.disabled_by_default
                or not policy.operator_supplied_metadata_only
                or policy.live_fetch_allowed
                or policy.browser_automation_allowed
                or policy.openwebui_web_search_allowed
                or policy.model_provider_calls_allowed
                or policy.raw_body_storage_allowed
                or policy.downloads_allowed
                or policy.auth_allowed
                or policy.cookies_allowed
                or policy.redirects_allowed
                or policy.backend_route_allowed
            ):
                failures.append("governed web evidence policy allows unsafe authority")

            record = validate_governed_web_evidence_intake_record(
                build_fixture_governed_web_evidence_intake_record()
            )
            bundle = validate_governed_web_evidence_intake_bundle(
                build_fixture_governed_web_evidence_intake_bundle()
            )
            if bundle.evidence_records[0].evidence_ref != record.evidence_ref:
                failures.append(
                    "governed web evidence fixture bundle does not bind evidence record"
                )

            try:
                validate_governed_web_evidence_intake_record(
                    record.model_copy(update={"live_fetch_performed": True})
                )
                failures.append("governed web evidence accepted live_fetch_performed")
            except (ValidationError, ValueError) as exc:
                if "WEB_EVIDENCE_NO_LIVE_FETCH" not in str(exc):
                    failures.append(
                        f"governed web evidence live fetch denial reason drifted: {exc}"
                    )

            future_plan = validate_future_allowlisted_https_get_lane_plan(
                FutureAllowlistedHttpsGetLanePlan(
                    rollback_plan_ref="rollback:web-evidence-future-lane",
                    non_goal_ref="non-goal:web-evidence-future-lane",
                )
            )
            if (
                not future_plan.future_lane_only
                or not future_plan.disabled_by_default
                or not future_plan.https_get_only
                or not future_plan.allowlisted_targets_only
                or future_plan.auth_allowed
                or future_plan.cookies_allowed
                or future_plan.redirects_allowed
                or future_plan.downloads_allowed
                or future_plan.raw_body_storage_allowed
            ):
                failures.append(
                    "future governed web evidence HTTPS GET lane boundary drifted"
                )
        except Exception as exc:
            failures.append(f"governed web evidence validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_memory_file_contracts_valid(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        try:
            MemoryRecord(
                memory_id="mem_gate",
                memory_type=MemoryType.artifact_summary,
                scope=MemoryScope.project,
                scope_id="workspace_gate",
                authority=MemoryAuthority.event_ledger_derived,
                sensitivity=MemorySensitivity.project_private,
                content="Recall only: gate check. Canonical files and event ledger outrank memory.",
                source_refs=[
                    MemorySourceRef(
                        source_id="notes/m5.md",
                        source_type="file_change",
                        file_ref="notes/m5.md",
                        event_ref="evt_gate",
                    )
                ],
            )
            FileRef(
                file_ref="file_gate",
                path="notes/m5.md",
                kind=FileKind.generated,
                sensitivity=FileSensitivity.project_private,
                source_event_ref="evt_gate",
            )
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/memory", "src/ultimate_ai_agent/core/files"],
        )

    def check_m5_shadow_replay_passes(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        replay = run_m5_shadow_replay()
        failures = list(replay.failures)
        warnings = list(replay.warnings)
        if not replay.passed and not failures:
            failures.append("shadow replay did not pass")
        status = (
            FoundationGateStatus.passed if not failures else FoundationGateStatus.failed
        )
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=status,
            safe_message="M5 shadow replay passed."
            if status == FoundationGateStatus.passed
            else criterion.failure_message,
            evidence_refs=[*replay.event_ids, replay.receipt_ref or "receipt_missing"],
            failures=failures,
            warnings=warnings,
        )

    def check_model_router_decision_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            profile = ModelCapabilityProfile(
                model_profile_id="m7_gate_local",
                provider_kind=ModelProviderKind.local_runtime,
                runtime_id="rt_gate",
                model_id="local_policy_model",
                display_name="Local Policy Model",
                capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding],
                privacy_class=ModelPrivacyClass.local_only,
                max_context_tokens=8192,
                enabled=True,
                owner="core.gate",
                source="foundation_gate",
                version="0.0.0",
            )
            request = ModelRouteRequest(
                request_id="m7_gate_route",
                run_id="run_foundation_gate",
                actor_context=self._actor(),
                task_class="coding",
                prompt_summary="Foundation Gate model routing metadata check.",
                data_classification=DataClassification(
                    classification=ClassificationValue.project_private,
                    source="foundation_gate",
                ),
                required_capabilities=[ModelTaskCapability.chat],
                estimated_input_tokens=256,
                estimated_output_tokens=128,
                routing_policy=ModelRoutingPolicy(
                    policy_id="m7_gate_policy",
                    required_capabilities=[ModelTaskCapability.chat],
                    prefer_local=True,
                    allow_cloud=False,
                    allow_paid=False,
                ),
                available_profiles=[profile],
            )
            decision = ModelRouter().route(request)
            if decision.status != ModelRouteStatus.selected:
                failures.append(f"route status was {decision.status}")
            if decision.selected_profile_id != profile.model_profile_id:
                failures.append("local policy profile was not selected")
        except (ValidationError, ValueError) as exc:
            failures.append(str(exc))
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_router"]
        )

    def check_cost_governor_blocks_over_budget(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [
                CostBudget(
                    budget_id="m7_gate_budget", scope=BudgetScope.run, max_cost_usd=1
                )
            ],
        )
        if decision.status != BudgetStatus.denied or decision.allowed:
            failures.append("over-budget route was not denied")
        if "COST_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("cost denial reason missing")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/core/costs"])

    def check_m7_arbitrary_approval_ref_rejected(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_cloud_profile()
        request = self._gate_route_request(
            profile,
            data_classification=ClassificationValue.sensitive_personal,
            approval_ref="arbitrary-string",
            policy=ModelRoutingPolicy(
                policy_id="m7_gate_approval_policy",
                required_capabilities=[ModelTaskCapability.chat],
                allow_cloud=True,
                allow_paid=True,
                require_human_approval_for_cloud=True,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.approval_required:
            failures.append(f"route status was {decision.status}")
        if decision.selected_profile_id is not None:
            failures.append("arbitrary approval_ref selected a cloud profile")
        if "APPROVAL_REF_UNVALIDATED" not in decision.reason_codes:
            failures.append("unvalidated approval reason missing")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"]
        )

    def check_m7_context_budget_exhaustion_blocks_route(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_local_profile()
        request = self._gate_route_request(
            profile,
            context_budget=ContextBudget(
                model_context_limit=4096,
                system_prompt_tokens=1000,
                tool_schema_tokens=1000,
                world_state_tokens=1000,
                context_pack_tokens=1000,
                completion_reserve_tokens=96,
                safety_margin_tokens=0,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.context_too_small:
            failures.append(f"route status was {decision.status}")
        if decision.selected_profile_id is not None:
            failures.append("exhausted context budget selected a profile")
        if "CONTEXT_BUDGET_EXHAUSTED" not in decision.reason_codes:
            failures.append("context budget exhaustion reason missing")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"]
        )

    def check_m7_soft_budget_warning_allows_route(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_soft_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [
                CostBudget(
                    budget_id="m7_gate_soft_budget",
                    scope=BudgetScope.run,
                    max_cost_usd=1,
                    hard_limit=False,
                )
            ],
        )
        if not decision.allowed or decision.status != BudgetStatus.warning:
            failures.append("soft budget overage was not allowed with warning")
        if "SOFT_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("soft budget reason missing")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/costs/governor.py"]
        )

    def check_m7_hard_budget_denies_route(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        decision = CostGovernor().evaluate(
            CostEstimate(
                estimate_id="m7_gate_hard_estimate",
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
                estimated_cost_usd=2,
            ),
            [
                CostBudget(
                    budget_id="m7_gate_hard_budget",
                    scope=BudgetScope.run,
                    max_cost_usd=1,
                    hard_limit=True,
                )
            ],
        )
        if decision.allowed or decision.status != BudgetStatus.denied:
            failures.append("hard budget overage was not denied")
        if "HARD_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("hard budget reason missing")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/costs/governor.py"]
        )

    def check_m7_cost_warnings_visible_in_route_decision(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        profile = self._gate_local_profile(
            cost_per_1k_input_tokens=0.02, cost_per_1k_output_tokens=0.02
        )
        request = self._gate_route_request(
            profile,
            policy=ModelRoutingPolicy(
                policy_id="m7_gate_soft_route_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=True,
                allow_paid=True,
                max_estimated_cost_usd=0.01,
                max_estimated_cost_hard_limit=False,
            ),
        )
        decision = ModelRouter().route(request)
        if decision.status != ModelRouteStatus.selected:
            failures.append(f"route status was {decision.status}")
        if "SOFT_BUDGET_EXCEEDED" not in decision.reason_codes:
            failures.append("soft budget warning was not visible in route decision")
        if "with policy warnings" not in decision.safe_message:
            failures.append("route decision safe_message did not mention warnings")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"]
        )

    def check_api_manifest_endpoint_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import build_api_manifest

        failures: List[str] = []
        manifest = build_api_manifest(app)
        paths = {route.path for route in manifest.routes}
        if "/api/manifest" not in paths:
            failures.append("/api/manifest missing from route inventory")
        active_package_version = self._package_version(self._active_version() or "")
        if manifest.api_version != active_package_version:
            failures.append("manifest api_version does not match active baseline")
        if not manifest.no_runtime_integrations:
            failures.append("manifest does not declare no_runtime_integrations")
        return self._result(
            criterion,
            failures,
            [
                "src/ultimate_ai_agent/api/manifest.py",
                "src/ultimate_ai_agent/api/app.py",
            ],
        )

    def check_openapi_contract_valid(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.openapi import verify_openapi_contract

        status = self._verify_openapi_contract(app)
        failures = list(status.errors)
        if not status.openapi_generated:
            failures.append("OpenAPI schema was not generated")
        if not status.version_consistent:
            failures.append("OpenAPI version mismatch")
        if not status.route_inventory_valid:
            failures.append("route inventory invalid")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/api/openapi.py"],
            status.warnings,
        )

    def check_api_operation_ids_unique(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        routes = iter_api_route_items(app)
        failures = operation_id_failures(routes)
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"]
        )

    def check_forbidden_runtime_routes_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import (
            FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS,
            FORBIDDEN_ROUTE_FRAGMENTS,
        )

        failures = forbidden_route_fragment_failures(
            iter_api_route_items(app),
            FORBIDDEN_ROUTE_FRAGMENTS,
            exact_path_exemptions=FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS,
        )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/api/openapi.py"]
        )

    def check_agents_md_guidance_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "AGENTS.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/standards/agents_md_support.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        agents_md = self._read(self.root / "AGENTS.md")
        for marker in [
            "Ultimate AI Agent",
            "/api/manifest",
            "OpenAPI",
            "Do not add runtime model calls",
        ]:
            if marker not in agents_md:
                failures.append(f"AGENTS.md missing marker: {marker}")
        return self._result(criterion, failures, required)

    def check_runtime_agent_config_loading_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        forbidden = [
            "AGENTS" + ".md",
            "agent_config",
            "agent-config",
            "runtime_config",
            "workspace_config",
            "load_agent_config",
        ]
        allowed_runtime_config_posture = {
            "runtime_configured_metadata_only",
            "runtime_config_mutation_performed",
            "runtime_config_mutation_enabled",
            "runtime_config_write_performed",
            "runtime_config_write_enabled",
            "can_write_runtime_config",
            "unsigned_runtime_config_override_performed",
            "unsigned_runtime_config_override_enabled",
        }
        failures = [
            f"{path}:{line_no} runtime agent config loading reference"
            for path, line_no, stripped in self._runtime_lines()
            if path
            not in {
                "src/ultimate_ai_agent/api/openapi.py",
                "src/ultimate_ai_agent/core/gate/evaluators.py",
            }
            and not self._is_static_scanner_text(stripped)
            and any(
                fragment in stripped
                and not (
                    fragment == "runtime_config"
                    and any(
                        allowed_fragment in stripped
                        for allowed_fragment in allowed_runtime_config_posture
                    )
                )
                for fragment in forbidden
            )
        ]
        return self._result(criterion, failures, ["src/ultimate_ai_agent"])

    def check_m8_model_runtime_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/__init__.py",
            "src/ultimate_ai_agent/core/model_runtime/enums.py",
            "src/ultimate_ai_agent/core/model_runtime/manifests.py",
            "src/ultimate_ai_agent/core/model_runtime/requests.py",
            "src/ultimate_ai_agent/core/model_runtime/responses.py",
            "src/ultimate_ai_agent/core/model_runtime/simulator.py",
            "src/ultimate_ai_agent/core/model_runtime/adapters.py",
            "src/ultimate_ai_agent/core/model_runtime/validation.py",
            "src/ultimate_ai_agent/core/model_runtime/redaction.py",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m8_runtime_kinds_stub_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeKind

        allowed = {
            "simulated",
            "local_stub",
            "cloud_stub",
            "openai_compatible_stub",
            "sdk_adapter_stub",
        }
        actual = {kind.value for kind in ModelRuntimeKind}
        failures = [
            f"unexpected runtime kind: {kind}" for kind in sorted(actual - allowed)
        ]
        missing = allowed - actual
        failures.extend(f"missing runtime kind: {kind}" for kind in sorted(missing))
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/enums.py"]
        )

    def check_m8_model_runtime_no_real_calls(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        runtime_root = self.src_root / "core" / "model_runtime"
        forbidden = [
            "import " + "openai",
            "from " + "openai import",
            "import " + "anthropic",
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "socket",
            "sub" + "process",
            "token" + "izer",
            "tiktoken",
            "sentencepiece",
            "bill" + "ing",
            "api" + "_key",
            "API" + "_KEY",
        ]
        failures = []
        for path in sorted(self._context.rglob(runtime_root, "*.py")):
            rel_path = self._context.relative_path(path)
            for line_no, line in enumerate(
                self._context.read_text(path, encoding="utf-8").splitlines(), start=1
            ):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(f"{rel_path}:{line_no} real runtime fragment")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_runtime"]
        )

    def check_m8_simulation_endpoint_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        schema = self._openapi_schema()
        failures = []
        route = schema.get("paths", {}).get("/model-runtime/simulate", {}).get("post")
        if not route:
            failures.append("/model-runtime/simulate missing")
        elif route.get("operationId") != "post_model_runtime_simulate":
            failures.append("simulate endpoint operation ID is not stable")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m8_runtime_responses_simulated_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeOutputFormat,
            ModelRuntimeResponse,
            ModelRuntimeResponseStatus,
            response_is_truth_authority,
        )

        failures = []
        response = ModelRuntimeResponse(
            runtime_response_id="m8_gate_response",
            runtime_request_id="m8_gate_request",
            run_id="run_foundation_gate",
            status=ModelRuntimeResponseStatus.simulated_success,
            output_format=ModelRuntimeOutputFormat.text,
            output_summary="Simulated response for request m8_gate_request; no model was called.",
            model_profile_id="m8_gate_profile",
            adapter_id="m8_gate_adapter",
            metadata={"simulated": True, "truth_authority": False},
        )
        if response.status != ModelRuntimeResponseStatus.simulated_success:
            failures.append("response status was not simulated_success")
        if response_is_truth_authority(response):
            failures.append("response became truth authority")
        if "no model was called" not in response.output_summary:
            failures.append("simulated response marker missing")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/responses.py"],
        )

    def check_m8_runtime_secret_prompt_blocked(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeOutputFormat,
            ModelRuntimeRequest,
            ModelRuntimeSafetyMode,
        )

        failures = []
        try:
            ModelRuntimeRequest(
                runtime_request_id="m8_gate_secret_request",
                run_id="run_foundation_gate",
                model_profile_id="m8_gate_profile",
                model_id="m8_gate_model",
                adapter_id="m8_gate_adapter",
                actor_context=self._actor(),
                prompt_summary="api_" + "key='ABCDEFGHIJKLMNOP'",
                input_refs=["context_pack:m8_gate"],
                output_format=ModelRuntimeOutputFormat.text,
                estimated_input_tokens=10,
                max_output_tokens=10,
                safety_mode=ModelRuntimeSafetyMode.simulated,
                data_classification=DataClassification(
                    classification=ClassificationValue.project_private,
                    source="foundation_gate",
                ),
            )
            failures.append("secret-like prompt summary was accepted")
        except (ValidationError, ValueError):
            pass
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/requests.py"],
        )

    def check_m8_api_validation_secret_echo_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import (
            ModelRuntimeRequestValidatePayload,
            ModelRuntimeSimulatePayload,
            post_simulate_model_runtime,
            post_validate_model_runtime_manifest,
            post_validate_model_runtime_request,
        )

        failures = []
        secret = "sk_" + "test_" + "secret_" + "value"
        assignment = "api_" + "key=" + secret
        manifest_with_secret = {"metadata": {"note": assignment}}
        request_with_secret = {"prompt_summary": assignment}
        cases = [
            (
                "/model-runtime/manifests/validate",
                lambda: post_validate_model_runtime_manifest(manifest_with_secret),
            ),
            (
                "/model-runtime/manifests/validate",
                lambda: post_validate_model_runtime_manifest({"api_" + "key": secret}),
            ),
            (
                "/model-runtime/requests/validate",
                lambda: post_validate_model_runtime_request(
                    ModelRuntimeRequestValidatePayload(
                        request=request_with_secret,
                        manifest=manifest_with_secret,
                    )
                ),
            ),
            (
                "/model-runtime/simulate",
                lambda: post_simulate_model_runtime(
                    ModelRuntimeSimulatePayload(
                        request=request_with_secret,
                        manifest=manifest_with_secret,
                    )
                ),
            ),
        ]
        for path, call in cases:
            response = call()
            if response.success is not False:
                failures.append(f"{path} did not return a validation failure")
            response_text = response.model_dump_json()
            if secret in response_text or assignment in response_text:
                failures.append(f"{path} echoed secret-like input")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m85_approval_authority_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/approvals/__init__.py",
            "src/ultimate_ai_agent/core/approvals/enums.py",
            "src/ultimate_ai_agent/core/approvals/requests.py",
            "src/ultimate_ai_agent/core/approvals/grants.py",
            "src/ultimate_ai_agent/core/approvals/decisions.py",
            "src/ultimate_ai_agent/core/approvals/authority.py",
            "src/ultimate_ai_agent/core/approvals/policies.py",
            "src/ultimate_ai_agent/core/approvals/validation.py",
            "src/ultimate_ai_agent/core/approvals/receipts.py",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m85_arbitrary_approval_refs_rejected(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import (
            ApprovalDecisionStatus,
            LocalApprovalAuthority,
        )

        request = self._m85_gate_approval_request()
        authority = LocalApprovalAuthority()
        authority.create_request(request)
        decision = authority.validate_for_request(request, "human_approved_ref_123")
        failures = []
        if decision.allowed:
            failures.append("arbitrary approval_ref was allowed")
        if decision.status != ApprovalDecisionStatus.invalid:
            failures.append("arbitrary approval_ref did not return invalid")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"]
        )

    def check_m85_local_approval_grant_validates(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import (
            ApprovalDecisionStatus,
            LocalApprovalAuthority,
        )

        request = self._m85_gate_approval_request()
        authority = LocalApprovalAuthority()
        authority.create_request(request)
        grant = authority.grant(
            request.approval_request_id, approved_by_actor_id="foundation_gate"
        )
        decision = authority.validate_for_request(request, grant.approval_ref)
        failures = []
        if not decision.allowed:
            failures.append("valid approval grant was denied")
        if decision.status != ApprovalDecisionStatus.approved:
            failures.append("valid approval grant did not return approved")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"]
        )

    def check_m85_expired_revoked_approval_denies(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from datetime import timedelta

        from ultimate_ai_agent.core.approvals import (
            ApprovalDecisionStatus,
            LocalApprovalAuthority,
        )
        from ultimate_ai_agent.core.time import utc_now

        failures = []
        expired_request = self._m85_gate_approval_request("m85_gate_expired")
        expired_authority = LocalApprovalAuthority()
        expired_authority.create_request(expired_request)
        expired = expired_authority.grant(
            expired_request.approval_request_id,
            approved_by_actor_id="foundation_gate",
            expires_at=utc_now() - timedelta(seconds=1),
        )
        expired_decision = expired_authority.validate_for_request(
            expired_request, expired.approval_ref
        )
        if (
            expired_decision.allowed
            or expired_decision.status != ApprovalDecisionStatus.expired
        ):
            failures.append("expired approval was accepted")

        revoked_request = self._m85_gate_approval_request("m85_gate_revoked")
        revoked_authority = LocalApprovalAuthority()
        revoked_authority.create_request(revoked_request)
        revoked = revoked_authority.grant(
            revoked_request.approval_request_id, approved_by_actor_id="foundation_gate"
        )
        revoked_authority.revoke(revoked.approval_ref, "foundation gate check")
        revoked_decision = revoked_authority.validate_for_request(
            revoked_request, revoked.approval_ref
        )
        if (
            revoked_decision.allowed
            or revoked_decision.status != ApprovalDecisionStatus.revoked
        ):
            failures.append("revoked approval was accepted")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/approvals/authority.py"]
        )
