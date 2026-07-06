# UAA Hermes Runtime Progressive Skill Disclosure

Status: Hermes Runtime Adoption Phase 13 repo-safe metadata posture

## Full-Strength Version

UAA can help operators discover and use skills by loading compact metadata
first, then loading full instructions only when relevant, reviewed, and
operator-selected for a task. Skills can eventually contribute context,
verification expectations, and tool posture without becoming hidden authority.

## Repo-Safe Version

Phase 13 extends the existing inspectable extension catalog with progressive
skill-disclosure posture:

- compact skill index refs
- metadata summary refs
- reviewed/unknown provenance and hash posture
- trust posture and review evidence refs
- full-instruction load posture
- blocked automatic instruction loading
- blocked hidden activation
- blocked skill runtime import
- blocked external marketplace fetch
- CLI/API parity through `scripts/dev/uaa_extensions.py inspect-catalog` and
  `GET /extensions/catalog`

This is metadata only. It does not import skills, install packages, execute
plugin code, fetch marketplace data, inject hidden context, or auto-load full
skill instructions.

## Blocked / Needs Authority

- external marketplace fetch
- automatic skill activation
- hidden skill instruction loading
- plugin or skill runtime import
- package install
- executable skill enablement
- connector writes
- shell/subprocess execution
- browser automation
- provider/model calls
- production authority

## Exact Promotion Path

Future promotion requires reviewed UAA-owned adaptation records, static scan
evidence, operator-selected instruction preview, exact approval scope, safe
disable posture, quarantine/rollback posture, redacted receipts, proof refs,
CLI/API/Core parity, and focused tests proving no hidden context injection or
runtime import.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_progressive_skills.py tests/test_inspectable_extension_catalog.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_13.py
```
