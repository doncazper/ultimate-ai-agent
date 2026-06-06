# Foundation Gate Implementation Plan v0.84.0

v0.84.0 adds Foundation Gate coverage for M80 Network/Browser/OpenWebUI
Hardening Freeze.

Gate coverage:

- M80 freeze contracts exist and build a freeze-only, review-only,
  deterministic report.
- Accepted milestone refs for M71-M79 and checklist refs are required.
- Runtime expansion flags are denied and evaluator boundaries revalidate
  model-copy mutated fields.
- Static safety checks deny unrestricted network, browser action execution,
  OpenWebUI authority, plugin runtime behavior, shell execution, background
  worker, backend route, Control Center control, dependency, and production
  authority fragments.
- OpenAPI remains at 75 paths and forbidden network/browser/OpenWebUI/plugin
  execution routes are absent.
- M81 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill or plugin-related
package review requires a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

M80 does not install, enable, execute, import, or trust any skill package,
plugin package, OpenWebUI tool, browser tool, network tool, shell tool, or
external package runtime.
