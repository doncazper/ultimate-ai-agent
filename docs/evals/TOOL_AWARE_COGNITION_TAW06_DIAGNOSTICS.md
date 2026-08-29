# TAW-06 Operator Diagnostics

Status: bounded founder-private-dogfood implementation evidence. This slice adds
one redacted Python Core read model plus CLI and protected API inspection. It
does not change ordinary-chat routing, model context, capability proposal,
approval, execution, provider/model behavior, connectors, external writes, or
authority. No Control Center surface is included in this slice.

## Shared Read Model

`build_tool_aware_operator_diagnostic` validates one exact TAW-04 shadow
decision, derives its existing inspection projection, and produces fixed
human-readable route, familiarity, approval, limitation, and next-step text.
The text is table-derived from the validated state rather than caller-supplied
content. All nine familiarity states and failed-closed awareness evidence have
explicit readable postures.

The diagnostic binds its output to the exact TAW-04 decision and inspection
fingerprints. Directly deserialized output is rederived during validation, so a
caller cannot substitute an approval or familiarity label and repair only the
outer fingerprint. Reason, selected-operation, and evidence refs are unique,
sorted, safe-ref-only, and bounded. Requests are capped at 262144 canonical JSON
bytes before nested decision validation. The protected API also enforces the
same 262144-byte raw-body ceiling in ASGI middleware before JSON decoding.
That middleware also scans JSON structure before decoding so excessive nesting
returns the shared redacted validation envelope instead of reaching the recursive
JSON decoder. Chunked request messages are aggregated into one bounded body and
one downstream replay message rather than retained individually. Its structured
413 contract is published in OpenAPI and retains the
accepted loopback CORS response headers. Request strings are capped at 512
characters, request nesting is capped at 32 levels, request traversal is capped
at 4096 nodes, and reason,
selected-operation, and material-effect collections are capped at 16 entries.
Raw operator/model content, provider payloads, and local paths are excluded.

Routine machinery remains absent from ordinary chat. The separate diagnostic
surface makes a material limitation, exact-approval requirement, authority
block, ambiguity, unavailable capability, or uncertain terminal outcome clear
when it is relevant. Non-material ambiguity preserves TAW-04 direct chat and
does not claim that clarification is required. Invalid awareness evidence is
reported separately from valid awareness whose capability evidence failed. It
reports an honest combined posture when a supported capability could mean
approval was not applicable or exact request-scoped approval was already
validated, because TAW-04 does not retain that distinction. It also defers
approval posture when typed input is incomplete or an exact
capability is unavailable, because exact approval may still be required after
input validation succeeds or availability is restored. Outcome-uncertain
diagnostics likewise defer approval posture rather than erase a required or
already-validated dimension. Authority-blocked diagnostics do not claim that
exactly one capability matched because the policy-first state can precede match
cardinality evaluation. It
does not treat readiness evidence, an approval ref, or the diagnostic itself as
authority.

## CLI And API Parity

The CLI reads one bounded `uaa-taw06-diagnostic-request.v1` JSON object from
standard input:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_tool_aware_diagnostics.py
PYTHONPATH=src .venv/bin/python scripts/inspect_tool_aware_diagnostics.py --json
```

Readable mode omits evidence machinery and shows Route, Familiarity, Approval,
Limitations, and Next. JSON mode emits the exact shared Python Core model used
by the API.

`POST /api/capability-diagnostics/preview` has stable operation ID
`preview_tool_aware_capability_diagnostics`. It is a protected local-sensitive,
validation-only route with no idempotency requirement because it performs no
mutation. OpenAPI and `/api/manifest` contain the same operation ID, side-effect
classification, auth posture, and route inventory entry. The endpoint accepts
only the typed safe-ref request and returns the shared read model directly.

## Compatibility And Authority Boundary

TAW-06's string enums use the Python 3.10-compatible `(str, Enum)` form. The
diagnostic records zero model calls, zero second ordinary-chat calls, and false
for provider calls, proposals, approvals, execution, connectors, external
writes, authority, production authority, and Control Center surface creation.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_aware_cognition_taw06.py
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw06.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
```

The focused suite covers all state mappings, required-approval disclosure,
safe-disable direct-chat preservation, invalid-awareness versus capability-
evidence failure diagnostics, non-material ambiguity preservation, bounded
evidence, label-substitution rejection, oversized request/string/collection
rejection with typed API errors, pre-decode oversized raw-body and extreme-
nesting rejection through the shared validation envelope, bounded aggregation
of chunked ASGI messages, loopback CORS on guard responses, deep unknown-object
rejection before recursive materialization, raw-field rejection, Python 3.10
enum shape, redacted CLI recursion failure, real CLI/API parity, human-readable
CLI output, protected-route
failure, stable operation ID, structured 413 and shared-envelope 422 OpenAPI
publication, API manifest,
and zero-authority invariants.

## Next Slice

TAW-07 remains responsible for development-corpus quality, latency, fault,
safe-disable, and adversarial hardening under the accepted sealed-holdout
boundary. TAW-06 does not complete Q22; TAW-07, TAW-08, founder-dogfood
acceptance, and later independent promotion remain required.
