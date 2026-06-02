# Ultimate AI Agent Version

Current active baseline: **v0.18.0**

v0.18.0 implements M14: Web Control Center Local Backend Connection Stabilization. The local React/Vite shell now validates API base URLs as local-only, allows only relative, localhost, 127.0.0.1, and loopback IPv6 bases, rejects external absolute or secret-like API bases, and displays clear backend online, degraded, offline-safe, and mock fallback states. Mock fallback remains visibly non-authoritative. Backend OpenAPI path count remains unchanged at 74. This release does not add M15 Approval Queue + Receipt/Event Viewer UI, backend API routes, runtime execution, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, auth, credentials, cookies, analytics/SaaS SDKs, dependencies, native build workflows, or production Control Center authority.
