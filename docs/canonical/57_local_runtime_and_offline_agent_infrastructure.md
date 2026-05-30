# 57 — Local Runtime and Offline Agent Infrastructure

Status: Active foundation contract in v0.5.5.

## Purpose

The Ultimate AI Agent should treat local models as first-class runtimes, not just model names. Local execution introduces resource, context, latency, health, and privacy concerns that cloud APIs hide.

## Supported runtime categories

```text
ollama
lm_studio
llama_cpp_server
vllm
sglang
local_embedding_server
openai_compatible_cloud
provider_native_cloud
```

## Runtime registry requirements

Each runtime must have a manifest describing:

```text
runtime type
base URL or launch command
model profile
context limit
actual capability probes
privacy mode
resource requirements
health-check endpoint
streaming/tool/json/vision/embedding support
prefix-cache and optimization support
```

## Local resource governor

Local runs should account for:

```text
CPU
RAM
GPU/VRAM
battery
thermal pressure
disk
parallel requests
model load/unload time
latency
```

High-volume background jobs must not monopolize local inference. Scanners and proactive tasks should use small/cheap local models or scheduled windows after foundation approval.

## Privacy modes

```text
local_only
local_first
cloud_allowed
cloud_required
```

Sensitive/private tasks should default to local-first or local-only unless the user explicitly permits cloud routing.

## Runtime health

Before routing to a runtime, the Model Router must know whether the runtime is running, whether the model is loaded, whether the effective context limit is known, and whether required capabilities are supported.
