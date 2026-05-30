# 49 — Temporal Context and Freshness

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

Weather, news, messages, memory, reminders, provider results, and proactive alerts are time-sensitive. The agent must know not only what a fact says, but when it was observed, fetched, published, updated, and when it expires.

## Core rule

> Every context pack, provider result, memory snippet, event, and proactive signal must carry temporal metadata sufficient to evaluate freshness.

## Temporal fields

```text
current_time_utc
user_timezone
source_observed_at
source_published_at
source_updated_at
fetched_at
processed_at
valid_from
valid_to
expires_at
freshness_window_seconds
staleness_policy
```

## Freshness classes

```text
static
slow_changing
daily
hourly
near_real_time
breaking
expired
unknown
```

## Domain guidance

| Domain | Freshness expectation |
|---|---|
| Project ADR | static / slow_changing |
| Package docs | slow_changing but verify current version |
| Weather current conditions | hourly or fresher |
| Weather alerts | near_real_time |
| Breaking news | near_real_time with verification level |
| Personal calendar | near_real_time during active day |
| Memory preference | slow_changing with last_confirmed_at |
| Provider pricing/API limits | verify before recommending spend |

## Staleness rules

1. If a result is stale for its domain, the agent must label it or refresh it.
2. Proactive alerts require freshness checks before notifying.
3. Breaking-news items must include `source_published_at`, `fetched_at`, and verification level.
4. Memory with temporal uncertainty should be used softly, not as hard truth.

## Minimum implementation for M0/M1

Add schema and helper utilities. Use UTC internally. Convert to user timezone only at presentation boundaries.
