# Redacted File Preview Authority Boundary

Status: active M33 documentation.
Current active baseline: **v0.37.0**

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

M34 remains planned/provisional.

