# Prompt Integration Guide v0.5.1

## Loading prompts

Load prompts by `prompt_id` from `docs/prompts/prompt_registry_v0_5_1.json`.

Do not hard-code prompt paths in agent code.

## Prompt composition order

For foundation agents, compose instruction context in this order:

```text
1. Agent Constitution
2. Prompt Style Rules
3. Role-specific system prompt
4. Execution Contract summary
5. Context Pack summary
6. Task-specific instruction
7. Output schema
```

## Prompt change control

Prompt changes require:

```text
reason for change
updated prompt file
updated prompt registry if needed
eval impact check
Event Ledger entry once runtime exists
```

## First implementation

In M0-M2, prompts can be loaded as static markdown files. Later, prompt versions should be tracked in the File Manager and Event Ledger.
