# M151 Local OpenWebUI Test Shell

M151 Local OpenWebUI Test Shell is the corrective post-M150 milestone that
turns the alpha expectation gap into a local, testable chat surface.

The target is deliberately narrow:

- local-dev-only
- disabled by default
- localhost-only
- OpenWebUI is a shell, not the agent brain
- OpenAI-compatible endpoint shape for local smoke testing
- one deterministic test model: `uaa-safe-local`
- no provider call
- no model authority
- no tool execution
- no memory write
- no context injection
- no external network
- no raw prompt logging
- no production authority

M151 adds a local OpenAI-compatible gateway at:

- `GET /v1/models`
- `POST /v1/chat/completions`

Both routes require:

- UAA backend bound to `127.0.0.1`
- `UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1`
- bearer value `uaa-local-test`

The chat response is deterministic and does not echo prompt content. It exists
only to prove that OpenWebUI can call UAA in a governed local smoke path.

## Definition Of Done

M151 is complete when a developer can:

1. Start UAA locally with the M151 gateway flag.
2. Start OpenWebUI locally.
3. Configure OpenWebUI to use UAA's local `/v1` gateway.
4. Select `uaa-safe-local`.
5. Send a prompt.
6. Receive the deterministic governed response.
7. Verify tests and safety flags show no provider call, tool execution, memory
   write, context injection, external network, raw prompt logging, or
   production authority.

M151 does not make OpenWebUI authoritative. Agent Core remains the policy and
authority boundary.
