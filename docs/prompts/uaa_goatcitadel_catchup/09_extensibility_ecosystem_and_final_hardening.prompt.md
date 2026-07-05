# Phase 09: Extensibility, Ecosystem, And Final Hardening

Goal: give UAA a stronger long-term platform shape: inspectable extension and
capability catalogs, safe activation boundaries, developer experience, and a
final release-truth hardening sweep.

This phase must keep plugin runtime import and broad extension execution
blocked unless a separate exact authority lane has already promoted them.

## Required Work

1. Inspect UAA skill workbench, plugin/skill ecosystem boundary, inspectable
   extension catalog, activation grants, MCP/A2A compatibility, capability
   registries, API/CLI surfaces, docs, and tests.
2. Add or harden an inspectable capability/extension catalog:
   - id;
   - type;
   - source;
   - status;
   - trust posture;
   - callable posture;
   - required grants;
   - blocked reason;
   - review evidence refs;
   - safe install/adoption posture.
3. Split catalog visibility from runtime callability.
4. Add future activation-grant contracts only where they remain exact-scoped,
   expiring, auditable, revocable, and deny-by-default.
5. Add developer guidance for creating UAA-native capabilities without
   bypassing policy, approval, redaction, route classification, OpenAPI, CLI
   parity, or Foundation Gate checks.
6. Run a final catch-up hardening sweep across Phases 01-08:
   - route contract drift;
   - docs/product truth drift;
   - missing tests;
   - UI-only truth;
   - redaction leaks;
   - unsafe authority claims;
   - unsupported GoatCitadel parity claims.
7. Produce a final 30-day plan ranked by impact, effort, risk, and authority
   needed.

## Explicit Non-Goals

Do not import or execute plugins, external skills, remote MCP tools, connector
writes, browser automation, remote code, or public marketplace behavior.

Do not merge a GoatCitadel-style broad extension model if it conflicts with
UAA's local-first governed authority boundaries.

## Acceptance Criteria

- Operators can inspect available capabilities and why they are visible,
  inactive, callable, approval-required, or blocked.
- Extension/capability runtime activation remains deny-by-default.
- Final docs and product truth distinguish implemented, partial, planned,
  mock-only, blocked, deprecated, contradicted, and unknown states.
- Final verifiers prove no broad authority, raw payload persistence, or
  product-language overclaim was introduced.

## Verification

Run focused ecosystem tests plus the final gate set:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
make frontend-visual-check
```

Report any skipped checks with concrete blockers.
