# Foundation Gate Implementation Plan v0.57.0

v0.57.0 adds Foundation Gate coverage for M53 Controlled Tool Expansion Review.

All skills are untrusted packages by default. Coverage requires a manifest,
declared permissions, source/provenance metadata, static review, sandbox test execution,
Tool Broker permission mapping, Event Ledger logging, version pinning,
revocation/disable support, and human approval for high-risk capabilities as
continuing Skill Package Security Rule language.

M53-specific Gate checks verify the controlled tool expansion review module
exists, safe metadata review candidates are review-ready only, effectful
candidate categories require a future milestone, unknown candidates are denied,
approval_ref cannot authorize execution or enablement, policy flags cannot
enable runtime behavior, static scans reject tool expansion/runtime route
fragments, OpenAPI stays at the accepted route boundary, and M54 remains future.
