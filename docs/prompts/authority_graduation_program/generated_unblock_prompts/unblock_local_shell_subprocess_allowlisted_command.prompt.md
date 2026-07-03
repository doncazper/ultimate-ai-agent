# Unblock Local Shell / Subprocess Allowlisted Command

Goal:
Prepare, then possibly promote, one exact local maintenance command family
without granting arbitrary shell or subprocess authority.

Branch:
`codex/unblock-local-shell-subprocess-allowlisted-command`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- do not add arbitrary shell authority
- do not execute through shell strings
- do not add unrestricted subprocess execution
- no privileged commands
- no package installs
- no network shell behavior unless a later exact network lane grants it
- no background processes, daemons, schedulers, or long-running workers
- no raw command string, raw stdout/stderr, env dump, local path, credential, or
  secret-like persistence
- no provider/model calls, connector writes, browser automation, memory writes,
  context injection, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/local_shell_subprocess_allowlisted_command_2026_07_03.md`
   - `docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_AUTHORITY_BOUNDARY.md`
   - `docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_POLICY.md`
   - `docs/control_center/authority_candidate_scorecard.json`
2. Select exactly one local maintenance command family, or record no-go if none
   can be made safe.
3. First implement only a validation-only classifier/receipt contract for that
   command family:
   - safe command family ref
   - safe argument refs
   - blocked raw shell string posture
   - approval scope refs
   - cwd/env allowlist refs
   - timeout/safe-disable refs
   - stdout/stderr redaction plan refs
   - idempotency/audit/replay refs
   - CLI inspection refs
4. Do not add a subprocess runner in the classifier PR.
5. Only after classifier/verifier coverage is merged, consider a second PR for
   exactly one foreground command invocation with exact approval and redacted
   receipt evidence.
6. Add or update tests proving:
   - shell strings are rejected;
   - unapproved command refs are blocked;
   - unsafe cwd/env/output shapes are blocked;
   - network/background/privileged/package-install attempts are blocked;
   - CLI inspection does not execute commands;
   - broad shell/subprocess authority remains blocked.

Tests/verifiers:
- focused sandbox pytest for the new classifier/read model
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_m85_read_only_command_allowlist.py tests/test_m90_shell_subprocess_hardening_freeze.py -q`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if routes change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and no shell/subprocess execution authority was
  added
