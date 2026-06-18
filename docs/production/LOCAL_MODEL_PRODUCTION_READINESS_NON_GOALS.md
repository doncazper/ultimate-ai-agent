# Local Model Production Readiness Non-Goals

M166 does not add new backend routes, Control Center execute controls,
OpenWebUI admin integration, OpenWebUI plugins, OpenWebUI functions, OpenWebUI
pipelines, external SaaS analytics, provider SDK dependencies, model training,
model-provider authority, memory write authority, context injection authority,
tool execution authority, shell-string execution, browser automation,
non-loopback serving, credential export, raw prompt export, raw response export,
raw provider payload export, raw local path export, raw log export, or
unreviewed side effects.

M166 does not make OpenWebUI the agent brain. OpenWebUI remains a shell pointed
at UAA's local `/v1` gateway.
