# Model Routing Eval

Status: Required foundation eval, v0.4.5

## Purpose

Verify that the Model Router selects the correct model class for common task types and records the decision in the Event Ledger.

## Required cases

| Case | Input | Expected route |
|---|---|---|
| Intent classification | Short user request | `fast_classifier` |
| Architecture review | Review foundation design | `strong_reasoner` |
| Code patch | Generate and test code change | `coding_model` + verifier |
| Memory extraction | Extract durable memory | `structured_output_model` |
| Long PDF summary | Large source document | `long_context_model` or chunking + `standard_assistant` |
| Breaking news interrupt | Time-sensitive alert | `research_synthesizer` + `strong_reasoner` verifier |
| Sensitive personal note | Private user data | `local_private_model` or approval required |
| External action approval | Send/publish/modify external system | `high_reliability_critical_model` + human approval |
| Scanner triage batch | 500 low-risk items | `small_batch_worker` / `fast_classifier` |
| Vision/UI review | Screenshot or diagram | `vision_model` |

## Pass criteria

```text
90% route-class accuracy on foundation cases
100% privacy-blocking accuracy on sensitive cases
100% Event Ledger trace presence
100% independent-verifier routing for critical cases
```
