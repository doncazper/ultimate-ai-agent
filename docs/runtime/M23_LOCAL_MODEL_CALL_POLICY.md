# M23 Local Model Call Policy

Status: Active M23 policy documentation for v0.27.0.

M23 permits one narrow local model call path.

## Endpoint Policy

Allowed endpoints:

- `http://localhost/...`
- `http://127.0.0.1/...`
- `http://[::1]/...`

Denied endpoints:

- HTTPS endpoints.
- public hosts.
- private LAN hosts.
- remote IPs.
- URL credentials.
- secret-like query strings such as token, key, password, credential, auth,
  authorization, access token, refresh token, admin token, session token, API
  key, or client secret.

## Prompt Policy

Only `m23_fixed_local_model_smoke_v1` is allowed.

The CLI must not accept arbitrary prompt flags, stdin prompt input, prompt-file
input, clipboard input, memory input, OpenWebUI transcript input, raw files, raw
memory contents, credentials, or user task content.

## Approval Policy

Actual execution requires:

- `--execute-local-call`.
- `dry_run=false`.
- a local approval ref.
- validation against the existing local approval authority.
- an approved decision with matched grant evidence.

Arbitrary approval strings are identifiers only and are not authority.

## Response Policy

Responses are capped, redacted, and treated as non-authoritative. Secret-like
responses are blocked. Raw responses are not stored. A response may be displayed
only as safe text/summary from the M23 contract.

## Receipt Policy

Every result must record:

- fixed prompt id.
- call performed flag.
- non-authoritative model output flag.
- no tools executed.
- no memory written.
- no files written.
- no provider call.
- no remote call.
- redaction status.

## Test And Gate Policy

Tests and Foundation Gate must use fake transport only. Release validation may
run dry-run CLI checks. Real manual local calls are optional operator actions
and are not production readiness evidence.

M23 does not authorize runtime activation, endpoint probes, production runtime
execution, OpenWebUI runtime behavior, Control Center execution controls, tool
execution, memory writes, file writes, remote execution, dependency changes, or
production authority.
