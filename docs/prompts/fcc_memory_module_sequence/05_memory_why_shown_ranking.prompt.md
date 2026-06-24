# Why Shown Ranking

Goal: improve L1/L2/L3 and Workbench ranking without embeddings.

Ranking inputs:
- Review state.
- Source quality.
- Evidence presence.
- Recency.
- Loop relevance.
- Unresolved Actions.
- Explicit tags.

Requirements:
- Every ranked item includes `why_shown_refs`.
- Ranking is deterministic and explainable.
- Ranking does not imply truth, context injection, or automatic recall.

Verification:
- Tests prove ordering and required why-shown refs.
- Frontend renders why-shown refs for Memory and bound surfaces.
