# Local Prototype No-Authority Boundary

Status: Active for v0.45.0 / M41 - Local Prototype Safety Freeze.

The local prototype is an inspection and review environment. It is not
production authority, execution authority, model authority, memory authority, or
filesystem authority. Mock/non-authoritative data is allowed only when visibly
labeled as local preview data.

The freeze preserves these boundaries:

- no raw file browsing
- no raw file export
- no full-file reads
- no arbitrary caller-selected roots
- no shell/subprocess
- no unrestricted network tools
- no provider/model calls as authority
- no background workers
- no mobile sensors
- no plugin enablement
- no production authority
- no unreviewed memory writes
- no automatic context injection
- no raw prompt/provider payload exposure
- no credentials/cookie handling
- no remote execution
- no browser automation execution

Approval refs are not authority. Approval refs, approval test refs, review
packet refs, context proposal refs, memory refs, model output refs, OpenWebUI
refs, Control Center preview refs, and tool intent refs may explain review
state only; they cannot authorize raw access, context injection, memory writes,
exports, execution, browser automation execution, plugin enablement, mobile
sensors, or production authority.

M42 remains future.
