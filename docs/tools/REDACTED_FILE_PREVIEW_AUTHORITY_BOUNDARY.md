# Redacted File Preview Authority Boundary

Status: active M33 documentation.
Current active baseline: **v0.39.0**

M33 file preview proposals are not authority. They are bounded, redacted,
non-authoritative inspection aids.

These refs cannot authorize arbitrary filesystem access:

- `approval_ref` alone.
- `approval_test_*`.
- task plan refs.
- context pack refs.
- memory refs.
- tool-intent refs.
- approval decision refs.
- model output refs.
- runtime output refs.
- OpenWebUI output refs.
- Control Center preview refs.
- arbitrary strings.

Truth/evidence refs may explain why a preview was requested, but they do not
authorize filesystem access or execution. Python Agent Core remains the
governed authority boundary. Redacted previews are not context injection and do
not create production authority.

v0.37.1 keeps evaluator revalidation at the authority boundary: pre-built or
model_copy-mutated requests still re-check safe roots, relative paths, disabled
raw/full-read flags, disabled mutation/context flags, and the allowlisted tool
ref before any redacted preview decision can be returned.

v0.38.0 implemented M34 Broader File Capability Review as
planning/docs/verifier work only. v0.39.0 implements M35 Safe File Review
Workflow Contracts. M36-M60 remain planned/provisional.
