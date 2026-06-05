# OpenWebUI Bridge Adapter Policy

The M51 adapter policy allows only local deterministic safe-summary adaptation
for future shell display. The policy requires safe-summary-only input and
output, Agent Core authority, and no side effects.

Denied by policy:

- no raw prompt exposure.
- no raw provider payload exposure.
- no raw content.
- no live OpenWebUI connection.
- no OpenWebUI runtime call.
- no provider call.
- no model authority.
- no tool execution.
- no memory write.
- no context injection.
- no approval_ref authority.
- no backend route.

M52 remains future.

