from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart002Mixin:
    """Legacy checks from m85_router_uses_valid_approval_grant through m143_no_live_mesh_integrations."""
    def check_m85_router_uses_valid_approval_grant(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

        profile = self._gate_cloud_profile()
        request = self._gate_route_request(
            profile,
            data_classification=ClassificationValue.sensitive_personal,
            policy=ModelRoutingPolicy(
                policy_id="m85_gate_cloud_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=False,
                allow_cloud=True,
                allow_paid=True,
                require_human_approval_for_cloud=True,
            ),
        )
        authority = LocalApprovalAuthority()
        approval_request = authority.create_request(
            LocalApprovalAuthority.request_for_model_route(
                request, resource_refs=[profile.model_profile_id]
            )
        )
        grant = authority.grant(
            approval_request.approval_request_id, approved_by_actor_id="foundation_gate"
        )
        decision = ModelRouter(approval_authority=authority).route(
            request.model_copy(update={"approval_ref": grant.approval_ref})
        )
        failures = []
        if decision.status != ModelRouteStatus.selected:
            failures.append("valid approval grant did not permit selected route")
        if "APPROVAL_VALIDATED" not in decision.reason_codes:
            failures.append("route decision did not expose approval validation reason")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_router/router.py"]
        )

    def check_m85_runtime_factory_rejects_arbitrary_approval(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import ModelRuntimeRequestFactory

        route = self._gate_route_request(
            self._gate_cloud_profile(), approval_ref="human_approved_ref_123"
        )
        decision = ModelRouter().route(route.model_copy(update={"approval_ref": None}))
        failures = []
        try:
            ModelRuntimeRequestFactory.from_route_decision(
                decision, route, self._m85_runtime_manifest()
            )
            failures.append("runtime factory accepted arbitrary approval_ref")
        except ValueError:
            pass
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/adapters.py"],
        )

    def check_m85_tool_broker_rejects_arbitrary_approval(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.consent import (
            ConsentGrant,
            ConsentScopeType,
            ConsentSubjectType,
        )
        from ultimate_ai_agent.core.consent.enums import PermissionAction
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

        registry = ToolRegistry()
        registry.register_tool(
            ToolManifest(
                tool_id="m85_gate_tool",
                display_name="M8.5 Gate Tool",
                category=ToolCategory.mock,
                description="Approval authority gate check.",
                execution_mode=ToolExecutionMode.dry_run,
                risk_level=ToolRiskLevel.high,
                capability_flag="m85_gate_tool",
                owner="core.gate",
                source="foundation_gate",
                version="0.0.0",
            )
        )
        ledger = ConsentLedger()
        ledger.add_grant(
            ConsentGrant(
                consent_id="m85_gate_consent",
                subject_type=ConsentSubjectType.tool,
                subject_id="m85_gate_tool",
                granted_to_actor="foundation_gate",
                on_behalf_of_user_id="foundation_gate",
                scope_type=ConsentScopeType.project,
                allowed_actions=[PermissionAction.execute],
                source="foundation_gate",
            )
        )
        decision = ToolBroker(
            registry,
            CapabilityFirewallPolicy(max_risk_level=ToolRiskLevel.high),
            approval_authority=LocalApprovalAuthority(),
        ).evaluate_request(
            ToolRequest(
                request_id="m85_gate_tool_request",
                run_id="run_foundation_gate",
                tool_id="m85_gate_tool",
                actor_context=self._actor(),
                requested_action="execute",
                purpose="foundation_gate_check",
                data_classification=DataBoundary.project_private,
                approval_ref="human_approved_ref_123",
            ),
            ledger,
        )
        failures = []
        if decision.status != ToolDecisionStatus.approval_required:
            failures.append(
                "tool broker did not keep arbitrary approval_ref approval-required"
            )
        if "APPROVAL_REF_UNKNOWN" not in decision.reason_codes:
            failures.append("tool broker did not report unknown approval ref")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/tools/broker.py"]
        )

    def check_m85_no_real_auth_oauth_network(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        approval_root = self.src_root / "core" / "approvals"
        forbidden = [
            "import " + "requests",
            "import " + "httpx",
            "urllib",
            "socket",
            "oauth",
            "OAuth",
            "OpenID",
            "session_cookie",
            "jwt",
            "sqlite",
            "psycopg",
            "sub" + "process",
        ]
        failures = []
        for path in sorted(self._context.rglob(approval_root, "*.py")):
            rel_path = self._context.relative_path(path)
            for line_no, line in enumerate(
                self._context.read_text(path, encoding="utf-8").splitlines(), start=1
            ):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(
                        f"{rel_path}:{line_no} forbidden auth/network/persistence fragment"
                    )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/approvals"]
        )

    def check_m85_approval_api_secret_echo_absent(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import post_validate_approval_request

        secret = "sk_" + "test_" + "secret_" + "value"
        assignment = "api_" + "key=" + secret
        payload = self._m85_gate_approval_request().model_dump(mode="json")
        payload["metadata"] = {"note": assignment}
        response = post_validate_approval_request(payload)
        response_text = response.model_dump_json()
        failures = []
        if response.success is not False:
            failures.append("approval API did not return a validation failure")
        if (
            secret in response_text
            or assignment in response_text
            or "api_key" in response_text
        ):
            failures.append("approval API echoed secret-like input")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m9_loopback_runtime_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/loopback.py",
            "src/ultimate_ai_agent/core/model_runtime/execution_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/transports.py",
            "src/ultimate_ai_agent/core/model_runtime/local_adapter.py",
        ]
        failures = [
            f"missing {path}" for path in required if not (self.root / path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m9_non_loopback_endpoints_denied(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            LocalLoopbackModelRuntimeAdapter,
            LoopbackRuntimeEndpoint,
            LoopbackRuntimePolicy,
            ModelRuntimeKind,
        )

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(
            policy_id="m9_gate_policy", allow_real_loopback_execution=True
        )

        def endpoint(base_url: str) -> Any:
            return LoopbackRuntimeEndpoint(
                endpoint_id="m9_gate_endpoint",
                base_url=base_url,
                allowed_hosts=["127.0.0.1", "localhost", "::1"],
                runtime_kind=ModelRuntimeKind.local_stub,
                model_id="m9_gate_model",
                enabled=True,
                owner="foundation_gate",
                source="foundation_gate",
                version="0.0.0",
            )

        failures = []
        remote = adapter.validate_endpoint(
            endpoint("http" + "://example.com/api/generate"), policy
        )
        credentials = adapter.validate_endpoint(
            endpoint("http" + "://user:pass@127.0.0.1:11434/api/generate"), policy
        )
        query = adapter.validate_endpoint(
            endpoint("http" + "://127.0.0.1:11434/api/generate?token=abc"), policy
        )
        if remote.allowed or "NON_LOOPBACK_HOST_DENIED" not in remote.reason_codes:
            failures.append("remote host was not denied")
        if (
            credentials.allowed
            or "URL_CREDENTIALS_DENIED" not in credentials.reason_codes
        ):
            failures.append("URL credentials were not denied")
        if query.allowed or "SECRET_QUERY_DENIED" not in query.reason_codes:
            failures.append("secret-like query parameter was not denied")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"],
        )

    def check_m9_non_loopback_policy_override_denied(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            LocalLoopbackModelRuntimeAdapter,
            LoopbackRuntimeEndpoint,
            LoopbackRuntimePolicy,
            ModelRuntimeKind,
        )

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(
            policy_id="m9_gate_override_policy",
            allow_real_loopback_execution=True,
        ).model_copy(
            update={
                "allowed_hosts": ["example.com"],
                "deny_non_loopback": False,
            }
        )
        endpoint = LoopbackRuntimeEndpoint(
            endpoint_id="m9_gate_override_endpoint",
            base_url="http" + "://example.com/api/generate",
            allowed_hosts=["example.com"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id="m9_gate_model",
            enabled=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
        )
        decision = adapter.validate_endpoint(endpoint, policy)
        failures = []
        if decision.allowed:
            failures.append("caller override allowed a remote endpoint")
        for reason in (
            "NON_LOOPBACK_HOST_DENIED",
            "POLICY_CANNOT_DISABLE_LOOPBACK_GUARD",
        ):
            if reason not in decision.reason_codes:
                failures.append(f"override decision missing {reason}")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"],
        )

    def check_m9_loopback_policy_model_rejects_hostile_inputs(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

        failures = []
        hostile_inputs = [
            {"deny_non_loopback": False},
            {"allowed_hosts": ["example.com"]},
            {"allowed_hosts": ["192.168.1.5"]},
            {"allowed_hosts": ["10.0.0.5"]},
            {"allowed_hosts": ["8.8.8.8"]},
            {"allowed_hosts": ["127.0.0.1", "example.com"]},
        ]
        for payload in hostile_inputs:
            try:
                LoopbackRuntimePolicy(policy_id="m9_gate_hostile_policy", **payload)
            except ValueError:
                continue
            failures.append(f"hostile policy accepted: {payload}")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/execution_policy.py"],
        )

    def check_m9_public_and_private_ip_endpoints_denied(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            LocalLoopbackModelRuntimeAdapter,
            LoopbackRuntimeEndpoint,
            LoopbackRuntimePolicy,
            ModelRuntimeKind,
        )

        adapter = LocalLoopbackModelRuntimeAdapter()
        policy = LoopbackRuntimePolicy(
            policy_id="m9_gate_ip_policy", allow_real_loopback_execution=True
        )
        failures = []
        for host in ["192.168.1.5", "10.0.0.5", "8.8.8.8"]:
            endpoint = LoopbackRuntimeEndpoint(
                endpoint_id=f"m9_gate_{host.replace('.', '_')}",
                base_url="http" + f"://{host}/api/generate",
                allowed_hosts=[host],
                runtime_kind=ModelRuntimeKind.local_stub,
                model_id="m9_gate_model",
                enabled=True,
                owner="foundation_gate",
                source="foundation_gate",
                version="0.0.0",
            )
            decision = adapter.validate_endpoint(endpoint, policy)
            if (
                decision.allowed
                or "NON_LOOPBACK_HOST_DENIED" not in decision.reason_codes
            ):
                failures.append(f"{host} was not denied")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"],
        )

    def check_m9_approval_api_uses_public_authority_helper(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        app_source = self._read(self.root / "src/ultimate_ai_agent/api/app.py")
        authority_source = self._read(
            self.root / "src/ultimate_ai_agent/core/approvals/authority.py"
        )
        failures = []
        if "authority._grants" in app_source:
            failures.append("approval API mutates private _grants")
        if "load_grant_for_validation" not in app_source:
            failures.append("approval API does not use public grant-loading helper")
        if "def load_grant_for_validation" not in authority_source:
            failures.append("LocalApprovalAuthority helper is missing")
        return self._result(
            criterion,
            failures,
            [
                "src/ultimate_ai_agent/api/app.py",
                "src/ultimate_ai_agent/core/approvals/authority.py",
            ],
        )

    def check_m9_arbitrary_approval_refs_denied(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            LocalLoopbackModelRuntimeAdapter,
        )

        request = self._m9_runtime_request(approval_ref="human_approved_ref_123")
        decision = LocalLoopbackModelRuntimeAdapter().validate_execution(
            request,
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval_decision=None,
        )
        failures = []
        if decision.allowed:
            failures.append("arbitrary approval_ref allowed execution")
        if "APPROVAL_DECISION_REQUIRED" not in decision.reason_codes:
            failures.append(
                "arbitrary approval_ref did not require validated approval decision"
            )
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"],
        )

    def check_m9_fake_transport_only_in_gate(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        runtime_root = self.src_root / "core" / "model_runtime"
        forbidden = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "openai",
            "import " + "anthropic",
            "tiktoken",
            "tokenizers",
            "billing",
            "sub" + "process",
        ]
        failures = []
        for path in sorted(self._context.rglob(runtime_root, "*.py")):
            rel_path = self._context.relative_path(path)
            for line_no, line in enumerate(
                self._context.read_text(path, encoding="utf-8").splitlines(), start=1
            ):
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(
                        f"{rel_path}:{line_no} forbidden M9 runtime fragment"
                    )
                if "DisabledNetworkTransport().send(" in stripped:
                    failures.append(
                        f"{rel_path}:{line_no} disabled transport send call in gate path"
                    )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_runtime"]
        )

    def check_m9_simulated_fallback_available(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.model_runtime import (
            LocalLoopbackModelRuntimeAdapter,
            ModelRuntimeResponseStatus,
        )

        response = LocalLoopbackModelRuntimeAdapter().execute_dev(
            self._m9_runtime_request(approval_ref="human_approved_ref_123"),
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval_decision=None,
        )
        failures = []
        if response.status != ModelRuntimeResponseStatus.simulated_success:
            failures.append("blocked execution did not return simulated fallback")
        if response.response_origin != "simulated":
            failures.append("fallback response origin was not simulated")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/local_adapter.py"],
        )

    def check_m9_model_output_not_truth_authority(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import (
            ApprovalRiskLevel,
            ApprovalSubjectType,
            LocalApprovalAuthority,
        )
        from ultimate_ai_agent.core.model_runtime import (
            FakeModelRuntimeTransport,
            LocalLoopbackModelRuntimeAdapter,
            response_is_truth_authority,
        )

        request = self._m9_runtime_request()
        approval_request = LocalApprovalAuthority.request_for_model_route(
            self._gate_route_request(self._gate_local_profile()),
            subject_type=ApprovalSubjectType.model_runtime_request,
            subject_id=request.runtime_request_id,
            requested_action="execute_local_loopback_model",
            resource_refs=[request.adapter_id, request.model_profile_id],
            risk_level=ApprovalRiskLevel.high,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        grant = authority.grant(
            approval_request.approval_request_id, approved_by_actor_id="foundation_gate"
        )
        approval = authority.validate_for_request(approval_request, grant.approval_ref)
        response = LocalLoopbackModelRuntimeAdapter().execute_dev(
            request.model_copy(update={"approval_ref": grant.approval_ref}),
            self._m9_runtime_manifest(),
            self._m9_loopback_endpoint(),
            self._m9_loopback_policy(),
            approval,
            transport=FakeModelRuntimeTransport(),
        )
        failures = []
        if response_is_truth_authority(response):
            failures.append("local loopback response is truth authority")
        if response.metadata.get("truth_authority") is not False:
            failures.append("local loopback metadata did not mark non-authoritative")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/responses.py"],
        )

    def check_m10_manual_smoke_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/model_runtime/smoke_policy.py",
            "src/ultimate_ai_agent/core/model_runtime/smoke.py",
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "scripts/local_loopback_smoke.py",
            "tests/test_manual_loopback_smoke_policy.py",
            "tests/test_manual_loopback_smoke_transport.py",
            "tests/test_manual_loopback_smoke_script.py",
            "tests/test_manual_loopback_smoke_api_routes.py",
            "tests/test_m10_gate_integration.py",
        ]
        failures = [
            f"missing {rel_path}"
            for rel_path in required
            if not (self.root / rel_path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m10_stdlib_network_isolated(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        allowed = {
            "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
            "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py",
            "scripts/local_loopback_smoke.py",
            "scripts/manual_local_model_call.py",
        }
        forbidden = [
            "import " + "requests",
            "from " + "requests import",
            "import " + "httpx",
            "from " + "httpx import",
            "import " + "openai",
            "import " + "anthropic",
            "tiktoken",
            "tokenizers",
            "billing",
            "socket",
            "subprocess",
        ]
        failures = []
        paths = [
            *list(
                (self.root / "src/ultimate_ai_agent/core/model_runtime").rglob("*.py")
            ),
            self.root / "scripts/local_loopback_smoke.py",
            self.root / "scripts/manual_local_model_call.py",
        ]
        for path in paths:
            if not path.exists():
                continue
            rel_path = self._context.relative_path(path)
            source = self._read(path)
            if (
                "urllib.request" in source or "from urllib import request" in source
            ) and rel_path not in allowed:
                failures.append(
                    f"urllib request outside isolated smoke file: {rel_path}"
                )
            for line in source.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden):
                    failures.append(
                        f"forbidden runtime fragment in {rel_path}: {stripped}"
                    )
        return self._result(criterion, failures, sorted(allowed))

    def check_m10_gate_and_verify_do_not_call_smoke_script(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        for rel_path in ["scripts/run_foundation_gate.py", "scripts/verify_all.py"]:
            source = self._read(self.root / rel_path)
            if "scripts/local_loopback_smoke.py" in source:
                failures.append(f"{rel_path} references manual smoke script")
        return self._result(
            criterion,
            failures,
            ["scripts/run_foundation_gate.py", "scripts/verify_all.py"],
        )

    def check_m10_public_api_has_no_smoke_execute_endpoint(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        paths = {route.path for route in app.routes}
        failures = []
        if "/model-runtime/local/smoke/validate" not in paths:
            failures.append("smoke validation endpoint missing")
        for forbidden in [
            "/model-runtime/local/smoke/execute",
            "/model-runtime/local/execute",
        ]:
            if forbidden in paths:
                failures.append(f"forbidden execute endpoint present: {forbidden}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m10_fixed_prompt_and_loopback_policy_enforced(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        try:
            self._m10_smoke_request(fixed_prompt="Summarize this user file content.")
            failures.append("arbitrary user-content prompt accepted")
        except ValueError:
            pass
        try:
            self._m10_smoke_request(
                endpoint=self._m10_smoke_endpoint(
                    base_url="http" + "://example.com/api/generate",
                    allowed_hosts=["example.com"],
                )
            )
            failures.append("remote smoke endpoint accepted")
        except ValueError:
            pass
        try:
            self._m10_smoke_request()
        except ValueError as exc:
            failures.append(f"safe fixed smoke request rejected: {exc}")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/model_runtime/smoke_policy.py"],
        )

    def check_m10_smoke_approval_required(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import (
            smoke_approval_request,
            validate_manual_loopback_smoke_request,
        )

        request = self._m10_smoke_request()
        missing = validate_manual_loopback_smoke_request(
            request.model_copy(update={"approval_ref": None}), None
        )
        arbitrary = validate_manual_loopback_smoke_request(
            request.model_copy(update={"approval_ref": "human_approved_ref_123"}), None
        )
        approval = smoke_approval_request(request)
        authority = LocalApprovalAuthority()
        authority.create_request(approval)
        grant = authority.grant(
            approval.approval_request_id, approved_by_actor_id="human_reviewer"
        )
        decision = authority.validate_for_request(approval, grant.approval_ref)
        allowed = validate_manual_loopback_smoke_request(
            request.model_copy(update={"approval_ref": grant.approval_ref}), decision
        )
        failures = []
        if missing.allowed or "APPROVAL_REQUIRED" not in missing.reason_codes:
            failures.append("missing approval was not denied")
        if (
            arbitrary.allowed
            or "APPROVAL_DECISION_REQUIRED" not in arbitrary.reason_codes
        ):
            failures.append("arbitrary approval ref was not denied")
        if not allowed.allowed:
            failures.append("valid scoped approval did not permit smoke validation")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke.py"]
        )

    def check_m10_smoke_response_not_truth_authority(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
        from ultimate_ai_agent.core.model_runtime import (
            FakeManualLoopbackSmokeTransport,
            smoke_approval_request,
        )

        request = self._m10_smoke_request()
        approval = smoke_approval_request(request)
        authority = LocalApprovalAuthority()
        authority.create_request(approval)
        grant = authority.grant(
            approval.approval_request_id, approved_by_actor_id="human_reviewer"
        )
        decision = authority.validate_for_request(approval, grant.approval_ref)
        result = FakeManualLoopbackSmokeTransport().send_smoke(
            request.model_copy(update={"approval_ref": grant.approval_ref}), decision
        )
        failures = []
        if result.metadata.get("truth_authority") is not False:
            failures.append("smoke result metadata does not mark truth_authority false")
        if (
            result.response_preview == request.fixed_prompt
            or request.fixed_prompt in result.model_dump_json()
        ):
            failures.append("smoke result leaked fixed prompt content")
        if result.response_origin != "fake_manual_loopback_smoke":
            failures.append("gate did not use fake manual smoke transport")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/model_runtime/smoke.py"]
        )

    def check_m105_remote_worker_files_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required = [
            "src/ultimate_ai_agent/core/remote_workers/__init__.py",
            "src/ultimate_ai_agent/core/remote_workers/enums.py",
            "src/ultimate_ai_agent/core/remote_workers/nodes.py",
            "src/ultimate_ai_agent/core/remote_workers/transports.py",
            "src/ultimate_ai_agent/core/remote_workers/registry.py",
            "src/ultimate_ai_agent/core/remote_workers/policy.py",
            "src/ultimate_ai_agent/core/remote_workers/jobs.py",
            "src/ultimate_ai_agent/core/remote_workers/results.py",
            "src/ultimate_ai_agent/core/remote_workers/audit.py",
            "src/ultimate_ai_agent/core/remote_workers/status.py",
            "src/ultimate_ai_agent/core/remote_workers/validation.py",
            "src/ultimate_ai_agent/core/remote_workers/dry_run.py",
            "tests/test_remote_worker_models.py",
            "tests/test_remote_worker_registry.py",
            "tests/test_remote_worker_policy.py",
            "tests/test_remote_worker_transports.py",
            "tests/test_remote_worker_dry_run.py",
            "tests/test_remote_worker_api_routes.py",
            "tests/test_remote_worker_no_network.py",
            "tests/test_remote_worker_gate_integration.py",
        ]
        failures = [
            f"missing {rel_path}"
            for rel_path in required
            if not (self.root / rel_path).exists()
        ]
        return self._result(criterion, failures, required)

    def check_m105_remote_capabilities_default_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import NodeCapabilitySet

        capabilities = NodeCapabilitySet()
        failures = []
        for name, value in capabilities.model_dump().items():
            if value is not False:
                failures.append(f"{name} defaulted to {value}")
        for field, value in {
            "can_approve_actions": True,
            "can_run_critical": True,
        }.items():
            try:
                NodeCapabilitySet(**{field: value})
                failures.append(f"{field} accepted true")
            except ValueError:
                pass
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/nodes.py"]
        )

    def check_m105_unknown_node_and_transport_denied(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteNodeRegistry,
            RemoteTransportRegistry,
        )

        node = RemoteNodeRegistry().validate_node("missing_node")
        transport = RemoteTransportRegistry().validate_transport("missing_transport")
        failures = []
        if node.allowed or "REMOTE_NODE_UNKNOWN" not in node.reason_codes:
            failures.append("unknown node was not denied")
        if (
            transport.allowed
            or "REMOTE_TRANSPORT_UNKNOWN" not in transport.reason_codes
        ):
            failures.append("unknown transport was not denied")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/remote_workers/registry.py"],
        )

    def check_m105_planned_transports_disabled(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            default_remote_transport_registry,
        )

        registry = default_remote_transport_registry()
        failures = []
        for transport_id in ["tailnet_planned", "lan_planned"]:
            descriptor = registry.get_transport(transport_id)
            decision = registry.validate_transport(transport_id)
            if descriptor is None:
                failures.append(f"{transport_id} missing")
                continue
            if descriptor.enabled:
                failures.append(f"{transport_id} enabled")
            if decision.allowed:
                failures.append(f"{transport_id} allowed")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/remote_workers/registry.py"],
        )

    def check_m105_dry_run_dispatches_nothing(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteDryRunBuilder,
            RemoteExecutionPolicy,
            default_remote_node_registry,
            default_remote_transport_registry,
        )

        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        envelope = RemoteDryRunBuilder().build_envelope(
            task_summary="Validate remote worker dry-run metadata.",
            node_id="mock_node",
            transport_id="mock_metadata",
            actor_context=self._actor(),
            policy=policy,
        )
        result = RemoteDryRunBuilder().dry_run(
            envelope,
            default_remote_node_registry(),
            default_remote_transport_registry(),
            policy,
        )
        failures = []
        if result.dispatch_performed:
            failures.append("dry-run marked dispatch performed")
        if result.remote_execution_performed:
            failures.append("dry-run marked remote execution performed")
        if result.subagent_launched:
            failures.append("dry-run launched subagent")
        if result.tools_executed:
            failures.append("dry-run executed tools")
        if result.network_connections_opened:
            failures.append("dry-run opened network connections")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/remote_workers/dry_run.py"],
        )

    def check_m105_no_remote_network_or_background_execution(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        root = self.root / "src/ultimate_ai_agent/core/remote_workers"
        forbidden_imports = {
            "socket",
            "subprocess",
            "threading",
            "asyncio",
            "requests",
            "httpx",
            "urllib",
        }
        forbidden_fragments = [
            "Popen",
            "os.system",
            "Thread(",
            "urlopen",
            "dispatch_job(",
            "execute_remote(",
            "launch_subagent(",
        ]
        failures = []
        for path in self._context.rglob(root, "*.py"):
            source = self._read(path)
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    if any(fragment in stripped for fragment in forbidden_imports):
                        failures.append(
                            f"{path.relative_to(self.root)} forbidden import: {stripped}"
                        )
                if any(fragment in stripped for fragment in forbidden_fragments):
                    failures.append(
                        f"{path.relative_to(self.root)} forbidden fragment: {stripped}"
                    )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/remote_workers"]
        )

    def check_m105_no_remote_subagents_tools_or_approvals(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteExecutionPolicy,
            evaluate_remote_job_policy,
        )

        failures = []
        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        for capability, reason in [
            ("subagent", "REMOTE_SUBAGENT_DENIED"),
            ("tools", "REMOTE_TOOL_EXECUTION_DENIED"),
            ("approve", "REMOTE_APPROVAL_DENIED"),
            ("personal_data", "REMOTE_PERSONAL_DATA_DENIED"),
            ("write", "REMOTE_WRITE_DENIED"),
            ("send", "REMOTE_SEND_DENIED"),
        ]:
            envelope = self._m105_remote_job(requested_capabilities=[capability])
            decision = evaluate_remote_job_policy(
                envelope,
                self._m105_node_registry(),
                self._m105_transport_registry(),
                policy,
            )
            if decision.allowed or reason not in decision.reason_codes:
                failures.append(f"{capability} not denied")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"]
        )

    def check_m105_remote_output_untrusted(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteDryRunBuilder,
            RemoteExecutionPolicy,
            RemoteOutputTrustLevel,
        )

        policy = RemoteExecutionPolicy(
            policy_id="m105_gate_policy",
            remote_workers_enabled=True,
            remote_transports_enabled=True,
            remote_accept_jobs=True,
        )
        result = RemoteDryRunBuilder().dry_run(
            self._m105_remote_job(),
            self._m105_node_registry(),
            self._m105_transport_registry(),
            policy,
        )
        failures = []
        if result.output_trust_level != RemoteOutputTrustLevel.untrusted_remote_output:
            failures.append("remote output not marked untrusted")
        if result.metadata.get("foundation_only") is not True:
            failures.append("remote result missing foundation_only marker")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/remote_workers/results.py"],
        )

    def check_m105_api_routes_are_dry_run_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.api.app import app

        paths = {route.path for route in app.routes}
        failures = []
        required = {
            "/remote-workers/nodes/validate",
            "/remote-workers/transports/validate",
            "/remote-workers/policy/validate",
            "/remote-workers/jobs/validate",
            "/remote-workers/dry-run",
            "/remote-workers/status",
            "/remote-workers/tailnet/status",
            "/remote-workers/mesh/status",
        }
        for path in required:
            if path not in paths:
                failures.append(f"missing route {path}")
        for forbidden in [
            "/remote-workers/dispatch",
            "/remote-workers/execute",
            "/remote-workers/subagents/launch",
        ]:
            if forbidden in paths:
                failures.append(f"forbidden route present: {forbidden}")
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m105_docs_foundation_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        docs = [
            "docs/remote/REMOTE_WORKER_FOUNDATION.md",
            "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
            "docs/remote/REMOTE_JOB_ENVELOPE.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/decisions/remote_worker_tailnet_foundation.md",
            "docs/release_notes/v0_14_2.md",
        ]
        failures = []
        required_phrases = [
            "foundation-only",
            "No live networking",
            "No job dispatch",
            "No remote approvals",
        ]
        for rel_path in docs:
            path = self.root / rel_path
            if not path.exists():
                failures.append(f"missing {rel_path}")
                continue
            source = self._read(path)
            for phrase in required_phrases:
                if phrase not in source:
                    failures.append(f"{rel_path} missing phrase: {phrase}")
        return self._result(criterion, failures, docs)

    def check_m105_remote_tailnet_enable_flag_rejected(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy

        failures = []
        try:
            RemoteExecutionPolicy(
                policy_id="m105_tailnet_policy", remote_tailnet_enabled=True
            )
            failures.append("remote_tailnet_enabled=true was accepted")
        except ValueError as exc:
            if "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5" not in str(exc):
                failures.append(
                    "remote_tailnet_enabled=true failed without the expected reason code"
                )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"]
        )

    def check_m105_remote_personal_data_enable_flag_rejected(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import RemoteExecutionPolicy

        failures = []
        try:
            RemoteExecutionPolicy(
                policy_id="m105_personal_data_policy", remote_personal_data_enabled=True
            )
            failures.append("remote_personal_data_enabled=true was accepted")
        except ValueError as exc:
            if "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5" not in str(exc):
                failures.append(
                    "remote_personal_data_enabled=true failed without the expected reason code"
                )
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/remote_workers/policy.py"]
        )

    def check_m105_remote_worker_api_extra_fields_forbidden(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from pydantic import ValidationError as PydanticValidationError

        from ultimate_ai_agent.api.app import (
            RemotePolicyValidatePayload,
            sanitize_validation_errors,
        )

        failures = []
        try:
            RemotePolicyValidatePayload(
                policy={"policy_id": "m105_extra_policy"},
                **{"api_" + "key": "sk_" + "secret_" + "value_" + "123456"},
            )
            failures.append("extra top-level field did not produce validation failure")
            response_text = ""
        except PydanticValidationError as exc:
            response_text = json.dumps(sanitize_validation_errors(exc.errors()))
        if "api_key" in response_text or "sk_secret_value_123456" in response_text:
            failures.append(
                "extra top-level secret-like field leaked in validation response"
            )
        return self._result(criterion, failures, ["src/ultimate_ai_agent/api/app.py"])

    def check_m143_private_mesh_taxonomy_open_source_first(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            PrivateMeshProviderKind,
            RemoteTransportSelectionPolicy,
            default_remote_transport_registry,
        )

        policy = RemoteTransportSelectionPolicy(policy_id="m143_private_mesh_policy")
        registry = default_remote_transport_registry()
        failures = []
        for transport_id in [
            "headscale_planned",
            "generic_wireguard_planned",
            "tailscale_planned",
            "private_mesh_planned",
        ]:
            if registry.get_transport(transport_id) is None:
                failures.append(f"{transport_id} missing")
        if policy.prefer_open_source_first is not True:
            failures.append("open-source-first preference disabled")
        if policy.prefer_self_hosted_control_plane is not True:
            failures.append("self-hosted control-plane preference disabled")
        if policy.allow_proprietary_control_plane:
            failures.append("proprietary control plane allowed by default")
        if policy.allowed_provider_kinds[:2] != [
            PrivateMeshProviderKind.headscale_planned,
            PrivateMeshProviderKind.generic_wireguard_planned,
        ]:
            failures.append(
                "planned provider order does not evaluate Headscale and generic WireGuard first"
            )
        if (
            PrivateMeshProviderKind.tailscale_planned
            not in policy.blocked_provider_kinds
        ):
            failures.append("Tailscale planned provider was not blocked by default")
        docs = [
            "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
            "docs/remote/TAILNET_TRANSPORT_POLICY.md",
            "docs/decisions/ADR-open-source-first-private-networking.md",
            "docs/release_notes/v0_14_3.md",
        ]
        required_phrases = [
            "open-source-first",
            "Headscale",
            "generic WireGuard",
            "Tailscale",
            "planned",
        ]
        for rel_path in docs:
            source = self._read(self.root / rel_path)
            if not source:
                failures.append(f"missing {rel_path}")
                continue
            for phrase in required_phrases:
                if phrase.lower() not in source.lower():
                    failures.append(f"{rel_path} missing phrase: {phrase}")
        return self._result(
            criterion, failures, ["src/ultimate_ai_agent/core/remote_workers", *docs]
        )

    def check_m143_planned_mesh_transports_disabled(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        from ultimate_ai_agent.core.remote_workers import (
            default_remote_transport_registry,
        )

        registry = default_remote_transport_registry()
        failures = []
        for transport_id in [
            "private_mesh_planned",
            "headscale_planned",
            "generic_wireguard_planned",
            "tailscale_planned",
            "tailnet_planned",
            "lan_planned",
        ]:
            descriptor = registry.get_transport(transport_id)
            decision = registry.validate_transport(transport_id)
            if descriptor is None:
                failures.append(f"{transport_id} missing")
                continue
            if descriptor.enabled:
                failures.append(f"{transport_id} enabled")
            if descriptor.requires_network:
                failures.append(f"{transport_id} requires network")
            if descriptor.requires_credentials:
                failures.append(f"{transport_id} requires credentials")
            if descriptor.supports_dispatch:
                failures.append(f"{transport_id} supports dispatch")
            if decision.allowed:
                failures.append(f"{transport_id} allowed")
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/remote_workers/registry.py"],
        )

    def check_m143_no_live_mesh_integrations(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures = []
        forbidden_runtime_fragments = [
            "tailscaled",
            "tailscale.",
            "tailscale(",
            "headscale.",
            "headscale(",
            "wireguard.",
            "wireguard(",
            "wg ",
            "wg-quick",
            "serve",
            "funnel",
            "urlopen",
            "socket.",
            "dispatch_job(",
            "execute_remote(",
            "launch_subagent(",
        ]
        for path in (self.root / "src/ultimate_ai_agent/core/remote_workers").rglob(
            "*.py"
        ):
            source = self._read(path).lower()
            for fragment in forbidden_runtime_fragments:
                if fragment in source:
                    failures.append(
                        f"{path.relative_to(self.root)} contains live mesh fragment: {fragment}"
                    )
        docs_to_scan = [
            self.root / "docs/remote",
            self.root / "docs/decisions",
            self.root / "docs/release_notes",
            self.root / "docs/implementation",
        ]
        tracked = "\n".join(
            self._read(path)
            for path in (self.root / "src/ultimate_ai_agent/core/remote_workers").rglob(
                "*.py"
            )
        )
        for doc_root in docs_to_scan:
            tracked += "\n" + "\n".join(
                self._read(path) for path in self._context.rglob(doc_root, "*.md")
            )
        private_ip = re.compile(
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
        )
        if private_ip.search(tracked):
            failures.append("private IP literal found in runtime/docs")
        for forbidden_secretish in [
            "authkey-",
            "nodekey:",
            "tailnet name:",
            "oauth_client_secret",
        ]:
            if forbidden_secretish in tracked.lower():
                failures.append(
                    f"secret/private mesh config marker found: {forbidden_secretish}"
                )
        return self._result(
            criterion,
            failures,
            ["src/ultimate_ai_agent/core/remote_workers", "docs/remote"],
        )
