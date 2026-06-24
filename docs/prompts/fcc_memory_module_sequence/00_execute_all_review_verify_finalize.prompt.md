# Execute FCC Memory Module Sequence

Repository: this repository.

Goal: finish the governed Memory module by executing prompts 01-14 in order,
reviewing after each phase, repairing failures, then running final verifiers,
cleaning the worktree, committing, creating a new annotated tag, and pushing.

Sequence:
1. Run the baseline audit.
2. Implement the Workbench read model.
3. Expand lifecycle receipts.
4. Add deterministic quality detection.
5. Add why-shown ranking.
6. Add read-only search/filter.
7. Add manual safe-summary candidate intake.
8. Bind real candidate refs from existing surfaces.
9. Add Today, Action, and Morning Briefing memory hints/proposals.
10. Add correction, merge, and supersede UI.
11. Polish Evidence Timeline memory answers.
12. Add Memory Health counts and ordering.
13. Add CLI parity.
14. Add tests, verifiers, docs, and board/product-truth updates.

Hard constraints:
- No raw prompt, response, provider payload, source body, raw path, credential,
  username, hostname, environment dump, or unredacted private content in durable
  code, docs, tests, logs, fixtures, or UI.
- No delete/export execution. `forget_request` is receipt/posture only.
- No context injection, connector writes, model/provider calls, embeddings,
  vector DB, semantic search, generic execution, public beta, public
  distribution, production readiness, or production authority.
- Product behavior must not live only in React state.
- Every mutating Memory route must be exact-scoped, idempotent, receipt-backed,
  safe-ref only, auditable, and rollback/safe-disable aware.

Final gates:
- Run all new Memory verifiers and tests.
- Run focused Memory/API/OpenAPI/manifest/frontend/docs/product-truth checks.
- Run `make frontend-check`, visual checks if snapshots change, and
  `git diff --check`.
- Review the diff for overclaims and raw-content leakage.
- Commit, create a new annotated audit tag, and push `main` plus the tag.
