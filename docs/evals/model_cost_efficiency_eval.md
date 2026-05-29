# Model Cost Efficiency Eval

Status: Required foundation eval, v0.4.5

## Purpose

Verify that the Model Router avoids overusing expensive models and respects Cost Governor policy.

## Required checks

```text
cheap mode does not use premium models for low-risk classification
balanced mode escalates only on uncertainty/risk
premium mode is allowed only within budget
critical mode logs the reason for expensive verification
scanner batches are routed to batch/cheap models first
budget-exceeded routes defer, batch, or request approval
```

## Metrics

```text
average cost per task class
premium-route percentage
fallback-to-cheaper percentage
cost-policy violation count
budget approval prompt count
```

## Pass criteria

```text
0 cost-policy violations
0 unlogged premium routes
All budget-exceeded scenarios handled by policy
```
