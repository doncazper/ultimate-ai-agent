# FCC-POLISH-001 Native And Apple-Grade UX Layer

Role: You are a Principal Software Engineer implementing UX polish over proven
backend-owned state.

Task: Improve launcher, setup, notifications posture, blocked states, visual
hierarchy, and product copy so normal daily use feels calm and professional
while route/authority details remain inspectable.

Requirements:
- Polish must sit on existing backend-owned route/API/core evidence.
- Keep technical route refs, authority boundaries, blocked states, and
  inspection paths visible.
- Any native/macOS scaffold must be source-only or read-only unless a later
  exact packaging/signing/installer milestone grants more.
- Visual changes must be tested with frontend checks and screenshots/visual
  baselines where the repo already has that pattern.

Non-goals:
- No signed/public distribution, installer mutation, LaunchAgent install/load,
  notification delivery, shell/subprocess execution, model/provider authority,
  connector writes, hidden authority, public beta, or production readiness
  claim.

Focused checks:
- `make frontend-check`
- `npm --prefix apps/control-center run visual:check` when visual surfaces change
- `.venv/bin/python scripts/verify_control_center_frontend.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_product_truth.py --root .`
- `git diff --check`
