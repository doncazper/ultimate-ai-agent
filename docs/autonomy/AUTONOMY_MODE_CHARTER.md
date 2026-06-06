# Autonomy Mode Charter

Status: M61 / v0.65.0 implemented-released contract.

M61 adds the Autonomy Mode Charter as a planning and validation contract only.
It defines authority levels for future work while keeping default mode off. The
charter has no global autonomy switch, no production authority, no execution,
no tool execution, no browser automation, no shell execution, no network tools,
no background worker, no autonomous session, no backend route, and no dependency.

## Modes

| Mode | Name | M61 status |
| --- | --- | --- |
| Mode 0 | Off | Default mode off and required. |
| Mode 1 | Observe only | Defined only; no enablement in M61. |
| Mode 2 | Dry-run plan | Defined only; no enablement in M61. |
| Mode 3 | Ask before every action | Defined only; no enablement in M61. |
| Mode 4 | Scoped autonomy window | Future only. |
| Mode 5 | Trusted recurring automation | Future only. |
| Mode 6 | Production authority, later | Future only and not enabled through M100. |

M61 does not allow a jump from Mode 0 to broad autonomy. Approval refs,
context packs, memory refs, model output, runtime output, tool intents, and task
plans are identifiers or rationale only. They cannot enable autonomy.

## Authority Staging

Future capability work must pass through:

capability exists, disabled by default, dry-run first, limited allowlist,
explicit approval, scoped autonomy window, audit/replay, revocation, and only
then broader autonomy after a later reviewed milestone.

M62 remains future.
