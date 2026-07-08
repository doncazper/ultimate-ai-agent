from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart003Mixin:
    """Legacy checks from documentation_integrity_current through m13_backend_api_contract_unchanged."""
    def check_documentation_integrity_current(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        version = self._active_version()
        version_key = self._version_key(version or "0.0.0")
        required = [
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/maintenance/documentation_integrity_checklist.md",
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
            f"docs/archive/releases/v{version_key}/README_IMPORT.md",
            f"docs/archive/releases/v{version_key}/master_plan.md",
            f"docs/release_notes/v{version_key}.md",
            f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        readme = self._read(self.root / "README.md")
        if (
            version
            and f"docs/archive/releases/v{version_key}/README_IMPORT.md" not in readme
        ):
            failures.append("README.md missing active archived import README")
        if (
            version
            and f"docs/archive/releases/v{version_key}/master_plan.md" not in readme
        ):
            failures.append("README.md missing active archived master plan")
        if "docs/DOCUMENTATION_INDEX.md" not in readme:
            failures.append("README.md missing documentation index")
        if "docs/canonical/CANONICAL_DOC_MAP.md" not in readme:
            failures.append("README.md missing canonical doc map")

        unsafe_claims = [
            "tailscale integration is implemented",
            "headscale integration is implemented",
            "remote execution is supported",
            "mobile camera access is implemented",
            "microphone capture is implemented",
            "gps access is implemented",
            "skill factory is implemented",
            "scanner runtime is implemented",
            "production_ready=true",
            "real_model_runtime_ready=true",
            "remote_execution_ready=true",
            "mobile_sensor_ready=true",
            "plugin_or_native_build_ready=true",
        ]
        active_docs = [
            "README.md",
            "VERSION.md",
            "AGENTS.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/api/README.md",
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/runtime/model_runtime_adapter_harness.md",
            "docs/runtime/local_loopback_model_runtime.md",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "docs/remote/REMOTE_WORKER_FOUNDATION.md",
            "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
            "docs/remote/REMOTE_JOB_ENVELOPE.md",
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/mobile_companion_backlog.md",
            "docs/backlog/device_capability_broker_backlog.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
        ]
        for rel_path in active_docs:
            path = self.root / rel_path
            if not path.exists():
                continue
            source = self._read(path).lower()
            for phrase in unsafe_claims:
                if phrase in source:
                    failures.append(
                        f"{rel_path} contains unsafe implementation claim: {phrase}"
                    )
        return self._result(criterion, failures, required)

    def check_roadmap_milestone_charters_current(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/canonical/09_roadmap.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        if failures:
            return self._result(criterion, failures, required)

        charter = self._read(self.root / "docs/roadmap/MILESTONE_CHARTERS.md").lower()
        sequence = self._read(
            self.root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
        ).lower()
        roadmap = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        for field in [
            "version",
            "milestone code",
            "title",
            "status",
            "purpose",
            "allowed scope",
            "must not add",
            "dependencies",
            "acceptance criteria",
            "review prompt required",
            "hardening patch expectation",
            "source-of-truth docs",
            "notes",
        ]:
            if field not in charter:
                failures.append(f"charter template missing {field}")
        if (
            "m14" not in sequence
            or "web control center local backend connection stabilization"
            not in sequence
        ):
            failures.append(
                "M14 sequence is not local backend connection stabilization"
            )
        if (
            "m15" not in sequence
            or "approval queue + receipt/event viewer ui" not in sequence
        ):
            failures.append(
                "M15 sequence is not approval queue + receipt/event viewer UI"
            )
        if (
            "v0.17.4" not in sequence
            or "local browser smoke" not in sequence
            or "not m14" not in sequence
        ):
            failures.append("v0.17.4 browser smoke boundary is not preserved")
        if (
            "m14 is web control center local backend connection stabilization"
            not in roadmap
        ):
            failures.append("canonical roadmap does not resolve M14")
        if "approval queue + receipt/event viewer ui moves to m15" not in roadmap:
            failures.append(
                "canonical roadmap does not move approval/receipt UI to M15"
            )
        if "v0.18.0 / m14" not in roadmap or "implemented" not in roadmap:
            failures.append(
                "canonical roadmap does not mark M14 connection stabilization as implemented in v0.18.0"
            )
        forbidden = [
            "m14 - local browser smoke",
            "m14 — local browser smoke",
            "m14: local browser smoke",
            "m14 - ux polish",
            "m14 — ux polish",
            "m14: ux polish",
        ]
        version_tuple = self._active_version_tuple()
        if version_tuple < (0, 19, 0):
            forbidden.extend(
                [
                    "m15 is implemented",
                    "m15 has been implemented",
                    "implemented m15",
                    "m15 implementation complete",
                ]
            )
        combined = "\n".join([sequence, roadmap])
        for phrase in forbidden:
            if phrase in combined:
                failures.append(f"ambiguous or unsafe M14 claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_codex_plugin_governance_docs_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        combined = "\n".join(
            self._read(self.root / path).lower()
            for path in required
            if (self.root / path).exists()
        )
        expectations = {
            "iOS/macOS build plugins disabled": [
                "build ios apps",
                "build macos apps",
                "disabled",
            ],
            "Computer Use disabled": ["computer use", "disabled"],
            "Chrome authenticated profile disabled": [
                "chrome authenticated",
                "disabled",
            ],
            "plugin/skill installers disabled": ["plugin/skill installers", "disabled"],
            "Browser + Build Web Apps approval boundary": [
                "browser + build web apps",
                "approval",
            ],
        }
        for label, fragments in expectations.items():
            if not all(fragment in combined for fragment in fragments):
                failures.append(f"missing policy phrase: {label}")
        forbidden_enablement_claims = [
            "plugins are enabled",
            "xcode workflow is enabled",
            "computer use is enabled",
            "chrome authenticated profile control is enabled",
            "plugin installers are enabled",
        ]
        for phrase in forbidden_enablement_claims:
            if phrase in combined:
                failures.append(f"unsafe plugin enablement claim: {phrase}")
        return self._result(criterion, failures, required)

    def check_m11_runtime_readiness_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/runtime_readiness/__init__.py",
            "src/ultimate_ai_agent/core/runtime_readiness/enums.py",
            "src/ultimate_ai_agent/core/runtime_readiness/matrix.py",
            "src/ultimate_ai_agent/core/runtime_readiness/reports.py",
            "src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py",
            "src/ultimate_ai_agent/core/runtime_readiness/validators.py",
            "src/ultimate_ai_agent/core/runtime_readiness/gate.py",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
            "tests/test_runtime_capability_matrix.py",
            "tests/test_manual_smoke_report_validation.py",
            "tests/test_runtime_readiness_report.py",
            "tests/test_runtime_readiness_api_routes.py",
            "tests/test_runtime_readiness_no_execution.py",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m11_runtime_capability_matrix_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import (
            RuntimeCapabilityStatus,
            RuntimeSurface,
            build_matrix,
        )

        matrix = build_matrix()
        entries = {entry.surface: entry for entry in matrix.entries}
        expected = {
            RuntimeSurface.remote_worker_foundation.value: RuntimeCapabilityStatus.dry_run_only.value,
            RuntimeSurface.private_mesh_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.tailnet_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.headscale_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.generic_wireguard_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.tailscale_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.cloud_provider_runtime.value: RuntimeCapabilityStatus.blocked.value,
            RuntimeSurface.manual_loopback_smoke.value: RuntimeCapabilityStatus.manual_only.value,
            RuntimeSurface.mobile_companion_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.device_capability_broker_planned.value: RuntimeCapabilityStatus.planned_disabled.value,
            RuntimeSurface.codex_plugin_governance.value: RuntimeCapabilityStatus.planned_disabled.value,
        }
        failures = []
        for surface, status in expected.items():
            entry = entries.get(surface)
            if entry is None:
                failures.append(f"missing matrix surface: {surface}")
            elif entry.status != status:
                failures.append(
                    f"{surface} status is {entry.status}, expected {status}"
                )
        if not matrix.assert_no_runtime_expansion():
            failures.append("matrix allows runtime expansion")
        if not matrix.assert_foundation_gate_coverage():
            failures.append("matrix entry missing Foundation Gate coverage")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/runtime_readiness/matrix.py"],
        )

    def check_m11_manual_smoke_report_validation_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import (
            validate_manual_smoke_report,
        )
        from ultimate_ai_agent.core.runtime_readiness.gate import (
            m11_gate_safe_smoke_report_payload,
        )

        safe = validate_manual_smoke_report(m11_gate_safe_smoke_report_payload())
        unsafe_payloads = [
            (
                "raw prompt",
                {**m11_gate_safe_smoke_report_payload(), "raw_prompt": "user prompt"},
            ),
            (
                "secret response",
                {
                    **m11_gate_safe_smoke_report_payload(),
                    "response_preview": "api" + "_key='abcdefghijklmnop'",
                },
            ),
            (
                "remote endpoint",
                {
                    **m11_gate_safe_smoke_report_payload(),
                    "endpoint_summary": "https" + "://api.example.com",
                },
            ),
            (
                "cloud claim",
                {
                    **m11_gate_safe_smoke_report_payload(),
                    "metadata": {"claim": "cloud provider model call executed"},
                },
            ),
            (
                "authoritative output",
                {
                    **m11_gate_safe_smoke_report_payload(),
                    "model_output_authoritative": True,
                },
            ),
        ]
        failures = []
        if not safe.allowed:
            failures.append("safe manual smoke report was rejected")
        for label, payload in unsafe_payloads:
            validation = validate_manual_smoke_report(payload)
            if validation.allowed:
                failures.append(f"unsafe manual smoke report accepted: {label}")
            if "abcdefghijklmnop" in validation.safe_message:
                failures.append("unsafe secret echoed in validation message")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py"],
        )

    def check_m11_no_production_readiness_claim(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.runtime_readiness import build_readiness_report

        report = build_readiness_report()
        failures = []
        checks = {
            "production_ready": report.production_ready,
            "real_model_runtime_ready": report.real_model_runtime_ready,
            "remote_execution_ready": report.remote_execution_ready,
            "mobile_sensor_ready": report.mobile_sensor_ready,
            "plugin_or_native_build_ready": report.plugin_or_native_build_ready,
            "model_output_authoritative": report.model_output_authoritative,
        }
        failures.extend(
            f"{name} is true" for name, value in checks.items() if value is True
        )
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/runtime_readiness/reports.py"],
        )

    def check_m11_runtime_api_status_validation_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import FORBIDDEN_ROUTE_FRAGMENTS

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        required = {
            "/runtime/readiness",
            "/runtime/capability-matrix",
            "/runtime/smoke-reports/validate",
        }
        failures = [
            f"missing runtime route: {path}" for path in sorted(required - set(paths))
        ]
        for path in sorted(path for path in paths if path.startswith("/runtime")):
            route = paths[path]
            if "runtime-readiness" not in route.tags:
                failures.append(f"{path} has unexpected tags {route.tags}")
            if not route.validation_only:
                failures.append(f"{path} is not validation/status only")
        unsafe_routes = [
            path
            for path in paths
            if path.startswith("/runtime")
            and any(fragment in path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
        ]
        failures.extend(
            f"forbidden runtime route present: {path}" for path in sorted(unsafe_routes)
        )
        return self._result(
            criterion,
            failures,
            [
                "src/ultimate_ai_agent/api/app.py",
                "src/ultimate_ai_agent/api/openapi.py",
            ],
        )

    def check_m11_no_smoke_script_execution_in_gate(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        for rel_path in ["scripts/verify_all.py", "scripts/run_foundation_gate.py"]:
            source = self._read(self.root / rel_path)
            if "local_loopback_smoke.py" in source:
                failures.append(f"{rel_path} references local_loopback_smoke.py")
        return self._result(
            criterion,
            failures,
            ["scripts/verify_all.py", "scripts/run_foundation_gate.py"],
        )

    def check_m11_no_runtime_expansion_imports(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        package = self.root / "src/ultimate_ai_agent/core/runtime_readiness"
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib",
            "from " + "urllib import",
            "import " + "socket",
            "import " + "subprocess",
            "import " + "openai",
            "import " + "anthropic",
            "import " + "tiktoken",
            "import " + "tokenizers",
        ]
        forbidden_fragments = ["billing", "eval(", "exec("]
        failures = []
        for path in sorted(package.glob("*.py")):
            rel_path = self._context.relative_path(path)
            for line_no, stripped in enumerate(self._read(path).splitlines(), start=1):
                stripped = stripped.strip()
                if self._is_static_scanner_text(stripped) or stripped.startswith("["):
                    continue
                if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                    failures.append(f"{rel_path}:{line_no} forbidden import")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(f"{rel_path}:{line_no} forbidden runtime fragment")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/runtime_readiness"]
        )

    def check_m11_no_remote_mesh_mobile_or_plugin_enablement(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        sources = [
            "src/ultimate_ai_agent/core/runtime_readiness",
            "src/ultimate_ai_agent/api/app.py",
            "docs/runtime/RUNTIME_READINESS.md",
            "docs/runtime/MANUAL_SMOKE_REPORTS.md",
            "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
        ]
        forbidden_claims = [
            "remote_execution_ready=true",
            "live mesh is enabled",
            "tailnet is enabled",
            "headscale is connected",
            "wireguard is connected",
            "mobile sensors are enabled",
            "camera access is implemented",
            "plugin enablement is implemented",
            "native build execution is enabled",
            "computer use automation is enabled",
        ]
        combined = ""
        for source in sources:
            path = self.root / source
            if path.is_dir():
                combined += "\n".join(self._read(child) for child in path.glob("*.py"))
            else:
                combined += "\n" + self._read(path)
        lowered = combined.lower()
        failures = [
            f"unsafe enablement claim: {phrase}"
            for phrase in forbidden_claims
            if phrase in lowered
        ]
        return self._result(criterion, failures, sources)

    def check_m12_control_center_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/control_center/__init__.py",
            "src/ultimate_ai_agent/core/control_center/enums.py",
            "src/ultimate_ai_agent/core/control_center/manifest.py",
            "src/ultimate_ai_agent/core/control_center/dashboard.py",
            "src/ultimate_ai_agent/core/control_center/actions.py",
            "src/ultimate_ai_agent/core/control_center/summaries.py",
            "src/ultimate_ai_agent/core/control_center/validation.py",
            "src/ultimate_ai_agent/core/control_center/policy.py",
            "tests/test_control_center_manifest.py",
            "tests/test_control_center_dashboard.py",
            "tests/test_control_center_action_preview.py",
            "tests/test_control_center_api_routes.py",
            "tests/test_control_center_no_execution.py",
            "tests/test_m12_gate_integration.py",
            "docs/control_center/CONTROL_CENTER_CONTRACT.md",
            "docs/control_center/DASHBOARD_SNAPSHOT.md",
            "docs/control_center/ACTION_PREVIEW_POLICY.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m12_control_center_manifest_read_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import (
            ControlCenterCapabilityStatus,
            build_control_center_manifest,
        )

        manifest = build_control_center_manifest()
        allowed_statuses = {
            ControlCenterCapabilityStatus.available_read_only.value,
            ControlCenterCapabilityStatus.preview_only.value,
            ControlCenterCapabilityStatus.validation_only.value,
            ControlCenterCapabilityStatus.planned_disabled.value,
            ControlCenterCapabilityStatus.blocked.value,
            ControlCenterCapabilityStatus.not_implemented.value,
        }
        failures = []
        for surface in manifest.surfaces:
            if surface.status not in allowed_statuses:
                failures.append(f"{surface.surface} has unsafe status {surface.status}")
            if surface.execution_allowed:
                failures.append(f"{surface.surface} allows execution")
        for capability in [
            "runtime_execution",
            "model_execution",
            "provider_invocation",
            "remote_dispatch",
            "mobile_sensor_access",
            "plugin_enablement",
            "frontend_build_tooling",
        ]:
            if capability not in manifest.blocked_capabilities:
                failures.append(f"missing blocked capability: {capability}")
        if manifest.metadata.get("frontend_implemented") is not False:
            failures.append("manifest does not mark frontend unimplemented")
        if manifest.metadata.get("production_control_center") is not False:
            failures.append("manifest implies production Control Center")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/control_center/manifest.py"],
        )

    def check_m12_control_center_dashboard_secret_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import build_control_center_dashboard
        from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like

        snapshot = build_control_center_dashboard(
            api_route_count=74, foundation_gate_status="passed"
        )
        failures = []
        if contains_secret_like(snapshot.model_dump(mode="json")):
            failures.append("dashboard contains secret-like values")
        if snapshot.runtime_readiness_summary.production_ready:
            failures.append("dashboard claims production runtime readiness")
        if snapshot.remote_worker_summary.execution_enabled:
            failures.append("dashboard enables remote worker execution")
        if snapshot.mobile_planning_summary.sensor_access_enabled:
            failures.append("dashboard enables mobile sensors")
        if snapshot.plugin_governance_summary.plugin_enablement_allowed:
            failures.append("dashboard enables plugins")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/control_center/dashboard.py"],
        )

    def check_m12_control_center_action_preview_no_execution(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.control_center import (
            ControlCenterActionKind,
            ControlCenterRiskLevel,
            preview_control_center_action,
        )

        base = {
            "request_id": "m12_gate_preview",
            "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
            "action_kind": ControlCenterActionKind.view_status,
            "target_ref": "dashboard",
            "purpose": "review status",
            "risk_level": ControlCenterRiskLevel.safe,
            "data_classification": "system_internal",
            "consent_refs": [],
        }
        failures = []
        safe = preview_control_center_action(base)
        if not safe.allowed:
            failures.append("safe preview was not allowed")
        unsafe_cases = [
            (
                "execute action",
                {**base, "action_kind": ControlCenterActionKind.disabled_execute},
            ),
            ("runtime execute", {**base, "target_ref": "runtime/execute/model"}),
            ("remote dispatch", {**base, "target_ref": "remote-workers/dispatch/job"}),
            ("plugin enable", {**base, "target_ref": "plugins/enable/build-web-apps"}),
            ("mobile sensor", {**base, "target_ref": "mobile/sensors/camera"}),
            (
                "provider invocation",
                {**base, "metadata": {"claim": "provider invocation requested"}},
            ),
            (
                "credential use",
                {**base, "metadata": {"claim": "credential use requested"}},
            ),
            ("mutation", {**base, "metadata": {"claim": "mutate file requested"}}),
            ("arbitrary approval", {**base, "approval_ref": "approval_any_string"}),
        ]
        for label, payload in unsafe_cases:
            decision = preview_control_center_action(payload)
            if decision.allowed:
                failures.append(f"unsafe preview allowed: {label}")
            if decision.metadata.get("executed") is not False:
                failures.append(f"preview execution marker unsafe: {label}")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/control_center/actions.py"],
        )

    def check_m12_control_center_api_read_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items
        from ultimate_ai_agent.api.openapi import (
            FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS,
            FORBIDDEN_ROUTE_FRAGMENTS,
        )

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        required = {
            "/control-center/manifest",
            "/control-center/dashboard",
            "/control-center/status",
            "/control-center/routes",
            "/control-center/approvals/summary",
            "/control-center/runtime-readiness/summary",
            "/control-center/foundation-gate/summary",
            "/control-center/actions/preview",
        }
        failures = [
            f"missing control-center route: {path}"
            for path in sorted(required - set(paths))
        ]
        for path in sorted(
            path for path in paths if path.startswith("/control-center")
        ):
            route = paths[path]
            if "control-center" not in route.tags:
                failures.append(f"{path} has unexpected tags {route.tags}")
            is_founder_loop_summary = (
                path in FOUNDER_LOOP_CONTROL_CENTER_ROUTES
                and route.method == "GET"
                and route.side_effect_class == "local_dev_workspace_only"
            )
            is_founder_loop_local_sensitive_read_model = (
                path
                in {
                    "/control-center/proof/index",
                    "/control-center/proof/{proof_ref}",
                    "/control-center/start-here/summary",
                    "/control-center/trust-authority/matrix",
                }
                and route.method == "GET"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "local_sensitive"
                and route.protected_route
                and route.blocked_from_production
            )
            is_founder_loop_decision_state = (
                path in FOUNDER_LOOP_ACTION_DECISION_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "action_decision"
                and route.blocked_from_production
            )
            is_founder_loop_action_envelope_state = (
                path in FOUNDER_LOOP_ACTION_ENVELOPE_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "today_to_action_envelope"
                and route.blocked_from_production
            )
            is_founder_loop_chat_durable_receipt_state = (
                path in FOUNDER_LOOP_CHAT_DURABLE_RECEIPT_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "chat_durable_receipt"
                and route.blocked_from_production
            )
            is_founder_loop_memory_review_decision_state = (
                path in FOUNDER_LOOP_MEMORY_REVIEW_DECISION_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "memory_review_decision"
                and route.blocked_from_production
            )
            is_founder_loop_local_task_commit_state = (
                path in FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "action_decision"
                and route.blocked_from_production
            )
            is_founder_loop_memory_context_action_proposal_state = (
                path in FOUNDER_LOOP_MEMORY_CONTEXT_ACTION_PROPOSAL_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "memory_context_pack_action_proposal"
                and route.blocked_from_production
            )
            is_founder_loop_memory_feedback_state = (
                path in FOUNDER_LOOP_MEMORY_FEEDBACK_ROUTES
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "memory_feedback"
                and route.blocked_from_production
            )
            is_tiny_provider_lane_state = (
                path == "/control-center/providers/exact-approved-lanes/tiny"
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "provider_exact_approved_lane"
                and route.blocked_from_production
            )
            is_provider_credential_validation_state = (
                path == "/control-center/providers/credentials/validate"
                and route.method == "POST"
                and route.side_effect_class == "governed_network_read_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "provider_credential_validation"
                and route.blocked_from_production
            )
            is_web_evidence_product_slice_state = (
                path == "/control-center/web-evidence/attach"
                and route.method == "POST"
                and route.side_effect_class == "governed_network_read_only"
                and route.route_classification == "local_sensitive"
                and route.protected_route
                and route.approval_posture == "not_required_for_route_classification"
                and not route.idempotency_required
                and route.rate_limit_targeted
                and route.rate_limit_group == "web_evidence_product_slice"
                and route.blocked_from_production
            )
            is_coding_cockpit_read_model = (
                path in CONTROL_CENTER_CODING_COCKPIT_ROUTES
                and route.method == "GET"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "local_sensitive"
                and route.protected_route
                and route.approval_posture == "not_required_for_route_classification"
                and not route.idempotency_required
                and not route.rate_limit_targeted
                and route.rate_limit_group is None
                and route.blocked_from_production
            )
            is_work_board_read_model = (
                path in CONTROL_CENTER_WORK_BOARD_ROUTES
                and route.method == "GET"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "local_sensitive"
                and route.protected_route
                and route.approval_posture == "not_required_for_route_classification"
                and not route.idempotency_required
                and not route.rate_limit_targeted
                and route.rate_limit_group is None
                and route.blocked_from_production
            )
            is_control_center_runtime_cockpit_read_model = (
                path in CONTROL_CENTER_RUNTIME_COCKPIT_ROUTES
                and route.method == "GET"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "local_sensitive"
                and route.protected_route
                and route.approval_posture == "not_required_for_route_classification"
                and not route.idempotency_required
                and not route.rate_limit_targeted
                and route.rate_limit_group is None
                and route.blocked_from_production
            )
            is_crm_read_model = (
                path in CONTROL_CENTER_CRM_COMMAND_CENTER_ROUTES
                and route.method == "GET"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "local_readonly"
                and route.protected_route
                and route.approval_posture == "not_required_for_route_classification"
                and not route.idempotency_required
                and not route.rate_limit_targeted
                and route.rate_limit_group is None
                and route.blocked_from_production
            )
            is_crm_or_work_board_command_state = (
                path
                in (
                    CONTROL_CENTER_CRM_LOCAL_MUTATION_PATHS
                    | CONTROL_CENTER_WORK_BOARD_COMMAND_ROUTES
                )
                and route.method == "POST"
                and route.side_effect_class == "local_dev_workspace_only"
                and route.route_classification == "mutating_requires_authority"
                and route.protected_route
                and route.approval_posture == "required_before_mutation_authority"
                and route.idempotency_required
                and not route.rate_limit_targeted
                and route.rate_limit_group is None
                and route.blocked_from_production
            )
            if (
                not route.validation_only
                and not is_founder_loop_summary
                and not is_founder_loop_local_sensitive_read_model
                and not is_founder_loop_decision_state
                and not is_founder_loop_action_envelope_state
                and not is_founder_loop_chat_durable_receipt_state
                and not is_founder_loop_memory_review_decision_state
                and not is_founder_loop_local_task_commit_state
                and not is_founder_loop_memory_context_action_proposal_state
                and not is_founder_loop_memory_feedback_state
                and not is_tiny_provider_lane_state
                and not is_provider_credential_validation_state
                and not is_web_evidence_product_slice_state
                and not is_coding_cockpit_read_model
                and not is_work_board_read_model
                and not is_control_center_runtime_cockpit_read_model
                and not is_crm_read_model
                and not is_crm_or_work_board_command_state
            ):
                failures.append(
                    f"{path} is not read-only/preview-only/founder-loop-state"
                )
        unsafe_routes = [
            path
            for path in paths
            if path.startswith("/control-center")
            and path not in FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS
            and any(fragment in path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
        ]
        failures.extend(
            f"forbidden control-center route present: {path}"
            for path in sorted(unsafe_routes)
        )
        return self._result(
            criterion,
            failures,
            [
                "src/ultimate_ai_agent/api/app.py",
                "src/ultimate_ai_agent/api/openapi.py",
            ],
        )

    def check_m12_no_frontend_dependencies(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        forbidden_paths = [
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "vite.config.ts",
            "vite.config.js",
            "next.config.js",
            "next.config.ts",
            "tailwind.config.js",
            "tailwind.config.ts",
            "components.json",
            "node_modules",
        ]
        failures = [
            f"frontend artifact exists: {path}"
            for path in forbidden_paths
            if (self.root / path).exists()
        ]
        pyproject = self._read(self.root / "pyproject.toml").lower()
        for dependency in ["react", "next", "vite", "tailwind", "shadcn"]:
            if dependency in pyproject:
                failures.append(
                    f"frontend dependency marker in pyproject: {dependency}"
                )
        return self._result(criterion, failures, forbidden_paths + ["pyproject.toml"])

    def check_m12_no_runtime_network_mobile_plugin_expansion(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        package = self.root / "src/ultimate_ai_agent/core/control_center"
        forbidden_starts = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "urllib",
            "from " + "urllib import",
            "import " + "socket",
            "from " + "socket import",
            "import " + "subprocess",
            "from " + "subprocess import",
            "import " + "openai",
            "from " + "openai import",
            "import " + "anthropic",
            "from " + "anthropic import",
            "import " + "tiktoken",
            "import " + "tokenizers",
        ]
        forbidden_fragments = [
            "urlopen",
            "billing",
            "eval(",
            "exec(",
            "enable_plugin(",
            "dispatch_remote",
            "mobile_sensor_access=true",
            "runtime_execution=true",
            "provider_invocation=true",
            "browser automation is enabled",
        ]
        failures = []
        for path in sorted(package.glob("*.py")):
            rel_path = self._context.relative_path(path)
            for line_no, stripped in enumerate(self._read(path).splitlines(), start=1):
                stripped = stripped.strip().lower()
                if stripped.startswith("[") or self._is_static_scanner_text(stripped):
                    continue
                if any(stripped.startswith(pattern) for pattern in forbidden_starts):
                    failures.append(f"{rel_path}:{line_no} forbidden import")
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(
                        f"{rel_path}:{line_no} forbidden runtime expansion fragment"
                    )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/control_center"]
        )

    def check_m13_web_control_center_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "apps/control-center/package.json",
            "apps/control-center/package-lock.json",
            "apps/control-center/index.html",
            "apps/control-center/vite.config.ts",
            "apps/control-center/tsconfig.json",
            "apps/control-center/src/App.tsx",
            "apps/control-center/src/main.tsx",
            "apps/control-center/src/api/client.ts",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/redaction.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/components/ActionPreviewForm.tsx",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m13_web_shell_read_only_preview_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        app_root = self.root / "apps/control-center"
        package = json.loads(self._read(app_root / "package.json") or "{}")
        runtime_deps = set(package.get("dependencies", {}))
        dev_deps = set(package.get("devDependencies", {}))
        deps = runtime_deps | dev_deps
        allowed_deps = {
            "react",
            "react-dom",
            "@playwright/test",
            "@vitejs/plugin-react",
            "vite",
            "typescript",
            "@types/react",
            "@types/react-dom",
            "@types/node",
            "vitest",
            "@testing-library/react",
            "@testing-library/jest-dom",
            "jsdom",
        }
        forbidden_deps = {
            "next",
            "tailwindcss",
            "stripe",
            "@stripe/stripe-js",
            "@supabase/supabase-js",
            "firebase",
            "auth0-js",
            "openai",
            "anthropic",
            "expo",
            "react-native",
            "electron",
            "playwright",
            "puppeteer",
        }
        failures = [
            f"unexpected frontend dependency: {dep}"
            for dep in sorted(deps - allowed_deps)
        ]
        failures.extend(
            f"forbidden frontend dependency: {dep}"
            for dep in sorted(deps & forbidden_deps)
        )
        if "@playwright/test" in runtime_deps:
            failures.append(
                "@playwright/test must remain a dev-only visual proof dependency"
            )
        source_paths = [
            *sorted((app_root / "src").rglob("*.ts")),
            *sorted((app_root / "src").rglob("*.tsx")),
            *sorted((app_root / "src").rglob("*.css")),
        ]
        source_text = "\n".join(
            self._read(path).lower()
            for path in source_paths
            if self._context.is_file(path) and ".test." not in path.name
        )
        forbidden = [
            "/control-center/actions/execute",
            "/control-center/plugins/enable",
            "/control-center/runtime/execute",
            "/control-center/remote-workers/dispatch",
            "/control-center/mobile/sensors",
            "/model-runtime/execute",
            "document.cookie",
            "localstorage",
            "sessionstorage",
            "navigator.geolocation",
            "mediadevices",
            "getusermedia",
            "chrome.",
            "computer use",
            "xcode",
            "app store connect",
            "keychain",
        ]
        failures.extend(
            f"forbidden frontend source fragment: {fragment}"
            for fragment in forbidden
            if fragment in source_text
        )
        if "no authority to run actions" not in source_text:
            failures.append("frontend does not visibly mark no action authority")
        return self._result(
            criterion,
            failures,
            ["apps/control-center/package.json", "apps/control-center/src"],
        )

    def check_m13_action_preview_ui_posts_only_to_preview(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        endpoints = self._read(app_root / "api/endpoints.ts")
        client = self._read(app_root / "api/client.ts")
        failures = []
        if 'actionPreview: "/control-center/actions/preview"' not in endpoints:
            failures.append("action preview endpoint declaration missing")
        if endpoints.count("/control-center/actions/preview") != 1:
            failures.append(
                "action preview endpoint should appear exactly once in endpoint declarations"
            )
        allowed_post_targets = {
            "API_ENDPOINTS.actionPreview",
            "actionDecisionEndpoint(actionId, decision)",
            "actionLocalTaskCommitEndpoint(actionId)",
            "API_ENDPOINTS.controlCenterWorkBoardReorder",
            "API_ENDPOINTS.controlCenterWorkBoardCards",
            "API_ENDPOINTS.controlCenterWorkBoardTasks",
            "API_ENDPOINTS.runtimeAuthorityDecisionPreview",
            "API_ENDPOINTS.runtimeAuthorityMissionPlan",
            "API_ENDPOINTS.runtimeAuthorityLeases",
            "API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue",
            "API_ENDPOINTS.runtimeAuthorityLeaseRevoke",
            "API_ENDPOINTS.founderTodayActionEnvelope",
            "API_ENDPOINTS.controlCenterChatTurns",
            "chatTurnHandoffEndpoint(turnRef)",
            "API_ENDPOINTS.founderMemoryManualCandidate",
            "API_ENDPOINTS.founderMemoryFeedback",
            "memoryReviewDecisionEndpoint(candidateRef, decision)",
            "memoryContextPackActionProposalEndpoint(contextPackRef)",
            "API_ENDPOINTS.localChatCompletions",
            "API_ENDPOINTS.controlCenterWebEvidenceAttach",
            "API_ENDPOINTS.turnRouterPreview",
        }
        for target in sorted(allowed_post_targets):
            if target not in client:
                failures.append(f"frontend client missing scoped POST target: {target}")
        post_files = [
            path
            for path in self._context.rglob(app_root, "*.ts*")
            if ".test." not in path.name
            and "test" not in path.parts
            and 'method: "POST"' in self._read(path)
        ]
        if post_files != [app_root / "api/client.ts"]:
            failures.append(
                "frontend POST declarations must stay centralized in api/client.ts"
            )
        post_count = client.count('method: "POST"')
        if post_count != len(allowed_post_targets):
            failures.append(f"unexpected frontend POST declaration count: {post_count}")
        return self._result(
            criterion,
            failures,
            [
                "apps/control-center/src/api/endpoints.ts",
                "apps/control-center/src/api/client.ts",
            ],
        )

    def check_m13_mock_data_safe_non_authoritative(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        mock_path = self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        text = self._read(mock_path).lower()
        failures = []
        required_safe_fragments = [
            "mock: true",
            "production_control_center: false",
            "production_ready: false",
            "real_model_runtime_ready: false",
            "remote_execution_ready: false",
            "mobile_sensor_ready: false",
            "plugin_or_native_build_ready: false",
            "execution_enabled: false",
            "dispatch_enabled: false",
            "sensor_access_enabled: false",
            "plugin_enablement_allowed: false",
            "native_build_tools_enabled: false",
            "model_output_authoritative: false",
        ]
        for fragment in required_safe_fragments:
            if fragment not in text:
                failures.append(f"mock data missing safe fragment: {fragment}")
        forbidden = [
            "production_ready: true",
            "real_model_runtime_ready: true",
            "remote_execution_ready: true",
            "mobile_sensor_ready: true",
            "plugin_or_native_build_ready: true",
            "execution_enabled: true",
            "dispatch_enabled: true",
            "sensor_access_enabled: true",
            "plugin_enablement_allowed: true",
            "native_build_tools_enabled: true",
            "api_key",
            "password",
            "authorization",
            "cookie",
        ]
        scan_text = text.replace("uaa_authorization_status", "uaa_authority_status")
        failures.extend(
            f"unsafe mock data fragment: {fragment}"
            for fragment in forbidden
            if fragment in scan_text
        )
        return self._result(
            criterion, failures, ["apps/control-center/src/mocks/controlCenterData.ts"]
        )

    def check_m13_no_tracked_generated_or_native_artifacts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        forbidden_paths = [
            "apps/control-center/.next",
            "apps/control-center/ios",
            "apps/control-center/android",
            "apps/control-center/Podfile",
            "apps/control-center/Package.swift",
            "apps/control-center/electron",
        ]
        failures = [
            f"forbidden frontend/native artifact exists: {path}"
            for path in forbidden_paths
            if (self.root / path).exists()
        ]
        gitignore = self._read(self.root / ".gitignore")
        for required_ignore in ["node_modules/", "dist/", "coverage/", ".env"]:
            if required_ignore not in gitignore:
                failures.append(
                    f".gitignore missing frontend artifact guard: {required_ignore}"
                )
        return self._result(criterion, failures, forbidden_paths + [".gitignore"])

    def check_m13_backend_api_contract_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        routes = iter_api_route_items(app)
        paths = {route.path: route for route in routes}
        historical_paths = _historical_openapi_path_set(paths)
        failures = []
        if len(historical_paths) != EXPECTED_M36_OPENAPI_PATH_COUNT:
            failures.append(
                "API normalized pre-M37 path count changed from accepted "
                f"boundary: expected {EXPECTED_M36_OPENAPI_PATH_COUNT}, found {len(historical_paths)}"
            )
        control_center_routes = [
            path for path in paths if path.startswith("/control-center")
        ]
        if len(control_center_routes) != EXPECTED_M13_CONTROL_CENTER_ROUTE_COUNT:
            failures.append(
                f"unexpected Control Center route count: {len(control_center_routes)}"
            )
        forbidden = [
            "/control-center/actions/execute",
            "/control-center/plugins/enable",
            "/control-center/runtime/execute",
            "/control-center/remote-workers/dispatch",
            "/control-center/mobile/sensors",
            "/control-center/frontend",
        ]
        failures.extend(
            f"forbidden Control Center route present: {path}"
            for path in forbidden
            if path in paths
        )
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/api/app.py", "apps/control-center"],
        )
