# Ultimate AI Agent Master Plan v0.5.6

Status: Active pre-coding baseline after Truth, Grounding, and Evidence Governance.

## v0.5.6 change log

v0.5.6 adds an explicit truth governance layer so factual answers are grounded in the right authority instead of model memory or unsupported generation.

Added:

```text
docs/canonical/59_truth_grounding_and_evidence_governance.md
docs/decisions/ADR-0049-use-truth-source-router-and-evidence-manifests.md
docs/schemas/truth_source_manifest.schema.json
docs/schemas/grounding_policy.schema.json
docs/schemas/evidence_manifest.schema.json
docs/schemas/claim_evidence.schema.json
docs/schemas/source_conflict_report.schema.json
docs/schemas/retrieval_log_entry.schema.json
docs/evals/citation_accuracy_eval.md
docs/evals/api_over_document_truth_eval.md
docs/evals/stale_source_refusal_eval.md
docs/evals/source_conflict_detection_eval.md
docs/evals/unsupported_claim_refusal_eval.md
```

## Rule

The model is never the source of truth. Truth lives in governed systems: canonical files, approved documents, source databases, APIs/provider adapters, Event Ledger records, World State snapshots, artifact records, knowledge bases, and human approvals.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
