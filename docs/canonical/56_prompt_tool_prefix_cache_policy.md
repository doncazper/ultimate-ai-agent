# 56 — Prompt and Tool Prefix Cache Policy

Status: Active foundation contract in v0.5.5.

## Purpose

Local and cloud runtimes benefit when fixed prompts and tool schemas are stable. Prompt/tool bundle changes can invalidate prefix caches and force the runtime to reread large fixed prefixes.

## Requirements

- Assemble system prompts and tool schemas deterministically.
- Use task-mode-specific tool bundles instead of attaching all tools to every request.
- Version prompt bundles and tool schema bundles.
- Keep tool ordering stable within a run.
- Log prefix-cache invalidation causes.
- Avoid changing model/runtime mid-run unless the Execution Contract permits escalation.
- Record prompt/tool bundle hashes in Event Ledger and Context Budget records.

## Tool bundle examples

```text
foundation_file_write_bundle
read_only_research_bundle
code_review_bundle
weather_read_only_bundle
```

## Non-goals

This policy does not require a specific inference server. It defines metadata and discipline so runtimes such as Ollama, LM Studio, llama.cpp, vLLM, and cloud providers can be used efficiently and reproducibly.
