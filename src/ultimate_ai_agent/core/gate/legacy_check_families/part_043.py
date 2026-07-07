from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart043Mixin:
    """Legacy checks from m161_local_system_probe_static_safety through m25_m26_remains_future."""
    def check_m161_local_system_probe_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/local_model_management/system_probe.py",
            "docs/model_management/M161_LOCAL_SYSTEM_CAPABILITY_PROBE.md",
            "tests/test_m161_local_system_probe.py",
        ]
        failures = [
            f"missing M161 local system probe file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.local_model_management import (
                BYTES_PER_GIB,
                M161LocalSystemProbePolicy,
                M161LocalSystemProbeRequest,
                M161SystemProbeSample,
                probe_local_system_capabilities,
                validate_m161_local_system_probe_policy,
            )

            policy = validate_m161_local_system_probe_policy(
                M161LocalSystemProbePolicy()
            )
            if (
                not policy.local_read_only
                or not policy.stdlib_only
                or not policy.redacted_buckets_only
                or not policy.hardware_fit_metadata_only
                or policy.broad_scan_allowed
                or policy.hostname_allowed
                or policy.serial_allowed
                or policy.username_allowed
                or policy.raw_path_allowed
                or policy.env_dump_allowed
                or policy.subprocess_allowed
                or policy.network_allowed
                or policy.download_allowed
                or policy.model_call_allowed
                or policy.dependency_added
                or policy.production_authority_granted
            ):
                failures.append("M161 probe policy is unsafe")
            result = probe_local_system_capabilities(
                M161LocalSystemProbeRequest(
                    request_ref="local-system-probe-request:m161-gate"
                ),
                sample=M161SystemProbeSample(
                    os_name="Darwin",
                    machine_arch="arm64",
                    cpu_count=12,
                    ram_bytes=64 * BYTES_PER_GIB,
                    vram_bytes=None,
                    disk_free_bytes=512 * BYTES_PER_GIB,
                    power_source_hint="ac",
                    thermal_state_hint="nominal",
                ),
            )
            if (
                not result.local_system_probe_performed
                or not result.local_only
                or not result.stdlib_only
                or not result.redacted
                or not result.bucketed_only
                or result.raw_hostname_included
                or result.raw_serial_included
                or result.raw_username_included
                or result.raw_path_included
                or result.env_dump_included
                or result.broad_scan_performed
                or result.subprocess_execution_performed
                or result.network_access_performed
                or result.download_performed
                or result.model_call_performed
                or result.backend_route_added
                or result.dependency_added
                or result.production_authority_granted
            ):
                failures.append("M161 probe result is unsafe")
            if result.os_arch_bucket != "os-arch:macos-arm64":
                failures.append(
                    "M161 probe did not return expected redacted OS/arch bucket"
                )
        except Exception as exc:
            failures.append(f"M161 local system probe validation failed: {exc}")

        source_path = (
            self.root
            / "src/ultimate_ai_agent/core/local_model_management/system_probe.py"
        )
        source = self._read(source_path)
        for fragment in [
            "platform.system()",
            "platform.machine()",
            "os.cpu_count()",
            "os.sysconf",
            "shutil.disk_usage",
            "BYTES_PER_GIB",
            "redacted_buckets_only",
            "bucketed_only",
        ]:
            if fragment not in source:
                failures.append(
                    f"M161 probe source missing required stdlib bucket fragment: {fragment}"
                )
        for forbidden in [
            "platform.uname(",
            "psutil.",
            "system_profiler",
            "nvidia-smi",
            "import " + "subprocess",
            "from subprocess import",
            "subprocess" + ".",
            "os.walk(",
            "Path.home(",
            ".rglob(",
            "os.environ",
            "getpass.",
            "socket.gethostname",
            "uuid.getnode",
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import huggingface_hub",
            "from huggingface_hub import",
            "llama_cpp",
            "openai.OpenAI(",
            "download_performed=True",
            "model_call_performed=True",
            "backend_route_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
        ]:
            if forbidden in source:
                failures.append(
                    f"M161 probe source contains forbidden fragment: {forbidden}"
                )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "m161 local system capability probe",
            "core-only",
            "stdlib-only",
            "local read-only",
            "redacted",
            "bucketed-only",
            "os and architecture bucket",
            "cpu core bucket",
            "ram bucket",
            "vram bucket",
            "backend/device family bucket",
            "disk budget bucket",
            "power/thermal hint",
            "no serials",
            "no usernames",
            "no raw paths",
            "no environment dump",
            "no broad scans",
            "no subprocess",
            "no network access",
            "no downloads",
            "no model/provider call",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
        ]:
            if fragment not in docs_text:
                failures.append(f"M161 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m162_exact_approved_gguf_acquisition_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py",
            "docs/model_management/M162_GGUF_MODEL_ACQUISITION.md",
            "tests/test_m162_model_acquisition.py",
        ]
        failures = [
            f"missing M162 GGUF acquisition file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            import hashlib

            from ultimate_ai_agent.core.local_model_management import (
                ArtifactRole,
                FakeM162ModelAcquisitionTransport,
                M162GgufArtifactRequest,
                M162ModelAcquisitionPolicy,
                M162ModelAcquisitionRequest,
                acquire_huggingface_gguf_artifacts,
                validate_m162_model_acquisition_policy,
            )

            policy = validate_m162_model_acquisition_policy(
                M162ModelAcquisitionPolicy()
            )
            if (
                not policy.exact_user_approval_required
                or not policy.pinned_revision_required
                or not policy.exact_filename_required
                or not policy.explicit_artifact_refs_required
                or not policy.uaa_owned_cache_required
                or not policy.gguf_artifacts_only
                or not policy.sharded_artifacts_explicit_only
                or not policy.mmproj_artifacts_explicit_only
                or not policy.unauthenticated_by_default
                or not policy.https_get_only
                or policy.raw_response_storage_allowed
                or policy.raw_url_storage_allowed
                or policy.token_use_allowed
                or policy.model_call_allowed
                or policy.llama_cpp_process_allowed
                or policy.subprocess_allowed
                or policy.backend_route_allowed
                or policy.control_center_control_allowed
                or policy.dependency_added
                or policy.production_authority_granted
            ):
                failures.append("M162 acquisition policy is unsafe")

            payload = b"gate-primary"
            shard_payload = b"gate-shard"
            mmproj_payload = b"gate-mmproj"
            primary = M162GgufArtifactRequest(
                artifact_ref="gguf-artifact:m162-gate-primary",
                repo_id="org/qwopus",
                revision="0123456789abcdef0123456789abcdef01234567",
                filename="qwopus-q4_k_m.gguf",
                expected_size_bytes=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
            )
            shard = M162GgufArtifactRequest(
                artifact_ref="gguf-artifact:m162-gate-shard",
                repo_id="org/qwopus",
                revision="0123456789abcdef0123456789abcdef01234567",
                filename="qwopus-00001-of-00002.gguf",
                role=ArtifactRole.shard,
                expected_size_bytes=len(shard_payload),
                expected_sha256=hashlib.sha256(shard_payload).hexdigest(),
            )
            mmproj = M162GgufArtifactRequest(
                artifact_ref="gguf-artifact:m162-gate-mmproj",
                repo_id="org/qwopus",
                revision="0123456789abcdef0123456789abcdef01234567",
                filename="mmproj-qwopus.gguf",
                role=ArtifactRole.mmproj,
                expected_size_bytes=len(mmproj_payload),
                expected_sha256=hashlib.sha256(mmproj_payload).hexdigest(),
            )
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_root = Path(temp_dir) / ".uaa" / "model-cache"
                result = acquire_huggingface_gguf_artifacts(
                    M162ModelAcquisitionRequest(
                        request_ref="model-acquisition-request:m162-gate",
                        approval_ref="approval:m162-gguf-acquisition-gate",
                        artifacts=[primary, shard, mmproj],
                    ),
                    cache_root=cache_root,
                    transport=FakeM162ModelAcquisitionTransport(
                        {
                            primary.artifact_ref: payload,
                            shard.artifact_ref: shard_payload,
                            mmproj.artifact_ref: mmproj_payload,
                        }
                    ),
                    max_artifact_bytes=1024,
                )
                cached_names = sorted(path.name for path in cache_root.rglob("*.gguf"))
            if cached_names != [
                "mmproj-qwopus.gguf",
                "qwopus-00001-of-00002.gguf",
                "qwopus-q4_k_m.gguf",
            ]:
                failures.append(
                    "M162 fake acquisition did not cache expected GGUF artifacts"
                )
            if (
                not result.exact_user_approved
                or not result.exact_artifacts_only
                or not result.uaa_owned_cache
                or not result.pinned_revision_used
                or not result.unauthenticated
                or not result.https_get_only
                or not result.download_performed
                or not result.cache_write_performed
                or not result.network_access_performed
                or result.raw_response_stored
                or result.raw_url_stored
                or result.local_path_included
                or result.token_used
                or result.model_file_read_performed
                or result.model_call_performed
                or result.llama_cpp_process_started
                or result.subprocess_execution_performed
                or result.backend_route_added
                or result.control_center_control_added
                or result.dependency_added
                or result.production_authority_granted
            ):
                failures.append("M162 acquisition result is unsafe")
        except Exception as exc:
            failures.append(f"M162 GGUF acquisition validation failed: {exc}")

        source_path = (
            self.root
            / "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py"
        )
        source = self._read(source_path)
        for fragment in [
            'HF_MODEL_RESOLVE_URL_PREFIX = "https://huggingface.co"',
            "StdlibM162HuggingFaceArtifactTransport",
            "M162_ALLOWED_REDIRECT_HOST_SUFFIXES",
            "request.urlopen",
            "hashlib.sha256",
            "tempfile.NamedTemporaryFile",
            "expected_sha256",
            "ArtifactRole.mmproj",
        ]:
            if fragment not in source:
                failures.append(
                    f"M162 acquisition source missing required fragment: {fragment}"
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
            "shell=True",
            "llama_cpp.Llama(",
            "llama-server",
            "llama_server",
            "openai.OpenAI(",
            "AutoModel.from_pretrained(",
            "AutoTokenizer.from_pretrained(",
            "pipeline(",
            "backend_route_added=True",
            "dependency_added=True",
            "production_authority_granted=True",
        ]:
            if forbidden in source:
                failures.append(
                    f"M162 acquisition source contains forbidden fragment: {forbidden}"
                )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "m162 gguf model acquisition",
            "core-only",
            "stdlib-only",
            "exact-approved",
            "exact user approval",
            "pinned revision",
            "exact `.gguf` filename",
            "explicit sharded artifact refs",
            "explicit `mmproj*.gguf` artifact refs",
            "uaa-owned cache",
            "unauthenticated https get by default",
            "no auth by default",
            "no token use",
            "no raw url storage",
            "no raw local path storage",
            "no raw response storage",
            "no model/provider call",
            "no llama.cpp process",
            "no subprocess",
            "no backend route",
            "no control center control",
            "no dependency",
            "no production authority",
        ]:
            if fragment not in docs_text:
                failures.append(f"M162 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m166_local_model_production_readiness_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/production_release_gate.py",
            "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_GATE.md",
            "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_BOUNDARY.md",
            "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_RECEIPT_PLAN.md",
            "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_NON_GOALS.md",
            "docs/production/M166_PRODUCTION_AUTHORITY_GATE.md",
            "docs/release_notes/checkpoint_m166.md",
            "tests/test_m166_local_model_production_readiness.py",
            "tests/test_m166_gate_integration.py",
        ]
        failures = [
            f"missing M166 production readiness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.production_readiness import (
                REQUIRED_M166_EVIDENCE_KINDS,
                ProductionReadinessEvidenceKind,
                ProductionReleaseGateStatus,
                build_m166_green_production_readiness_evidence,
                build_m166_production_release_gate_record,
                validate_m166_production_readiness_evidence_record,
                validate_m166_production_release_gate_record,
            )

            fixture_evidence = build_m166_green_production_readiness_evidence()
            try:
                build_m166_production_release_gate_record(
                    evidence_records=fixture_evidence
                )
                failures.append(
                    "M166 fixture evidence unexpectedly granted production authority"
                )
            except ValueError as exc:
                if "M166_REVIEWED_LIVE_EVIDENCE_REQUIRED" not in str(exc):
                    failures.append(
                        f"M166 fixture evidence failed with wrong reason: {exc}"
                    )
            evidence = [
                record.model_copy(
                    update={
                        "reviewed_live_evidence": True,
                        "reviewed_by_ref": f"review-ref:m166:{record.kind.value}",
                    }
                )
                for record in fixture_evidence
            ]
            gate = build_m166_production_release_gate_record(evidence_records=evidence)
            expected_kinds = [
                ProductionReadinessEvidenceKind(kind)
                for kind in REQUIRED_M166_EVIDENCE_KINDS
            ]
            if (
                gate.status != ProductionReleaseGateStatus.production_authority_granted
                or gate.source_checkpoint_ref != "checkpoint:m165"
                or gate.required_evidence_kinds != expected_kinds
                or [item.evidence_ref for item in evidence] != gate.evidence_refs
                or not gate.production_authority_granted
                or not gate.production_runtime_authorized
                or not gate.go_live_authorized
                or not gate.production_deployment_authorized
                or not gate.traffic_routing_authorized
                or not gate.exact_scope_bound
                or not gate.all_evidence_passed
                or not gate.redacted_evidence_only
                or not gate.blockers_cleared
                or not gate.rollback_ready
                or not gate.audit_required
                or not gate.replay_safe
                or gate.side_effects_performed
                or "M166_PRODUCTION_AUTHORITY_GRANTED" not in gate.reason_codes
            ):
                failures.append(
                    "M166 release gate does not grant exact green production authority"
                )

            for evidence_record in evidence:
                if (
                    evidence_record.source_checkpoint_ref != "checkpoint:m165"
                    or not evidence_record.redacted
                    or not evidence_record.safe_refs_only
                    or not evidence_record.loopback_only
                    or not evidence_record.openwebui_shell_only
                    or evidence_record.openwebui_is_agent_brain
                    or evidence_record.raw_prompt_included
                    or evidence_record.raw_response_included
                    or evidence_record.raw_path_included
                    or evidence_record.secret_included
                    or evidence_record.blocker_refs
                    or not evidence_record.reviewed_live_evidence
                    or evidence_record.reviewed_by_ref is None
                ):
                    failures.append(
                        f"M166 evidence record unsafe: {evidence_record.evidence_ref}"
                    )
                validate_m166_production_readiness_evidence_record(evidence_record)

            for update, reason in [
                (
                    {"production_authority_granted": False},
                    "M166_PRODUCTION_AUTHORITY_GRANT_REQUIRED",
                ),
                ({"go_live_authorized": False}, "M166_GO_LIVE_AUTH_REQUIRED"),
                ({"raw_prompt_exported": True}, "M166_RAW_PROMPT_DENIED"),
                (
                    {"credential_material_exported": True},
                    "M166_CREDENTIAL_MATERIAL_DENIED",
                ),
                ({"backend_route_added": True}, "M166_BACKEND_ROUTE_DENIED"),
                (
                    {"side_effects_performed": ["deploy"]},
                    "M166_RELEASE_GATE_SIDE_EFFECTS_DENIED",
                ),
            ]:
                try:
                    validate_m166_production_release_gate_record(
                        gate.model_copy(update=update)
                    )
                    failures.append(
                        f"M166 unsafe gate mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M166 unsafe gate mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M166 production readiness validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "m166",
            "production authority granted",
            "live install/run tests",
            "openwebui e2e tests",
            "security review",
            "packaging",
            "operational rollback",
            "load tests",
            "all required evidence is green",
            "reviewed live evidence",
            "generated fixture evidence",
            "non-authoritative",
            "revocable",
            "replay-safe",
            "redacted summary only",
            "safe-ref-only",
            "localhost-only",
            "audit-bound",
            "rollback-bound",
            "no raw prompt",
            "no raw response",
            "no raw provider payload",
            "no credential",
            "no raw local path",
            "no raw log",
            "no backend route",
            "no control center control",
            "no openwebui admin",
            "no openwebui plugin",
            "no dependency",
            "no unreviewed side effects",
        ]:
            if fragment not in docs_text:
                failures.append(f"M166 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m166_local_model_production_readiness_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "production_authority_granted=True",
            "raw_prompt_exported=True",
            "raw_response_exported=True",
            "raw_provider_payload_exported=True",
            "credential_material_exported=True",
            "raw_local_path_exported=True",
            "raw_log_exported=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "unreviewed_dependency_added=True",
            "/production/release-gate/apply",
            "/production/release-gate/run",
            "/production/release-gate/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/production_release_gate.py",
        }
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
            if not root.exists():
                continue
            candidate_files: list[Path] = []
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
                            f"M166 forbidden production readiness fragment in {rel}: {fragment}"
                        )

        source = self._read(
            self.root
            / "src/ultimate_ai_agent/core/production_readiness/production_release_gate.py"
        )
        for fragment in [
            "REQUIRED_M166_EVIDENCE_KINDS",
            "ProductionReadinessEvidenceKind",
            "ProductionReleaseGateStatus",
            "reviewed_live_evidence",
            "reviewed_by_ref",
            "M166_REVIEWED_LIVE_EVIDENCE_REQUIRED",
            "build_m166_production_release_gate_record",
            "validate_m166_production_release_gate_record",
            "checkpoint:m165",
        ]:
            if fragment not in source:
                failures.append(
                    f"M166 release gate source missing required fragment: {fragment}"
                )
        for forbidden in [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "subprocess",
            "from subprocess import",
            "request.urlopen(",
            "shell=True",
            "openai.OpenAI(",
            "chat.completions.create(",
            "hf_hub_download(",
            "snapshot_download(",
            "raw_prompt_exported=True",
            "credential_material_exported=True",
            "backend_route_added=True",
            "control_center_control_added=True",
        ]:
            if forbidden in source:
                failures.append(
                    f"M166 release gate source contains forbidden fragment: {forbidden}"
                )
        return self._result(criterion, failures, [])

    def check_m166_local_model_production_readiness_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.api.openapi import verify_openapi_contract

            failures.extend(m166_openapi_route_failures(app.openapi().get("paths", {})))
            contract_status = verify_openapi_contract(app)
            if contract_status.errors:
                failures.extend(contract_status.errors)
        except Exception as exc:
            failures.append(f"M166 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m167_live_model_production_hardening_contracts(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/production_readiness/live_model_hardening.py",
            "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md",
            "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_BOUNDARY.md",
            "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_RUNBOOK.md",
            "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_NON_GOALS.md",
            "docs/release_notes/checkpoint_m167.md",
            "tests/test_m167_live_model_production_hardening.py",
            "tests/test_m167_gate_integration.py",
        ]
        failures = [
            f"missing M167 live model hardening file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.production_readiness import (
                REQUIRED_M167_EVIDENCE_KINDS,
                REQUIRED_M167_HARDWARE_PROFILES,
                LiveModelHardeningEvidenceKind,
                LiveModelHardeningHardwareProfile,
                LiveModelProductionHardeningStatus,
                build_m167_fixture_live_model_hardening_evidence,
                build_m167_live_model_production_hardening_report,
                validate_m167_live_model_hardening_evidence_record,
                validate_m167_live_model_production_hardening_report,
            )

            fixture_evidence = build_m167_fixture_live_model_hardening_evidence()
            try:
                build_m167_live_model_production_hardening_report(
                    evidence_records=fixture_evidence
                )
                failures.append(
                    "M167 fixture evidence unexpectedly passed live hardening"
                )
            except ValueError as exc:
                if "M167_REVIEWED_LIVE_EVIDENCE_REQUIRED" not in str(exc):
                    failures.append(
                        f"M167 fixture evidence failed with wrong reason: {exc}"
                    )
            evidence = [
                record.model_copy(
                    update={
                        "actual_live_evidence": True,
                        "reviewed_by_ref": (
                            f"review-ref:m167:{record.evidence_ref.rsplit(':', 1)[-1]}"
                        ),
                    }
                )
                for record in fixture_evidence
            ]
            report = build_m167_live_model_production_hardening_report(
                evidence_records=evidence
            )
            expected_kinds = [
                LiveModelHardeningEvidenceKind(kind)
                for kind in REQUIRED_M167_EVIDENCE_KINDS
            ]
            expected_profiles = [
                LiveModelHardeningHardwareProfile(profile)
                for profile in REQUIRED_M167_HARDWARE_PROFILES
            ]
            if (
                report.status
                != LiveModelProductionHardeningStatus.live_production_hardening_passed
                or report.source_checkpoint_ref != "checkpoint:m166"
                or report.required_evidence_kinds != expected_kinds
                or report.required_hardware_profiles != expected_profiles
                or [item.evidence_ref for item in evidence] != report.evidence_refs
                or not report.model_matrix_passed
                or not report.installer_runtime_packaging_ready
                or not report.selection_quality_validated
                or not report.tuning_loop_hardened
                or not report.openwebui_real_e2e_passed
                or not report.load_soak_passed
                or not report.operational_controls_ready
                or not report.actual_live_evidence_reviewed
                or not report.production_authority_inherited_from_m166
                or report.new_production_authority_granted
                or report.backend_route_added
                or report.control_center_control_added
                or report.dependency_added
                or report.side_effects_performed
                or "M167_NO_NEW_AUTHORITY_GRANTED" not in report.reason_codes
            ):
                failures.append(
                    "M167 hardening report is not exact reviewed-evidence-bound"
                )

            for evidence_record in evidence:
                if (
                    evidence_record.source_checkpoint_ref != "checkpoint:m166"
                    or not evidence_record.actual_live_evidence
                    or evidence_record.reviewed_by_ref is None
                    or not evidence_record.redacted
                    or not evidence_record.safe_refs_only
                    or not evidence_record.loopback_only
                    or evidence_record.openwebui_is_agent_brain
                    or evidence_record.raw_prompt_included
                    or evidence_record.raw_response_included
                    or evidence_record.raw_log_included
                    or evidence_record.credential_material_included
                    or evidence_record.blocker_refs
                ):
                    failures.append(
                        f"M167 evidence record unsafe: {evidence_record.evidence_ref}"
                    )
                validate_m167_live_model_hardening_evidence_record(evidence_record)

            for update, reason in [
                ({"model_matrix_passed": False}, "M167_MODEL_MATRIX_REQUIRED"),
                (
                    {"new_production_authority_granted": True},
                    "M167_NEW_AUTHORITY_DENIED",
                ),
                ({"backend_route_added": True}, "M167_BACKEND_ROUTE_DENIED"),
                (
                    {"runtime_execution_started_by_report": True},
                    "M167_REPORT_RUNTIME_EXECUTION_DENIED",
                ),
                (
                    {"model_download_started_by_report": True},
                    "M167_REPORT_DOWNLOAD_DENIED",
                ),
                ({"raw_prompt_exported": True}, "M167_RAW_PROMPT_DENIED"),
                (
                    {"credential_material_exported": True},
                    "M167_CREDENTIAL_MATERIAL_DENIED",
                ),
                (
                    {"side_effects_performed": ["deploy"]},
                    "M167_REPORT_SIDE_EFFECTS_DENIED",
                ),
            ]:
                try:
                    validate_m167_live_model_production_hardening_report(
                        report.model_copy(update=update)
                    )
                    failures.append(
                        f"M167 unsafe report mutation was not denied with {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(f"M167 unsafe report mutation raised {exc!s}")
        except Exception as exc:
            failures.append(f"M167 live model hardening validation failed: {exc}")

        docs_text = " ".join(
            "\n".join(
                self._read(self.root / path).lower()
                for path in required_files
                if path.startswith("docs/") and (self.root / path).exists()
            ).split()
        )
        for fragment in [
            "m167",
            "live production hardening",
            "real live model matrix testing",
            "apple silicon",
            "cpu-only",
            "low ram",
            "discrete gpu",
            "limited disk",
            "installer/runtime packaging",
            "llama-server discovery",
            "binary provenance",
            "selection quality validation",
            "real gguf repos",
            "gated model handling",
            "quant choice",
            "context limits",
            "disk/ram/vram",
            "tuning advisor hardening",
            "one change at a time",
            "approval-bound",
            "restart",
            "rollback",
            "openwebui real e2e",
            "/v1/models",
            "/v1/chat/completions",
            "load and soak tests",
            "operational controls",
            "cache cleanup",
            "model removal",
            "stuck downloads",
            "corrupted ggufs",
            "credential rotation",
            "offline mode",
            "redacted summary only",
            "safe-ref-only",
            "localhost-only",
            "no raw prompt",
            "no raw response",
            "no raw provider payload",
            "no credential",
            "no raw local path",
            "no raw log",
            "no backend route",
            "no control center control",
            "no dependency",
            "no unreviewed side effects",
        ]:
            if fragment not in docs_text:
                failures.append(f"M167 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m167_live_model_production_hardening_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "new_production_authority_granted=True",
            "runtime_execution_started_by_report=True",
            "model_download_started_by_report=True",
            "raw_prompt_exported=True",
            "raw_response_exported=True",
            "raw_provider_payload_exported=True",
            "credential_material_exported=True",
            "raw_local_path_exported=True",
            "raw_log_exported=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
            "/production/live-model-hardening/run",
            "/production/live-model-hardening/apply",
            "/production/model-matrix/run",
            "/production/llama-server/install",
            "/production/model-selection/calibrate",
            "/production/tuning/apply",
            "/production/load-soak/run",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/production_readiness/__init__.py",
            "src/ultimate_ai_agent/core/production_readiness/live_model_hardening.py",
        }
        for root in [
            self.root / "src" / "ultimate_ai_agent",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]:
            if not root.exists():
                continue
            candidate_files: list[Path] = []
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
                            f"M167 forbidden live hardening fragment in {rel}: {fragment}"
                        )

        source_path = (
            self.root
            / "src/ultimate_ai_agent/core/production_readiness/live_model_hardening.py"
        )
        source = self._read(source_path)
        for fragment in [
            "REQUIRED_M167_HARDWARE_PROFILES",
            "REQUIRED_M167_EVIDENCE_KINDS",
            "M167_REQUIRED_COVERAGE_FLAGS",
            "LiveModelHardeningHardwareProfile",
            "LiveModelHardeningEvidenceKind",
            "actual_live_evidence",
            "reviewed_by_ref",
            "M167_REVIEWED_LIVE_EVIDENCE_REQUIRED",
            "M167_NO_NEW_AUTHORITY_GRANTED",
            "build_m167_live_model_production_hardening_report",
            "validate_m167_live_model_production_hardening_report",
            "checkpoint:m166",
        ]:
            if fragment not in source:
                failures.append(
                    f"M167 live hardening source missing required fragment: {fragment}"
                )
        for forbidden in [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "subprocess",
            "from subprocess import",
            "request.urlopen(",
            "shell=True",
            "openai.OpenAI(",
            "chat.completions.create(",
            "hf_hub_download(",
            "snapshot_download(",
            "new_production_authority_granted=True",
            "runtime_execution_started_by_report=True",
            "model_download_started_by_report=True",
            "raw_prompt_exported=True",
            "credential_material_exported=True",
            "backend_route_added=True",
            "control_center_control_added=True",
            "dependency_added=True",
        ]:
            if forbidden in source:
                failures.append(
                    f"M167 live hardening source contains forbidden fragment: {forbidden}"
                )
        return self._result(criterion, failures, [])

    def check_m167_live_model_production_hardening_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app
            from ultimate_ai_agent.api.openapi import verify_openapi_contract

            failures.extend(m167_openapi_route_failures(app.openapi().get("paths", {})))
            contract_status = verify_openapi_contract(app)
            if contract_status.errors:
                failures.extend(contract_status.errors)
        except Exception as exc:
            failures.append(f"M167 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_v0292_local_dev_api_authority_and_preview_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/core/tools/broker.py",
            "src/ultimate_ai_agent/core/truth/validation.py",
            "tests/test_kernel_api_routes.py",
            "tests/test_file_api_routes.py",
            "tests/test_api_safe_exception_messages.py",
        ]
        failures = [
            f"missing v0.29.2 hardening file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from pydantic import ValidationError as PydanticValidationError

            from ultimate_ai_agent.api.app import (
                FileReadPreviewAPIRequest,
                post_preview_file_read,
                post_run_kernel_task,
                sanitize_validation_errors,
            )
            from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV
            from ultimate_ai_agent.core.kernel import (
                KernelTaskStatus,
                MinimumKernelRunner,
            )

            old_bearer = os.environ.get(LOCAL_API_BEARER_ENV)
            bearer = "foundation-gate-v0292-local-bearer"
            os.environ[LOCAL_API_BEARER_ENV] = bearer

            def kernel_payload(
                workspace_root: Path, approval_ref: str
            ) -> dict[str, Any]:
                return {
                    "request_id": "ktr_gate_v0292",
                    "run_id": "run_gate_v0292",
                    "actor_context": {
                        "actor_type": "human_user",
                        "actor_id": "gate_user",
                        "authority_source": "explicit_user_request",
                    },
                    "user_id": "gate_user",
                    "workspace_root": str(workspace_root),
                    "task_type": "create_dev_file",
                    "user_request": "Create a local dev note.",
                    "target_path": "notes/m5.md",
                    "new_content": "# Gate\n",
                    "purpose": "create_dev_note",
                    "consent_grants": [
                        {
                            "consent_id": "consent_gate_v0292",
                            "subject_type": "user",
                            "subject_id": "gate_user",
                            "granted_to_actor": "gate_user",
                            "on_behalf_of_user_id": "gate_user",
                            "scope_type": "workspace",
                            "scope_id": "workspace_gate_v0292",
                            "allowed_actions": ["create", "update", "write"],
                            "allowed_resources": ["file.write.local_dev"],
                            "allowed_data_boundaries": ["project_private"],
                            "allowed_purposes": ["create_dev_note"],
                            "source": "foundation_gate",
                        }
                    ],
                    "approval_ref": approval_ref,
                    "idempotency_key": "idem_gate_v0292",
                    "data_classification": "project_private",
                    "tags": ["foundation_gate", "v0292"],
                }

            try:
                with tempfile.TemporaryDirectory(
                    prefix="uaa-gate-v0292-kernel-"
                ) as probe_dir:
                    probe_root = Path(probe_dir)
                    payload = kernel_payload(probe_root, "approval_test_gate")
                    response = post_run_kernel_task(payload)
                    if response.success is not True:
                        failures.append(
                            "kernel API dry-run probe returned failure envelope"
                        )
                    else:
                        data = response.data or {}
                        if data.get("status") != KernelTaskStatus.dry_run:
                            failures.append(
                                "kernel API did not force local-dev mutation requests into dry-run"
                            )
                        if (probe_root / "notes" / "m5.md").exists():
                            failures.append("kernel API dry-run probe created a file")

                    direct_result = MinimumKernelRunner().run_payload(
                        kernel_payload(probe_root, "approval_test_gate")
                    )
                    if (
                        direct_result.success
                        or "APPROVAL_REF_UNVALIDATED" not in direct_result.errors
                    ):
                        failures.append(
                            "kernel runner accepted a test-prefixed approval without authority"
                        )

                with tempfile.TemporaryDirectory(
                    prefix="uaa-gate-v0292-preview-"
                ) as preview_dir:
                    preview_root = Path(preview_dir)
                    preview_file = preview_root / "note.txt"
                    preview_file.write_text("hello", encoding="utf-8")
                    old_safe_root = os.environ.get("UAA_FILE_API_SAFE_ROOT")
                    os.environ["UAA_FILE_API_SAFE_ROOT"] = str(preview_root)
                    try:
                        preview_response = post_preview_file_read(
                            FileReadPreviewAPIRequest(
                                safe_root_ref="local_dev_workspace",
                                request={
                                    "request_id": "frr_gate_v0292",
                                    "run_id": "run_gate_v0292",
                                    "actor_context": {
                                        "actor_type": "human_user",
                                        "actor_id": "gate_user",
                                        "authority_source": "explicit_user_request",
                                    },
                                    "path": "note.txt",
                                    "purpose": "preview",
                                    "max_bytes": 100,
                                },
                            )
                        )
                        if preview_response.success is not True:
                            failures.append("file preview metadata probe failed")
                        else:
                            preview_data = preview_response.data or {}
                            if preview_data.get("text_preview") != "":
                                failures.append(
                                    "file preview API returned raw text content"
                                )
                            if preview_data.get("content_hash") != "redacted":
                                failures.append(
                                    "file preview API returned a content hash"
                                )
                            if "hello" in preview_response.model_dump_json():
                                failures.append(
                                    "file preview API echoed raw file content"
                                )
                            if "raw_content_omitted" not in preview_data.get(
                                "redactions_applied", []
                            ):
                                failures.append(
                                    "file preview API did not mark raw content omitted"
                                )
                        try:
                            FileReadPreviewAPIRequest(
                                workspace_root=str(preview_root),
                                safe_root_ref="local_dev_workspace",
                                request={
                                    "request_id": "frr_gate_v0292_caller_root",
                                    "run_id": "run_gate_v0292",
                                    "actor_context": {
                                        "actor_type": "human_user",
                                        "actor_id": "gate_user",
                                        "authority_source": "explicit_user_request",
                                    },
                                    "path": "note.txt",
                                    "purpose": "preview",
                                    "max_bytes": 100,
                                },
                            )
                            failures.append(
                                "file preview API accepted caller-selected workspace_root"
                            )
                            caller_root_response_text = ""
                        except PydanticValidationError as exc:
                            caller_root_response_text = json.dumps(
                                sanitize_validation_errors(exc.errors())
                            )
                        if str(preview_root) in caller_root_response_text:
                            failures.append(
                                "file preview API echoed caller-selected workspace_root"
                            )
                    finally:
                        if old_safe_root is None:
                            os.environ.pop("UAA_FILE_API_SAFE_ROOT", None)
                        else:
                            os.environ["UAA_FILE_API_SAFE_ROOT"] = old_safe_root
            finally:
                if old_bearer is None:
                    os.environ.pop(LOCAL_API_BEARER_ENV, None)
                else:
                    os.environ[LOCAL_API_BEARER_ENV] = old_bearer

            app_source = (
                self.root / "src" / "ultimate_ai_agent" / "api" / "app.py"
            ).read_text(encoding="utf-8")
            forbidden_exception_echo = (
                "safe_message=str(e)",
                "safe_message = str(e)",
                "safe_message=str(exc)",
                "safe_message = str(exc)",
                "detail=str(e)",
                "detail = str(e)",
                "detail=str(exc)",
                "detail = str(exc)",
            )
            failures.extend(
                f"API handler contains raw exception echo fragment: {fragment}"
                for fragment in forbidden_exception_echo
                if fragment in app_source
            )
        except Exception as exc:
            failures.append(f"v0.29.2 local-dev API hardening validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m25_m26_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
        ]
        failures = [
            f"missing M25 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.29.0" in text and "truth source router + evidence claim checker" in text:
            if "implemented/released" not in text:
                failures.append("M25 docs do not mark v0.29.0 implemented/released")
        else:
            failures.append(
                "M25 docs do not mention v0.29.0 Truth Source Router + Evidence Claim Checker"
            )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 32, 0):
            if (
                "v0.32.0" in text
                and "approval authority v2 + action policy expansion" in text
            ):
                if "implemented/released" not in text:
                    failures.append(
                        "M28 docs must mark v0.32.0 implemented/released after M28"
                    )
            else:
                failures.append(
                    "M28 docs do not mention v0.32.0 Approval Authority v2 + Action Policy Expansion"
                )
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
        elif version_tuple >= (0, 31, 0):
            if (
                "v0.31.0" in text
                and "tool broker v2 + safe tool intent contracts" in text
            ):
                if "implemented/released" not in text:
                    failures.append(
                        "M27 docs must mark v0.31.0 implemented/released after M27"
                    )
            else:
                failures.append(
                    "M27 docs do not mention v0.31.0 Tool Broker v2 + Safe Tool Intent Contracts"
                )
            if "m28-m40 remain planned/provisional" not in text:
                failures.append("M28-M40 must remain planned/provisional after M27")
        elif version_tuple >= (0, 30, 0):
            if (
                "m26 is implemented/released" not in text
                and "v0.30.0 implements m26" not in text
            ):
                failures.append(
                    "M26 docs must mark v0.30.0 implemented/released after M26"
                )
            if "m27-m40 remain planned/provisional" not in text:
                failures.append("M27-M40 must remain planned/provisional after M26")
        else:
            if "v0.30.0 | m26" in text and "planned/provisional" not in text:
                failures.append("M26 roadmap row is not planned/provisional")
            if "m26 is implemented" in text or "v0.30.0 implements m26" in text:
                failures.append("M26 is incorrectly marked implemented")
            forbidden_m26_fragments = (
                "context injection implementation",
                "context-pack builder implemented",
                "grounded recall router implemented",
            )
            failures.extend(
                f"M25 docs imply M26 implementation: {fragment}"
                for fragment in forbidden_m26_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)
