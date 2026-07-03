# Unblock Production Authority Release Decision

Goal:
Run a no-go-first production authority release decision review without adding
runtime authority by implication.

Branch:
`codex/unblock-production-authority-release-decision`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- no public beta, public release, production distribution, signed installer,
  notarization, reliable unattended operation, broad autonomy, or production
  support claim unless an explicit accepted release milestone and manual signoff
  grant exactly that claim
- no provider/model calls
- no connector reads/writes/sends
- no browser automation
- no shell/subprocess execution
- no background worker/scheduler authority
- no credential/OAuth/account runtime
- no production data ingestion
- no raw prompt, response, provider payload, local path, credential, token,
  cookie, account, contact, raw log, or environment dump persistence

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/production_authority_release_decision_2026_07_03.md`
   - `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
   - `docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md`
   - `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
2. Collect current merged lane evidence and blockers.
3. Reconcile every visible release/public/product claim against current
   Python Core/API/CLI/test evidence.
4. Run the release gate bundle:
   - release-surface verifier
   - product truth verifier
   - documentation integrity verifier
   - security/redaction checks available in repo
   - focused backend/frontend/visual checks for public-facing surfaces
5. If any high-risk lane remains blocked, any claim is stale, or manual signoff
   is absent, update the blocker report and keep the lane blocked.
6. Only if every prerequisite is met, create a release decision packet naming:
   - exact allowed claim
   - evidence refs
   - manual signoff ref
   - rollback/freeze plan
   - support boundary
   - still-blocked authority.
7. Do not add runtime routes, provider calls, connector runtime, browser/shell
   authority, scheduler authority, credential/OAuth runtime, or production data
   handling in this PR.

Tests/verifiers:
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_product_truth.py`
- `.venv/bin/python scripts/verify_control_center_release_surface.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- focused product-language/security/redaction verifiers
- frontend/visual checks if public-facing surfaces or claims change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless the PR either keeps production authority blocked or
  contains explicit accepted release signoff for one exact claim
