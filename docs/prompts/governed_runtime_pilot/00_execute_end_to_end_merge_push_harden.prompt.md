# Execute Governed Runtime Pilot End To End

Role: Principal engineer, product architect, security reviewer, release
engineer, and adversarial hardening reviewer for UAA governed runtime.

Goal: move UAA from governing blocked authority to governing real local runtime
authority. Implement the `v0.105.0 Governed Runtime Pilot` as one coherent
milestone, not as endless tiny slices.

This wrapper is intentionally aggressive. It promotes several related local
runtime capabilities together:

- local model calls through a single governed runtime gateway;
- allowlisted local command execution through argv-only adapters;
- exact Action Inbox approval before runtime execution;
- redacted runtime receipts and evidence refs;
- CLI/API/Control Center parity.

It does not promote browser automation, connector writes, unrestricted web,
plugin runtime import, remote execution, production authority, or broad
autonomy.

## Read First

Read these files completely before making changes:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/governed_runtime_pilot/README.md`
- every prompt in `docs/prompts/governed_runtime_pilot/`
- existing overlapping authority prompts:
  - `docs/prompts/authority_graduation_program/README.md`
  - `docs/prompts/fcc_authority_ramp/README.md`
  - `docs/prompts/fcc_action_inbox_loop/README.md`

Then inspect:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
git remote -v
rg --files
rg "runtime|authority|approval|policy|manifest|OpenAPI|idempotency|redaction|evidence|chat|model|provider|shell|subprocess|command|action|rollback|safe-disable" src tests apps docs scripts
```

Do not proceed from a dirty or stale base unless the dirty files are explicitly
the files you are about to commit. Never overwrite unrelated user changes.

## Prompt Sequence

Execute these prompts in order:

1. `01_baseline_freeze_and_runtime_milestone.prompt.md`
2. `02_runtime_contracts_profiles_and_manifest.prompt.md`
3. `03_local_model_runtime_gateway.prompt.md`
4. `04_governed_command_runtime.prompt.md`
5. `05_action_inbox_execution_bridge.prompt.md`
6. `06_control_center_cli_evidence_runtime_ux.prompt.md`
7. `07_review_fix_harden_release_truth.prompt.md`

## Per-Phase Merge Loop

For each phase:

1. Start from current `main`.
2. Create a phase branch named
   `codex/governed-runtime-<phase-number>-<short-name>`.
3. Implement the phase.
4. Run focused tests and verifiers for the changed files.
5. Review the diff adversarially for:
   - unsafe authority expansion;
   - UI-only behavior;
   - raw prompt/response/log/path/provider payload persistence;
   - missing approval scope validation;
   - missing idempotency or replay behavior;
   - missing rollback or safe-disable posture;
   - route manifest/OpenAPI drift;
   - product-language overclaims;
   - missing CLI parity;
   - hidden dependency on browser, connector, plugin, remote execution, or
     unrestricted web authority.
6. Fix and harden until no in-scope high or medium risk remains.
7. Commit only intentional files.
8. Push the phase branch.
9. Open a draft PR.
10. Review failing checks and review comments. Fix and push again.
11. When green, merge the PR to `main` using a merge commit.
12. Pull `main`, record the merge SHA, and continue to the next phase.

If PR infrastructure is unavailable, use a local integration branch and merge
with explicit merge commits. Do not squash away phase history unless the
operator explicitly changes the release process.

## Required Hardening Loops

After every phase, run at least one hardening loop. After the full sequence,
run at least three hardening loops:

1. Security hardening: authority boundaries, redaction, approval, idempotency,
   rollback, env handling, command execution, model call safety.
2. Product hardening: operator readability, blocked/partial/implemented labels,
   no raw JSON primary UX, no production/beta/autonomy overclaim.
3. Verification hardening: route contract, API manifest, OpenAPI, CLI parity,
   frontend checks, foundation gate, docs integrity.

If any loop finds a fault, fix it and repeat the relevant loop. Do not ship with
known high or medium safety defects.

## Baseline And Tag Discipline

Before changing authority:

1. Verify current branch, commit, and status.
2. Commit or explicitly exclude unrelated pending work.
3. Create an annotated baseline tag such as
   `uaa-governed-runtime-baseline-YYYY-MM-DD` only if it does not already
   exist.
4. Never delete, move, retarget, or force-push historical tags.

After the full milestone is verified and merged, create an annotated milestone
tag such as `v0.105.0-governed-runtime-pilot` only if the release truth packet
and tests support it.

## Runtime Authority Boundaries

Allowed in this pilot:

- loopback/local OpenAI-compatible model endpoint calls through
  `RuntimeGateway`;
- allowlisted argv-only local command execution;
- exact Action Inbox approval envelope execution;
- redacted bounded evidence receipts;
- CLI/API/UI parity.

Still blocked:

- browser observe;
- browser action;
- unrestricted web fetch;
- remote provider SDK calls;
- connector writes;
- plugin runtime import;
- unrestricted shell strings;
- remote execution;
- memory truth/context injection authority beyond explicit tested scope;
- production authority;
- public beta/release/distribution claims.

## Default Checks

Run focused tests for changed files plus these where relevant:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

Add new runtime-specific tests and verifiers as the implementation requires.
If an environment dependency blocks a check, report the blocker and do not
claim success.

## Final Response Requirements

Report:

- baseline tag and baseline commit;
- phase branches, PR URLs, merge SHAs, and pushed branches;
- files changed;
- authority promoted;
- authority still blocked;
- tests/verifiers run with pass/fail/blocker;
- hardening loops completed and faults fixed;
- remaining risks;
- current `main` commit;
- milestone tag, if created;
- recommended next steps.

