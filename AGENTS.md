# Ultimate AI Agent Workspace Standards

Active baseline: v0.11.2.

This repository is the Ultimate AI Agent foundation workspace. Treat it as a contract-first Python core, not a production runtime integration layer.

## API Boundary

- `/api/manifest` is the typed metadata endpoint for the current API boundary.
- OpenAPI is the public route contract. Keep operation IDs stable, unique, and generated from method plus path.
- API routes may validate, preview, evaluate policy, or expose metadata. They must not perform production provider calls or autonomous external actions.
- Do not add runtime model calls.
- Do not add web fetching.
- Do not add provider SDK calls, browser automation, production persistence, scanner runtimes, or runtime agent config loading.

## Workspace

- Keep milestone changes small and release-gated.
- Prefer typed contracts, deterministic tests, and metadata-only verification before implementation work.
- Update `scripts/verify_openapi_contract.py` and the Foundation Gate when the API boundary changes.
- Keep generated OpenAPI JSON out of git unless a release explicitly asks for a versioned schema snapshot.
