# UAA-P1-063 Governed Web Evidence v1

UAA-P1-063 adds a governed web evidence contract and API surface for UAA-backed
chat without granting unrestricted browsing.

Implemented:

- `GET /web-evidence/status` for operator-visible status and chatbot capability
  disclosure.
- `POST /web-evidence/request` for a governed evidence request envelope.
- `governed_network_read_only` API route side-effect classification.
- Host allowlist and enablement environment policy.
- HTTPS-only target validation, public-host validation, no query/fragment,
  bounded preview size, redaction, safe refs, and receipt refs.
- Tests for disabled state, host allowlist denial, redirect denial, redaction,
  receipt refs, API status, API fail-closed behavior, and manifest metadata.

Not added:

- unrestricted browsing
- browser automation
- request bodies
- caller-supplied request headers
- session state or credential material
- redirects
- downloads
- raw page/body or raw header storage
- hidden network access
- provider/model calls
- context injection or memory writes

The current API route fails closed unless governed web evidence is enabled and a
reviewed transport is available. This is intentional: it preserves the M72
read-only fetch discipline while establishing the UAA-owned guardrail and
operator-visible capability disclosure.
