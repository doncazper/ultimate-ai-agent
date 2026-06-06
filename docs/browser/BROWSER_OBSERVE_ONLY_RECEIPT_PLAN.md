# M74 Browser Observe-Only Receipt Plan

M74 receipt planning records only safe metadata for a redacted observe-only
result.

Receipt metadata may include:

- safe output ref.
- safe request ref.
- safe target ref.
- safe URL ref.
- redaction summary ref.
- preview truncation status.
- reason codes.

Receipt metadata must not include:

- raw visible text.
- raw DOM.
- screenshot bytes.
- raw absolute URL.
- authenticated browser profile path.
- cookies or credentials.
- browser network payload.
- model/provider payload.
- memory write payload.
- context injection payload.
- tool execution payload.
- production authority claims.

Receipt plans remain no-authority records. They do not authorize browser
automation, backend routes, Control Center controls, memory writes, context
injection, tool execution, or production authority.

M75 remains future.
