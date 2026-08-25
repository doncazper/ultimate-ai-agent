# Founder Private-Dogfood Direction Acceptance

Status: founder accepted for private dogfood; independent promotion pending.

Ledger: `docs/product/private_dogfood_direction_acceptance_v1.json`

Verifier: `scripts/verify_private_dogfood_direction_acceptance.py`

## Decision

On 2026-08-25, the founder accepted the displayed Q25 Social and Q26 Finance
surface direction as good enough to begin private dogfooding. The accepted
baseline is the render inventory at
`git-sha:fd1152d209fb0871873d74147bcbf391a64474a3`. Real-use feedback is
expected to change copy, spacing, density, responsive layout, interaction
details, and accessibility implementation.

This is a direction and implementation-sequencing decision. It is not a claim
that every rendered state is polished, implemented, independently reviewed, or
ready for public or production use.

## What This Unblocks

- Q25 may continue the exact read-only foundation-gap work needed for private
  dogfooding. Work Board and Communications direction no longer wait on
  pixel-perfect visual approval. The missing CRM relationship projection and
  the independent promotion profile remain explicit gates before Q25 can be
  called fully accepted.
- Q26 may begin the FIN-001 synthetic local book and double-entry kernel. It
  must use synthetic fixtures and remain connector-free. Persistent real
  financial data is not allowed by this decision.

## Refinement Policy

Cosmetic and usability iteration does not invalidate this private-dogfood
direction decision. The ledger retains hashes of the images the founder saw as
historical evidence, but its verifier reports later asset-byte drift as an
advisory rather than a failed decision.

A new founder decision is required for a material change to canonical record
ownership, workflow purpose, sensitive-data boundaries, or authority. The
separate FIN-000 independent-promotion pack stays byte-bound and fail-closed;
its stricter digest and five-role review contract are not weakened here.

## Authority Boundary

This acceptance grants no social publishing, platform write, live connector,
bank connection, real financial-data processing, financial advice, payment,
filing, public release, supported distribution, or production authority.
Independent domain, privacy/security, accessibility, implementation, and
promotion review remain required before those stronger claims or capabilities.
