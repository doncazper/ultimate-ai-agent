# Checkpoint M129 - Connector Audit + Revocation Hardening

Status: implemented/released as a checkpoint milestone while the product
baseline remains v1.7.2.

M129 adds:

- connector audit + revocation hardening request, report, audit ledger entry,
  and revocation readiness record contracts
- exact binding to M128 connector write execution decisions and results
- safe audit summary and safe revocation summary receipt records
- denial paths for live connector runtime, account auth, network access,
  credentials, raw connector content, full content reads, connector
  write/send/delete/export behavior, attachment download, audit export,
  revocation execution, kill-switch execution, model calls, memory writes,
  context injection, backend routes, Control Center controls, dependencies, and
  production authority
- documentation, tests, Foundation Gate criteria, documentation-integrity
  checks, and `verify_all.py` coverage

M129 does not add live connector runtime, account auth, network access,
credential handling, raw connector content, full content reads, connector write
execution, connector send execution, connector delete execution, connector
export, connector bulk export, attachment download, audit export, revocation
execution, kill-switch execution, backend routes, Control Center controls,
dependencies, broad autonomy, beta release, or production authority.

M130 remains future.
