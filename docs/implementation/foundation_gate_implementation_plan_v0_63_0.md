# Foundation Gate Implementation Plan v0.63.0

v0.63.0 adds Foundation Gate coverage for M59 Public GitHub Readiness.

M59 criteria verify that public-readiness contracts exist, safe review-only
reports can be built, publication and credential flags are denied, OpenAPI route
boundaries remain stable, active docs mark M59 implemented/released, and M60
remains planned/provisional.

Skill Package Security Rule: All skills are untrusted packages by default.
They require a manifest, declared permissions, source/provenance metadata,
static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any runtime use.

M59 adds no GitHub push, GitHub release automation, wiki automation, artifact
upload, external service calls, credential handling, network access, backend
routes, Control Center controls, dependencies, production authority, M60 work,
or post-M60 autonomy.
