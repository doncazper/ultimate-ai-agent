# UI Copy And Action Language

Status: Active design governance for v0.18.2. Documentation only.

Control Center copy must distinguish display, preview, validation, simulation, approval, and execution. Copy must state when no action occurred.

Restricted action words in preview-only UI:

- Execute
- Run
- Send
- Deploy
- Enable
- Approve
- Commit
- Publish
- Install
- Connect
- Sync

These words may appear in documentation when describing forbidden controls or future capabilities, but they must not label a preview-only control unless a future reviewed milestone grants that authority.

Safer terms:

- Preview action
- View status
- Review details
- Validate
- Simulate
- Dry-run
- Check connection
- View summary

Copy rules:

- state when no action occurred.
- approval UI must not use dark patterns.
- disabled and planned features must not sound available.
- local backend connected must not imply authority.
- mock must be visible when mock fallback is used.
- non-authoritative data must say what it cannot prove.
- model output must not be described as truth authority.
