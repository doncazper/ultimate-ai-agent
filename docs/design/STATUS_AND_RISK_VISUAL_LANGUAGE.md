# Status And Risk Visual Language

Status: Active design governance for v0.19.1. Documentation only.

Risk and status labels must be textual, not color-only. Icons, color, borders, and tone may support meaning, but visible text carries the contract.

## Risk Levels

| Label | Treatment | Copy rule |
| --- | --- | --- |
| safe | quiet positive/neutral | Indicates low-risk display or validation only. |
| low | informational | Explain the limited consequence. |
| medium | caution | Describe what needs review. |
| high | strong warning | State that execution or sensitive action is not allowed without a reviewed contract. |
| critical | strongest warning | State blocked or requires explicit future authority. |
| forbidden | blocked/danger | State unavailable and explain the policy boundary. |

## Capability States

| Label | Meaning |
| --- | --- |
| preview-only | A policy preview only; no action occurred. |
| read-only | Display or summary only; no mutation or approval authority. |
| validation-only | Validates contract or payload shape only. |
| dry-run-only | Simulates a decision path without dispatching work. |
| simulated-only | Deterministic simulated behavior; not real runtime evidence. |
| manual-only | Requires human-run procedure; not automated authority. |
| blocked | Not allowed by current policy. |
| planned | Future work; not available. |
| disabled | Present as metadata only; not usable. |
| degraded | Some data is unavailable or fallback-filled. |
| mock fallback | Mock data is shown and is non-authoritative. |
| non-authoritative | Cannot be used as truth, approval, evidence, or execution proof. |
| local-only | Limited to localhost, 127.0.0.1, or safe loopback forms. |

Rules:

- do not use ambiguous "enabled" language for planned or disabled capabilities.
- connected must not imply authority.
- online must not imply production readiness.
- mock, degraded, local-only, simulated, and non-authoritative states must be explicit.
- blocked and forbidden states must not appear as available controls.
- risk/state labels must remain readable at narrow widths.
