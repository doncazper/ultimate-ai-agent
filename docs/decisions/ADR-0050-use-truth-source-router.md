# ADR-0050: Use Truth Source Router

Status: Accepted.
Date: v0.5.6.

## Context

Different facts require different truth paths. Policies should be retrieved from approved docs. Account status should come from APIs/databases. Metrics should be calculated deterministically. Weather should come from weather providers. News should use live sources and credibility checks. Code behavior should come from tests and source files.

## Decision

Use a Truth Source Router to select source paths by question type, grounding mode, permissions, freshness, and authority level.

## Consequences

- The agent must prefer canonical APIs/databases over documents for hard structured facts.
- The agent must prefer approved/current documents over drafts.
- The agent must surface source conflicts.
- The agent must not access sources the user cannot access.
- Truth source route decisions must be logged.
