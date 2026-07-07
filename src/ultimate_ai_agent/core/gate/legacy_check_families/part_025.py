from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart025Mixin:
    """Legacy checks from m99_autonomy_v1_safety_freeze_review through m101_roadmap_currentness."""
    def check_m99_autonomy_v1_safety_freeze_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/autonomy/v1_safety_freeze.py",
            "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE.md",
            "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_POLICY.md",
            "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_AUTHORITY_BOUNDARY.md",
            "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_RECEIPT_PLAN.md",
            "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_NON_GOALS.md",
            "docs/autonomy/M99_TO_M100_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "tests/test_m99_autonomy_v1_safety_freeze.py",
            "tests/test_m99_gate_integration.py",
        ]
        failures = [
            f"missing M99 Autonomy v1 Safety Freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.gate.checkpoint_builders.m99_autonomy_v1_safety_freeze import _request
            from ultimate_ai_agent.core.autonomy import (
                AutonomyV1SafetyFreezeStatus,
                build_autonomy_v1_safety_freeze_report,
                validate_autonomy_v1_safety_freeze_report,
            )

            report = build_autonomy_v1_safety_freeze_report(_request())
            if (
                report.status != AutonomyV1SafetyFreezeStatus.frozen_for_review
                or not report.freeze_only
                or not report.review_only
                or not report.m61_m98_covered
                or not report.no_broad_unsandboxed_autonomy
                or not report.no_production_authority
                or report.broad_autonomy_granted
                or report.global_autonomy_switch_enabled
                or report.execution_performed
                or report.tool_execution_performed
                or report.shell_execution_performed
                or report.browser_action_performed
                or report.network_mutation_performed
                or report.plugin_execution_performed
                or report.background_worker_started
                or report.scheduler_started
                or report.mobile_sensor_performed
                or report.memory_write_performed
                or report.context_injection_performed
                or report.raw_prompt_payload_exposed
                or report.raw_file_export_performed
                or report.full_file_read_performed
                or report.remote_execution_performed
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.production_authority_granted
                or "M99_AUTONOMY_V1_SAFETY_FREEZE_REVIEW_ONLY"
                not in report.reason_codes
                or "M100_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M99 Autonomy v1 Safety Freeze report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"shell_execution_performed": True}, "SHELL_EXECUTION_DENIED"),
                ({"background_worker_started": True}, "BACKGROUND_WORKER_DENIED"),
                ({"production_authority_granted": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_autonomy_v1_safety_freeze_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M99 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M99 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M99 Autonomy v1 Safety Freeze validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "autonomy v1 safety freeze",
            "m61-m98",
            "freeze-only",
            "review-only",
            "no broad unsandboxed autonomy",
            "no global autonomy switch",
            "no production authority",
            "no shell execution",
            "no browser action",
            "no network mutation",
            "no plugin execution",
            "no scheduler",
            "no background worker",
            "no mobile sensor",
            "no memory write",
            "no context injection",
            "no raw prompt",
            "no raw file export",
            "no full-file read",
            "no backend route",
            "no dependency",
            "evaluator boundaries revalidate",
            "m100 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M99 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m99_autonomy_v1_safety_freeze_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "broad_autonomy_enabled=True",
            "global_autonomy_switch_enabled=True",
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_action_enabled=True",
            "network_mutation_enabled=True",
            "plugin_execution_enabled=True",
            "background_worker_enabled=True",
            "scheduler_enabled=True",
            "mobile_sensor_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "credential_cookie_access_enabled=True",
            "raw_prompt_payload_exposure_enabled=True",
            "raw_file_export_enabled=True",
            "full_file_read_enabled=True",
            "remote_execution_enabled=True",
            "production_authority_enabled=True",
            "broad_autonomy_requested=True",
            "global_autonomy_switch_requested=True",
            "execution_requested=True",
            "tool_execution_requested=True",
            "shell_execution_requested=True",
            "browser_action_requested=True",
            "network_mutation_requested=True",
            "plugin_execution_requested=True",
            "background_worker_requested=True",
            "scheduler_requested=True",
            "mobile_sensor_requested=True",
            "memory_write_requested=True",
            "context_injection_requested=True",
            "production_authority_requested=True",
            "broad_autonomy_granted=True",
            "tool_execution_performed=True",
            "shell_execution_performed=True",
            "browser_action_performed=True",
            "network_mutation_performed=True",
            "plugin_execution_performed=True",
            "background_worker_started=True",
            "scheduler_started=True",
            "mobile_sensor_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "production_authority_granted=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/autonomy/__init__.py",
            "src/ultimate_ai_agent/core/autonomy/v1_safety_freeze.py",
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
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M99 forbidden autonomy freeze fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m99_autonomy_v1_safety_freeze_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m99_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M99 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m99_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M99 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.3.0" not in text
            or "m99" not in text
            or "autonomy v1 safety freeze" not in text
        ):
            failures.append(
                "active docs do not identify v1.3.0/M99 Autonomy v1 Safety Freeze"
            )
        if (
            "m99 is implemented/released" not in text
            and "v1.3.0 implements m99" not in text
        ):
            failures.append("active docs do not mark M99 implemented/released")
        if (
            "v1.4.0" not in text
            or "m100" not in text
            or "mobile permission model v1" not in text
        ):
            failures.append("active docs missing planned M100 row")
        for fragment in (
            "mobile permission runtime is implemented",
            "mobile sensors are implemented",
            "background collection is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "global autonomy switch is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M99 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m100_mobile_permission_model_v1_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
            "docs/mobile/MOBILE_PERMISSION_MODEL_V1.md",
            "docs/mobile/MOBILE_PERMISSION_MODEL_V1_POLICY.md",
            "docs/mobile/MOBILE_PERMISSION_MODEL_V1_CONSENT_REVOCATION.md",
            "docs/mobile/MOBILE_PERMISSION_MODEL_V1_PRIVACY_COPY.md",
            "docs/mobile/MOBILE_PERMISSION_MODEL_V1_AUDIT.md",
            "docs/mobile/MOBILE_PERMISSION_MODEL_V1_NON_GOALS.md",
            "docs/mobile/M100_FINAL_BOUNDARY.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "tests/test_m100_mobile_permission_model_v1.py",
            "tests/test_m100_gate_integration.py",
        ]
        failures = [
            f"missing M100 Mobile Permission Model v1 file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobilePermissionModelV1Status,
                build_mobile_permission_model_v1_report,
                validate_mobile_permission_model_v1_report,
            )

            report = build_mobile_permission_model_v1_report()
            if (
                report.status != MobilePermissionModelV1Status.contract_only
                or not report.contract_only
                or not report.permission_taxonomy_defined
                or not report.consent_model_defined
                or not report.revocation_model_defined
                or not report.privacy_copy_defined
                or not report.permission_audit_defined
                or not report.sensors_remain_off
                or not report.no_background_collection
                or report.runtime_permission_prompts_enabled
                or report.native_permission_requests_enabled
                or report.mobile_sensor_enabled
                or report.location_access_enabled
                or report.camera_access_enabled
                or report.photos_access_enabled
                or report.microphone_access_enabled
                or report.background_collection_enabled
                or report.push_execution_enabled
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.backend_route_added
                or report.dependency_added
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M100_MOBILE_PERMISSION_MODEL_V1_CONTRACT_ONLY"
                not in report.reason_codes
                or "POST_M100_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M100 Mobile Permission Model v1 report is unsafe or over-authoritative"
                )
            for update, reason in [
                ({"mobile_sensor_enabled": True}, "MOBILE_SENSOR_DENIED"),
                (
                    {"background_collection_enabled": True},
                    "BACKGROUND_COLLECTION_DENIED",
                ),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_permission_model_v1_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M100 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M100 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M100 Mobile Permission Model v1 validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile permission model v1",
            "permission taxonomy",
            "consent",
            "revocation",
            "privacy copy",
            "permission audit",
            "contract-only",
            "sensors remain off",
            "no background collection",
            "no runtime permission prompts",
            "no native permission request",
            "no production authority",
            "no backend route",
            "no dependency",
            "m100 implemented/released",
            "do not start m101",
        ]:
            if fragment not in docs_text:
                failures.append(f"M100 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m100_mobile_permission_model_v1_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "runtime_permission_prompts_enabled=True",
            "native_permission_requests_enabled=True",
            "runtime_prompt_enabled=True",
            "native_permission_request_enabled=True",
            "mobile_sensor_enabled=True",
            "sensor_access_enabled=True",
            "location_access_enabled=True",
            "camera_access_enabled=True",
            "photos_access_enabled=True",
            "microphone_access_enabled=True",
            "background_collection_enabled=True",
            "push_execution_enabled=True",
            "production_authority_enabled=True",
            "runtime_consent_granted=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
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
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M100 forbidden mobile permission fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m100_mobile_permission_model_v1_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m100_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M100 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m100_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M61_M100_ROADMAP.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M100 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.4.0" not in text
            or "m100" not in text
            or "mobile permission model v1" not in text
        ):
            failures.append(
                "active docs do not identify v1.4.0/M100 Mobile Permission Model v1"
            )
        if (
            "m100 is implemented/released" not in text
            and "v1.4.0 implements m100" not in text
        ):
            failures.append("active docs do not mark M100 implemented/released")
        implemented_m101 = "v1.5.0" in text and (
            "m101 is implemented/released" in text or "v1.5.0 implements m101" in text
        )
        forbidden_fragments = [
            "mobile permission runtime is implemented",
            "mobile sensors are implemented",
            "background collection is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
            "global autonomy switch is implemented",
        ]
        if not implemented_m101:
            forbidden_fragments.extend(
                [
                    "m101 is implemented",
                    "v1.5.0 implements m101",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M100 docs imply forbidden/post-M100 capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_post_m100_roadmap_reconciliation(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        def contains_affirmative_fragment(text: str, fragment: str) -> bool:
            pattern = re.compile(
                rf"\b{re.escape(fragment)}\b",
                re.IGNORECASE,
            )
            negation_tokens = {
                "absence",
                "absent",
                "cannot",
                "cant",
                "can't",
                "didnt",
                "didn't",
                "doesnt",
                "doesn't",
                "dont",
                "don't",
                "never",
                "no",
                "none",
                "not",
                "without",
            }
            for match in pattern.finditer(text):
                prefix = text[max(0, match.start() - 160) : match.start()]
                tokens = re.findall(r"[a-z0-9']+", prefix.lower())[-8:]
                if any(token in negation_tokens for token in tokens):
                    continue
                compound_negation = tokens[-2:] in (
                    ["does", "not"],
                    ["do", "not"],
                    ["did", "not"],
                    ["can", "not"],
                )
                if len(tokens) >= 2 and compound_negation:
                    continue
                return True
            return False

        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/README.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/reviews/post_m100_full_repository_review_v1_4_1.md",
            "docs/release_notes/v1_4_1.md",
        ]
        failures = [
            f"missing post-M100 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v1.4.1" not in text or "post-m100" not in text:
            failures.append(
                "active docs do not identify v1.4.1 post-M100 reconciliation"
            )
        if (
            "m100 remains implemented/released" not in text
            and "m100 is implemented/released" not in text
        ):
            failures.append(
                "active docs do not preserve M100 implemented/released status"
            )
        expected_labels = [
            ("v1.5.0", "pre-alpha internal", "m101", "mobile sensor contract review"),
            ("v1.6.0", "pre-alpha internal", "m102", "location sensor, off by default"),
            (
                "v1.7.0",
                "pre-alpha internal",
                "m103",
                "camera/photos metadata-only contract",
            ),
            *[
                (f"checkpoint {milestone}", "pre-alpha checkpoint", milestone, title)
                for milestone, title in [
                    ("m104", "notification planning, no push execution"),
                    ("m105", "background task contract, no execution"),
                    ("m106", "mobile background read-only status sync"),
                    ("m107", "mobile approval renewal ux"),
                    ("m108", "mobile kill switch + revocation"),
                    ("m109", "mobile sensor audit ledger"),
                    ("m110", "mobile sensor hardening freeze"),
                    ("m111", "production threat model"),
                    ("m112", "user/workspace identity model"),
                    ("m113", "secrets boundary + credential vault contract"),
                    ("m114", "account connector contract review"),
                    ("m115", "production audit retention policy"),
                    ("m116", "role-based authority model"),
                    ("m117", "remote agent coordination contract"),
                    ("m118", "deployment mode matrix"),
                    ("m119", "production red-team harness"),
                    ("m120", "production authority readiness review"),
                    ("m121", "email connector contract refresh"),
                    ("m122", "calendar connector contract refresh"),
                    ("m123", "contacts connector contract refresh"),
                    ("m124", "messages connector contract review"),
                    ("m125", "connector read-only runtime"),
                    ("m126", "connector approval capture"),
                    ("m127", "connector write dry-run planner"),
                    ("m128", "connector write execution, low-risk only"),
                    ("m129", "connector audit + revocation hardening"),
                    ("m130", "connector safety freeze"),
                    ("m131", "autonomy mode 4, scoped work session"),
                    ("m132", "autonomy mode 5, trusted recurring workflow"),
                    ("m133", "long-running task supervisor"),
                    ("m134", "human checkpoint scheduling"),
                    ("m135", "autonomous recovery planner"),
                    ("m136", "cross-tool dependency execution"),
                    ("m137", "autonomous browser + connector combined workflows"),
                    ("m138", "autonomous error handling guardrails"),
                    ("m139", "autonomy abuse/loop detection"),
                    ("m140", "higher-autonomy red-team freeze"),
                    ("m141", "multi-user product boundary"),
                    ("m142", "alpha privacy review"),
                    ("m143", "alpha ui and app readiness"),
                    ("m144", "plugin marketplace policy draft"),
                    ("m145", "enterprise/pro safety modes"),
                    ("m146", "billing/plan boundary, if needed"),
                    ("m147", "public docs + wiki readiness"),
                    ("m148", "external security review"),
                    ("m149", "alpha release candidate freeze"),
                ]
            ],
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        active_version_text = self._read(self.root / "VERSION.md").lower()
        implemented_milestones = set()
        if (
            "v1.5.0" in active_version_text
            or "m101" in active_version_text
            or "mobile sensor contract review" in active_version_text
        ):
            implemented_milestones.add("m101")
        if (
            "v1.6.0" in active_version_text
            or "m102" in active_version_text
            or "location sensor, off by default" in active_version_text
        ):
            implemented_milestones.add("m102")
        if (
            "v1.7.0" in active_version_text
            or "m103" in active_version_text
            or "camera/photos metadata-only contract" in active_version_text
        ):
            implemented_milestones.add("m103")
        if (
            "checkpoint m104" in active_version_text
            or "m104" in active_version_text
            or "notification planning, no push execution" in active_version_text
        ):
            implemented_milestones.add("m104")
        if (
            "checkpoint m105" in active_version_text
            or "m105" in active_version_text
            or "background task contract, no execution" in active_version_text
        ):
            implemented_milestones.add("m105")
        if (
            "checkpoint m106" in active_version_text
            or "m106" in active_version_text
            or "mobile background read-only status sync" in active_version_text
        ):
            implemented_milestones.add("m106")
        if (
            "checkpoint m107" in active_version_text
            or "m107" in active_version_text
            or "mobile approval renewal ux" in active_version_text
        ):
            implemented_milestones.add("m107")
        if (
            "checkpoint m108" in active_version_text
            or "m108" in active_version_text
            or "mobile kill switch + revocation" in active_version_text
        ):
            implemented_milestones.add("m108")
        if (
            "checkpoint m109" in active_version_text
            or "m109" in active_version_text
            or "mobile sensor audit ledger" in active_version_text
        ):
            implemented_milestones.add("m109")
        if (
            "checkpoint m110" in active_version_text
            or "m110" in active_version_text
            or "mobile sensor hardening freeze" in active_version_text
        ):
            implemented_milestones.add("m110")
        if (
            "checkpoint m111" in active_version_text
            or "m111" in active_version_text
            or "production threat model" in active_version_text
        ):
            implemented_milestones.add("m111")
        if (
            "checkpoint m112" in active_version_text
            or "m112" in active_version_text
            or "user/workspace identity model" in active_version_text
        ):
            implemented_milestones.add("m112")
        if (
            "checkpoint m113" in active_version_text
            or "m113" in active_version_text
            or "secrets boundary + credential vault contract" in active_version_text
        ):
            implemented_milestones.add("m113")
        if (
            "checkpoint m114" in active_version_text
            or "m114" in active_version_text
            or "account connector contract review" in active_version_text
        ):
            implemented_milestones.add("m114")
        if (
            "checkpoint m115" in active_version_text
            or "m115" in active_version_text
            or "production audit retention policy" in active_version_text
        ):
            implemented_milestones.add("m115")
        if (
            "checkpoint m116" in active_version_text
            or "m116" in active_version_text
            or "role-based authority model" in active_version_text
        ):
            implemented_milestones.add("m116")
        if (
            "checkpoint m117" in active_version_text
            or "m117" in active_version_text
            or "remote agent coordination contract" in active_version_text
        ):
            implemented_milestones.add("m117")
        if (
            "checkpoint m118" in active_version_text
            or "m118" in active_version_text
            or "deployment mode matrix" in active_version_text
        ):
            implemented_milestones.add("m118")
        if (
            "checkpoint m119" in active_version_text
            or "m119" in active_version_text
            or "production red-team harness" in active_version_text
        ):
            implemented_milestones.add("m119")
        if (
            "checkpoint m120" in active_version_text
            or "m120" in active_version_text
            or "production authority readiness review" in active_version_text
        ):
            implemented_milestones.add("m120")
        if (
            "checkpoint m121" in active_version_text
            or "m121" in active_version_text
            or "email connector contract refresh" in active_version_text
        ):
            implemented_milestones.add("m121")
        if (
            "checkpoint m122" in active_version_text
            or "m122" in active_version_text
            or "calendar connector contract refresh" in active_version_text
        ):
            implemented_milestones.add("m122")
        if (
            "checkpoint m123" in active_version_text
            or "m123" in active_version_text
            or "contacts connector contract refresh" in active_version_text
        ):
            implemented_milestones.add("m123")
        if (
            "checkpoint m124" in active_version_text
            or "m124" in active_version_text
            or "messages connector contract review" in active_version_text
        ):
            implemented_milestones.add("m124")
        if (
            "checkpoint m125" in active_version_text
            or "m125" in active_version_text
            or "connector read-only runtime" in active_version_text
        ):
            implemented_milestones.add("m125")
        if (
            "checkpoint m126" in active_version_text
            or "m126" in active_version_text
            or "connector approval capture" in active_version_text
        ):
            implemented_milestones.add("m126")
        if (
            "checkpoint m127" in active_version_text
            or "m127" in active_version_text
            or "connector write dry-run planner" in active_version_text
        ):
            implemented_milestones.add("m127")
        if (
            "checkpoint m128" in active_version_text
            or "m128" in active_version_text
            or "connector write execution, low-risk only" in active_version_text
        ):
            implemented_milestones.add("m128")
        if (
            "checkpoint m129" in active_version_text
            or "m129" in active_version_text
            or "connector audit + revocation hardening" in active_version_text
        ):
            implemented_milestones.add("m129")
        if (
            "checkpoint m130" in active_version_text
            or "m130" in active_version_text
            or "connector safety freeze" in active_version_text
        ):
            implemented_milestones.add("m130")
        if (
            "checkpoint m131" in active_version_text
            or "m131" in active_version_text
            or "autonomy mode 4, scoped work session" in active_version_text
        ):
            implemented_milestones.add("m131")
        if (
            "checkpoint m132" in active_version_text
            or "m132" in active_version_text
            or "autonomy mode 5, trusted recurring workflow" in active_version_text
        ):
            implemented_milestones.add("m132")
        if (
            "checkpoint m133" in active_version_text
            or "m133" in active_version_text
            or "long-running task supervisor" in active_version_text
        ):
            implemented_milestones.add("m133")
        if (
            "checkpoint m134" in active_version_text
            or "m134" in active_version_text
            or "human checkpoint scheduling" in active_version_text
        ):
            implemented_milestones.add("m134")
        if (
            "checkpoint m135" in active_version_text
            or "m135" in active_version_text
            or "autonomous recovery planner" in active_version_text
        ):
            implemented_milestones.add("m135")
        if (
            "checkpoint m136" in active_version_text
            or "m136" in active_version_text
            or "cross-tool dependency execution" in active_version_text
        ):
            implemented_milestones.add("m136")
        if (
            "checkpoint m137" in active_version_text
            or "m137" in active_version_text
            or "autonomous browser + connector combined workflows"
            in active_version_text
        ):
            implemented_milestones.add("m137")
        if (
            "checkpoint m138" in active_version_text
            or "m138" in active_version_text
            or "autonomous error handling guardrails" in active_version_text
        ):
            implemented_milestones.add("m138")
        if (
            "checkpoint m139" in active_version_text
            or "m139" in active_version_text
            or "autonomy abuse/loop detection" in active_version_text
        ):
            implemented_milestones.add("m139")
        if (
            "checkpoint m140" in active_version_text
            or "m140" in active_version_text
            or "higher-autonomy red-team freeze" in active_version_text
        ):
            implemented_milestones.add("m140")
        if _version_doc_marks_milestone_implemented(active_version_text, "m141"):
            implemented_milestones.add("m141")
        if _version_doc_marks_milestone_implemented(active_version_text, "m142"):
            implemented_milestones.add("m142")
        if _version_doc_marks_milestone_implemented(active_version_text, "m143"):
            implemented_milestones.add("m143")
        if _version_doc_marks_milestone_implemented(active_version_text, "m144"):
            implemented_milestones.add("m144")
        if _version_doc_marks_milestone_implemented(active_version_text, "m145"):
            implemented_milestones.add("m145")
        if _version_doc_marks_milestone_implemented(active_version_text, "m146"):
            implemented_milestones.add("m146")
        if _version_doc_marks_milestone_implemented(active_version_text, "m147"):
            implemented_milestones.add("m147")
        if _version_doc_marks_milestone_implemented(active_version_text, "m148"):
            implemented_milestones.add("m148")
        if _version_doc_marks_milestone_implemented(active_version_text, "m149"):
            implemented_milestones.add("m149")
        if _version_doc_marks_milestone_implemented(active_version_text, "m150"):
            implemented_milestones.add("m150")
        if "m150" in implemented_milestones:
            implemented_m150_row = (
                "| v1.2.0-alpha | alpha | m150 | ultimate ai agent v1.2.0-alpha | "
                "implemented/released |"
            )
            if implemented_m150_row not in text:
                failures.append(
                    "M101-M150 roadmap row must mark M150 implemented/released"
                )
        for version_label, product_target, milestone, title in expected_labels:
            if milestone in implemented_milestones:
                continue
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"M101-M150 roadmap row must be planned/provisional: {version_label} / {milestone.upper()} - {title}"
                )
        for fragment in (
            "| v1.54.0 | m150 | ultimate ai agent beta 1 |",
            "| v1.8.0 | m104 | notification planning, no push execution |",
            "m150 | ultimate ai agent beta 1",
        ):
            if fragment in text:
                failures.append(
                    f"stale fast-version roadmap fragment remains active: {fragment}"
                )
        for minor in range(2, 49):
            future_semver_row = f"| v1.7.{minor} |"
            if future_semver_row in text:
                failures.append(
                    f"future milestone SemVer row remains active: {future_semver_row}"
                )
        for fragment in ("v1.2.0-alpha", "beta begins", "do not rewrite"):
            if fragment not in text:
                failures.append(
                    f"post-M100 roadmap missing alpha versioning policy fragment: {fragment}"
                )
        for fragment in (
            "mobile sensor runtime is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ):
            if contains_affirmative_fragment(text, fragment):
                failures.append(
                    f"post-M100 docs imply forbidden future capability: {fragment}"
                )
        for version_label, _product_target, milestone, _title in expected_labels:
            if milestone in implemented_milestones:
                continue
            for fragment in (
                f"{milestone} is implemented",
                f"{version_label} implements {milestone}",
                f"{milestone} has started",
            ):
                if contains_affirmative_fragment(text, fragment):
                    failures.append(
                        f"post-M100 docs imply forbidden future milestone state: {fragment}"
                    )
        return self._result(criterion, failures, required_docs)

    def check_m101_mobile_sensor_contract_review_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/sensor_contract_review.py",
            "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW.md",
            "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_POLICY.md",
            "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_RECEIPT_PLAN.md",
            "docs/mobile/MOBILE_SENSOR_CONTRACT_REVIEW_NON_GOALS.md",
            "docs/mobile/M101_TO_M102_BOUNDARY.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "tests/test_m101_mobile_sensor_contract_review.py",
            "tests/test_m101_gate_integration.py",
        ]
        failures = [
            f"missing M101 mobile sensor contract review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            sys.path.insert(0, str(self.root))
            from ultimate_ai_agent.core.mobile_companion import (
                MobileSensorContractReviewStatus,
                build_mobile_sensor_contract_review_report,
                validate_mobile_sensor_contract_review_report,
            )

            report = build_mobile_sensor_contract_review_report()
            if (
                report.status != MobileSensorContractReviewStatus.contract_only
                or not report.contract_only
                or not report.sensor_taxonomy_defined
                or not report.permission_state_contract_defined
                or not report.sensor_risk_classification_defined
                or not report.consent_revocation_required
                or not report.audit_required
                or not report.sensors_default_off
                or not report.unknown_sensor_denied
                or report.runtime_sensor_access_enabled
                or report.native_permission_prompt_enabled
                or report.background_collection_enabled
                or report.location_sensor_enabled
                or report.camera_sensor_enabled
                or report.photos_sensor_enabled
                or report.microphone_sensor_enabled
                or report.raw_sensor_payload_enabled
                or report.backend_route_added
                or report.dependency_added
                or report.memory_write_enabled
                or report.context_injection_enabled
                or report.execution_enabled
                or report.production_authority_enabled
                or report.side_effects_performed
                or "M101_MOBILE_SENSOR_CONTRACT_REVIEW_ONLY" not in report.reason_codes
                or "M102_REMAINS_FUTURE" not in report.reason_codes
            ):
                failures.append(
                    "M101 mobile sensor contract review report is unsafe or over-authoritative"
                )
            for update, reason in [
                (
                    {"runtime_sensor_access_enabled": True},
                    "RUNTIME_SENSOR_ACCESS_DENIED",
                ),
                (
                    {"native_permission_prompt_enabled": True},
                    "NATIVE_PERMISSION_PROMPT_DENIED",
                ),
                (
                    {"background_collection_enabled": True},
                    "BACKGROUND_COLLECTION_DENIED",
                ),
                ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
            ]:
                try:
                    validate_mobile_sensor_contract_review_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M101 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M101 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(
                f"M101 mobile sensor contract review validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "mobile sensor contract review",
            "contract-only",
            "sensor capability classes",
            "permission-state contract",
            "sensor risk classification",
            "consent",
            "revocation",
            "audit",
            "sensors default off",
            "unknown sensor denied",
            "no runtime sensor access",
            "no native permission prompt",
            "no background collection",
            "no backend route",
            "no dependency",
            "no production authority",
            "m102 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M101 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m101_mobile_sensor_contract_review_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "runtime_sensor_access_enabled=True",
            "native_permission_prompt_enabled=True",
            "background_collection_enabled=True",
            "location_sensor_enabled=True",
            "camera_sensor_enabled=True",
            "photos_sensor_enabled=True",
            "microphone_sensor_enabled=True",
            "raw_sensor_payload_enabled=True",
            "backend_route_enabled=True",
            "backend_route_added=True",
            "production_authority_enabled=True",
        ]
        allowed_files = {
            "scripts/verify_all.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
            "src/ultimate_ai_agent/core/mobile_companion/permission_model_v1.py",
            "src/ultimate_ai_agent/core/mobile_companion/sensor_contract_review.py",
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
                if ".test." in rel:
                    continue
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M101 forbidden mobile sensor fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m101_mobile_sensor_contract_review_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m101_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M101 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m101_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        ]
        failures = [
            f"missing M101 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v1.5.0" not in text
            or "m101" not in text
            or "mobile sensor contract review" not in text
        ):
            failures.append(
                "active docs do not identify v1.5.0/M101 Mobile Sensor Contract Review"
            )
        if (
            "m101 is implemented/released" not in text
            and "v1.5.0 implements m101" not in text
        ):
            failures.append("active docs do not mark M101 implemented/released")
        m102_implemented = "v1.6.0" in text and "m102" in text
        m103_implemented = "v1.7.0" in text and "m103" in text
        planned_rows = [
            ("v1.2.0-alpha", "alpha", "m150", "ultimate ai agent v1.2.0-alpha"),
        ]
        if not m103_implemented:
            planned_rows.insert(
                0,
                (
                    "v1.7.0",
                    "pre-alpha internal",
                    "m103",
                    "camera/photos metadata-only contract",
                ),
            )
        if not m102_implemented:
            planned_rows.insert(
                0,
                (
                    "v1.6.0",
                    "pre-alpha internal",
                    "m102",
                    "location sensor, off by default",
                ),
            )
        for version_label, product_target, milestone, title in planned_rows:
            row = (
                f"| {version_label} | {product_target} | {milestone} | "
                f"{title} | planned/provisional |"
            )
            if not _roadmap_row_present(text, row):
                failures.append(
                    f"active docs missing planned M102-M150 row: {version_label} / {milestone.upper()} - {title}"
                )
        forbidden_fragments = [
            "location sensor runtime is implemented",
            "native permission prompt is implemented",
            "background collection is implemented",
            "production authority is implemented",
            "broad autonomy is implemented",
        ]
        if not m102_implemented:
            forbidden_fragments.extend(
                ["m102 is implemented", "v1.6.0 implements m102"]
            )
        if not m103_implemented:
            forbidden_fragments.extend(
                ["m103 is implemented", "v1.7.0 implements m103"]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M101 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
