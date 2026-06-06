# M74 Browser Observe-Only Authority Boundary

M74 creates no browser authority. It is a local adapter contract over an
explicit injected observation, not a browser runtime integration.

The adapter cannot be used as authority for:

- browser automation.
- browser navigation.
- browser click.
- form fill.
- screenshot capture.
- raw DOM reads.
- authenticated browser profile access.
- cookies or credentials.
- download or upload.
- remote browser control.
- network interception.
- network call.
- model call.
- tool execution.
- memory write.
- context injection.
- backend route.
- Control Center control.
- dependency addition.
- production authority.

Approval refs, `approval_test_` refs, context refs, memory refs, tool-intent
refs, task-plan refs, runtime refs, OpenWebUI refs, Control Center refs, and
model-output refs are not browser observe authority. They may explain review
context only when separately validated as safe refs.

M75 remains future.
