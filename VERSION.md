# Active Project Version

Current planning baseline: **v0.5.5**

This version adds Local Runtime, Context Survival, Structured World State, and Agent Runtime Adapter strategy before M0/M1 coding.

v0.5.5 incorporates lessons from local LLM agent infrastructure: the agent must not rely on transcript history as the durable record; long-running sessions need structured world state, context budgeting, token calibration, tool-result retention, local runtime profiles, prefix-cache-aware prompt/tool bundles, and explicit SDK/A2A adapter boundaries.

v0.5.5 remains pre-coding architecture. It does not implement scanners, provider integrations, companion proactivity, Skill Factory, self-improvement, external high-autonomy execution, or production model/runtime calls.
