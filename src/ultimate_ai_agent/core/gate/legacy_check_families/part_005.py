from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart005Mixin:
    """Legacy checks from m19_mobile_companion_contract_planning_safe through m25_truth_openapi_routes_unchanged."""
    def check_m19_mobile_companion_contract_planning_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.mobile_companion import (
            MobileCapabilityKind,
            MobileCapabilityStatus,
            build_default_mobile_companion_manifest,
            build_default_mobile_permission_manifest,
        )
        from ultimate_ai_agent.core.mobile_companion.planning import (
            assert_mobile_contract_only,
        )

        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/permissions.py",
            "src/ultimate_ai_agent/core/mobile_companion/receipts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "tests/test_mobile_companion_contracts.py",
            "tests/test_mobile_companion_permissions.py",
            "tests/test_mobile_companion_no_sensor_access.py",
            "tests/test_mobile_companion_no_authority.py",
            "tests/test_m19_gate_integration.py",
            "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
            "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
            "docs/mobile/MOBILE_API_PLANNING.md",
            "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
            "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
            "docs/mobile/MOBILE_SECURITY_MODEL.md",
            "docs/mobile/MOBILE_CAPTURE_POLICY.md",
            "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
            "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
            "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_23_1.md",
            "docs/release_notes/v0_23_1.md",
        ]
        failures = [
            f"missing M19 mobile companion contract/planning file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_mobile_companion_manifest()
            permission_manifest = build_default_mobile_permission_manifest()
            assert_mobile_contract_only(manifest)
            if not manifest.contract_only:
                failures.append(
                    "default mobile companion manifest is not contract-only"
                )
            if manifest.mobile_client_is_authority:
                failures.append(
                    "default mobile companion manifest claims mobile authority"
                )
            if manifest.sensor_access_enabled:
                failures.append(
                    "default mobile companion manifest enables sensor access"
                )
            if manifest.mobile_approval_execution_implemented:
                failures.append("default manifest enables mobile approval execution")
            if not manifest.device_capability_broker_required:
                failures.append(
                    "default manifest does not require Device Capability Broker"
                )
            if not permission_manifest.contract_only:
                failures.append(
                    "default mobile permission manifest is not contract-only"
                )
            if permission_manifest.os_permission_integration_implemented:
                failures.append("default permission manifest enables OS permissions")
            capabilities_by_kind = {
                capability.capability: capability
                for capability in manifest.capabilities
            }
            for capability_kind in [
                MobileCapabilityKind.contacts_planned,
                MobileCapabilityKind.calendar_planned,
            ]:
                capability = capabilities_by_kind.get(capability_kind)
                if capability is None:
                    failures.append(f"default manifest missing {capability_kind.value}")
                    continue
                if (
                    capability.status
                    != MobileCapabilityStatus.future_requires_device_capability_broker
                ):
                    failures.append(
                        f"{capability_kind.value} must remain future-broker-only"
                    )
                if capability.allowed_now:
                    failures.append(f"{capability_kind.value} is enabled")
                if capability.os_permission_integrated:
                    failures.append(
                        f"{capability_kind.value} integrates OS permissions"
                    )
                if capability.background_service_enabled:
                    failures.append(
                        f"{capability_kind.value} enables background services"
                    )
                if not capability.requires_device_capability_broker:
                    failures.append(
                        f"{capability_kind.value} must require Device Capability Broker"
                    )
        except Exception as exc:
            failures.append(
                f"M19 mobile companion default contract failed validation: {exc}"
            )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M19 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m19_openapi_route_failures(openapi_paths))

        forbidden_dirs = [
            "ios",
            "android",
            "mobile-app",
            "react-native",
            "expo",
            "flutter",
            "capacitor",
            "ionic",
            "src/ultimate_ai_agent/core/device_capability_broker",
        ]
        for rel_path in forbidden_dirs:
            if (self.root / rel_path).exists():
                failures.append(
                    f"M19 forbidden native/mobile implementation directory exists: {rel_path}"
                )

        forbidden_files = [
            "build.gradle",
            "settings.gradle",
            "gradlew",
            "AndroidManifest.xml",
            "Info.plist",
            "Package.swift",
            "Podfile",
            "pubspec.yaml",
            "app.json",
            "app.config.js",
            "capacitor.config.ts",
            "ionic.config.json",
        ]
        for file_name in forbidden_files:
            for rel in [
                file_name,
                f"apps/{file_name}",
                f"apps/control-center/{file_name}",
                f"src/{file_name}",
            ]:
                if (self.root / rel).exists():
                    failures.append(
                        f"M19 forbidden native/mobile implementation file exists: {rel}"
                    )

        scan_roots = ["src", "apps", "scripts", "tests"]
        forbidden_fragments = [
            "navigator.geolocation",
            "navigator.mediaDevices",
            "Notification.requestPermission",
            "PushManager",
            "android.permission",
            "Manifest.permission",
            "CLLocation",
            "AVCapture",
            "LocationManager",
            "CameraManager",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "scripts/verify_all.py",
            "scripts/verification/run_all_legacy.py",
            "scripts/verify_control_center_frontend.py",
            "tests/test_control_center_frontend_safety_verifier.py",
        }
        for rel_root in scan_roots:
            root = self.root / rel_root
            if not root.exists():
                continue
            candidate_files = []
            if rel_root in {"src", "scripts", "tests"}:
                candidate_files.extend(self._context.rglob(root, "*.py"))
            if rel_root == "apps":
                candidate_files.extend(self._context.rglob(root, "*.ts"))
                candidate_files.extend(self._context.rglob(root, "*.tsx"))
                candidate_files.extend(self._context.rglob(root, "*.js"))
                candidate_files.extend(self._context.rglob(root, "*.jsx"))
            for path in candidate_files:
                rel = self._context.relative_path(path)
                if not self._context.is_file(path) or "__pycache__" in rel or "node_modules/" in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._read(path)
                for fragment in forbidden_fragments:
                    if fragment in text:
                        failures.append(
                            f"M19 forbidden mobile sensor fragment in {rel}: {fragment}"
                        )

        return self._result(criterion, failures, required_files)

    def check_m20_device_capability_broker_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.device_capabilities import (
            DeviceCapabilityKind,
            DeviceCapabilityStatus,
            build_default_device_capability_manifest,
        )
        from ultimate_ai_agent.core.device_capabilities.validation import (
            assert_device_contract_only,
        )

        required_files = [
            "src/ultimate_ai_agent/core/device_capabilities/__init__.py",
            "src/ultimate_ai_agent/core/device_capabilities/enums.py",
            "src/ultimate_ai_agent/core/device_capabilities/contracts.py",
            "src/ultimate_ai_agent/core/device_capabilities/manifests.py",
            "src/ultimate_ai_agent/core/device_capabilities/validation.py",
            "src/ultimate_ai_agent/core/device_capabilities/policy.py",
            "src/ultimate_ai_agent/core/device_capabilities/receipts.py",
            "tests/test_device_capability_contracts.py",
            "tests/test_device_capability_manifest.py",
            "tests/test_device_capability_validation.py",
            "tests/test_device_capability_no_sensor_access.py",
            "tests/test_device_capability_no_authority.py",
            "tests/test_m20_gate_integration.py",
            "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
            "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
            "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
            "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
            "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
            "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
            "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
            "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
            "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_24_0.md",
            "docs/release_notes/v0_24_0.md",
        ]
        failures = [
            f"missing M20 Device Capability Broker contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_device_capability_manifest()
            assert_device_contract_only(manifest)
            if not manifest.contract_only:
                failures.append(
                    "default device capability manifest is not contract-only"
                )
            if manifest.sensor_access_enabled:
                failures.append(
                    "default device capability manifest enables sensor access"
                )
            if manifest.os_permission_integration_implemented:
                failures.append(
                    "default device capability manifest enables OS permissions"
                )
            if manifest.backend_routes_added:
                failures.append(
                    "default device capability manifest adds backend routes"
                )
            if manifest.runtime_broker_implemented:
                failures.append(
                    "default device capability manifest implements runtime broker"
                )
            if manifest.native_client_implemented:
                failures.append(
                    "default device capability manifest implements native clients"
                )
            if manifest.device_clients_are_authority:
                failures.append(
                    "default device capability manifest claims device authority"
                )
            if manifest.device_output_is_trusted_control_input:
                failures.append("default device output is trusted control input")
            if manifest.automatic_memory_write_allowed:
                failures.append("default manifest allows automatic memory write")
            if manifest.external_send_allowed:
                failures.append("default manifest allows external sends")
            if manifest.raw_payload_allowed:
                failures.append("default manifest allows raw payloads")
            capabilities_by_kind = {
                capability.kind: capability for capability in manifest.capabilities
            }
            for capability_kind in [
                DeviceCapabilityKind.camera,
                DeviceCapabilityKind.microphone,
                DeviceCapabilityKind.location,
                DeviceCapabilityKind.notifications,
                DeviceCapabilityKind.contacts,
                DeviceCapabilityKind.calendar,
                DeviceCapabilityKind.photos,
                DeviceCapabilityKind.files,
                DeviceCapabilityKind.clipboard,
                DeviceCapabilityKind.bluetooth,
                DeviceCapabilityKind.nfc,
                DeviceCapabilityKind.biometrics,
                DeviceCapabilityKind.local_network,
                DeviceCapabilityKind.motion,
                DeviceCapabilityKind.health,
                DeviceCapabilityKind.screen_capture,
            ]:
                capability = capabilities_by_kind.get(capability_kind)
                if capability is None:
                    failures.append(f"default manifest missing {capability_kind.value}")
                    continue
                if capability.status not in {
                    DeviceCapabilityStatus.planned_disabled,
                    DeviceCapabilityStatus.future_requires_broker,
                    DeviceCapabilityStatus.blocked,
                }:
                    failures.append(
                        f"{capability_kind.value} is not future-broker-only"
                    )
                if capability.allowed_now:
                    failures.append(f"{capability_kind.value} is enabled")
                if capability.implemented_now:
                    failures.append(f"{capability_kind.value} is implemented")
                if not capability.requires_device_capability_broker:
                    failures.append(
                        f"{capability_kind.value} must require Device Capability Broker"
                    )
            background_service = capabilities_by_kind.get(
                DeviceCapabilityKind.background_service
            )
            if background_service is None:
                failures.append("default manifest missing background_service")
            elif background_service.status != DeviceCapabilityStatus.blocked:
                failures.append("background_service must remain blocked")
        except Exception as exc:
            failures.append(
                f"M20 device capability default contract failed validation: {exc}"
            )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M20 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m20_openapi_route_failures(openapi_paths))

        forbidden_dirs = [
            "ios",
            "android",
            "mobile-app",
            "react-native",
            "expo",
            "flutter",
            "capacitor",
            "ionic",
            "src/ultimate_ai_agent/core/device_capability_broker",
        ]
        for rel_path in forbidden_dirs:
            if (self.root / rel_path).exists():
                failures.append(
                    f"M20 forbidden native/mobile implementation directory exists: {rel_path}"
                )

        forbidden_files = [
            "build.gradle",
            "settings.gradle",
            "gradlew",
            "AndroidManifest.xml",
            "Info.plist",
            "Package.swift",
            "Podfile",
            "pubspec.yaml",
            "app.json",
            "app.config.js",
            "capacitor.config.ts",
            "ionic.config.json",
        ]
        for file_name in forbidden_files:
            for rel in [
                file_name,
                f"apps/{file_name}",
                f"apps/control-center/{file_name}",
                f"src/{file_name}",
            ]:
                if (self.root / rel).exists():
                    failures.append(
                        f"M20 forbidden native/mobile implementation file exists: {rel}"
                    )

        scan_roots = ["src", "apps", "scripts", "tests"]
        forbidden_fragments = [
            "navigator.geolocation",
            "navigator.mediaDevices",
            "Notification.requestPermission",
            "PushManager",
            "android.permission",
            "Manifest.permission",
            "CLLocation",
            "AVCapture",
            "LocationManager",
            "CameraManager",
            "AudioRecord",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "scripts/verify_all.py",
            "scripts/verification/run_all_legacy.py",
            "scripts/verify_control_center_frontend.py",
            "tests/test_control_center_frontend_safety_verifier.py",
        }
        for rel_root in scan_roots:
            root = self.root / rel_root
            if not root.exists():
                continue
            candidate_files = []
            if rel_root in {"src", "scripts", "tests"}:
                candidate_files.extend(self._context.rglob(root, "*.py"))
            if rel_root == "apps":
                candidate_files.extend(self._context.rglob(root, "*.ts"))
                candidate_files.extend(self._context.rglob(root, "*.tsx"))
                candidate_files.extend(self._context.rglob(root, "*.js"))
                candidate_files.extend(self._context.rglob(root, "*.jsx"))
            for path in candidate_files:
                rel = self._context.relative_path(path)
                if not self._context.is_file(path) or "__pycache__" in rel or "node_modules/" in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._read(path)
                for fragment in forbidden_fragments:
                    if fragment in text:
                        failures.append(
                            f"M20 forbidden device/sensor fragment in {rel}: {fragment}"
                        )

        roadmap_text = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        if "v0.24.0 / m20" not in roadmap_text or "implemented" not in roadmap_text:
            failures.append("canonical roadmap must mark v0.24.0 / M20 implemented")
        if (
            "v0.25.0 / m21" not in roadmap_text
            or "planned/provisional" not in roadmap_text
        ):
            failures.append("canonical roadmap must keep M21 planned/provisional")

        return self._result(criterion, failures, required_files)

    def check_m21_openwebui_bridge_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.openwebui_bridge import (
            OpenWebUIAuthorityBoundary,
            OpenWebUIBridgeStatus,
            build_default_openwebui_bridge_manifest,
            build_default_openwebui_bridge_plan,
        )
        from ultimate_ai_agent.core.openwebui_bridge.validation import (
            assert_agent_core_authority_boundary,
            assert_no_approval_grant,
            assert_no_memory_write,
            assert_no_provider_call,
            assert_no_raw_content,
            assert_no_runtime_execution,
            assert_no_tool_execution,
            assert_openwebui_contract_only,
        )

        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/__init__.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/enums.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/manifests.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/policy.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/receipts.py",
            "tests/test_openwebui_bridge_contracts.py",
            "tests/test_openwebui_bridge_validation.py",
            "tests/test_openwebui_bridge_no_authority.py",
            "tests/test_openwebui_bridge_no_execution.py",
            "tests/test_openwebui_bridge_no_raw_content.py",
            "tests/test_m21_gate_integration.py",
            "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
            "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
            "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
            "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
            "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/OPENWEBUI_NON_GOALS.md",
            "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_25_0.md",
            "docs/release_notes/v0_25_0.md",
        ]
        failures = [
            f"missing M21 OpenWebUI bridge contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_openwebui_bridge_manifest()
            plan = build_default_openwebui_bridge_plan()
            assert_openwebui_contract_only(manifest)
            assert_agent_core_authority_boundary(manifest)
            assert_no_raw_content(manifest)
            assert_no_tool_execution(manifest)
            assert_no_memory_write(manifest)
            assert_no_runtime_execution(manifest)
            assert_no_provider_call(manifest)
            assert_no_approval_grant(manifest)
            if manifest.status != OpenWebUIBridgeStatus.contract_only:
                failures.append("default OpenWebUI manifest is not contract-only")
            if plan.status != OpenWebUIBridgeStatus.planned_disabled:
                failures.append("default OpenWebUI bridge plan is not planned-disabled")
            if not manifest.openwebui_is_preferred_conversational_shell:
                failures.append(
                    "OpenWebUI must remain a supported local/dev conversational shell"
                )
            if manifest.openwebui_is_agent_brain:
                failures.append("OpenWebUI must not be the agent brain")
            if not manifest.agent_core_remains_authority:
                failures.append("Agent Core must remain authority")
            for boundary in [
                OpenWebUIAuthorityBoundary.agent_core_authority,
                OpenWebUIAuthorityBoundary.no_direct_tool_execution,
                OpenWebUIAuthorityBoundary.no_direct_memory_write,
                OpenWebUIAuthorityBoundary.no_direct_runtime_execution,
                OpenWebUIAuthorityBoundary.no_direct_provider_call,
            ]:
                if boundary not in manifest.authority_boundaries:
                    failures.append(
                        f"default OpenWebUI manifest missing boundary: {boundary.value}"
                    )
            if "M22" not in plan.required_future_milestones:
                failures.append("M22 must remain a future required milestone")
            if "M23" not in plan.required_future_milestones:
                failures.append("M23 must remain a future required milestone")
        except Exception as exc:
            failures.append(
                f"M21 OpenWebUI bridge default contract failed validation: {exc}"
            )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M21 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m21_openapi_route_failures(openapi_paths))

        for rel_path in m21_forbidden_openwebui_config_path_matches(self.root):
            failures.append(
                f"M21 forbidden OpenWebUI deployment/config path exists: {rel_path}"
            )

        failures.extend(m21_forbidden_openwebui_runtime_fragment_failures(self.root, self._context))

        roadmap_text = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        if "v0.25.0 / m21" not in roadmap_text or "implemented" not in roadmap_text:
            failures.append("canonical roadmap must mark v0.25.0 / M21 implemented")
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 26, 0):
            if "v0.26.0 / m22" not in roadmap_text or "implemented" not in roadmap_text:
                failures.append("canonical roadmap must mark v0.26.0 / M22 implemented")
        elif (
            "v0.26.0 / m22" not in roadmap_text
            or "planned/provisional" not in roadmap_text
        ):
            failures.append("canonical roadmap must keep M22 planned/provisional")
        if version_tuple >= (0, 27, 0):
            if "v0.27.0 / m23" not in roadmap_text or "implemented" not in roadmap_text:
                failures.append("canonical roadmap must mark v0.27.0 / M23 implemented")
        elif (
            "v0.27.0 / m23" not in roadmap_text
            or "planned/provisional" not in roadmap_text
        ):
            failures.append("canonical roadmap must keep M23 planned/provisional")

        return self._result(criterion, failures, required_files)

    def check_m22_local_model_runtime_activation_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.core.model_runtime import (
            LocalModelRuntimeKind,
            LocalModelRuntimeStatus,
            build_default_local_runtime_activation_manifest,
            validate_local_runtime_activation_manifest,
        )

        required_files = [
            "src/ultimate_ai_agent/core/model_runtime/activation.py",
            "src/ultimate_ai_agent/core/model_runtime/provider_profiles.py",
            "src/ultimate_ai_agent/core/model_runtime/endpoint_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/health_plan.py",
            "src/ultimate_ai_agent/core/model_runtime/activation_manifest.py",
            "tests/test_local_runtime_activation_contracts.py",
            "tests/test_local_runtime_provider_profiles.py",
            "tests/test_local_runtime_endpoint_policy.py",
            "tests/test_local_runtime_activation_validation.py",
            "tests/test_local_runtime_health_probe_plan.py",
            "tests/test_local_runtime_no_execution.py",
            "tests/test_m22_gate_integration.py",
            "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
            "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
            "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
            "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
            "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
            "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
            "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_26_0.md",
            "docs/release_notes/v0_26_0.md",
        ]
        failures = [
            f"missing M22 local runtime activation contract file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            manifest = build_default_local_runtime_activation_manifest()
            validate_local_runtime_activation_manifest(manifest)
            if manifest.status != LocalModelRuntimeStatus.contract_only:
                failures.append(
                    "default local runtime activation manifest is not contract-only"
                )
            if manifest.activation_allowed_now:
                failures.append(
                    "default local runtime activation manifest allows activation"
                )
            if manifest.real_model_call_allowed:
                failures.append(
                    "default local runtime activation manifest allows a real model call"
                )
            if manifest.runtime_execution_allowed:
                failures.append(
                    "default local runtime activation manifest allows runtime execution"
                )
            if manifest.provider_call_allowed:
                failures.append(
                    "default local runtime activation manifest allows provider call"
                )
            if manifest.endpoint_probe_allowed:
                failures.append(
                    "default local runtime activation manifest allows endpoint probe"
                )
            if manifest.user_content_allowed:
                failures.append(
                    "default local runtime activation manifest allows user content"
                )
            if manifest.tool_call_allowed:
                failures.append(
                    "default local runtime activation manifest allows tool call"
                )
            if manifest.memory_write_allowed:
                failures.append(
                    "default local runtime activation manifest allows memory write"
                )
            if manifest.secret_material_allowed:
                failures.append(
                    "default local runtime activation manifest allows secret material"
                )
            if not manifest.no_model_called:
                failures.append("default manifest must record no model was called")
            if not manifest.no_runtime_activated:
                failures.append("default manifest must record no runtime was activated")
            if not manifest.no_endpoint_contacted:
                failures.append(
                    "default manifest must record no endpoint was contacted"
                )
            kinds = {profile.kind for profile in manifest.provider_profiles}
            expected_kinds = {
                LocalModelRuntimeKind.ollama_planned,
                LocalModelRuntimeKind.llama_cpp_planned,
                LocalModelRuntimeKind.mlx_planned,
                LocalModelRuntimeKind.vllm_planned,
                LocalModelRuntimeKind.lm_studio_planned,
                LocalModelRuntimeKind.openai_compatible_local_planned,
                LocalModelRuntimeKind.generic_loopback_http_planned,
            }
            if kinds != expected_kinds:
                failures.append(
                    "default local runtime activation manifest missing provider profiles"
                )
        except Exception as exc:
            failures.append(
                f"M22 local runtime activation default contract failed validation: {exc}"
            )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M22 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m22_openapi_route_failures(openapi_paths))

        failures.extend(m22_local_runtime_forbidden_fragment_failures(self.root, self._context))

        roadmap_text = self._read(self.root / "docs/canonical/09_roadmap.md").lower()
        version_tuple = self._active_version_tuple()
        if "v0.26.0 / m22" not in roadmap_text or "implemented" not in roadmap_text:
            failures.append("canonical roadmap must mark v0.26.0 / M22 implemented")
        if version_tuple >= (0, 27, 0):
            if "v0.27.0 / m23" not in roadmap_text or "implemented" not in roadmap_text:
                failures.append("canonical roadmap must mark v0.27.0 / M23 implemented")
        elif (
            "v0.27.0 / m23" not in roadmap_text
            or "planned/provisional" not in roadmap_text
        ):
            failures.append("canonical roadmap must keep M23 planned/provisional")

        return self._result(criterion, failures, required_files)

    def check_m23_first_local_llm_call_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/model_runtime/local_call_contracts.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call.py",
            "scripts/manual_local_model_call.py",
            "tests/test_m23_local_model_call_contracts.py",
            "tests/test_m23_local_model_endpoint_policy.py",
            "tests/test_m23_local_model_fake_transport.py",
            "tests/test_m23_manual_cli_dry_run.py",
            "docs/runtime/FIRST_LOCAL_LLM_CALL.md",
            "docs/runtime/M23_FIXED_PROMPT_POLICY.md",
            "docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md",
            "docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md",
            "docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md",
            "docs/runtime/M23_MANUAL_CLI_USAGE.md",
            "docs/runtime/M23_TO_M24_BOUNDARY.md",
        ]
        failures = [
            f"missing M23 local model call file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.core.approvals import (
                ApprovalDecisionStatus,
                ApprovalValidationDecision,
                LocalApprovalAuthority,
            )
            from ultimate_ai_agent.core.model_runtime import (
                M23_FIXED_LOCAL_MODEL_PROMPT_ID,
                FakeLocalModelCallTransport,
                LocalModelCallRequest,
                LocalModelRuntimeKind,
                build_dry_run_local_model_call_result,
                build_m23_fixed_prompt,
                local_model_call_approval_request,
                run_local_model_call,
                validate_fixed_prompt,
                validate_local_model_endpoint,
                validate_local_model_call_request,
            )

            prompt = validate_fixed_prompt(build_m23_fixed_prompt())
            if prompt.prompt_id != M23_FIXED_LOCAL_MODEL_PROMPT_ID:
                failures.append("M23 fixed prompt id is not allowlisted")
            request = LocalModelCallRequest(
                request_id="m23_gate_req",
                run_id="run_m23_gate",
                runtime_kind=LocalModelRuntimeKind.ollama_planned,
                endpoint_url="".join(["http", "://127.0.0.1:11434"]),
                safe_endpoint_label="loopback gate endpoint",
                model_ref="local_gate_model",
                fixed_prompt_id=prompt.prompt_id,
                prompt_text=prompt.prompt_text,
            )
            validate_local_model_call_request(request)
            try:
                hostile_query_key = "to" + "ken"
                hostile_endpoint = "".join(
                    [
                        "http",
                        "://localhost:11434/api",
                        "/generate?",
                        hostile_query_key,
                        "=abc",
                    ]
                )
                validate_local_model_endpoint(hostile_endpoint)
                failures.append("M23 accepted secret-like endpoint query key")
            except ValueError:
                pass
            try:
                validate_local_model_call_request(
                    request.model_copy(
                        update={"safe_endpoint_label": request.endpoint_url}
                    )
                )
                failures.append("M23 safe endpoint label echoed raw endpoint URL")
            except ValueError:
                pass
            dry_run = build_dry_run_local_model_call_result(
                request, transport=FakeLocalModelCallTransport()
            )
            if dry_run.transport_result.call_performed:
                failures.append("M23 dry-run performed a local model call")
            if dry_run.receipt.model_output_non_authoritative is not True:
                failures.append(
                    "M23 dry-run receipt does not mark output non-authoritative"
                )

            executable = request.model_copy(
                update={
                    "dry_run": False,
                    "execute_local_call": True,
                    "approval_ref": "approval_m23_gate",
                }
            )
            approval_request = local_model_call_approval_request(executable)
            authority = LocalApprovalAuthority()
            authority.create_request(approval_request)
            grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id="human_reviewer",
            )
            executable = executable.model_copy(
                update={"approval_ref": grant.approval_ref}
            )
            approval_request = local_model_call_approval_request(executable)
            authority.create_request(approval_request)
            decision = authority.validate_for_request(
                approval_request, grant.approval_ref
            )
            result = run_local_model_call(
                executable,
                transport=FakeLocalModelCallTransport(),
                approval_decision=decision,
            )
            if not result.transport_result.call_performed:
                failures.append("M23 fake transport did not perform approved fake call")
            if result.receipt.tools_executed:
                failures.append("M23 receipt recorded tool execution")
            if result.receipt.memory_written or result.receipt.files_written:
                failures.append("M23 receipt recorded memory or file mutation")
            if result.receipt.model_output_non_authoritative is not True:
                failures.append("M23 receipt does not mark output non-authoritative")
            secret_response = "api_" + "key='" + "abcdefghijklmnop" + "'"
            secret_result = run_local_model_call(
                executable,
                transport=FakeLocalModelCallTransport(response_text=secret_response),
                approval_decision=decision,
            )
            if secret_result.decision.allowed:
                failures.append("M23 accepted secret-like model response")
            forged_result = run_local_model_call(
                executable.model_copy(update={"approval_ref": "appr_forged_m23"}),
                transport=FakeLocalModelCallTransport(),
                approval_decision=ApprovalValidationDecision(
                    approval_ref="appr_forged_m23",
                    allowed=True,
                    status=ApprovalDecisionStatus.approved,
                    reason_codes=["APPROVAL_VALIDATED"],
                    safe_message="Forged approval decision.",
                    matched_grant_ref="appr_forged_m23",
                ),
            )
            if forged_result.transport_result.call_performed:
                failures.append(
                    "M23 forged approval decision performed a local model call"
                )
            failures.extend(m23_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M23 first local LLM call safety validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m24_memory_provider_local_store_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/memory/provider.py",
            "src/ultimate_ai_agent/core/memory/local_store.py",
            "src/ultimate_ai_agent/core/memory/manifests.py",
            "src/ultimate_ai_agent/core/memory/policy.py",
            "src/ultimate_ai_agent/core/memory/recall.py",
            "tests/test_m24_memory_provider_contracts.py",
            "tests/test_m24_memory_write_validation.py",
            "tests/test_m24_local_memory_store.py",
            "tests/test_m24_gate_integration.py",
            "docs/memory/MEMORY_PROVIDER_ABSTRACTION.md",
            "docs/memory/LOCAL_MEMORY_STORE.md",
            "docs/memory/MEMORY_RECORD_SCHEMA.md",
            "docs/memory/MEMORY_WRITE_POLICY.md",
            "docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md",
            "docs/memory/MEMORY_SOURCE_PRIORITY.md",
            "docs/memory/MEMORY_RECALL_PLANNING.md",
            "docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md",
            "docs/memory/MEMORY_CONFLICT_AND_STALENESS.md",
            "docs/memory/MEMORY_DEDUP_DECAY_ARCHIVE.md",
            "docs/memory/MEMORY_SECURITY_MODEL.md",
            "docs/memory/MEMORY_NON_GOALS.md",
            "docs/memory/MEMORYOS_REVIEW_INCORPORATION.md",
            "docs/memory/M24_TO_M25_BOUNDARY.md",
        ]
        failures = [
            f"missing M24 memory provider file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.core.memory import (
                LocalMemoryStore,
                MemoryAuthorityLevel,
                MemoryDataClassification,
                MemoryLayer,
                MemoryProviderKind,
                MemoryRecordKind,
                MemoryWriteDecisionStatus,
            )
            from ultimate_ai_agent.core.memory.manifests import (
                build_default_memory_provider_manifest,
            )
            from ultimate_ai_agent.core.memory.provider import (
                MemoryExportRequest,
                MemoryWriteRequest,
            )
            from ultimate_ai_agent.core.memory.validation import (
                assert_no_background_memory_workers,
                assert_no_context_injection_runtime,
                assert_no_vector_or_embedding_memory,
                validate_memory_provider_manifest,
                validate_memory_write_request,
            )

            manifest = build_default_memory_provider_manifest(baseline_version="0.28.0")
            validate_memory_provider_manifest(manifest)
            assert_no_vector_or_embedding_memory(manifest)
            assert_no_context_injection_runtime(manifest)
            assert_no_background_memory_workers(manifest)
            if manifest.cloud_providers_enabled:
                failures.append("M24 manifest enabled cloud memory providers")
            if manifest.automatic_writes_enabled:
                failures.append("M24 manifest enabled automatic memory writes")

            safe = MemoryWriteRequest(
                request_id="m24_gate_safe",
                provider_ref="local_dev_memory",
                memory_kind=MemoryRecordKind.structured_fact,
                memory_layer=MemoryLayer.record,
                provider_kind=MemoryProviderKind.local_in_memory,
                safe_summary="Reviewed M24 gate memory summary.",
                source_refs=["source:m24:gate"],
                event_refs=["event:m24:gate"],
                receipt_refs=["receipt:m24:gate"],
                user_reviewed=True,
                data_classification=MemoryDataClassification.internal,
            )
            safe_decision = validate_memory_write_request(safe)
            if (
                safe_decision.status
                != MemoryWriteDecisionStatus.allowed_for_local_store
            ):
                failures.append(
                    "M24 reviewed safe write was not allowed for local store"
                )

            blocked_checks = [
                ("automatic_write", "automatic memory write"),
                ("model_output_source", "model-output memory write"),
                ("local_llm_output_source", "local LLM output memory write"),
                ("openwebui_source", "OpenWebUI memory write"),
                ("mobile_capture_source", "mobile capture memory write"),
                ("tool_output_source", "tool output memory write"),
                ("contains_raw_prompt", "raw prompt memory write"),
                ("contains_raw_model_output", "raw model output memory write"),
                ("contains_raw_file_content", "raw file content memory write"),
                ("contains_raw_transcript", "raw transcript memory write"),
            ]
            for field, label in blocked_checks:
                if field not in MemoryWriteRequest.model_fields:
                    failures.append(
                        f"M24 missing required guard field for {label}: {field}"
                    )
                    continue
                decision = validate_memory_write_request(
                    safe.model_copy(update={field: True})
                )
                if decision.allowed:
                    failures.append(f"M24 allowed blocked {label}")

            store = LocalMemoryStore()
            write = store.put_record(safe)
            if not write.allowed or not write.memory_id:
                failures.append("M24 local store did not retain reviewed safe memory")
            else:
                record = store.get_record(write.memory_id)
                if record is None:
                    failures.append("M24 local store could not read retained memory")
                elif record.authority_level != MemoryAuthorityLevel.recall_only:
                    failures.append("M24 memory record was not recall-only")

            raw_export = store.export_records(
                MemoryExportRequest(
                    request_id="m24_gate_export_raw",
                    provider_ref="local_dev_memory",
                    include_raw_content=True,
                    redacted_only=False,
                )
            )
            if raw_export.allowed:
                failures.append("M24 allowed raw memory export")

            failures.extend(m24_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M24 memory provider local store validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m25_truth_source_router_contracts_valid(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/truth/enums.py",
            "src/ultimate_ai_agent/core/truth/sources.py",
            "src/ultimate_ai_agent/core/truth/claims.py",
            "src/ultimate_ai_agent/core/truth/evidence.py",
            "src/ultimate_ai_agent/core/truth/verification.py",
            "src/ultimate_ai_agent/core/truth/manifests.py",
            "tests/test_truth_source_contracts.py",
            "tests/test_claim_verification_decisions.py",
            "tests/test_truth_no_memory_authority.py",
            "tests/test_truth_no_model_output_authority.py",
        ]
        failures = [
            f"missing M25 truth/evidence file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.core.truth import (
                Claim,
                ClaimRiskLevel,
                ClaimStatus,
                EvidenceChain,
                EvidenceRef,
                EvidenceStrength,
                TruthSourceKind,
                VerificationDecisionStatus,
                VerificationRequest,
                assert_memory_not_truth,
                assert_model_output_not_truth,
                build_truth_router_manifest,
                verify_claim_against_evidence_chain,
            )

            manifest = build_truth_router_manifest("0.29.0")
            if manifest.external_verification_enabled:
                failures.append("M25 manifest enables external verification")
            if manifest.web_search_enabled:
                failures.append("M25 manifest enables web search")
            if manifest.model_verification_enabled:
                failures.append("M25 manifest enables model verification")
            if manifest.memory_as_authority_enabled:
                failures.append("M25 manifest enables memory authority")
            if manifest.automatic_claim_verification_enabled:
                failures.append("M25 manifest enables automatic claim verification")

            claim = Claim(
                claim_id="claim:m25-gate",
                safe_claim_summary="M25 safe gate claim.",
                claim_text_hash="sha256:m25",
                claim_status=ClaimStatus.unverified,
                claim_risk=ClaimRiskLevel.low,
                data_classification="public",
            )
            safe_chain = EvidenceChain(
                chain_id="chain:m25-gate",
                claim_ref="claim:m25-gate",
                source_refs=["canonical:m25"],
                evidence_refs=["evidence:m25"],
                evidence_strength=EvidenceStrength.evidence_supported,
                source_priority_summary="canonical source",
                safe_summary="Safe canonical evidence summary.",
            )
            safe_request = VerificationRequest(
                request_id="verify:m25-gate",
                claim=claim,
                evidence_chain=safe_chain,
                evidence_refs=[
                    EvidenceRef(
                        evidence_ref="evidence:m25",
                        source_ref="canonical:m25",
                        source_kind=TruthSourceKind.canonical_document,
                        evidence_strength=EvidenceStrength.evidence_supported,
                        data_classification="public",
                        redaction_status="redacted",
                        safe_summary="Safe canonical evidence summary.",
                    )
                ],
                requested_status=ClaimStatus.verified_by_primary_source,
            )
            safe_decision = verify_claim_against_evidence_chain(safe_request)
            if (
                not safe_decision.allowed
                or safe_decision.status != VerificationDecisionStatus.allowed
            ):
                failures.append("M25 primary-source-backed evidence was not allowed")

            memory_chain = safe_chain.model_copy(
                update={
                    "chain_id": "chain:m25-memory",
                    "source_refs": ["memory:m25"],
                    "evidence_refs": ["evidence:m25-memory"],
                    "memory_refs": ["memory:m25"],
                    "source_priority_summary": "memory only",
                }
            )
            memory_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-memory",
                    "evidence_chain": memory_chain,
                    "evidence_refs": [
                        EvidenceRef(
                            evidence_ref="evidence:m25-memory",
                            source_ref="memory:m25",
                            source_kind=TruthSourceKind.reviewed_memory,
                            evidence_strength=EvidenceStrength.source_linked,
                            data_classification="public",
                            redaction_status="redacted",
                            safe_summary="Safe memory summary.",
                        )
                    ],
                }
            )
            memory_decision = verify_claim_against_evidence_chain(memory_request)
            if memory_decision.allowed:
                failures.append("M25 allowed memory-only verification")
            try:
                assert_memory_not_truth(memory_chain)
                failures.append(
                    "M25 memory assertion helper did not reject memory refs"
                )
            except ValueError:
                pass

            model_chain = safe_chain.model_copy(
                update={
                    "chain_id": "chain:m25-model",
                    "source_refs": ["model:m25"],
                    "evidence_refs": ["evidence:m25-model"],
                    "evidence_strength": EvidenceStrength.blocked,
                    "source_priority_summary": "blocked model output",
                }
            )
            model_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-model",
                    "evidence_chain": model_chain,
                    "evidence_refs": [
                        EvidenceRef(
                            evidence_ref="evidence:m25-model",
                            source_ref="model:m25",
                            source_kind=TruthSourceKind.model_output,
                            evidence_strength=EvidenceStrength.blocked,
                            data_classification="public",
                            redaction_status="redacted",
                            safe_summary="Blocked model output summary.",
                        )
                    ],
                }
            )
            model_decision = verify_claim_against_evidence_chain(model_request)
            if model_decision.allowed:
                failures.append("M25 allowed model-output verification")
            try:
                assert_model_output_not_truth(model_chain)
                failures.append(
                    "M25 model-output assertion helper did not reject model refs"
                )
            except ValueError:
                pass

            unknown_chain = safe_chain.model_copy(
                update={
                    "chain_id": "chain:m25-unknown",
                    "source_refs": ["random:m25"],
                    "evidence_refs": ["evidence:m25-unknown"],
                    "source_priority_summary": "unknown source",
                }
            )
            unknown_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-unknown",
                    "evidence_chain": unknown_chain,
                    "evidence_refs": [],
                    "requested_status": ClaimStatus.evidence_supported,
                }
            )
            unknown_decision = verify_claim_against_evidence_chain(unknown_request)
            if (
                unknown_decision.allowed
                or "ARBITRARY_SOURCE_REF_DENIED" not in unknown_decision.reason_codes
            ):
                failures.append("M25 allowed inferred unknown/arbitrary truth refs")

            explicit_unknown_request = safe_request.model_copy(
                update={
                    "request_id": "verify:m25-explicit-unknown",
                    "evidence_chain": unknown_chain,
                    "evidence_refs": [
                        EvidenceRef(
                            evidence_ref="evidence:m25-unknown",
                            source_ref="unknown:m25",
                            source_kind=TruthSourceKind.unknown,
                            evidence_strength=EvidenceStrength.evidence_supported,
                            data_classification="public",
                            redaction_status="redacted",
                            safe_summary="Unknown source kind summary.",
                        )
                    ],
                    "requested_status": ClaimStatus.evidence_supported,
                }
            )
            explicit_unknown_decision = verify_claim_against_evidence_chain(
                explicit_unknown_request
            )
            if (
                explicit_unknown_decision.allowed
                or "UNKNOWN_SOURCE_KIND_DENIED"
                not in explicit_unknown_decision.reason_codes
            ):
                failures.append("M25 allowed explicit unknown truth source kind")

            unknown_primary_request = unknown_request.model_copy(
                update={
                    "request_id": "verify:m25-unknown-primary",
                    "requested_status": ClaimStatus.verified_by_primary_source,
                }
            )
            unknown_primary_decision = verify_claim_against_evidence_chain(
                unknown_primary_request
            )
            if (
                unknown_primary_decision.allowed
                or "PRIMARY_SOURCE_EVIDENCE_REQUIRED"
                not in unknown_primary_decision.reason_codes
            ):
                failures.append(
                    "M25 allowed unknown refs to verify primary-source truth"
                )

            try:
                EvidenceChain(
                    chain_id="chain:m25-self",
                    claim_ref="claim:m25-gate",
                    source_refs=["claim:m25-gate"],
                    evidence_refs=["evidence:m25-self"],
                    evidence_strength=EvidenceStrength.evidence_supported,
                    source_priority_summary="self source",
                    safe_summary="Self-verifying source.",
                )
                failures.append("M25 allowed claim self-verification")
            except (ValueError, ValidationError):
                pass

            truth_source = "\n".join(
                self._read(path)
                for path in (
                    self.root / "src" / "ultimate_ai_agent" / "core" / "truth"
                ).glob("*.py")
            )
            forbidden_fragments = (
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "openai.",
                "anthropic.",
                "ollama.",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
            )
            failures.extend(
                f"M25 truth module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in truth_source
            )
        except Exception as exc:
            failures.append(f"M25 truth/evidence contract validation failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m25_truth_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m25_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M25 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
