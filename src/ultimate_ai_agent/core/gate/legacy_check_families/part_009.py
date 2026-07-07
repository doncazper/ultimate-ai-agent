from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart009Mixin:
    """Legacy checks from m35_safe_file_review_workflow_contract_safe through m39_context_proposal_route_boundary."""
    def check_m35_safe_file_review_workflow_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/file_review/__init__.py",
            "src/ultimate_ai_agent/core/file_review/contracts.py",
            "src/ultimate_ai_agent/core/file_review/enums.py",
            "src/ultimate_ai_agent/core/file_review/workflow.py",
            "docs/files/SAFE_FILE_REVIEW_WORKFLOW.md",
            "docs/files/FILE_REVIEW_PACKET_CONTRACT.md",
            "docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md",
            "docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/files/FILE_REVIEW_RECEIPT_PLAN.md",
            "docs/files/FILE_REVIEW_NON_GOALS.md",
            "docs/files/M35_TO_M36_BOUNDARY.md",
            "docs/release_notes/v0_39_0.md",
            "docs/archive/releases/v0_39_0/README_IMPORT.md",
            "docs/archive/releases/v0_39_0/master_plan.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_39_0.md",
            "tests/test_file_review_workflow_contracts.py",
            "tests/test_file_review_packet_validation.py",
            "tests/test_file_review_approval_gate.py",
            "tests/test_file_review_authority_boundaries.py",
            "tests/test_file_review_receipt_plan.py",
            "tests/test_m35_gate_integration.py",
        ]
        failures = [
            f"missing M35 file review workflow file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        version_tuple = self._active_version_tuple()
        required_fragments = {
            "M35 docs must say redacted review packets only": "redacted review packets only",
            "M35 docs must say exact approval binding": "exact approval binding",
            "M35 docs must say review-only": "review-only",
            "M35 docs must say no raw file access": "no raw file access",
            "M35 docs must say no raw content": "no raw content",
            "M35 docs must say no approval capture": "no approval capture",
            "M35 docs must say no approval persistence": "no approval persistence",
            "M35 docs must say no context proposal": "no context proposal",
            "M35 docs must say no context injection": "no context injection",
            "M35 docs must say no memory writes": "no memory writes",
            "M35 docs must say no export": "no export",
            "M35 docs must say no execution": "no execution",
            "M35 docs must say no backend routes": "no backend routes",
        }
        if version_tuple < (0, 40, 0):
            required_fragments["M36 must remain planned/provisional"] = (
                "m36 remains planned/provisional"
            )
        if version_tuple < (0, 41, 0):
            required_fragments["M37 must remain planned/provisional"] = (
                "m37 remains planned/provisional"
            )
        if version_tuple < (0, 42, 0):
            required_fragments["M38 must remain planned/provisional"] = (
                "m38 remains planned/provisional"
            )
        for failure, fragment in required_fragments.items():
            if fragment not in docs_text:
                failures.append(failure)

        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.file_review import (
                FileReviewDecisionStatus,
                UserFileReviewApproval,
                build_file_review_packet,
                evaluate_file_review_gate,
                evaluate_file_review_packet,
            )
            from ultimate_ai_agent.core.time import utc_now
            from ultimate_ai_agent.core.tools.runtime import (
                FilePreviewRedactionSummary,
                RedactedFilePreviewOutput,
                RedactedFilePreviewStatus,
            )

            preview = RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:gate",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:gate",
                safe_path_ref="filesystem-preview-path:safe-root_gate/docs/review.md",
                redacted_preview="Redacted preview only.",
                redaction_summary=FilePreviewRedactionSummary(
                    redaction_count=0, categories=[]
                ),
                file_size_bytes=32,
            )
            packet = build_file_review_packet(
                preview_output=preview,
                actor_ref="user:gate",
                request_ref="file-review-request:gate",
                file_ref="file-ref:gate-review",
                safe_summary="Review a redacted preview packet.",
            )
            packet_decision = evaluate_file_review_packet(packet)
            if (
                packet_decision.status
                != FileReviewDecisionStatus.packet_valid_for_review
            ):
                failures.append("M35 safe redacted packet was not valid for review")
            if (
                packet_decision.execution_authorized
                or packet_decision.execution_performed
            ):
                failures.append("M35 packet decision authorized or performed execution")
            raw_packet_decision = evaluate_file_review_packet(
                packet.model_copy(update={"raw_content": "raw secret"})
            )
            if "FILE_REVIEW_RAW_CONTENT_DENIED" not in raw_packet_decision.reason_codes:
                failures.append(
                    "M35 packet evaluator did not deny model_copy raw_content"
                )
            context_packet_decision = evaluate_file_review_packet(
                packet.model_copy(update={"context_injection_enabled": True})
            )
            if (
                "FILE_REVIEW_CONTEXT_INJECTION_DENIED"
                not in context_packet_decision.reason_codes
            ):
                failures.append(
                    "M35 packet evaluator did not deny model_copy context injection flag"
                )

            approval = UserFileReviewApproval(
                approval_ref="file-review-approval:gate",
                actor_ref="user:gate",
                review_packet_ref=packet.review_packet_ref,
                preview_result_ref=packet.source.preview_result_ref,
                redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
                file_ref=packet.source.file_ref,
                safe_path_ref=packet.source.safe_path_ref,
                issued_at=utc_now(),
                expires_at=utc_now() + timedelta(minutes=5),
            )
            allowed_decision = evaluate_file_review_gate(
                packet, approval=approval, current_time=utc_now()
            )
            if allowed_decision.status != FileReviewDecisionStatus.review_allowed:
                failures.append(
                    "M35 exact approval binding did not allow review-only decision"
                )
            if (
                allowed_decision.raw_file_access_authorized
                or allowed_decision.context_injection_authorized
                or allowed_decision.memory_write_authorized
                or allowed_decision.export_authorized
                or allowed_decision.execution_authorized
                or allowed_decision.execution_performed
            ):
                failures.append(
                    "M35 exact approval binding granted forbidden authority"
                )
            mismatch_decision = evaluate_file_review_gate(
                packet,
                approval=approval.model_copy(
                    update={"review_packet_ref": "file-review-packet:other"}
                ),
                current_time=utc_now(),
            )
            if (
                "FILE_REVIEW_APPROVAL_PACKET_MISMATCH"
                not in mismatch_decision.reason_codes
            ):
                failures.append("M35 approval gate did not deny mismatched packet")
            file_ref_mismatch_decision = evaluate_file_review_gate(
                packet.model_copy(
                    update={
                        "source": packet.source.model_copy(
                            update={"file_ref": "file-ref:gate-mutated"}
                        )
                    }
                ),
                approval=approval,
                current_time=utc_now(),
            )
            if (
                "FILE_REVIEW_APPROVAL_FILE_REF_MISMATCH"
                not in file_ref_mismatch_decision.reason_codes
            ):
                failures.append(
                    "M35 approval gate did not deny mutated packet file_ref"
                )
            path_ref_mismatch_decision = evaluate_file_review_gate(
                packet.model_copy(
                    update={
                        "source": packet.source.model_copy(
                            update={
                                "safe_path_ref": "filesystem-preview-path:safe-root_gate/docs/mutated.md"
                            }
                        )
                    }
                ),
                approval=approval,
                current_time=utc_now(),
            )
            if (
                "FILE_REVIEW_APPROVAL_PATH_REF_MISMATCH"
                not in path_ref_mismatch_decision.reason_codes
            ):
                failures.append(
                    "M35 approval gate did not deny mutated packet safe_path_ref"
                )
            test_ref_decision = evaluate_file_review_gate(
                packet,
                approval=approval.model_copy(
                    update={"approval_ref": "approval_test_gate"}
                ),
                current_time=utc_now(),
            )
            if (
                "FILE_REVIEW_APPROVAL_TEST_REF_DENIED"
                not in test_ref_decision.reason_codes
            ):
                failures.append("M35 approval gate did not deny approval_test ref")
        except Exception as exc:
            failures.append(f"M35 file review workflow contract probe failed: {exc}")

        return self._result(criterion, failures, required_files)

    def check_m35_file_review_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            paths = set(app.openapi().get("paths", {}))
            if self._active_version_tuple() >= (0, 41, 0):
                paths.discard(M37_ALLOWED_CAPTURE_ROUTE)
            failures.extend(m35_openapi_route_failures(paths))
        except Exception as exc:
            failures.append(f"M35 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m35_m36_m37_m38_remain_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        version_tuple = self._active_version_tuple()
        required_docs = [
            "README.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/files/SAFE_FILE_REVIEW_WORKFLOW.md",
            "docs/files/FILE_REVIEW_PACKET_CONTRACT.md",
            "docs/files/FILE_REVIEW_USER_APPROVAL_GATE.md",
            "docs/files/FILE_REVIEW_AUTHORITY_BOUNDARY.md",
            "docs/files/FILE_REVIEW_NON_GOALS.md",
            "docs/files/M35_TO_M36_BOUNDARY.md",
        ]
        failures = [
            f"missing M35/M36 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.39.0" not in text
            or "m35" not in text
            or "safe file review workflow contracts" not in text
        ):
            failures.append(
                "M35 roadmap docs do not identify v0.39.0 Safe File Review Workflow Contracts"
            )
        if (
            "m35 is implemented/released" not in text
            and "m35 implemented/released" not in text
        ):
            failures.append("M35 roadmap docs do not mark M35 implemented/released")
        if version_tuple < (0, 40, 0) and "m36 remains planned/provisional" not in text:
            failures.append("M36 must remain planned/provisional after M35")
        if version_tuple >= (0, 41, 0):
            if (
                "m37 is implemented/released" not in text
                and "m37 implemented/released" not in text
            ):
                failures.append(
                    "M37 must be implemented/released for active v0.41.0+ docs"
                )
        elif "m37 remains planned/provisional" not in text:
            failures.append("M37 must remain planned/provisional after M35")
        if version_tuple >= (0, 45, 0):
            if (
                "m41 is implemented/released" not in text
                and "v0.45.0 implements m41" not in text
            ):
                failures.append(
                    "M41 must be implemented/released for active v0.45.0+ docs"
                )
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
        elif version_tuple >= (0, 44, 0):
            if (
                "m40 is implemented/released" not in text
                and "v0.44.0 implements m40" not in text
            ):
                failures.append(
                    "M40 must be implemented/released for active v0.44.0+ docs"
                )
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif version_tuple >= (0, 43, 0):
            if (
                "m39 is implemented/released" not in text
                and "v0.43.0 implements m39" not in text
            ):
                failures.append(
                    "M39 must be implemented/released for active v0.43.0+ docs"
                )
            if "m40-m60 remain planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif version_tuple >= (0, 42, 0):
            if (
                "m38 is implemented/released" not in text
                and "m38 implemented/released" not in text
            ):
                failures.append(
                    "M38 must be implemented/released for active v0.42.0+ docs"
                )
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif "m38 remains planned/provisional" not in text:
            failures.append("M38 must remain planned/provisional after M35")
        future_fragments = [
            "ccc file review surface is implemented",
            "m36 is implemented",
            "v0.40.0 implements m36",
        ]
        if version_tuple >= (0, 40, 0):
            future_fragments = []
        future_fragments.extend(["file review ui is implemented"])
        if version_tuple < (0, 41, 0):
            future_fragments.extend(
                [
                    "approval persistence is implemented",
                    "review approval capture is implemented",
                    "m37 is implemented",
                    "v0.41.0 implements m37",
                ]
            )
        if version_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "context proposal is implemented",
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        future_fragments.append("context injection is implemented")
        for fragment in future_fragments:
            if fragment in text:
                failures.append(
                    f"M35 docs imply future milestone implementation: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m36_ccc_file_review_surface_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        if self._active_version_tuple() >= (0, 41, 0):
            return self._result(
                criterion,
                [],
                ["apps/control-center/src/components/FileReviewSurfacePanel.tsx"],
            )
        required_files = [
            "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/FILE_REVIEW_SURFACE.md",
            "docs/control_center/FILE_REVIEW_REVIEW_ONLY_POLICY.md",
            "docs/control_center/FILE_REVIEW_MOCK_DATA_POLICY.md",
            "docs/control_center/FILE_REVIEW_BINDING_DISPLAY_POLICY.md",
            "docs/control_center/M36_TO_M37_BOUNDARY.md",
            "tests/test_m36_gate_integration.py",
        ]
        failures = [
            f"missing M36 file review surface file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]

        combined = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if (self.root / path).exists()
        )
        required_fragments = {
            "M36 route missing": "/files/review",
            "review-only surface copy missing": "review-only surface",
            "mock non-authoritative copy missing": "mock and non-authoritative",
            "redacted preview display missing": "redacted preview",
            "redaction summary display missing": "redaction summary",
            "review packet ref display missing": "review_packet_ref",
            "safe refs only marker missing": "safe refs only",
            "no mutating request marker missing": "no mutating request is made",
            "preview result ref display missing": "preview_result_ref",
            "redaction summary ref display missing": "redaction_summary_ref",
            "file ref display missing": "file_ref",
            "safe path ref display missing": "safe_path_ref",
            "approval gate contract status missing": "approval gate contract status",
            "receipt plan metadata missing": "receipt plan metadata",
            "no approval capture marker missing": "no_approval_capture",
            "no approval persistence marker missing": "no_approval_persistence",
            "no raw display marker missing": "no_raw_file_display",
            "M37 future marker missing": "m37 remains planned/provisional",
        }
        for message, fragment in required_fragments.items():
            if fragment not in combined:
                failures.append(message)

        component_text = self._read(
            self.root / "apps/control-center/src/components/FileReviewSurfacePanel.tsx"
        ).lower()
        mock_text = self._read(
            self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        )
        failures.extend(
            m36_file_review_surface_failures(
                component_text=component_text, mock_text=mock_text
            )
        )
        for fragment in (
            "approve",
            "deny",
            "submit",
            "mark reviewed",
            "export",
            "download",
            "copy raw",
            "file picker",
            "root selector",
            "open raw file",
            "context proposal",
            "context injection control",
            "write memory",
            "execute",
            "run tool",
            "call model",
        ):
            if re.search(
                rf"<button\b[^>]*>\s*{re.escape(fragment)}\s*</button>",
                component_text,
                re.IGNORECASE,
            ):
                failures.append(f"M36 component exposes forbidden control: {fragment}")

        return self._result(criterion, failures, required_files)

    def check_m36_file_review_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            paths = set(app.openapi().get("paths", {}))
            if self._active_version_tuple() >= (0, 41, 0):
                paths.discard(M37_ALLOWED_CAPTURE_ROUTE)
            failures.extend(m36_openapi_route_failures(paths))
        except Exception as exc:
            failures.append(f"M36 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m36_m37_m38_remain_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        version_tuple = self._active_version_tuple()
        required_docs = [
            "README.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/control_center/M36_TO_M37_BOUNDARY.md",
            "docs/control_center/FILE_REVIEW_SURFACE.md",
        ]
        failures = [
            f"missing M36/M37 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.40.0" not in text
            or "m36" not in text
            or "ccc file review surface" not in text
        ):
            failures.append(
                "M36 roadmap docs do not identify v0.40.0 CCC File Review Surface"
            )
        if (
            "m36 is implemented/released" not in text
            and "m36 implemented/released" not in text
        ):
            failures.append("M36 roadmap docs do not mark M36 implemented/released")
        if version_tuple >= (0, 41, 0):
            if (
                "m37 is implemented/released" not in text
                and "m37 implemented/released" not in text
            ):
                failures.append(
                    "M37 must be implemented/released for active v0.41.0+ docs"
                )
        elif "m37 remains planned/provisional" not in text:
            failures.append("M37 must remain planned/provisional after M36")
        if version_tuple >= (0, 45, 0):
            if (
                "m41 is implemented/released" not in text
                and "v0.45.0 implements m41" not in text
            ):
                failures.append(
                    "M41 must be implemented/released for active v0.45.0+ docs"
                )
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
        elif version_tuple >= (0, 44, 0):
            if (
                "m40 is implemented/released" not in text
                and "v0.44.0 implements m40" not in text
            ):
                failures.append(
                    "M40 must be implemented/released for active v0.44.0+ docs"
                )
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif version_tuple >= (0, 43, 0):
            if (
                "m39 is implemented/released" not in text
                and "v0.43.0 implements m39" not in text
            ):
                failures.append(
                    "M39 must be implemented/released for active v0.43.0+ docs"
                )
            if "m40-m60 remain planned/provisional" not in text:
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif version_tuple >= (0, 42, 0):
            if (
                "m38 is implemented/released" not in text
                and "m38 implemented/released" not in text
            ):
                failures.append(
                    "M38 must be implemented/released for active v0.42.0+ docs"
                )
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif "m38 remains planned/provisional" not in text:
            failures.append("M38 must remain planned/provisional after M36")
        future_fragments = []
        if version_tuple < (0, 41, 0):
            future_fragments.extend(
                [
                    "approval persistence is implemented",
                    "review approval capture is implemented",
                    "m37 is implemented",
                    "v0.41.0 implements m37",
                ]
            )
        if version_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "context proposal is implemented",
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        future_fragments.append("context injection is implemented")
        for fragment in future_fragments:
            if fragment in text:
                failures.append(
                    f"M36 docs imply future milestone implementation: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m37_file_review_approval_capture_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/file_review/approval_capture.py",
            "src/ultimate_ai_agent/core/file_review/__init__.py",
            "tests/test_file_review_approval_capture_contracts.py",
            "tests/test_file_review_approval_store.py",
        ]
        failures = [
            f"missing M37 approval capture file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if (self.root / path).exists()
        )
        required_fragments = {
            "capture request contract missing": "filereviewapprovalcapturerequest",
            "capture record contract missing": "filereviewapprovalrecord",
            "approval store missing": "filereviewapprovalstore",
            "capture evaluator missing": "capture_file_review_approval",
            "safe-ref persistence missing": "safe refs only",
            "raw access denial missing": "raw_file_access_authorized",
            "context proposal denial missing": "context_proposal_authorized",
            "memory write denial missing": "memory_write_authorized",
            "execution denial missing": "execution_authorized",
            "idempotency/replay coverage missing": "idempotent",
        }
        for message, fragment in required_fragments.items():
            if fragment not in text:
                failures.append(message)
        for fragment in (
            "raw_file_access_authorized: bool = true",
            "context_proposal_authorized: bool = true",
            "memory_write_authorized: bool = true",
            "export_authorized: bool = true",
            "execution_authorized: bool = true",
            "execution_performed: bool = true",
        ):
            if fragment in text:
                failures.append(f"M37 contract grants forbidden authority: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m37_file_review_approval_capture_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m37_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M37 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m37_control_center_review_only_approval_capture(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/App.test.tsx",
        ]
        failures = [
            f"missing M37 Control Center file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        component_text = self._read(
            self.root / "apps/control-center/src/components/FileReviewSurfacePanel.tsx"
        )
        mock_text = self._read(
            self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        ).lower()
        failures.extend(m37_control_center_surface_failures(component_text))
        normalized_mock_text = mock_text.replace(" ", "").replace("\n", "")
        for fragment in (
            "m37_review_only_capture_surface",
            "safe_ref_persistence_only",
            "no_authority_granted",
            "rawfileaccessauthorized: false",
            "contextproposalauthorized: false",
            "memorywriteauthorized: false",
            "exportauthorized: false",
            "executionauthorized: false",
            "executionperformed: false",
        ):
            if fragment.replace(" ", "") not in normalized_mock_text:
                failures.append(f"M37 mock fixture missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m37_roadmap_currentness(
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
            f"missing M37 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.41.0" not in text
            or "m37" not in text
            or "review approval capture" not in text
        ):
            failures.append(
                "active docs do not identify v0.41.0/M37 Review Approval Capture"
            )
        if (
            "m37 is implemented/released" not in text
            and "m37 implemented/released" not in text
        ):
            failures.append("active docs do not mark M37 implemented/released")
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 45, 0):
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
        elif version_tuple >= (0, 44, 0):
            if (
                "m40 is implemented/released" not in text
                and "v0.44.0 implements m40" not in text
            ):
                failures.append("active docs do not mark M40 implemented/released")
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif version_tuple >= (0, 43, 0):
            if (
                "m39 is implemented/released" not in text
                and "v0.43.0 implements m39" not in text
            ):
                failures.append("active docs do not mark M39 implemented/released")
            if (
                "m40-m60 remain planned/provisional" not in text
                and "m40 remains planned/provisional" not in text
            ):
                failures.append("M40-M60 must remain planned/provisional after M39")
        elif version_tuple >= (0, 42, 0):
            if (
                "m38 is implemented/released" not in text
                and "m38 implemented/released" not in text
            ):
                failures.append("active docs do not mark M38 implemented/released")
            if "m39-m60 remain planned/provisional" not in text:
                failures.append("M39-M60 must remain planned/provisional after M38")
        elif "m38 remains planned/provisional" not in text:
            failures.append("M38 must remain planned/provisional after M37")
        future_fragments = [
            "context injection is implemented",
            "raw file reads are implemented",
        ]
        if version_tuple < (0, 42, 0):
            future_fragments.extend(
                [
                    "context proposal is implemented",
                    "m38 is implemented",
                    "v0.42.0 implements m38",
                ]
            )
        elif version_tuple < (0, 43, 0):
            future_fragments.extend(
                [
                    "m39 is implemented",
                    "v0.43.0 implements m39",
                    "m40 is implemented",
                    "v0.44.0 implements m40",
                ]
            )
        for fragment in future_fragments:
            if fragment in text:
                failures.append(
                    f"M37 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m38_safe_context_proposal_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/context_proposal/__init__.py",
            "src/ultimate_ai_agent/core/context_proposal/contracts.py",
            "src/ultimate_ai_agent/core/context_proposal/validation.py",
            "src/ultimate_ai_agent/core/context_proposal/workflow.py",
            "tests/test_safe_context_proposal_contracts.py",
            "tests/test_safe_context_proposal_binding.py",
            "tests/test_safe_context_proposal_no_raw_content.py",
            "tests/test_safe_context_proposal_authority_boundaries.py",
            "tests/test_safe_context_proposal_receipt_plan.py",
        ]
        failures = [
            f"missing M38 context proposal file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.context_proposal import (
                SafeContextProposalDecisionStatus,
                build_safe_context_proposal_policy,
                evaluate_safe_context_proposal_request,
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

            policy = build_safe_context_proposal_policy()
            for field_name in [
                "context_surface_enabled",
                "context_handoff_enabled",
                "context_injection_enabled",
                "openwebui_handoff_enabled",
                "model_call_enabled",
                "memory_write_enabled",
                "export_enabled",
                "execution_enabled",
                "raw_file_access_enabled",
            ]:
                if getattr(policy, field_name):
                    failures.append(f"M38 policy enables forbidden flag: {field_name}")

            preview = RedactedFilePreviewOutput(
                output_ref="redacted-file-preview-output:m38-gate",
                status=RedactedFilePreviewStatus.preview_generated,
                root_ref="safe-root:m38-gate",
                safe_path_ref="filesystem-preview-path:safe-root_m38_gate/docs/review.md",
                redacted_preview="Redacted preview only.",
                redaction_summary=FilePreviewRedactionSummary(
                    redaction_count=0, categories=[]
                ),
                file_size_bytes=32,
            )
            packet = build_file_review_packet(
                preview_output=preview,
                actor_ref="user:m38-gate",
                request_ref="file-review-request:m38-gate",
                file_ref="file-ref:m38-gate-review",
                safe_summary="Review a redacted packet for context proposal.",
            )
            record = FileReviewApprovalRecord(
                approval_ref="file-review-approval-capture:m38-gate",
                actor_ref=packet.source.actor_ref,
                review_packet_ref=packet.review_packet_ref,
                preview_result_ref=packet.source.preview_result_ref,
                redaction_summary_ref=packet.redaction_verification.redaction_summary_ref,
                file_ref=packet.source.file_ref,
                safe_path_ref=packet.source.safe_path_ref,
                decision=FileReviewApprovalDecisionKind.approve_review_only,
                status=FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
                idempotency_key="file-review-approval-idempotency:m38-gate",
                receipt_plan_ref="file-review-approval-capture-receipt:m38-gate",
                authority_decision_ref="authority-policy-decision-ref:m38-gate",
                authority_decision_outcome="ask",
                authority_lease_ref="authority-lease-ref:m38-gate-files-write",
            )
            allowed = evaluate_safe_context_proposal_request(
                packet=packet, approval_record=record
            )
            if (
                allowed.status != SafeContextProposalDecisionStatus.proposal_ready
                or not allowed.proposal_ready
            ):
                failures.append("M38 safe approved review did not build a proposal")
            if any(
                [
                    allowed.context_injection_authorized,
                    allowed.openwebui_handoff_authorized,
                    allowed.model_call_authorized,
                    allowed.memory_write_authorized,
                    allowed.export_authorized,
                    allowed.execution_authorized,
                    allowed.execution_performed,
                ]
            ):
                failures.append("M38 proposal decision granted forbidden authority")
            denied_ref = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=None,
                approval_ref=record.approval_ref,
            )
            if "approval_ref_not_authority" not in denied_ref.reason_codes:
                failures.append("M38 did not deny approval_ref alone")
            denied_test = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=record.model_copy(
                    update={"approval_ref": "approval_test_m38"}
                ),
            )
            if "approval_test_ref_denied" not in denied_test.reason_codes:
                failures.append("M38 did not deny approval_test_ ref")
            denied_path = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=record.model_copy(
                    update={
                        "safe_path_ref": "filesystem-preview-path:safe-root_m38_gate/docs/mutated.md"
                    }
                ),
            )
            if "path_ref_mismatch" not in denied_path.reason_codes:
                failures.append("M38 did not enforce safe_path_ref binding")
            denied_flag = evaluate_safe_context_proposal_request(
                packet=packet,
                approval_record=record,
                policy_overrides={"context_injection_enabled": True},
            )
            if "context_injection_denied" not in denied_flag.reason_codes:
                failures.append(
                    "M38 did not deny model_copy-mutated context injection flag"
                )
        except Exception as exc:
            failures.append(f"M38 context proposal probe failed: {exc}")

        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if (self.root / path).exists()
        )
        for fragment in [
            "safecontextproposalpolicy",
            "safecontextproposalrequest",
            "safecontextproposalsource",
            "safecontextproposalbinding",
            "safecontextproposalredactionverification",
            "safecontextproposalsection",
            "safecontextproposaldecision",
            "safecontextproposalreceiptplan",
            "context_injection_enabled: bool = false",
            "openwebui_handoff_enabled: bool = false",
            "memory_write_enabled: bool = false",
            "execution_enabled: bool = false",
        ]:
            if fragment not in text:
                failures.append(
                    f"M38 contracts/tests missing safety fragment: {fragment}"
                )
        return self._result(criterion, failures, required_files)

    def check_m38_safe_context_proposal_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m38_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M38 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m38_no_control_center_context_surface(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [
            f"missing M38 Control Center boundary file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if (self.root / path).exists()
        )
        current = self._active_version_tuple()
        forbidden_fragments = [
            "/context/proposals",
            "/context/propose",
            "/context/inject",
            "/openwebui/handoff",
            "context proposal surface",
            "send to openwebui",
            "export context",
        ]
        if current >= (0, 43, 0):
            forbidden_fragments = [
                fragment
                for fragment in forbidden_fragments
                if fragment not in {"/context/proposals", "context proposal surface"}
            ]
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M38 must not add M39/M40 Control Center surface/control: {fragment}"
                )
        for label in [
            "inject context",
            "write memory",
            "export context",
            "execute context",
        ]:
            if re.search(
                rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>",
                text,
                re.IGNORECASE,
            ):
                failures.append(
                    f"M38 must not add M39/M40 Control Center control: {label}"
                )
        return self._result(criterion, failures, required_files)

    def check_m38_roadmap_currentness(
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
            f"missing M38 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.42.0" not in text
            or "m38" not in text
            or "safe context proposal" not in text
        ):
            failures.append(
                "active docs do not identify v0.42.0/M38 Safe Context Proposal"
            )
        if (
            "m38 is implemented/released" not in text
            and "m38 implemented/released" not in text
        ):
            failures.append("active docs do not mark M38 implemented/released")
        current = self._active_version_tuple()
        if current >= (0, 45, 0):
            if (
                "m41 is implemented/released" not in text
                and "v0.45.0 implements m41" not in text
            ):
                failures.append(
                    "active docs do not mark M41 implemented/released after v0.45.0"
                )
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
        elif current >= (0, 44, 0):
            if (
                "m40 is implemented/released" not in text
                and "v0.44.0 implements m40" not in text
            ):
                failures.append(
                    "active docs do not mark M40 implemented/released after v0.44.0"
                )
            if "m41-m60 remain planned/provisional" not in text:
                failures.append("M41-M60 must remain planned/provisional after M40")
        elif current >= (0, 43, 0):
            if (
                "m39 is implemented/released" not in text
                and "v0.43.0 implements m39" not in text
            ):
                failures.append(
                    "active docs do not mark M39 implemented/released after v0.43.0"
                )
            if (
                "m40 remains planned/provisional" not in text
                and "m40-m60 remain planned/provisional" not in text
            ):
                failures.append("M40 must remain planned/provisional after M39")
        elif (
            "m39 remains planned/provisional" not in text
            and "m39-m60 remain planned/provisional" not in text
        ):
            failures.append("M39 must remain planned/provisional after M38")
        forbidden_future = [
            "context injection is implemented",
            "openwebui handoff is implemented",
        ]
        if current < (0, 44, 0):
            forbidden_future.extend(["m40 is implemented", "v0.44.0 implements m40"])
        if current < (0, 43, 0):
            forbidden_future.extend(["m39 is implemented", "v0.43.0 implements m39"])
        for fragment in forbidden_future:
            if fragment in text:
                failures.append(
                    f"M38 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m39_ccc_context_proposal_surface_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "apps/control-center/src/components/ContextProposalSurfacePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "apps/control-center/src/App.test.tsx",
            "docs/control_center/CONTEXT_PROPOSAL_SURFACE.md",
            "docs/control_center/CONTEXT_PROPOSAL_REVIEW_ONLY_POLICY.md",
            "docs/control_center/CONTEXT_PROPOSAL_MOCK_DATA_POLICY.md",
            "docs/control_center/CONTEXT_PROPOSAL_BINDING_DISPLAY_POLICY.md",
            "docs/control_center/M39_TO_M40_BOUNDARY.md",
        ]
        failures = [
            f"missing M39 context proposal surface file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        app_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("apps/") and (self.root / path).exists()
        )
        for fragment in [
            "/context/proposals",
            "contextproposalsurfacepanel",
            "m39contextproposals",
            "safe-context-proposal:mock_001",
            "safe proposal sections",
            "exact binding refs",
            "source chain refs",
            "control center output is not authority",
            "openwebui handoff authorized",
            "context injection authorized",
            "memory write authorized",
            "export authorized",
            "execution authorized",
            "rawfileaccessauthorized: false",
            "executionauthorized: false",
        ]:
            normalized = app_text.replace("_", "")
            if fragment not in app_text and fragment not in normalized:
                failures.append(f"M39 Control Center missing safe marker: {fragment}")
        for label in [
            "send to openwebui",
            "inject context",
            "write memory",
            "export context",
            "download context",
            "execute context",
            "call model",
            "open raw file",
        ]:
            if re.search(
                rf"<button\b[^>]*>\s*{re.escape(label)}\s*</button>",
                app_text,
                re.IGNORECASE,
            ):
                failures.append(f"M39 Control Center added forbidden control: {label}")
        for forbidden in [
            "/context/propose",
            "/context/inject",
            "/context/handoff",
            "/openwebui/handoff",
            "/memory/write",
            "/tools/execute",
        ]:
            if forbidden in app_text:
                failures.append(
                    f"M39 Control Center references forbidden route/control: {forbidden}"
                )

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "read-only",
            "proposal-only",
            "mock and non-authoritative",
            "no context handoff",
            "no context injection",
            "no openwebui handoff",
            "no memory writes",
            "no export",
            "no execution",
            "no raw file access",
            "m40 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M39 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m39_context_proposal_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m39_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M39 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
