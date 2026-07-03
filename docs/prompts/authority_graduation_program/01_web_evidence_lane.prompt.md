# Authority Lane 01: Web Evidence

Goal: Graduate runtime web evidence from blocked/contract posture to real,
read-only public evidence through `WebAccessGateway`.

Allowed next promotion: Level 1 read-only / dry-run.

Scope:

- HTTPS GET only.
- Explicit allowlist or policy-approved public refs.
- Bounded redacted preview.
- Audit/request/evidence refs.
- CLI/repo-local inspection.
- No raw body/header persistence.

Still blocked:

- Browser observe/action.
- Auth, cookies, sessions.
- POST/PUT/PATCH/DELETE.
- Downloads/uploads.
- Connector reads/writes.
- Provider/model calls.
- Memory writes, context injection, action execution.

Promotion condition:

One real public page fetch can produce a redacted evidence receipt, and denied
URLs produce safe blocked receipts.

Tests/verifiers:

- WebAccessGateway tests.
- static web access guard tests.
- redaction/no raw body tests.
- API/OpenAPI tests if a route is added.
- CLI inspection test.

If blocked:

Record the missing adapter/policy/test/evidence and generate an unblock prompt
for the smallest missing WebAccessGateway component.
