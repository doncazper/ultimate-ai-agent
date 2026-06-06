# Foundation Gate Implementation Plan v0.65.0

Current active baseline: **v0.65.0**

v0.65.0 implements Foundation Gate coverage for M61 Autonomy Mode Charter +
Authority Levels.

The Gate verifies that M61 defines Mode 0 through Mode 6, requires default mode
off, keeps capability toggles disabled by default and dry-run first, denies
approval_test_* authority, denies approval refs as autonomy authority, keeps
Mode 4 through Mode 6 future, blocks global autonomy, blocks backend routes,
and keeps M62 planned/provisional.

Skill Package Security Rule: All skills are untrusted packages by default.
They require a manifest, declared permissions, source/provenance metadata,
static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any runtime use.

v0.65.0 adds no global autonomy switch, production authority, execution, tool
execution, shell execution, network tools, browser automation, plugin
execution, mobile sensor access, remote execution, background worker,
autonomous session, memory writes, context injection, model/provider authority,
backend routes, Control Center controls, dependencies, M62 work, or production
authority.
