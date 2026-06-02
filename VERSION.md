# Ultimate AI Agent Version

Current active baseline: **v0.18.1**

v0.18.1 hardens M14: Web Control Center Local Backend Connection Safety. The local React/Vite shell keeps API base URLs local-only, strengthens rejection of public/private non-loopback hosts, URL credentials, and broad secret-like query parameters, and makes the checking/unknown connection states explicit alongside live, degraded, offline-safe, and mock fallback states. Mock fallback remains visibly non-authoritative. Backend OpenAPI path count remains unchanged at 74. This release does not add M15 Approval Queue + Receipt/Event Viewer UI, backend API routes, runtime execution, model/provider calls, remote dispatch, mobile sensor access, plugin enablement, auth, credentials, cookies, analytics/SaaS SDKs, dependencies, native build workflows, or production Control Center authority.
