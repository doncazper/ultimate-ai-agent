# Control Center Frontend Routes

Status: Active for v0.17.1 / M13 safety polish.

The frontend shell is served by Vite during local development. It is not mounted by the Python API and does not add OpenAPI paths.

Implemented frontend pages:

- `/`
- `/dashboard`
- `/runtime`
- `/foundation-gate`
- `/api-routes`
- `/approvals`
- `/remote-workers`
- `/mobile-planning`
- `/plugin-governance`
- `/action-preview`

Backend API endpoints consumed:

- `GET /health`
- `GET /version`
- `GET /api/manifest`
- `GET /control-center/manifest`
- `GET /control-center/dashboard`
- `GET /control-center/status`
- `GET /control-center/routes`
- `GET /control-center/approvals/summary`
- `GET /control-center/runtime-readiness/summary`
- `GET /control-center/foundation-gate/summary`
- `GET /runtime/readiness`
- `GET /runtime/capability-matrix`
- `POST /control-center/actions/preview`

Forbidden frontend route/API targets:

- Control Center action run endpoints.
- plugin enablement endpoints.
- runtime/model/provider invocation endpoints.
- remote worker dispatch endpoints.
- mobile sensor endpoints.
- native/mobile build endpoints.
- Chrome profile, Computer Use, iOS, macOS, keychain, signing, or App Store workflows.

v0.17.1 adds a static frontend safety verifier that rejects forbidden execute, plugin enablement, runtime execution, remote dispatch, and mobile sensor endpoint strings in frontend implementation files.

OpenAPI remains a backend contract. v0.17.1 changes only `info.version` to `0.17.1`; backend path count remains `74` with unique operation IDs.
