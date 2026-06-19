# Local Model Management Receipt Plan

M152 local model management receipt plans are no-effect records. They can bind
request refs, actor refs, injected hardware summary refs, model refs, model
profile refs, model artifact refs, settings-plan refs, selection-preview refs,
redacted observability refs, audit refs, and replay refs.

A receipt plan must not contain raw prompts, raw completions, raw provider
payloads, raw local paths, secrets, credentials, raw Hugging Face payloads, raw
logs, environment dumps, or executable command text.

Every M152 receipt remains route-free and advisory. Suggested tuning changes are
review metadata only. They do not apply settings, restart a runtime, start a
server, download a model, or alter OpenWebUI.
