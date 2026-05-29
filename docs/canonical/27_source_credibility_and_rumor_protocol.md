# 27 — Source Credibility and Rumor Protocol

Status: Foundation intelligence spec, v0.5.3
Owner: Research / Intelligence

## Purpose

Define how the agent treats breaking news, social signals, Reddit posts, RSS/news items, newsletters, official statements, retractions, and conflicting claims.

## Verification levels

```text
unverified_signal: single social/reddit/blog/newsletter item
single_source_report: one publisher or provider result
multi_source_report: two or more independent sources
primary_source: official filing, company/government/agency/source document
confirmed_event: primary or authoritative confirmation plus corroboration
contradicted: credible contradiction exists
retracted: source or primary authority retracted/updated claim
```

## Breaking-news rule

The agent may interrupt the user only when the item is:

```text
new
material
time-sensitive
relevant to user/project/watchlist
source-backed
not merely commentary or recycled coverage
worth the interruption cost
```

## Article vs event vs claim

```text
Article: one source item.
News Event: cluster of articles about the same happening.
Claim: specific assertion extracted from articles.
Evidence Bundle: supporting/contradicting sources and confidence.
```

## Reddit/social policy

Reddit and social content are early signals, not facts. They may seed research but cannot become confirmed alerts without source upgrade.

## Required fields for alerts

```text
what happened
why it matters to the user
verification level
confidence
sources
what is unknown
recommended action or no-action note
mute/tune controls
```

## Required evals

```text
breaking_news_verification_eval
source_credibility_eval
rumor_retraction_eval
alert_interruption_worthiness_eval
```
