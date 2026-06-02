# Ultimate AI Agent Master Plan v0.21.0

Status: Historical master plan for v0.21.0.

v0.21.0 implements M17 Evidence/File/Memory Viewer as a frontend-only CCC Web milestone.

Implemented scope:

- `/evidence` read-only evidence ref summary view.
- `/files` read-only file ref summary view.
- `/memory` read-only memory ref summary view.
- safe mock M17 knowledge data with evidence refs, file refs, memory refs, event refs, receipt refs, and redaction status.
- frontend tests proving M17 pages stay read-only and omit raw sensitive display.
- static frontend verifier coverage for raw M17 knowledge fields, credential-like fields, private path fragments, mutation routes, and required boundary copy.
- Foundation Gate criterion `m17_evidence_file_memory_viewer_safe`.
- M17 Control Center docs and release/version documentation.

Architecture boundary:

- Python Agent Core remains the brain.
- Evidence, file, and memory views are inspection surfaces only.
- Memory is recall, not authority.
- Canonical files and governed source systems outrank memory.
- CCC Web displays safe refs and redacted summaries only.
- v0.21.0 adds no backend API routes and keeps OpenAPI path count unchanged at `74`.

Not implemented in v0.21.0:

- file mutation, file browsing, or raw file display.
- memory mutation, memory provider implementation, embeddings, vector DB, pgvector, learn/forget/edit/delete controls, or raw memory display.
- raw evidence payload display.
- approval execution or approval grant/reject mutation.
- runtime execution or model/provider calls.
- remote execution or remote worker dispatch.
- mobile app, sensor API, OS permission integration, or native CCC implementation.
- plugin enablement, Chrome authenticated profile control, Computer Use automation, native build workflow, scanner runtime, Skill Factory, self-improvement, production persistence, or external action.
