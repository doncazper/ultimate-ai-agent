# Action Preview Policy

Status: active
Current through: v0.32.0
Purpose: Define Control Center action preview as non-executing UI policy.

Control Center action preview is not execution. It returns a safe decision object describing whether a future UI may display a preview. It does not mutate state, grant approval, resolve credentials, call tools, write files, dispatch remote workers, start runtimes, call providers, enable plugins, access sensors, or perform external actions.

Allowed preview examples:

- view status.
- view receipt summary.
- view event summary.
- preview an approval request.
- preview runtime readiness metadata.
- preview remote worker dry-run metadata.
- preview mobile capability planning metadata.

Blocked preview claims include:

- execute, run, connect, dispatch, or send.
- runtime/model/provider invocation.
- credential or secret use.
- file mutation or external action.
- remote worker dispatch.
- plugin enablement.
- mobile sensor access.
- arbitrary approval references used as authority.

High-risk and critical previews may return `approval_required`, but M12 still does not execute the action. Future execution-capable milestones must add separate authority, consent, Tool Broker, Event Ledger, receipt, and Foundation Gate checks.

v0.32.0 / M28 adds Approval Authority v2 + Action Policy Expansion for
policy-only decisions. These decisions do not authorize or perform execution,
and they do not add Control Center execute controls. M29-M40 remain
planned/provisional.
