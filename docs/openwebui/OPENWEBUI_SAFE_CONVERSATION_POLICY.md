# OpenWebUI Safe Conversation Policy

The M52 OpenWebUI Safe Conversation Surface policy allows safe-summary-only
conversation review data.

Allowed data:

- safe conversation refs
- safe session refs
- safe message refs
- safe redacted summaries
- safe event refs
- safe receipt refs
- safe metadata refs

Denied data and behavior:

- no raw prompt
- no raw provider payload
- no raw content
- no secret-like content
- no live OpenWebUI connection
- no OpenWebUI runtime call
- no provider call
- no model call
- no model authority
- no tool execution
- no memory write
- no context injection
- no backend route
- no dependency

The surface is review-only. It does not authorize OpenWebUI, model, provider,
tool, memory, context, or execution behavior.
