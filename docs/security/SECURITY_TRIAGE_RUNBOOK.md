# Security Triage Runbook

Status: active maintainer runbook
Program task: UAA-P0-003
Public policy: `SECURITY.md`

This runbook is a repeatable local maintainer process for security reports. It
does not add scanner runtime, dependency automation, connector writes, shell
authority, browser automation, plugin runtime import, mobile control, public
distribution, or production authority.

## Intake

1. Confirm the report arrived through a private channel when sensitive details
   are involved.
2. Create a safe tracking record using a report ref, affected component, safe
   summary, initial severity, owner, and target response date.
3. Do not copy secret-like values, private workspace data, unredacted request
   content, raw local paths, raw logs, environment dumps, or screenshots into
   durable evidence.
4. If the report arrived publicly with sensitive details, hide or redact the
   public material using the hosting platform controls, then continue privately.

## Triage Checks

| Area | Check | Required action |
|---|---|---|
| Secret scanning | Look for secret-like values in changed code, docs, tests, fixtures, and release-facing text. | Remove the value, rotate outside the repo if needed, and add a redaction regression test when a code path leaked it. |
| Dependency alerts | Review dependency alert metadata without adding network delivery or external scanner runtime. | Classify affected dependency, reachable surface, local-only exposure, and mitigation path. |
| Unsafe logging | Search for raw exception passthrough, traceback dumps, request/body echoing, or unredacted debug output. | Replace with safe error envelopes, redacted summaries, and no-secret-output tests. |
| Route auth issues | Check whether the route is disabled by default, local-only where required, and bound to side-effect classification. | Preserve PolicyEngine, LocalApprovalAuthority, OpenAPI, route metadata, and Foundation Gate checks. |
| Redaction regressions | Check safe refs, bounded summaries, evidence records, release docs, and API responses for unsafe disclosure. | Add or update redaction tests and documentation-integrity rules. |
| No-secret-output failures | Check API responses, error envelopes, receipt summaries, and release-facing docs for secret-like output. | Block the output, add regression coverage, and document the safe replacement. |
| Release-blocking security findings | Check whether the finding affects production authority, public claims, release docs, route safety, redaction, or no-secret-output evidence. | Mark the release lane blocked until mitigation, regression coverage, documentation updates, verifier updates, and rollback notes are complete. |

## Release Blocking

Treat a security finding as release-blocking when it could:

- expose secret-like values, private workspace data, raw prompts, raw responses,
  raw provider payloads, raw local paths, raw logs, usernames, hostnames,
  serials, or environment dumps
- bypass PolicyEngine, LocalApprovalAuthority, route side-effect
  classification, OpenAPI checks, or Foundation Gate checks
- grant unapproved runtime authority, shell/subprocess behavior, connector
  writes, plugin runtime import, mobile control, broad autonomy, or public
  distribution claims
- make release-facing docs or product truth packets overclaim production or
  public readiness

Release-blocking findings stay blocked until maintainers record a safe summary,
the affected invariant, mitigation, focused regression test, documentation or
verifier update, and rollback note.

## Required Verification Lane

Run the focused checks for UAA-P0-003 after any security-posture change:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_safe_exception_messages.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_secret_broker_redaction.py
.venv/bin/python scripts/verify_security_redaction_artifacts.py
.venv/bin/python scripts/verify_all.py --skip-ruff --skip-pytest
```

Use additional targeted tests when a report affects a specific subsystem.

## Safe Evidence Rules

Security evidence may include:

- report ref
- affected component
- safe impact summary
- reason codes
- redaction actions
- test names and verifier names
- rollback summary

Security evidence must not include:

- raw prompt, response, provider payload, path, or log content
- usernames, hostnames, serials, environment dumps, credentials, or secret-like
  values
- raw exploit payloads
- raw private workspace data

## Remediation And Rollback

Every accepted remediation must identify:

- the smallest affected code or doc surface
- the authority boundary that remains unchanged
- the regression test or verifier update
- the operator-visible claim that changes, if any
- rollback steps if the patch causes false positives or blocks safe local use

Rollback must not restore unsafe output, skipped approval gates, skipped
OpenAPI checks, skipped Foundation Gate checks, or unreviewed authority.
