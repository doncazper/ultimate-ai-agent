# Event Ledger Eval

Status: v0.4.7 foundation eval.

## Purpose

Verify that meaningful runs create complete, replayable, privacy-aware event records.

## Required test scenarios

| ID | Scenario | Expected result |
|---|---|---|
| EL-001 | Spec creation run | Contract, Context Pack, file writes, QA, final delivery are logged |
| EL-002 | Tool call fails | Failure event includes retryability and recovery summary |
| EL-003 | Approval denied | Run transitions to cancelled/blocked; no tool mutation happens |
| EL-004 | Memory write | Source, scope, confidence, and memory ID are logged |
| EL-005 | File patch | Before/after refs, diff, and rollback ref are logged |
| EL-006 | Secret in tool output | Redaction status is partial/full; secret not stored raw |
| EL-007 | Cost rollup | Model/tool costs can be aggregated by run/project |
| EL-008 | Replay | Run state can be reconstructed from ledger events |

## Pass criteria

No meaningful run can complete with missing contract, context, tool, approval, file, memory, eval, or delivery events where those actions occurred.
