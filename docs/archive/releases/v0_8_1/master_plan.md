Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.8.1

Status: Active project baseline after Milestone M4.5 (Truth Source Router + Evidence Governance foundation).

## v0.8.1 change log

v0.8.1 implements M4.5 as deterministic contract infrastructure.

M4.5 Truth Source + Evidence Governance added:

```text
src/ultimate_ai_agent/core/truth/
tests/test_truth_source_manifest.py
tests/test_grounding_policy.py
tests/test_evidence_manifest.py
tests/test_claim_evidence.py
tests/test_truth_source_router.py
tests/test_source_conflicts.py
tests/test_stale_source_policy.py
tests/test_unsupported_claims.py
tests/test_truth_api_routes.py
tests/test_retrieval_log.py
```

Updated:

```text
README.md
VERSION.md
pyproject.toml
src/ultimate_ai_agent/__init__.py
src/ultimate_ai_agent/api/app.py
scripts/verify_current_baseline.py
scripts/verify_all.py
```

## Rule

The model is never the source of truth. Memory is recall only and cannot outrank canonical files, approved documents, APIs, databases, provider results, event ledger records, or world state snapshots. M4.5 routes only caller-supplied source manifests and validates evidence metadata; it never performs web fetches, provider calls, model calls, embeddings, database access, browser automation, or external tool execution.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
