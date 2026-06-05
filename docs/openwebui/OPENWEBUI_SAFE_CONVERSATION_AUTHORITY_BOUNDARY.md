# OpenWebUI Safe Conversation Authority Boundary

M52 keeps OpenWebUI as a shell and bridge. OpenWebUI is not the agent brain.
Agent Core remains authority for governance decisions.

Safe conversation surface records are not authority. Approval refs are
identifiers only and cannot authorize OpenWebUI runtime calls, provider calls,
model calls, model authority, tool execution, memory write, context injection,
backend routes, export, or production authority.

Model output is never truth. Runtime output is never truth. Memory is recall,
not authority. Context packs are not authority. Tool intents are not execution
authority. Task plans are not execution authority.

The surface must remain safe-summary-only and may expose no raw prompt, no raw
provider payload, no raw content, and no secret-like content.
