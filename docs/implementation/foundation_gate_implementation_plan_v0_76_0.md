# Foundation Gate Implementation Plan v0.76.0

v0.76.0 adds Foundation Gate coverage for M72 Read-Only HTTP Fetch Tool,
Allowlisted.

Gate coverage includes:

- M72 Read-Only HTTP Fetch Tool
- M72 Read-Only HTTP Fetch Static Safety
- M72 Read-Only HTTP Fetch Route Boundary
- M72 Roadmap Currentness

The Gate checks that the M72 tool exists, is explicitly allowlisted in the tool
runtime adapter, uses a bounded redacted preview result contract, requires
redaction before return, denies missing or wildcard host allowlists, denies
non-HTTPS URLs, denies non-GET methods, denies credentials or cookies, denies
request body and request headers, denies query strings, denies raw response
body, denies raw headers, denies download or export, denies context injection,
denies memory write, denies model call, denies browser automation, denies tool
execution, denies backend route drift, denies Control Center control drift,
denies dependencies, and denies production authority.

The Gate uses fake transport only. It performs no live external network call.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.

M73 remains future.
