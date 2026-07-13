from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart004Mixin:
    """Legacy checks from m13_frontend_no_sensitive_browser_apis through m18_local_runtime_manual_smoke_surface_safe."""
    def check_m13_frontend_no_sensitive_browser_apis(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        forbidden = [
            "localstorage",
            "sessionstorage",
            "document.cookie",
            "indexeddb",
            "cachestorage",
            "serviceworker",
            "navigator.credentials",
            "clipboard.write",
            "navigator.geolocation",
            "navigator.mediadevices",
            "notification.requestpermission",
            "pushmanager",
        ]
        failures = []
        for path in [*self._context.rglob(app_root, "*.ts"), *self._context.rglob(app_root, "*.tsx")]:
            if ".test." in path.name or "test" in path.parts:
                continue
            lowered = self._read(path).lower()
            rel = path.relative_to(self.root)
            failures.extend(
                f"{rel} forbidden browser API: {fragment}"
                for fragment in forbidden
                if fragment in lowered
            )
        return self._result(criterion, failures, ["apps/control-center/src"])

    def check_m13_control_center_frontend_safety_verifier_passes(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util

        script = self.root / "scripts/verify_control_center_frontend.py"
        failures = []
        if not script.exists():
            failures.append("scripts/verify_control_center_frontend.py missing")
            return self._result(
                criterion, failures, [str(script.relative_to(self.root))]
            )
        spec = importlib.util.spec_from_file_location(
            "verify_control_center_frontend", script
        )
        if spec is None or spec.loader is None:
            failures.append("could not load frontend safety verifier")
            return self._result(
                criterion, failures, [str(script.relative_to(self.root))]
            )
        failures.extend(_control_center_frontend_verifier_failures(self))
        return self._result(
            criterion,
            failures,
            ["scripts/verify_control_center_frontend.py", "apps/control-center"],
        )

    def check_m13_frontend_ci_covers_local_checks(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util

        script = self.root / "scripts/verify_control_center_browser_smoke_readiness.py"
        failures = []
        if not script.exists():
            failures.append(
                "scripts/verify_control_center_browser_smoke_readiness.py missing"
            )
        else:
            spec = importlib.util.spec_from_file_location(
                "verify_control_center_browser_smoke_readiness_ci", script
            )
            if spec is None or spec.loader is None:
                failures.append("could not load browser smoke readiness verifier")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                failures.extend(module._ci_failures(self.root))
        return self._result(
            criterion,
            failures,
            [
                ".github/workflows/ci.yml",
                "scripts/verification/ci_command_manifest.py",
                "Makefile",
            ],
        )

    def check_m13_browser_smoke_readiness_manual_local_only(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        doc = self.root / "docs/control_center/LOCAL_BROWSER_SMOKE.md"
        text = self._read(doc).lower()
        required = [
            "manual local browser smoke",
            "local-only",
            "localhost",
            "127.0.0.1",
            "::1",
            "no authenticated browser profile",
            "no chrome authenticated profile control",
            "no computer use",
            "no external sites",
            "no production backend",
            "no screenshots with secrets",
            "preview-only",
            "non-authoritative",
        ]
        failures = [
            f"browser smoke doc missing safety fragment: {fragment}"
            for fragment in required
            if fragment not in text
        ]
        return self._result(
            criterion, failures, ["docs/control_center/LOCAL_BROWSER_SMOKE.md"]
        )

    def check_m13_browser_smoke_readiness_verifier_passes(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util

        script = self.root / "scripts/verify_control_center_browser_smoke_readiness.py"
        failures = []
        if not script.exists():
            failures.append(
                "scripts/verify_control_center_browser_smoke_readiness.py missing"
            )
            return self._result(
                criterion, failures, [str(script.relative_to(self.root))]
            )
        spec = importlib.util.spec_from_file_location(
            "verify_control_center_browser_smoke_readiness", script
        )
        if spec is None or spec.loader is None:
            failures.append("could not load browser smoke readiness verifier")
            return self._result(
                criterion, failures, [str(script.relative_to(self.root))]
            )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        failures.extend(module.verify(self.root))
        return self._result(
            criterion,
            failures,
            [
                "scripts/verify_control_center_browser_smoke_readiness.py",
                "docs/control_center/LOCAL_BROWSER_SMOKE.md",
            ],
        )

    def check_m14_local_backend_api_base_policy(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        app_root = self.root / "apps/control-center/src"
        base_url = self._read(app_root / "api/baseUrl.ts")
        client = self._read(app_root / "api/client.ts")
        tests = self._read(app_root / "api/baseUrl.test.ts")
        vite_config = self._read(self.root / "apps/control-center/vite.config.ts")
        failures = []
        required_policy_fragments = [
            "resolveApiBaseUrl",
            "localhost",
            "127.0.0.1",
            "::1",
            "EXTERNAL_API_BASE_URL_BLOCKED",
            "SECRET_LIKE_API_BASE_URL_REJECTED",
            "containsSecretLike",
        ]
        for fragment in required_policy_fragments:
            if fragment not in base_url:
                failures.append(f"API base policy missing fragment: {fragment}")
        external_fixture = "https" + "://api.example.com"
        for fragment in [
            external_fixture,
            "http://8.8.8.8:8000",
            "http://10.0.0.5:8000",
            "http://172.16.0.2:8000",
            "http://192.168.1.10:8000",
            "supersecretvalue123",
            '"tok" + "en"',
            "api_key",
            "credential",
        ]:
            if fragment not in tests:
                failures.append(
                    f"API base policy tests missing unsafe case: {fragment}"
                )
        if "resolveApiBaseUrl" not in client:
            failures.append("frontend client does not use resolveApiBaseUrl")
        local_proxy_target = 'target: "' + "http" + '://127.0.0.1:8000"'
        if local_proxy_target not in vite_config:
            failures.append("Vite dev proxy is not pinned to local backend loopback")
        required_proxy_routes = [
            '"/control-center"',
            '"/runtime/readiness"',
            '"/runtime/capability-matrix"',
            '"/runtime/smoke-reports"',
        ]
        for route in required_proxy_routes:
            if route not in vite_config:
                failures.append(
                    f"Vite dev proxy does not cover local backend route: {route}"
                )
        if re.search(r'["\']/runtime["\']\s*:', vite_config):
            failures.append(
                "Vite dev proxy must not proxy broad /runtime frontend route space"
            )
        if "changeOrigin: true" in vite_config:
            failures.append("Vite dev proxy rewrites origin")
        local_auth_fragments = [
            "withLocalApiAuthHeaders",
            "localApiBearerForRequest",
            "VITE_UAA_LOCAL_API_BEARER",
            "Authorization: `Bearer ${bearer}`",
        ]
        for fragment in local_auth_fragments:
            if fragment not in client:
                failures.append(
                    f"frontend client missing local auth posture fragment: {fragment}"
                )
        forbidden_client_fragments = [
            "api_key",
            "document.cookie",
            "localStorage",
            "sessionStorage",
        ]
        failures.extend(
            f"frontend client contains forbidden connection fragment: {fragment}"
            for fragment in forbidden_client_fragments
            if fragment in client
        )
        return self._result(
            criterion,
            failures,
            [
                "apps/control-center/src/api/baseUrl.ts",
                "apps/control-center/src/api/client.ts",
                "apps/control-center/vite.config.ts",
            ],
        )

    def check_m14_connection_states_visible_and_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        app = self._read(self.root / "apps/control-center/src/App.tsx")
        types = self._read(self.root / "apps/control-center/src/api/types.ts")
        client = self._read(self.root / "apps/control-center/src/api/client.ts")
        data_state = self._read(
            self.root / "apps/control-center/src/components/DataState.tsx"
        )
        mock = self._read(
            self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        )
        tests = self._read(self.root / "apps/control-center/src/App.test.tsx")
        combined = "\n".join([app, types, client, data_state, mock, tests])
        failures = []
        required_fragments = [
            "BackendConnectionSummary",
            "unknown",
            "checking",
            "online",
            "degraded",
            "offline",
            "mock_fallback",
            "Backend state unknown",
            "Checking backend connection",
            "Backend online",
            "Backend degraded",
            "Mock fallback active",
            "Checking local backend connection state",
            "non-authoritative mock fallback",
            "API base:",
            "usingMockData",
            "LOCAL_BACKEND_DEGRADED",
            "PARTIAL_MOCK_FALLBACK",
            "MOCK_DATA_ONLY",
        ]
        for fragment in required_fragments:
            if fragment not in combined:
                failures.append(f"connection state fragment missing: {fragment}")
        forbidden_fragments = [
            "production_authority: true",
            "productionControlCenter: true",
            "approval_grants_created: true",
            "document.cookie",
        ]
        failures.extend(
            f"unsafe connection state fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in combined
        )
        return self._result(
            criterion,
            failures,
            [
                "apps/control-center/src/App.tsx",
                "apps/control-center/src/api/client.ts",
                "apps/control-center/src/api/types.ts",
                "apps/control-center/src/components/DataState.tsx",
                "apps/control-center/src/mocks/controlCenterData.ts",
            ],
        )

    def check_m14_backend_api_contract_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        result = self.check_m13_backend_api_contract_unchanged(criterion)
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.manifest import iter_api_route_items

        paths = {route.path for route in iter_api_route_items(app)}
        forbidden = [
            "/control-center/approvals",
            "/control-center/approval-queue",
            "/control-center/events",
            "/control-center/receipts",
            "/control-center/actions/execute",
            "/control-center/runtime/connect",
        ]
        failures = list(result.failures)
        failures.extend(
            f"out-of-scope M14 route present: {path}"
            for path in forbidden
            if path in paths
        )
        return self._result(
            criterion,
            failures,
            [
                "src/ultimate_ai_agent/api/app.py",
                "src/ultimate_ai_agent/api/manifest.py",
            ],
        )

    def check_m15_approval_receipt_event_ui_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util

        required_files = [
            "apps/control-center/src/components/ApprovalQueuePanel.tsx",
            "apps/control-center/src/components/ReceiptViewerPanel.tsx",
            "apps/control-center/src/components/EventViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
        ]
        implementation_files = [
            "apps/control-center/src/components/ApprovalQueuePanel.tsx",
            "apps/control-center/src/components/ReceiptViewerPanel.tsx",
            "apps/control-center/src/components/EventViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [
            f"missing M15 frontend file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        components = "\n".join(
            self._read(self.root / path)
            for path in implementation_files
            if (self.root / path).exists()
        )
        lowered = components.lower()

        required_fragments = [
            "ApprovalQueuePanel",
            "ReceiptViewerPanel",
            "EventViewerPanel",
            'path: "/approvals"',
            'path: "/receipts"',
            'path: "/events"',
            "Approval Queue",
            "Receipt Viewer",
            "Event Viewer",
            "read-only",
            "preview-only",
            "Approval Authority handles final decision",
            "This UI cannot grant, deny, execute, or bypass approvals",
            "Approval refs are identifiers only and never authority",
            "Python Agent Core remains the only approval authority",
            "Receipt detail is redacted summary metadata only",
            "Event detail is redacted summary metadata only",
            "redacted_summary_only",
            "MOCK_DATA_ONLY",
            "nonAuthoritative",
            "approvalQueue",
            "receipts",
            "events",
        ]
        failures.extend(
            f"M15 UI missing required fragment: {fragment}"
            for fragment in required_fragments
            if fragment not in components
        )

        forbidden_fragments = [
            "/approvals/approve",
            "/approvals/deny",
            "/control-center/approvals/execute",
            "/control-center/approvals/approve",
            "/control-center/approvals/deny",
            "/receipts/delete",
            "/events/raw",
            "/memory/raw",
            "/files/raw",
            "<button>approve</button>",
            "<button>deny</button>",
            "<button>execute</button>",
            "<button>run</button>",
            "<button>send</button>",
            "<button>deploy</button>",
            "<button>enable</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawfilebody",
            "rawmemorycontent",
            "raweventpayload",
            "rawreceiptpayload",
            "credentialref",
            "credentialhandle",
        ]
        failures.extend(
            f"M15 UI contains forbidden fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in lowered
        )

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location(
                "verify_control_center_frontend", script
            )
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                failures.extend(_control_center_frontend_verifier_failures(self))

        return self._result(criterion, failures, required_files)

    def check_m16_event_timeline_trace_viewer_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/components/EventTimelineTracePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "docs/control_center/EVENT_TIMELINE_UI.md",
            "docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md",
            "docs/control_center/TRACE_REDACTION_POLICY.md",
        ]
        implementation_files = [
            "apps/control-center/src/components/EventTimelineTracePanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [
            f"missing M16 timeline trace file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        components = "\n".join(
            self._read(self.root / path)
            for path in implementation_files
            if (self.root / path).exists()
        )
        lowered = components.lower().replace(" ", "")

        required_fragments = [
            "EventTimelineTracePanel",
            'path: "/events/timeline"',
            "Event Timeline",
            "M16 trace surface",
            "Timeline and trace views are read-only",
            "Trace detail is redacted summary metadata only",
            "No trace export or external telemetry is available",
            "mock_run_ref_001",
            "mock_correlation_ref_001",
            "mock_event_ref_001",
            "mock_receipt_ref_001",
            "mock_evidence_ref_gate_001",
            "redacted_summary_only",
            "m16Trace",
            "traceRelations",
            "foundationGateEvidence",
            "NO_EXTERNAL_EXPORT",
            "external_export_allowed: false",
        ]
        failures.extend(
            f"M16 UI missing required fragment: {fragment}"
            for fragment in required_fragments
            if fragment not in components
        )

        forbidden_fragments = [
            "/events/timeline/raw",
            "/events/timeline/export",
            "/traces/raw",
            "/traces/export",
            "/runs/execute",
            "/control-center/traces/raw",
            "/control-center/traces/export",
            "<button>approve</button>",
            "<button>deny</button>",
            "<button>execute</button>",
            "<button>run</button>",
            "<button>send</button>",
            "<button>deploy</button>",
            "<button>enable</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawfilecontent",
            "rawmemorycontent",
            "raweventpayload",
            "rawreceiptpayload",
            "rawproviderpayload",
            "credentialref",
            "credentialhandle",
        ]
        failures.extend(
            f"M16 UI contains forbidden fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in lowered
        )

        docs_text = "\n".join(
            self._read(self.root / path)
            for path in required_files
            if path.startswith("docs/")
        )
        doc_fragments = [
            "read-only",
            "summary-only",
            "safe refs",
            "No backend route is added",
            "no raw prompts",
            "no raw secrets",
            "no raw file contents",
            "no raw memory contents",
            "no raw credentials",
            "no raw provider payloads",
            "no execution controls",
            "no external telemetry export",
        ]
        failures.extend(
            f"M16 docs missing required fragment: {fragment}"
            for fragment in doc_fragments
            if fragment not in docs_text
        )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M16 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m16_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location(
                "verify_control_center_frontend", script
            )
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                failures.extend(_control_center_frontend_verifier_failures(self))

        return self._result(criterion, failures, required_files)

    def check_m17_evidence_file_memory_viewer_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "docs/control_center/EVIDENCE_VIEWER.md",
            "docs/control_center/FILE_REFERENCE_VIEWER.md",
            "docs/control_center/MEMORY_VIEWER.md",
            "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
        ]
        implementation_files = [
            "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        failures = [
            f"missing M17 evidence/file/memory file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        components = "\n".join(
            self._read(self.root / path)
            for path in implementation_files
            if (self.root / path).exists()
        )
        lowered = components.lower().replace(" ", "")

        required_fragments = [
            "EvidenceViewerPanel",
            "FileReferenceViewerPanel",
            "MemoryViewerPanel",
            'path: "/evidence"',
            'path: "/files"',
            'path: "/memory"',
            "Evidence Viewer",
            "File Reference Viewer",
            "Memory Viewer",
            "M17 knowledge surface",
            "Evidence views are read-only",
            "File ref views are read-only",
            "Memory is recall, not authority",
            "Canonical files and governed source systems outrank memory",
            "mock_evidence_ref_001",
            "mock_file_ref_001",
            "mock_memory_ref_001",
            "redacted_summary_only",
            "NO_RAW_CONTENT",
            "MEMORY_NOT_AUTHORITY",
            "No filesystem browsing is available",
            "File writes are not available from this UI",
            "Memory detail is redacted summary metadata only",
            "Evidence detail is redacted summary metadata only",
            "File ref detail is redacted summary metadata only",
        ]
        failures.extend(
            f"M17 UI missing required fragment: {fragment}"
            for fragment in required_fragments
            if fragment not in components
        )

        forbidden_fragments = [
            "/evidence/raw",
            "/evidence/payload",
            "/files/content",
            "/files/write",
            "/files/delete",
            "/filesystem/browse",
            "/memory/raw",
            "/memory/content",
            "/memory/write",
            "/memory/delete",
            "/memory/learn",
            "/memory/forget",
            "<button>editmemory</button>",
            "<button>deletememory</button>",
            "<button>savememory</button>",
            "<button>learnthis</button>",
            "<button>forgetthis</button>",
            "<button>openfile</button>",
            "<button>deletefile</button>",
            "<button>writefile</button>",
            "<button>browsefilesystem</button>",
            "<button>revealraw</button>",
            "<button>showraw</button>",
            "<button>execute</button>",
            "<button>run</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawfilecontent",
            "rawmemorycontent",
            "rawevidencepayload",
            "rawproviderpayload",
            "authoritativetruth",
            "credentialref",
            "credentialhandle",
            "/users/",
            "/home/",
        ]
        failures.extend(
            f"M17 UI contains forbidden fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in lowered
        )

        docs_text = "\n".join(
            self._read(self.root / path)
            for path in required_files
            if path.startswith("docs/")
        )
        doc_fragments = [
            "read-only",
            "summary-only",
            "redacted",
            "safe refs",
            "No backend route is added",
            "memory is recall, not authority",
            "canonical files and governed source systems outrank memory",
            "no raw prompts",
            "no raw secrets",
            "no raw file contents",
            "no raw memory contents",
            "no raw evidence payloads",
            "no raw credentials",
            "no raw provider payloads",
            "no file mutation",
            "no memory mutation",
            "no filesystem browsing",
            "no execution controls",
        ]
        failures.extend(
            f"M17 docs missing required fragment: {fragment}"
            for fragment in doc_fragments
            if fragment not in docs_text
        )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M17 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m17_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location(
                "verify_control_center_frontend", script
            )
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                failures.extend(_control_center_frontend_verifier_failures(self))

        return self._result(criterion, failures, required_files)

    def check_m17_evidence_file_memory_viewer_hardening_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/App.test.tsx",
            "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "tests/test_control_center_frontend_safety_verifier.py",
            "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_21_1.md",
            "docs/release_notes/v0_21_1.md",
        ]
        failures = [
            f"missing M17 hardening file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        mock_text = self._read(
            self.root / "apps/control-center/src/mocks/controlCenterData.ts"
        )
        panel_text = self._read(
            self.root
            / "apps/control-center/src/components/EvidenceFileMemoryViewerPanel.tsx"
        )
        test_text = self._read(self.root / "apps/control-center/src/App.test.tsx")
        verifier_text = self._read(
            self.root / "scripts/verify_control_center_frontend.py"
        )
        docs_text = "\n".join(
            self._read(self.root / path)
            for path in [
                "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
                "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
                "docs/implementation/foundation_gate_implementation_plan_v0_21_1.md",
                "docs/release_notes/v0_21_1.md",
            ]
        )

        mock_fragments = [
            "mock_evidence_ref_002",
            "mock_file_ref_002",
            "mock_memory_ref_002",
            "memory_conflict_review_summary",
            "redacted-evidence-summary.json",
            "receipt_context",
            "redacted_summary_only",
            "MOCK_DATA_ONLY",
            "NO_RAW_CONTENT",
            "MEMORY_NOT_AUTHORITY",
        ]
        failures.extend(
            f"M17 hardening mock fixture missing fragment: {fragment}"
            for fragment in mock_fragments
            if fragment not in mock_text
        )

        selected_state_fragments = [
            'aria-current={selected ? "true" : undefined}',
            "evidence summary",
            "file ref summary",
            "memory summary",
        ]
        failures.extend(
            f"M17 hardening selected-state UI missing fragment: {fragment}"
            for fragment in selected_state_fragments
            if fragment not in panel_text
        )

        test_fragments = [
            "keeps alternate M17 metadata selection read-only and redacted",
            "mock_evidence_ref_002",
            "mock_file_ref_002",
            "mock_memory_ref_002",
            "aria-current",
            "redacted_summary_only",
        ]
        failures.extend(
            f"M17 hardening frontend test missing fragment: {fragment}"
            for fragment in test_fragments
            if fragment not in test_text
        )

        verifier_fragments = [
            "M17_HARDENING_MOCK_MARKERS",
            "M17_HARDENING_SELECTED_STATE_MARKERS",
            "M17 hardening mock marker missing",
            "M17 hardening selected-state marker missing",
        ]
        failures.extend(
            f"M17 hardening verifier missing fragment: {fragment}"
            for fragment in verifier_fragments
            if fragment not in verifier_text
        )

        doc_fragments = [
            "v0.21.1",
            "hardening",
            "read-only",
            "redacted summary-only",
            "visibly mock",
            "non-authoritative",
            "OpenAPI path count remains `74`",
            "no backend API route",
            "no raw file",
            "no raw memory",
            "no raw evidence",
            "no file mutation",
            "no memory mutation",
            "browser smoke",
        ]
        failures.extend(
            f"M17 hardening docs missing fragment: {fragment}"
            for fragment in doc_fragments
            if fragment not in docs_text
        )

        forbidden_fragments = [
            "/evidence/raw",
            "/evidence/payload",
            "/files/content",
            "/files/write",
            "/files/delete",
            "/filesystem/browse",
            "/memory/raw",
            "/memory/content",
            "/memory/write",
            "/memory/delete",
            "/memory/learn",
            "/memory/forget",
            "rawEvidencePayload",
            "rawFileContent",
            "rawMemoryContent",
            "credentialRef",
            "/Users/",
            "/home/",
        ]
        combined = "\n".join([mock_text, panel_text])
        failures.extend(
            f"M17 hardening implementation contains forbidden fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in combined
        )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(
                f"M17 hardening OpenAPI route guard could not generate schema: {exc}"
            )
        else:
            failures.extend(m17_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location(
                "verify_control_center_frontend", script
            )
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                failures.extend(_control_center_frontend_verifier_failures(self))

        return self._result(criterion, failures, required_files)

    def check_m18_local_runtime_manual_smoke_surface_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        import importlib.util
        from ultimate_ai_agent.api.app import app

        required_files = [
            "apps/control-center/src/App.test.tsx",
            "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
            "scripts/verify_control_center_frontend.py",
            "tests/test_control_center_frontend_safety_verifier.py",
            "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
            "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
            "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
            "docs/implementation/foundation_gate_implementation_plan_v0_22_0.md",
            "docs/release_notes/v0_22_0.md",
        ]
        failures = [
            f"missing M18 local runtime/manual smoke file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        implementation_files = [
            "apps/control-center/src/App.test.tsx",
            "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        runtime_implementation_files = [
            "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
            "apps/control-center/src/routes.tsx",
            "apps/control-center/src/api/endpoints.ts",
            "apps/control-center/src/api/types.ts",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        implementation_text = "\n".join(
            self._read(self.root / path)
            for path in implementation_files
            if (self.root / path).exists()
        )
        runtime_implementation_text = "\n".join(
            self._read(self.root / path)
            for path in runtime_implementation_files
            if (self.root / path).exists()
        )
        lowered = runtime_implementation_text.lower().replace(" ", "")

        required_fragments = [
            "LocalRuntimeStatusPanel",
            "ManualSmokeControlSurfacePanel",
            'path: "/runtime/local"',
            'path: "/runtime/manual-smoke"',
            'runtimeSmokeReportValidate: "/runtime/smoke-reports/validate"',
            "isRuntimeValidationEndpoint",
            "M18 local runtime surface",
            "Local runtime status is backend-owned",
            "Exact approved utility command execution is visible through RuntimeGateway receipts",
            "this UI does not start runtimes or grant arbitrary command",
            "production runtime readiness is not claimed",
            "Manual smoke reports are safe summaries",
            "Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated",
            "m18Runtime",
            "mock_manual_smoke_report_ref_001",
            "runtime_readiness_report",
            "manual_loopback_smoke",
            "fixed_prompt_hash_mock_001",
            "responsePreviewShown: false",
            "modelOutputAuthoritative: false",
            "NO_RUNTIME_EXECUTION",
            "VALIDATION_ONLY",
            "redacted_summary_only",
        ]
        failures.extend(
            f"M18 UI missing required fragment: {fragment}"
            for fragment in required_fragments
            if fragment not in implementation_text
        )

        forbidden_fragments = [
            "/runtime/smoke-reports/execute",
            "/runtime/local/execute",
            "/runtime/local/run",
            "/runtime/local/start",
            "/runtime/local/stop",
            "/runtime/local/connect",
            "/runtime/manual-smoke/execute",
            "/runtime/manual-smoke/run",
            "/model-runtime/local/smoke/execute",
            "<button>execute</button>",
            "<button>run</button>",
            "<button>runsmoke</button>",
            "<button>executesmoke</button>",
            "<button>startruntime</button>",
            "<button>stopruntime</button>",
            "<button>connectruntime</button>",
            "<button>callmodel</button>",
            "localstorage",
            "sessionstorage",
            "document.cookie",
            'type="password"',
            'name="apikey"',
            'name="token"',
            "rawpromptbody",
            "rawresponsebody",
            "rawtranscript",
            "rawproviderpayload",
            "credentialref",
            "credentialhandle",
            "apikey",
            "authtoken",
        ]
        failures.extend(
            f"M18 implementation contains forbidden fragment: {fragment}"
            for fragment in forbidden_fragments
            if fragment in lowered
        )

        docs_text = "\n".join(
            self._read(self.root / path)
            for path in [
                "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
                "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
                "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
                "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
                "docs/control_center/FRONTEND_SAFETY_POLICY.md",
                "docs/implementation/foundation_gate_implementation_plan_v0_22_0.md",
                "docs/release_notes/v0_22_0.md",
            ]
        )
        doc_fragments = [
            "v0.22.0",
            "M18",
            "read-only",
            "validation-only",
            "No backend route is added",
            "OpenAPI path count remains `74`",
            "no runtime execution",
            "no model/provider calls",
            "no manual smoke execution",
            "no raw smoke report",
            "no raw prompts",
            "no raw response bodies",
            "no credentials",
            "visibly mock",
            "non-authoritative",
        ]
        failures.extend(
            f"M18 docs missing required fragment: {fragment}"
            for fragment in doc_fragments
            if fragment not in docs_text
        )

        try:
            openapi_paths = self._openapi_paths()
        except Exception as exc:
            failures.append(f"M18 OpenAPI route guard could not generate schema: {exc}")
        else:
            failures.extend(m18_openapi_route_failures(openapi_paths))

        script = self.root / "scripts/verify_control_center_frontend.py"
        if script.exists():
            spec = importlib.util.spec_from_file_location(
                "verify_control_center_frontend", script
            )
            if spec is None or spec.loader is None:
                failures.append("could not load frontend safety verifier")
            else:
                failures.extend(_control_center_frontend_verifier_failures(self))

        return self._result(criterion, failures, required_files)
