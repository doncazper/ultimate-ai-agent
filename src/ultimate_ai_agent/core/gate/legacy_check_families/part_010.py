from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart010Mixin:
    """Legacy checks from m39_roadmap_currentness through m45_ios_local_connection_static_safety."""
    def check_m39_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M39 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.43.0" not in text
            or "m39" not in text
            or "ccc context proposal surface" not in text
        ):
            failures.append(
                "active docs do not identify v0.43.0/M39 CCC Context Proposal Surface"
            )
        if (
            "m39 is implemented/released" not in text
            and "v0.43.0 implements m39" not in text
        ):
            failures.append("active docs do not mark M39 implemented/released")
        m41_implemented = (
            "v0.45.0 implements m41" in text or "m41 is implemented/released" in text
        )
        m40_implemented = (
            "v0.44.0 implements m40" in text or "m40 is implemented/released" in text
        )
        if m41_implemented:
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
        elif m40_implemented:
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif (
            "m40 remains planned/provisional" not in text
            and "m40-m60 remain planned/provisional" not in text
        ):
            failures.append("M40 must remain planned/provisional after M39")
        for fragment in (
            "context injection is implemented",
            "openwebui handoff is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M39 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m40_context_handoff_approval_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/context_handoff/__init__.py",
            "src/ultimate_ai_agent/core/context_handoff/contracts.py",
            "src/ultimate_ai_agent/core/context_handoff/validation.py",
            "src/ultimate_ai_agent/core/context_handoff/workflow.py",
            "src/ultimate_ai_agent/core/context_handoff/receipts.py",
            "tests/test_context_handoff_approval_contracts.py",
            "tests/test_context_handoff_approval_binding.py",
            "tests/test_context_handoff_no_injection.py",
            "tests/test_m40_gate_integration.py",
            "docs/context/CONTEXT_HANDOFF_APPROVAL.md",
            "docs/context/CONTEXT_HANDOFF_APPROVAL_BOUNDARY.md",
            "docs/context/CONTEXT_HANDOFF_NO_INJECTION_POLICY.md",
            "docs/context/CONTEXT_HANDOFF_RECEIPT_PLAN.md",
            "docs/context/M40_TO_M41_BOUNDARY.md",
        ]
        failures = [
            f"missing M40 context handoff approval file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.context_handoff import (
                ContextHandoffApprovalDecisionStatus,
                ContextHandoffApprovalKind,
                ContextHandoffApprovalRequest,
                evaluate_context_handoff_approval,
            )
            from ultimate_ai_agent.core.context_proposal import (
                build_safe_context_proposal,
            )
            from ultimate_ai_agent.core.file_review import (
                FileReviewApprovalCaptureDecisionStatus,
                FileReviewApprovalDecisionKind,
                FileReviewApprovalRecord,
                build_file_review_packet,
            )
            from ultimate_ai_agent.core.tools.runtime import (
                FilePreviewRedactionSummary,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
            )

            preview = RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:m40-gate",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:m40-gate",
                safe_path_ref="filesystem-preview-path:safe-root_m40_gate/docs/review.md",
                redacted_preview="M40 gate redacted preview only.",
                redaction_summary=FilePreviewRedactionSummary(
                    redaction_count=1, categories=["secret_assignment"]
                ),
                file_size_bytes=64,
            )
            packet = build_file_review_packet(
                preview_output=preview,
                actor_ref="user:m40-gate",
                request_ref="file-review-request:m40-gate",
                file_ref="file-ref:m40-gate-review",
                safe_summary="Review a redacted packet for M40 handoff approval.",
            )
            approval_record = FileReviewApprovalRecord(
                approval_ref="file-review-approval-capture:m40-gate",
                actor_ref=packet.source.actor_ref,
                review_packet_ref=packet.review_packet_ref,
                preview_result_ref=packet.source.preview_result_ref,
                redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
                file_ref=packet.source.file_ref,
                safe_path_ref=packet.source.safe_path_ref,
                decision=FileReviewApprovalDecisionKind.approve_review_only,
                status=FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
                idempotency_key="file-review-approval-idempotency:m40-gate",
                safe_reason="User approved the redacted review packet for review-only follow-up.",
                receipt_plan_ref="file-review-approval-capture-receipt:m40-gate",
                authority_decision_ref="authority-policy-decision-ref:m40-gate",
                authority_decision_outcome="ask",
                authority_lease_ref="authority-lease-ref:m40-gate-files-write",
            )
            proposal = build_safe_context_proposal(
                packet=packet, approval_record=approval_record
            )
            request = ContextHandoffApprovalRequest(
                approval_ref="context-handoff-approval:m40-gate",
                actor_ref=proposal.binding.actor_ref,
                proposal_ref=proposal.proposal_ref,
                approval_record_ref=proposal.source.approval_record_ref,
                review_packet_ref=proposal.binding.review_packet_ref,
                preview_result_ref=proposal.binding.preview_result_ref,
                redaction_summary_ref=proposal.binding.redaction_summary_ref,
                file_ref=proposal.binding.file_ref,
                safe_path_ref=proposal.binding.safe_path_ref,
                decision=ContextHandoffApprovalKind.approve_handoff_review_only,
                idempotency_key="context-handoff-idempotency:m40-gate",
                safe_reason="Approve the safe context proposal for future handoff review only.",
            )
            decision = evaluate_context_handoff_approval(
                proposal=proposal, request=request
            )
            if (
                decision.status
                != ContextHandoffApprovalDecisionStatus.approved_for_handoff_review_only
            ):
                failures.append(
                    "M40 safe handoff approval did not produce review-only approval"
                )
            if not decision.handoff_approved_for_review:
                failures.append(
                    "M40 safe handoff approval did not preserve review decision"
                )
            for field_name in [
                "handoff_execution_authorized",
                "context_injection_authorized",
                "openwebui_handoff_authorized",
                "model_call_authorized",
                "memory_write_authorized",
                "export_authorized",
                "execution_authorized",
                "context_injection_performed",
                "openwebui_handoff_performed",
                "model_call_performed",
                "memory_write_performed",
                "export_performed",
                "execution_performed",
            ]:
                if getattr(decision, field_name):
                    failures.append(
                        f"M40 decision granted or performed forbidden authority: {field_name}"
                    )
            if decision.receipt_plan is None:
                failures.append("M40 approved decision is missing receipt plan")
            elif any(
                getattr(decision.receipt_plan, field_name)
                for field_name in [
                    "receipt_is_authority",
                    "raw_content_stored",
                    "full_file_content_stored",
                    "unredacted_preview_stored",
                    "context_injection_performed",
                    "openwebui_handoff_performed",
                    "model_call_performed",
                    "memory_write_performed",
                    "export_performed",
                    "execution_performed",
                ]
            ):
                failures.append(
                    "M40 receipt plan stores raw content or performs authority"
                )
            mutated_proposal = proposal.model_copy(
                update={"context_injection_enabled": True}
            )
            mutated_decision = evaluate_context_handoff_approval(
                proposal=mutated_proposal, request=request
            )
            if "context_injection_denied" not in mutated_decision.reason_codes:
                failures.append(
                    "M40 evaluator did not revalidate model_copy-mutated proposal context injection"
                )
            mutated_request = request.model_copy(
                update={"openwebui_handoff_execution_enabled": True}
            )
            mutated_request_decision = evaluate_context_handoff_approval(
                proposal=proposal, request=mutated_request
            )
            if "openwebui_handoff_denied" not in mutated_request_decision.reason_codes:
                failures.append(
                    "M40 evaluator did not revalidate model_copy-mutated request OpenWebUI handoff"
                )
            ref_only = evaluate_context_handoff_approval(
                proposal=None, request_ref="context-handoff-approval:m40-gate"
            )
            if "approval_ref_not_authority" not in ref_only.reason_codes:
                failures.append("M40 approval_ref-alone probe did not fail closed")
            test_ref_request = request.model_copy(
                update={"approval_ref": "approval_test_m40_gate"}
            )
            test_ref_decision = evaluate_context_handoff_approval(
                proposal=proposal, request=test_ref_request
            )
            if "approval_test_ref_denied" not in test_ref_decision.reason_codes:
                failures.append("M40 approval_test_ mutation probe did not fail closed")
            mismatch_request = request.model_copy(
                update={"proposal_ref": "safe-context-proposal:mismatch"}
            )
            mismatch_decision = evaluate_context_handoff_approval(
                proposal=proposal, request=mismatch_request
            )
            if "proposal_ref_mismatch" not in mismatch_decision.reason_codes:
                failures.append(
                    "M40 exact proposal binding mismatch probe did not fail closed"
                )
        except Exception as exc:
            failures.append(f"M40 context handoff approval probe failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "exact proposal binding",
            "review-only",
            "no context injection",
            "no openwebui handoff execution",
            "no model calls",
            "no memory writes",
            "no export",
            "no execution",
            "approval_ref alone is not authority",
            "approval_test_ is not runtime authority",
            "evaluator boundaries revalidate",
            "m41 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M40 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m40_context_handoff_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m40_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M40 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m40_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M40 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.44.0" not in text
            or "m40" not in text
            or "context handoff approval, no injection" not in text
        ):
            failures.append(
                "active docs do not identify v0.44.0/M40 Context Handoff Approval, No Injection"
            )
        if (
            "m40 is implemented/released" not in text
            and "v0.44.0 implements m40" not in text
        ):
            failures.append("active docs do not mark M40 implemented/released")
        active_version = self._active_version_tuple()
        if active_version >= (0, 45, 0):
            if (
                "m41 is implemented/released" not in text
                and "v0.45.0 implements m41" not in text
            ):
                failures.append("active docs do not mark M41 implemented/released")
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
        elif (
            "m41 remains planned/provisional" not in text
            and "m41-m60 remain planned/provisional" not in text
        ):
            failures.append("M41-M60 must remain planned/provisional after M40")
        for fragment in (
            "context injection is implemented",
            "openwebui handoff execution is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M40 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m41_local_prototype_safety_freeze(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "docs/prototype/LOCAL_PROTOTYPE_SAFETY_FREEZE.md",
            "docs/prototype/LOCAL_PROTOTYPE_BROWSER_SMOKE_REVIEW.md",
            "docs/prototype/LOCAL_PROTOTYPE_NO_AUTHORITY_BOUNDARY.md",
            "docs/prototype/M41_TO_M42_BOUNDARY.md",
            "docs/developer/LOCAL_LAUNCHER.md",
            "scripts/dev/uaa_launcher.py",
            "tests/test_m41_gate_integration.py",
            "tests/test_m41_local_prototype_safety_freeze.py",
        ]
        failures = [
            f"missing M41 local prototype safety freeze file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "local prototype safety freeze",
            "localhost-only",
            "review-only",
            "mock/non-authoritative",
            "no raw file browsing",
            "no raw file export",
            "no full-file reads",
            "no arbitrary caller-selected roots",
            "no shell/subprocess",
            "no network tools",
            "no provider/model calls as authority",
            "no background workers",
            "no mobile sensors",
            "no plugin enablement",
            "no production authority",
            "no unreviewed memory writes",
            "no automatic context injection",
            "no raw prompt/provider payload exposure",
            "no credentials/cookie handling",
            "no remote execution",
            "no browser automation execution",
            "approval refs are not authority",
            "browser smoke review is local-only",
            "m42 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M41 docs missing safety fragment: {fragment}")

        forbidden_fragments = [
            "raw file browsing is implemented",
            "raw file export is implemented",
            "full-file reads are implemented",
            "shell execution is implemented",
            "network tools are implemented",
            "model calls are authority",
            "background workers are implemented",
            "mobile sensors are implemented",
            "plugin enablement is implemented",
            "production authority is implemented",
            "automatic context injection is implemented",
            "remote execution is implemented",
            "browser automation execution is implemented",
            "approval refs are authority",
        ]
        for fragment in forbidden_fragments:
            if fragment in docs_text:
                failures.append(f"M41 docs imply forbidden capability: {fragment}")

        try:
            launcher_source = self._read(self.root / "scripts/dev/uaa_launcher.py")
            if (
                "SAFE_HOSTS" not in launcher_source
                or "validate_local_host" not in launcher_source
            ):
                failures.append(
                    "M41 launcher safety check cannot prove localhost-only refusal"
                )
            for fragment in ['"127.0.0.1"', '"localhost"']:
                if fragment not in launcher_source:
                    failures.append(
                        f"M41 launcher missing safe host fragment: {fragment}"
                    )
            for fragment in ["shell=True", "os." + "system(", "eval(", "ex" + "ec("]:
                if fragment in launcher_source:
                    failures.append(
                        f"M41 launcher contains forbidden shell/dynamic fragment: {fragment}"
                    )
        except Exception as exc:
            failures.append(f"M41 launcher safety read failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m41_local_prototype_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m41_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M41 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m41_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M41 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.45.0" not in text
            or "m41" not in text
            or "local prototype safety freeze" not in text
        ):
            failures.append(
                "active docs do not identify v0.45.0/M41 Local Prototype Safety Freeze"
            )
        if (
            "m41 is implemented/released" not in text
            and "v0.45.0 implements m41" not in text
        ):
            failures.append("active docs do not mark M41 implemented/released")
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif current_tuple >= (0, 48, 0):
            if "m45-m60 remain planned/provisional" not in text:
                failures.append("M45-M60 must remain planned/provisional after M44")
        elif current_tuple >= (0, 46, 0):
            if "m44-m60 remain planned/provisional" not in text:
                failures.append("M44-M60 must remain planned/provisional after M43")
        elif "m42-m60 remain planned/provisional" not in text:
            failures.append("M42-M60 must remain planned/provisional after M41")
        forbidden_fragments = ["testflight pipeline is implemented"]
        if current_tuple < (0, 48, 0):
            forbidden_fragments.append("ccc ios skeleton is implemented")
        if current_tuple < (0, 46, 0):
            forbidden_fragments.extend(
                [
                    "m42 is implemented",
                    "v0.46.0 implements m42",
                    "mobile companion product contract refresh is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M41 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m42_mobile_product_contract_refresh(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_COMPANION_PRODUCT_CONTRACT_REFRESH.md",
            "docs/mobile/M42_TO_M43_BOUNDARY.md",
            "docs/release_notes/v0_46_0.md",
            "docs/archive/releases/v0_46_0/README_IMPORT.md",
            "docs/archive/releases/v0_46_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_46_0.md",
            "tests/test_m42_mobile_product_contract_refresh.py",
        ]
        failures = [
            f"missing M42 mobile product contract refresh file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_mobile_product_contract_refresh_only,
                build_default_mobile_product_contract_refresh,
            )

            refresh = build_default_mobile_product_contract_refresh()
            assert_mobile_product_contract_refresh_only(refresh)
            if refresh.milestone != "M42" or refresh.version != "0.46.0":
                failures.append(
                    "default M42 mobile product refresh has wrong milestone/version"
                )
            if not refresh.contract_refresh_only:
                failures.append(
                    "default M42 mobile product refresh is not contract_refresh_only"
                )
            if (
                not refresh.m43_read_only_api_future
                or not refresh.m44_ios_skeleton_future
            ):
                failures.append("M42 does not keep M43/M44 future")
            forbidden_flags = [
                refresh.native_app_implemented,
                refresh.mobile_api_implemented,
                refresh.mobile_sensor_access_enabled,
                refresh.os_permission_integration_enabled,
                refresh.background_service_enabled,
                refresh.signing_or_store_workflow_enabled,
                refresh.approval_capture_enabled,
                refresh.approval_execution_enabled,
                refresh.memory_write_enabled,
                refresh.context_injection_enabled,
                refresh.raw_payload_exposure_enabled,
                refresh.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append(
                    "default M42 mobile product refresh enables forbidden authority"
                )
        except Exception as exc:
            failures.append(f"M42 mobile product contract validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "mobile companion product contract refresh",
            "planning/docs/contracts/verifier",
            "governance/control",
            "not the agent brain",
            "review-only",
            "read-only",
            "m43 is implemented/released",
            "m44 remains future",
            "no mobile app",
            "no ios app",
            "no android app",
            "no native package",
            "no native build workflow",
            "no signing",
            "no testflight",
            "no backend route",
            "no mobile api route",
            "no approval capture",
            "no approval execution",
            "no mobile sensor access",
            "no os permission integration",
            "no background service",
            "no notification runtime",
            "no raw payload exposure",
            "no memory write",
            "no context injection",
            "no production authority",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M42 docs missing safety fragment: {fragment}")

        forbidden_fragments = [
            "mobile app is implemented",
            "ios app is implemented",
            "android app is implemented",
            "mobile api is implemented",
            "mobile sensors are implemented",
            "approval execution is implemented",
            "production authority is implemented",
        ]
        for fragment in forbidden_fragments:
            if fragment in docs_text:
                failures.append(
                    f"M42 docs imply forbidden/future capability: {fragment}"
                )

        return self._result(criterion, failures, required_files)

    def check_m42_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m42_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M42 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m42_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M42 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.46.0" not in text
            or "m42" not in text
            or "mobile companion product contract refresh" not in text
        ):
            failures.append(
                "active docs do not identify v0.46.0/M42 Mobile Companion Product Contract Refresh"
            )
        if (
            "m42 is implemented/released" not in text
            and "v0.46.0 implements m42" not in text
        ):
            failures.append("active docs do not mark M42 implemented/released")
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif current_tuple >= (0, 48, 0):
            if "m45-m60 remain planned/provisional" not in text:
                failures.append("M45-M60 must remain planned/provisional after M44")
        elif "m44-m60 remain planned/provisional" not in text:
            failures.append("M44-M60 must remain planned/provisional after M43")
        forbidden_fragments = ["testflight pipeline is implemented"]
        if current_tuple < (0, 48, 0):
            forbidden_fragments.append("ccc ios skeleton is implemented")
        if current_tuple < (0, 47, 0):
            forbidden_fragments.extend(
                [
                    "m43 is implemented",
                    "v0.47.0 implements m43",
                    "mobile api boundary is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M42 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m43_mobile_api_boundary_read_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
            "src/ultimate_ai_agent/core/mobile_companion/planning.py",
            "src/ultimate_ai_agent/core/mobile_companion/enums.py",
            "docs/mobile/MOBILE_API_BOUNDARY_READ_ONLY.md",
            "docs/mobile/M43_TO_M44_BOUNDARY.md",
            "docs/release_notes/v0_47_0.md",
            "docs/archive/releases/v0_47_0/README_IMPORT.md",
            "docs/archive/releases/v0_47_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_47_0.md",
            "tests/test_m43_mobile_api_boundary_read_only.py",
        ]
        failures = [
            f"missing M43 mobile API boundary file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_mobile_api_boundary_read_only,
                build_default_mobile_read_only_api_boundary,
            )

            boundary = build_default_mobile_read_only_api_boundary()
            assert_mobile_api_boundary_read_only(boundary)
            if boundary.milestone != "M43" or boundary.version != "0.47.0":
                failures.append(
                    "default M43 mobile API boundary has wrong milestone/version"
                )
            if not boundary.boundary_contract_only or not boundary.read_only_boundary:
                failures.append(
                    "default M43 mobile API boundary is not contract/read-only"
                )
            if not boundary.redacted_summary_only:
                failures.append(
                    "default M43 mobile API boundary is not redacted-summary-only"
                )
            if not boundary.m44_ios_skeleton_future:
                failures.append("M43 does not keep M44 future")
            forbidden_flags = [
                boundary.backend_routes_added,
                boundary.mobile_mutation_enabled,
                boundary.mobile_sensor_access_enabled,
                boundary.approval_capture_enabled,
                boundary.approval_execution_enabled,
                boundary.raw_data_enabled,
                boundary.raw_payload_exposure_enabled,
                boundary.raw_absolute_path_exposure_enabled,
                boundary.context_injection_enabled,
                boundary.memory_write_enabled,
                boundary.export_enabled,
                boundary.execution_enabled,
                boundary.credential_or_cookie_handling_enabled,
                boundary.background_collection_enabled,
                boundary.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append(
                    "default M43 mobile API boundary enables forbidden authority"
                )
            if not boundary.endpoints:
                failures.append(
                    "default M43 mobile API boundary has no endpoint contracts"
                )
        except Exception as exc:
            failures.append(f"M43 mobile API boundary validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "mobile api boundary, read-only",
            "contract-only",
            "read-only",
            "redacted summary only",
            "planned endpoint refs",
            "no backend route",
            "no mobile mutation",
            "no approval capture",
            "no approval execution",
            "no mobile sensor access",
            "no raw data",
            "no raw payload exposure",
            "no raw absolute path",
            "no credential",
            "no cookie",
            "no context injection",
            "no memory write",
            "no export",
            "no execution",
            "no production authority",
            "m44 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M43 docs missing safety fragment: {fragment}")

        forbidden_fragments = [
            "mobile api route is implemented",
            "mobile mutation is implemented",
            "mobile sensors are implemented",
            "approval execution is implemented",
            "approval capture is implemented",
            "production authority is implemented",
            "m44 is implemented",
        ]
        for fragment in forbidden_fragments:
            if fragment in docs_text:
                failures.append(
                    f"M43 docs imply forbidden/future capability: {fragment}"
                )

        return self._result(criterion, failures, required_files)

    def check_m43_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m43_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M43 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m43_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M43 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.47.0" not in text
            or "m43" not in text
            or "mobile api boundary, read-only" not in text
        ):
            failures.append(
                "active docs do not identify v0.47.0/M43 Mobile API Boundary, Read-Only"
            )
        if (
            "m43 is implemented/released" not in text
            and "v0.47.0 implements m43" not in text
        ):
            failures.append("active docs do not mark M43 implemented/released")
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif current_tuple >= (0, 48, 0):
            if "m45-m60 remain planned/provisional" not in text:
                failures.append("M45-M60 must remain planned/provisional after M44")
        elif "m44-m60 remain planned/provisional" not in text:
            failures.append("M44-M60 must remain planned/provisional after M43")
        forbidden_fragments = [
            "mobile sensors are implemented",
            "approval execution is implemented",
            "production authority is implemented",
        ]
        if current_tuple < (0, 48, 0):
            forbidden_fragments.extend(
                [
                    "m44 is implemented",
                    "v0.48.0 implements m44",
                    "ccc ios skeleton is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M43 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m44_ccc_ios_skeleton_no_authority(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/ccc-ios/README.md",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
            "docs/mobile/CCC_IOS_SKELETON_NO_AUTHORITY.md",
            "docs/mobile/M44_TO_M45_BOUNDARY.md",
            "docs/release_notes/v0_48_0.md",
            "docs/archive/releases/v0_48_0/README_IMPORT.md",
            "docs/archive/releases/v0_48_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_48_0.md",
            "tests/test_m44_ccc_ios_skeleton_no_authority.py",
        ]
        failures = [
            f"missing M44 iOS skeleton file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_ccc_ios_skeleton_no_authority,
                build_default_ccc_ios_skeleton_manifest,
            )

            manifest = build_default_ccc_ios_skeleton_manifest()
            assert_ccc_ios_skeleton_no_authority(manifest)
            if manifest.milestone != "M44" or manifest.version != "0.48.0":
                failures.append(
                    "default M44 iOS skeleton manifest has wrong milestone/version"
                )
            if not manifest.source_only_skeleton or not manifest.no_authority:
                failures.append(
                    "default M44 iOS skeleton is not source-only/no-authority"
                )
            forbidden_flags = [
                manifest.production_workflow_enabled,
                manifest.signing_or_store_workflow_enabled,
                manifest.native_build_workflow_enabled,
                manifest.network_access_enabled,
                manifest.sensor_access_enabled,
                manifest.os_permission_integration_enabled,
                manifest.approval_capture_enabled,
                manifest.approval_execution_enabled,
                manifest.context_injection_enabled,
                manifest.memory_write_enabled,
                manifest.file_mutation_enabled,
                manifest.execution_enabled,
                manifest.credential_storage_enabled,
                manifest.background_task_enabled,
                manifest.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append("default M44 iOS skeleton enables forbidden authority")
            if not manifest.m45_local_read_only_connection_future:
                failures.append("M44 does not keep M45 future")
        except Exception as exc:
            failures.append(f"M44 iOS skeleton validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "ccc ios skeleton, no authority",
            "source-only",
            "mock-only",
            "read-only",
            "non-authoritative",
            "no xcode project",
            "no swift package",
            "no info.plist",
            "no entitlements",
            "no backend route",
            "no mobile api route runtime",
            "no network",
            "no mobile sensor access",
            "no os permission integration",
            "no approval capture",
            "no approval execution",
            "no context injection",
            "no memory write",
            "no file mutation",
            "no execution",
            "no credential",
            "no background",
            "no production authority",
            "m45 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M44 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m44_ios_skeleton_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        failures: List[str] = []
        if not swift_root.exists():
            failures.append("M44 Swift source root missing")
            return self._result(
                criterion, failures, [str(swift_root.relative_to(self.root))]
            )
        for forbidden_path in [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *self._context.rglob(ios_root, "*.entitlements"),
            *self._context.rglob(ios_root, "Info.plist"),
        ]:
            if forbidden_path.exists():
                failures.append(
                    f"M44 forbidden native workflow file present: {forbidden_path.relative_to(self.root)}"
                )
        swift_files = sorted(self._context.rglob(swift_root, "*.swift"))
        if not swift_files:
            failures.append("M44 Swift source files missing")
        swift_text = "\n".join(self._context.read_text(path, encoding="utf-8") for path in swift_files)
        for fragment in M44_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M44 forbidden Swift API fragment present: {fragment}")
        lowered = swift_text.lower()
        for required in ["swiftui", "mock", "non-authoritative", "read-only"]:
            if required not in lowered:
                failures.append(f"M44 Swift source missing required marker: {required}")
        return self._result(
            criterion,
            failures,
            [self._context.relative_path(path) for path in swift_files],
        )

    def check_m44_mobile_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m44_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M44 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m44_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        failures = [
            f"missing M44 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.48.0" not in text
            or "m44" not in text
            or "ccc ios skeleton, no authority" not in text
        ):
            failures.append(
                "active docs do not identify v0.48.0/M44 CCC iOS Skeleton, No Authority"
            )
        if (
            "m44 is implemented/released" not in text
            and "v0.48.0 implements m44" not in text
        ):
            failures.append("active docs do not mark M44 implemented/released")
        current_tuple = self._active_version_tuple()
        if current_tuple >= (0, 52, 0):
            self._append_post_m48_mobile_status_failures(text, failures)
        elif current_tuple >= (0, 51, 0):
            if "m48-m60 remain planned/provisional" not in text:
                failures.append("M48-M60 must remain planned/provisional after M47")
        elif current_tuple >= (0, 50, 0):
            if "m47-m60 remain planned/provisional" not in text:
                failures.append("M47-M60 must remain planned/provisional after M46")
        elif current_tuple >= (0, 49, 0):
            if "m46-m60 remain planned/provisional" not in text:
                failures.append("M46-M60 must remain planned/provisional after M45")
        elif "m45-m60 remain planned/provisional" not in text:
            failures.append("M45-M60 must remain planned/provisional after M44")
        forbidden_fragments = [
            "m45 is implemented",
            "v0.49.0 implements m45",
            "local read-only connection is implemented",
            "testflight pipeline is implemented",
            "mobile sensors are implemented",
            "approval execution is implemented",
            "production authority is implemented",
        ]
        if current_tuple >= (0, 49, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment
                not in {
                    "m45 is implemented",
                    "v0.49.0 implements m45",
                    "local read-only connection is implemented",
                }
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M44 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m45_ccc_ios_local_read_only_connection(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/ccc-ios/README.md",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/UltimateAIAgentCCCApp.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/ReadOnlyDashboardView.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/SkeletonFixtures.swift",
            "apps/ccc-ios/Sources/UltimateAIAgentCCC/LocalReadOnlyConnectionModels.swift",
            "docs/mobile/CCC_IOS_LOCAL_READ_ONLY_CONNECTION.md",
            "docs/mobile/M45_TO_M46_BOUNDARY.md",
            "docs/release_notes/v0_49_0.md",
            "docs/archive/releases/v0_49_0/README_IMPORT.md",
            "docs/archive/releases/v0_49_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_49_0.md",
            "tests/test_m45_ccc_ios_local_read_only_connection.py",
            "tests/test_m45_gate_integration.py",
        ]
        failures = [
            f"missing M45 iOS local connection file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.mobile_companion import (
                assert_ccc_ios_local_read_only_connection_safe,
                build_default_ccc_ios_local_read_only_connection_manifest,
            )

            manifest = build_default_ccc_ios_local_read_only_connection_manifest()
            assert_ccc_ios_local_read_only_connection_safe(manifest)
            if manifest.milestone != "M45" or manifest.version != "0.49.0":
                failures.append(
                    "default M45 local connection manifest has wrong milestone/version"
                )
            if not manifest.local_only or not manifest.read_only:
                failures.append(
                    "default M45 local connection is not local-only/read-only"
                )
            forbidden_flags = [
                manifest.connection_runtime_enabled,
                manifest.backend_routes_added,
                manifest.network_runtime_enabled,
                manifest.external_network_enabled,
                manifest.raw_data_enabled,
                manifest.approval_capture_enabled,
                manifest.approval_execution_enabled,
                manifest.context_injection_enabled,
                manifest.memory_write_enabled,
                manifest.file_mutation_enabled,
                manifest.execution_enabled,
                manifest.background_collection_enabled,
                manifest.sensor_access_enabled,
                manifest.credential_or_cookie_handling_enabled,
                manifest.native_build_workflow_enabled,
                manifest.signing_or_store_workflow_enabled,
                manifest.production_authority_enabled,
            ]
            if any(forbidden_flags):
                failures.append(
                    "default M45 local connection enables forbidden authority"
                )
            if not manifest.m46_review_receipt_surfaces_future:
                failures.append("M45 does not keep M46 future")
        except Exception as exc:
            failures.append(f"M45 local connection validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        required_fragments = [
            "ccc ios local read-only connection",
            "local-only",
            "loopback-only",
            "read-only",
            "redacted summary",
            "non-authoritative",
            "no runtime network call",
            "no backend route",
            "no approval capture",
            "no approval execution",
            "no raw data",
            "no context injection",
            "no memory write",
            "no file mutation",
            "no execution",
            "no background collection",
            "no mobile sensor access",
            "no credential",
            "no production authority",
            "m46 remains future",
        ]
        for fragment in required_fragments:
            if fragment not in docs_text:
                failures.append(f"M45 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m45_ios_local_connection_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        ios_root = self.root / "apps" / "ccc-ios"
        swift_root = ios_root / "Sources" / "UltimateAIAgentCCC"
        failures: List[str] = []
        if not swift_root.exists():
            failures.append("M45 Swift source root missing")
            return self._result(
                criterion, failures, [str(swift_root.relative_to(self.root))]
            )
        for forbidden_path in [
            ios_root / "Package.swift",
            *ios_root.glob("*.xcodeproj"),
            *self._context.rglob(ios_root, "*.entitlements"),
            *self._context.rglob(ios_root, "Info.plist"),
            *self._context.rglob(ios_root, "ExportOptions.plist"),
        ]:
            if forbidden_path.exists():
                failures.append(
                    f"M45 forbidden native workflow file present: {forbidden_path.relative_to(self.root)}"
                )
        swift_files = sorted(self._context.rglob(swift_root, "*.swift"))
        if not swift_files:
            failures.append("M45 Swift source files missing")
        swift_text = "\n".join(self._context.read_text(path, encoding="utf-8") for path in swift_files)
        for fragment in M45_FORBIDDEN_SWIFT_FRAGMENTS:
            if fragment in swift_text:
                failures.append(f"M45 forbidden Swift API fragment present: {fragment}")
        lowered = swift_text.lower()
        for required in [
            "local read-only connection",
            "loopback-only",
            "non-authoritative",
            "no runtime network call",
        ]:
            if required not in lowered:
                failures.append(f"M45 Swift source missing required marker: {required}")
        return self._result(
            criterion,
            failures,
            [self._context.relative_path(path) for path in swift_files],
        )
