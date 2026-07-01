# Public GitHub Readiness

Status: active public-facing portfolio/developer-preview readiness note
Baseline: v0.104.0 / 0.104.0
Scope: documentation-only readiness summary

This note explains what is ready for an external GitHub reviewer to inspect. It
does not publish the repository, create a release, grant distribution
authority, or claim public beta, public release, production readiness, broad
autonomy, connector writes, provider/model authority, unrestricted browsing,
browser execution, shell/subprocess authority, or production authority.

## Ready For Review

- Front-door portfolio docs: `README.md`, `docs/portfolio/CURRENT_STATUS.md`,
  `docs/portfolio/PRODUCT_NORTH_STAR.md`, `docs/portfolio/SCREENSHOTS.md`,
  `docs/portfolio/GOLDEN_PATH_DEMO.md`, and
  `docs/portfolio/CASE_STUDY.md`.
- Product-truth boundaries:
  `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`,
  `docs/control_center/PRODUCT_LANGUAGE_RULES.md`, and
  `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`.
- Verification entrypoints: `make verify`, `make frontend-check`,
  documentation integrity, product-truth, release-surface, visual-regression,
  operational-maturity, OpenAPI, and API manifest checks.

## Partial Or Blocked

- North-star screenshots are design targets, not implementation evidence.
- Portfolio screenshots are static sanitized visual-test snapshots and do not
  cover every visible route; the fixture-only `/crm` shell has no checked-in
  portfolio snapshot yet.
- Public-facing readiness remains a human review posture. It is not GitHub
  automation, publication authority, release authority, or production
  authority.
- Connector runtimes, CRM writes, sends, account sync, calendar writes,
  provider/model runtime authority, live web, browser execution, shell
  execution, hidden context injection, public beta, public distribution, and
  production authority remain blocked until separate scoped milestones add
  exact contracts, receipts, redaction, rollback or safe-disable posture, and
  verifier-backed evidence.

## Historical Note

M59 introduced deterministic local Public GitHub Readiness as review-only
contract work. That historical milestone remains an audit anchor; this document
is the current public-facing portfolio/developer-preview readiness summary.
