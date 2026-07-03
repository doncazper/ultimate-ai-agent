# Authority Lane 03: Provider / Model Invocation

Goal: Let UAA make one useful real model/provider call without treating model
output as truth or authority.

Allowed next promotion: Level 2 manual foreground exact invocation for one
summarize/classify/draft scope, if credential/cost gates already exist.

Scope:

- One provider/model adapter scope.
- Exact LocalApprovalAuthority approval.
- CostGovernor max USD and usage receipt.
- Redacted prompt envelope and response summary refs.
- No raw prompt/response/provider payload persistence.
- CLI inspection and receipt replay.

Still blocked:

- Autonomous model calls.
- Broad provider router fallback.
- Model output as production truth.
- Model output executing actions.
- Memory write/context injection from model output.

Promotion condition:

One capped invocation can run manually, produce redacted usage/cost/evidence
receipts, and deny when approval/cost/credential/safe-disable checks fail.

Tests/verifiers:

- provider invocation lane tests.
- CostGovernor tests.
- credential readiness/revocation tests.
- no raw prompt/response tests.
- API manifest/OpenAPI if route changes.

If blocked:

Generate an unblock prompt for the missing credential, cost, approval, adapter,
or redaction prerequisite.
