# Ultimate AI Agent Version

Current active baseline: **v0.28.0**

v0.28.0 implements M24 Memory Provider Abstraction + Local Memory Store. It adds
a governed MemoryProvider abstraction, local-only memory record contracts,
local dev/in-memory and explicit-path stdlib SQLite store support, reviewed-write
validation, source hierarchy, provenance/source/evidence/event/receipt refs,
structured memory kinds, trust/confidence metadata, dedup/decay/archive planning
metadata, future recall-planning metadata, retention/delete/export contracts,
conflict/staleness/supersession metadata, documentation, documentation-integrity
checks, static safety verification, and Foundation Gate coverage.

It incorporates safe MemoryOS-inspired concepts as metadata only while keeping
memory as high-salience recall rather than authority. It blocks automatic memory
writes, model-output writes, local-LLM-output writes, OpenWebUI writes,
mobile-capture writes, tool-output writes, raw prompt/model/file/transcript
content, secrets, cloud memory providers, vector DB, embeddings, Qdrant, Redis,
Docker, ARQ, cron/background workers, context injection, broad filesystem
scanning, production persistence, backend mutation routes, dependencies, and
production authority. M25 remains the future Truth Source Router + Evidence
Claim Checker milestone. OpenAPI path count remains `74`.
