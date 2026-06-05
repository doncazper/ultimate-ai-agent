# Foundation Gate Implementation Plan v0.56.0

v0.56.0 adds Foundation Gate coverage for M52 OpenWebUI Safe Conversation
Surface.

All skills are untrusted packages by default. Coverage requires a manifest,
declared permissions, source/provenance metadata, static review, sandbox test execution,
Tool Broker permission mapping, Event Ledger logging, version pinning,
revocation/disable support, and human approval for high-risk capabilities as
continuing Skill Package Security Rule language.

M52-specific Gate checks verify the safe conversation surface module exists,
safe-summary-only conversation turns pass, raw prompt/provider payload fields
are denied, approval_ref cannot authorize execution, static scans reject
OpenWebUI conversation/runtime/provider/model/tool/context/memory routes, and
M53 remains future.
