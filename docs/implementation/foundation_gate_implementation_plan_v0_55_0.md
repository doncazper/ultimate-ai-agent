# Foundation Gate Implementation Plan v0.55.0

v0.55.0 adds Foundation Gate coverage for M51 OpenWebUI Bridge Adapter Pilot.

All skills are untrusted packages by default. Coverage requires a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities as continuing Skill Package Security Rule language.

M51-specific Gate checks verify the adapter module exists, safe-summary-only
adapter requests pass, raw prompt/provider payload fields are denied,
approval_ref cannot authorize execution, static scans reject OpenWebUI runtime
or provider/tool/context/memory routes, and M52 remains future.
