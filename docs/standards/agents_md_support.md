# AGENTS.md Support Standard

`AGENTS.md` is a workspace guidance file for contributors and coding agents. It is documentation, not runtime configuration.

Rules:

- Runtime source must not load `AGENTS.md` to change request behavior.
- Runtime source must not load agent config or workspace config files at request time.
- API boundary changes must keep `/api/manifest`, OpenAPI verification, and Foundation Gate criteria aligned.
- Guidance updates must remain compatible with the active baseline and release notes.
