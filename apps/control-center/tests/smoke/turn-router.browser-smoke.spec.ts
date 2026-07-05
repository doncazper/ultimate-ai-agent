import { expect, test, type Page, type Route } from "@playwright/test";

type SampleId =
  | "diy-desk"
  | "office-memory"
  | "shopping-list"
  | "current-lumber-prices"
  | "order-materials"
  | "card-pickup"
  | "base-answer-bypass";

const sampleContracts: Record<SampleId, string> = {
  "diy-desk": "answer_directly",
  "office-memory": "answer_with_reviewed_memory",
  "shopping-list": "draft_or_plan",
  "current-lumber-prices": "prepare_tool_or_action",
  "order-materials": "approval_required",
  "card-pickup": "approval_required",
  "base-answer-bypass": "approval_required",
};

const sampleLabels: Record<SampleId, string> = {
  "diy-desk": "DIY desk",
  "office-memory": "Office memory",
  "shopping-list": "Shopping list",
  "current-lumber-prices": "Current lumber prices",
  "order-materials": "Order materials",
  "card-pickup": "Card and pickup",
  "base-answer-bypass": "Base-answer bypass",
};

const chatTurnRef = "chat-turn:local-operator:uaa-safe-local";
const bindingRef =
  "turn-harness-binding:v1-chat:v1-chat-completions-uaa-safe-local";

const consoleFindingsByPage = new WeakMap<Page, string[]>();

const allowedBackgroundReadPaths = new Set([
  "/health",
  "/version",
  "/api/manifest",
  "/control-center/manifest",
  "/control-center/dashboard",
  "/control-center/status",
  "/control-center/routes",
  "/control-center/approvals/summary",
  "/control-center/approvals/queue",
  "/control-center/runs/observability",
  "/control-center/runtime-readiness/summary",
  "/control-center/foundation-gate/summary",
  "/control-center/setup-assistant/summary",
  "/control-center/providers/setup-guide",
  "/control-center/settings/status",
  "/control-center/local-models/status",
  "/control-center/today/summary",
  "/control-center/start-here/summary",
  "/control-center/coding/session",
  "/control-center/coding/context",
  "/control-center/coding/patch-proposal",
  "/control-center/coding/patch-apply-readiness",
  "/control-center/coding/test-command-readiness",
  "/control-center/coding/git-review",
  "/control-center/coding/live-preview",
  "/control-center/coding/multi-agent-review",
  "/control-center/proof/index",
  "/control-center/trust-authority/matrix",
  "/control-center/evidence/timeline",
  "/control-center/memory/review",
  "/control-center/memory/workbench",
  "/control-center/memory/search",
  "/control-center/memory/context-packs",
  "/control-center/memory/retrieval-diagnostics",
  "/control-center/memory/citation-integrity",
  "/control-center/memory/quality-issues",
  "/control-center/memory/maintenance-runs",
  "/control-center/memory/context-manifest",
  "/control-center/memory/observation-candidates",
  "/control-center/memory/probe",
  "/control-center/memory/contradictions",
  "/control-center/actions/inbox",
  "/control-center/morning-briefing/summary",
  "/control-center/sources/readiness",
  "/control-center/storage/status",
  "/runtime/readiness",
  "/runtime/capability-matrix",
]);

const unsupportedAuthorityClaimPatterns = [
  new RegExp("production[- ]?" + "ready", "i"),
  new RegExp("public beta " + "ready", "i"),
  new RegExp("unrestricted " + "(tools|browsing|shell|execution)", "i"),
  new RegExp("broad " + "autonomy", "i"),
  new RegExp("connector writes? " + "(enabled|available|ready)", "i"),
  new RegExp("provider authority " + "(enabled|available|ready)", "i"),
  new RegExp("browser automation " + "(enabled|available|ready)", "i"),
  new RegExp("product runtime browser " + "automation", "i"),
];

test.beforeEach(async ({ page }) => {
  const consoleFindings: string[] = [];
  consoleFindingsByPage.set(page, consoleFindings);
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      consoleFindings.push(`${message.type()}:redacted-console-event`);
    }
  });
  page.on("pageerror", () => {
    consoleFindings.push("pageerror:redacted");
  });
  await page.route("**/*", async (route) => fulfillSmokeRoute(route));
});

test.afterEach(async ({ page }) => {
  expect(consoleFindingsByPage.get(page) ?? []).toEqual([]);
  await expectNoRawJsonPrimaryUi(page);
  await expectUnsupportedAuthorityClaimsAbsent(page);
});

test("router diagnostics preserve protected contracts on desktop and mobile", async ({
  page,
}) => {
  await openChatRoute(page);
  await expect(page.getByRole("heading", { name: "Router Diagnostics" })).toBeVisible();
  await expect(page.getByText("Backend-owned router preview")).toBeVisible();

  for (const sampleId of Object.keys(sampleContracts) as SampleId[]) {
    await page.getByRole("button", { name: sampleLabels[sampleId] }).click();
    await expect(page.locator(".router-contract-card")).toContainText(
      sampleContracts[sampleId],
    );
  }

  await expect(page.locator(".router-posture-card")).toContainText(
    "Approval boundary",
  );
  await expect(page.locator(".router-blocked-card")).toContainText(
    "blocked-state:turn-router-preview:no-action-execution",
  );

  await page.getByLabel("Ephemeral one-shot router text").fill(
    "How do I build a DIY table?",
  );
  await page.getByRole("button", { name: "Preview turn" }).click();
  await expect(page.locator(".router-contract-card")).toContainText(
    "answer_directly",
  );
  await expect(page.locator(".router-posture-card")).toContainText(
    "Lightweight answer posture",
  );
});

test("chat harness smoke records safe receipt refs without runtime authority", async ({
  page,
}) => {
  await openChatRoute(page);
  await expect(
    page.getByRole("heading", { exact: true, name: "Chat Local Operator" }),
  ).toBeVisible();
  await expect(page.getByText("Local model list is reachable")).toBeVisible();

  await page.getByRole("button", { name: "Probe redacted local turn" }).click();
  await expect(page.getByText(bindingRef).first()).toBeVisible();
  await expect(
    page.getByText("turn_harness_binding_compilation_only").first(),
  ).toBeVisible();
  await expect(page.getByText("answer_directly").first()).toBeVisible();
  await expect(page.getByText("receipt:chat-turn:control-center-smoke")).toBeVisible();
  await expect(page.getByText("proved")).toBeVisible();
  await expect(page.getByText("tools-functions-streaming-denied")).toBeVisible();

  const bodyText = await page.locator("body").innerText();
  expect(bodyText).not.toMatch(/\bmessages\b/i);
  expect(bodyText).not.toMatch(/completion text/i);
  expect(bodyText).not.toMatch(/prompt body/i);
});

async function openChatRoute(page: Page) {
  await page.goto("/chat");
  await expect(
    page.getByRole("heading", { exact: true, name: "Chat Local Operator" }),
  ).toBeVisible({ timeout: 20_000 });
}

async function expectNoRawJsonPrimaryUi(page: Page) {
  await expect(page.locator("pre")).toHaveCount(0);
  const bodyText = await page.locator("body").innerText();
  expect(bodyText).not.toMatch(
    /\{\s*"(ok|result|data|error|choices|messages|uaa_safety)"\s*:/i,
  );
  expect(bodyText).not.toMatch(
    /"(messages|choices|uaa_safety|provider_payload|raw_prompt|raw_response)"\s*:/i,
  );
}

async function expectUnsupportedAuthorityClaimsAbsent(page: Page) {
  const bodyText = await page.locator("body").innerText();
  for (const pattern of unsupportedAuthorityClaimPatterns) {
    expect(bodyText).not.toMatch(pattern);
  }
}

async function fulfillSmokeRoute(route: Route) {
  const request = route.request();
  const url = new URL(request.url());
  const path = url.pathname;
  if (path === "/control-center/turn-router/preview") {
    await route.fulfill(jsonResponse(turnRouterPreview(request.postData())));
    return;
  }
  if (path === "/v1/models") {
    await route.fulfill(
      jsonResponse({
        object: "list",
        data: [
          {
            id: "uaa-safe-local",
            object: "model",
            created: 0,
            owned_by: "ultimate-ai-agent-local",
          },
        ],
        uaa_safety: {
          local_dev_only: true,
          provider_call_enabled: false,
          model_authority_enabled: false,
          tool_execution_enabled: false,
        },
      }),
    );
    return;
  }
  if (path === "/v1/chat/completions") {
    const body = parseBody(request.postData());
    const validationErrors = validateLocalChatCompletionRequest(body);
    if (validationErrors.length > 0) {
      await route.fulfill(
        jsonResponse(
          {
            ok: false,
            error: {
              message: `turn-router-smoke-unsafe-chat-request:${validationErrors.join(
                ",",
              )}`,
            },
          },
          400,
        ),
      );
      return;
    }
    await route.fulfill(
      jsonResponse({
        id: "chatcmpl-uaa-safe-local-smoke",
        object: "chat.completion",
        created: 0,
        model: "uaa-safe-local",
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: "",
            },
            finish_reason: "stop",
          },
        ],
        usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
        uaa_safety: {
          provider_called: false,
          model_authority_granted: false,
          tool_executed: false,
          tools_enabled: false,
          functions_enabled: false,
          streaming_enabled: false,
          memory_written: false,
          context_injected: false,
          external_network_called: false,
          raw_prompt_logged: false,
          raw_provider_payload_exposed: false,
          turn_harness_binding: turnHarnessBinding(),
        },
      }),
    );
    return;
  }
  if (path === "/control-center/chat/turns" && request.method() === "POST") {
    const body = parseBody(request.postData());
    const validationErrors = validateChatTurnReceiptRequest(body);
    if (validationErrors.length > 0) {
      await route.fulfill(
        jsonResponse(
          {
            ok: false,
            error: {
              message: `turn-router-smoke-unsafe-receipt-request:${validationErrors.join(
                ",",
              )}`,
            },
          },
          400,
        ),
      );
      return;
    }
    await route.fulfill(jsonResponse({ ok: true, result: chatReceipt(body) }));
    return;
  }
  if (
    path ===
    `/control-center/chat/turns/${encodeURIComponent(chatTurnRef)}/receipt`
  ) {
    await route.fulfill(jsonResponse({ ok: true, result: chatReceipt() }));
    return;
  }
  if (request.method() === "GET" && allowedBackgroundReadPaths.has(path)) {
    await route.fulfill(
      jsonResponse(
        {
          ok: false,
          error: { message: "turn-router-smoke-fixture-fallback" },
        },
      ),
    );
    return;
  }
  if (
    path.startsWith("/control-center/") ||
    path.startsWith("/runtime/") ||
    url.origin !== "http://127.0.0.1:5173"
  ) {
    await route.fulfill(
      jsonResponse(
        {
          ok: false,
          error: { message: "turn-router-smoke-unexpected-route" },
        },
        418,
      ),
    );
    return;
  }
  await route.fallback();
}

function validateLocalChatCompletionRequest(
  body: Record<string, unknown>,
): string[] {
  const errors: string[] = [];
  if (body.model !== "uaa-safe-local") {
    errors.push("unexpected_model_ref");
  }
  const messages = Array.isArray(body.messages) ? body.messages : [];
  const message = asRecord(messages[0]);
  if (
    messages.length !== 1 ||
    message?.role !== "user" ||
    message.content !== "status"
  ) {
    errors.push("unexpected_probe_message");
  }
  if (body.max_tokens !== 8) {
    errors.push("unexpected_token_bound");
  }
  if (body.stream !== false) {
    errors.push("streaming_not_denied");
  }
  for (const key of [
    "tools",
    "functions",
    "response_format",
    "web_search_options",
    "parallel_tool_calls",
  ]) {
    if (key in body) {
      errors.push(`unexpected_${key}`);
    }
  }
  if ("tool_choice" in body && body.tool_choice !== "none") {
    errors.push("unexpected_tool_choice");
  }
  return [...errors, ...collectSensitiveStringReasons(body)];
}

function validateChatTurnReceiptRequest(
  body: Record<string, unknown>,
): string[] {
  const errors: string[] = [];
  const binding = asRecord(body.turn_harness_binding);
  if (body.turn_ref !== chatTurnRef) {
    errors.push("unexpected_turn_ref");
  }
  if (body.route_ref !== "/v1/chat/completions") {
    errors.push("unexpected_route_ref");
  }
  if (body.model_ref !== "model-ref:uaa-safe-local") {
    errors.push("unexpected_model_ref");
  }
  if (body.runtime_truth !== "local-chat-route-answered") {
    errors.push("unexpected_runtime_truth");
  }
  if (body.auth_truth !== "local-bearer-accepted") {
    errors.push("unexpected_auth_truth");
  }
  if (body.tool_denial_truth !== "tools-functions-streaming-denied") {
    errors.push("unexpected_tool_denial_truth");
  }
  if (body.safe_summary_ref !== "safe-summary-ref:control-center-chat-probe") {
    errors.push("unexpected_safe_summary_ref");
  }
  if (!binding) {
    errors.push("missing_turn_harness_binding");
  } else {
    errors.push(...validateTurnHarnessBindingRequest(binding));
  }
  return [...errors, ...collectUnsafeReceiptPayloadReasons(body)];
}

function validateTurnHarnessBindingRequest(
  binding: Record<string, unknown>,
): string[] {
  const errors: string[] = [];
  const expectedFalseKeys = [
    "memory_touched",
    "reviewed_memory_refs_allowed",
    "memory_content_retrieved",
    "memory_write_allowed",
    "memory_write_performed",
    "planner",
    "durable_state",
    "approval_required",
    "approval_envelope_required",
    "side_effects_allowed",
    "execution_ready",
    "receipt_required",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_memory_body_persisted",
    "raw_local_path_persisted",
    "credential_persisted",
  ];
  const expectedTrueKeys = [
    "safe_refs_only",
    "no_runtime_model_call_performed",
    "no_provider_call_performed",
    "no_tool_execution_performed",
    "no_action_execution_performed",
    "no_shell_subprocess_performed",
    "no_browser_network_performed",
    "no_connector_write_performed",
  ];
  if (binding.binding_ref !== bindingRef) {
    errors.push("unexpected_binding_ref");
  }
  if (binding.turn_contract !== "answer_directly") {
    errors.push("unexpected_turn_contract");
  }
  if (binding.no_effect_scope !== "turn_harness_binding_compilation_only") {
    errors.push("unexpected_no_effect_scope");
  }
  if (binding.memory_scope !== "none" || binding.tool_policy !== "none") {
    errors.push("unexpected_memory_or_tool_policy");
  }
  if (binding.approval_policy !== "not_required") {
    errors.push("unexpected_approval_policy");
  }
  if (binding.tools_exposed_count !== 0) {
    errors.push("unexpected_tool_exposure");
  }
  if (binding.execution_tools_exposed_count !== 0) {
    errors.push("unexpected_execution_tool_exposure");
  }
  if (Array.isArray(binding.tool_refs) && binding.tool_refs.length > 0) {
    errors.push("unexpected_tool_refs");
  }
  for (const key of expectedFalseKeys) {
    if (binding[key] !== false) {
      errors.push(`expected_false_${key}`);
    }
  }
  for (const key of expectedTrueKeys) {
    if (binding[key] !== true) {
      errors.push(`expected_true_${key}`);
    }
  }
  return errors;
}

function collectUnsafeReceiptPayloadReasons(
  value: unknown,
  path = "request",
): string[] {
  const reasons: string[] = [];
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      reasons.push(...collectUnsafeReceiptPayloadReasons(item, `${path}.${index}`));
    });
    return reasons;
  }
  if (!isRecord(value)) {
    return [...reasons, ...collectSensitiveStringReasons(value, path)];
  }
  for (const [key, child] of Object.entries(value)) {
    const loweredKey = key.toLowerCase();
    const childPath = `${path}.${key}`;
    if (loweredKey === "messages") {
      reasons.push("unexpected_messages_payload");
      continue;
    }
    if (
      /^(raw_.*|.*_body_persisted|sensitive_material_persisted|credential_persisted)$/.test(
        loweredKey,
      )
    ) {
      if (child !== false) {
        reasons.push(`unsafe_persistence_flag:${key}`);
      }
      continue;
    }
    if (
      /(prompt_body|response_body|completion_body|provider_payload|local_path_body)/.test(
        loweredKey,
      )
    ) {
      reasons.push(`unsafe_payload_key:${key}`);
      continue;
    }
    reasons.push(...collectUnsafeReceiptPayloadReasons(child, childPath));
  }
  return reasons;
}

function collectSensitiveStringReasons(
  value: unknown,
  path = "request",
): string[] {
  const reasons: string[] = [];
  if (typeof value === "string") {
    if (
      /\/users\//i.test(value) ||
      /bearer\s+/i.test(value) ||
      /api[_-]?key/i.test(value) ||
      /password/i.test(value) ||
      /private key/i.test(value) ||
      /provider payload/i.test(value) ||
      /raw prompt/i.test(value) ||
      /raw response/i.test(value)
    ) {
      reasons.push(`sensitive_string:${path}`);
    }
    return reasons;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      reasons.push(...collectSensitiveStringReasons(item, `${path}.${index}`));
    });
    return reasons;
  }
  if (isRecord(value)) {
    for (const [key, child] of Object.entries(value)) {
      reasons.push(...collectSensitiveStringReasons(child, `${path}.${key}`));
    }
  }
  return reasons;
}

function turnRouterPreview(postData: string | null) {
  const body = parseBody(postData);
  const sampleId = isSampleId(body.sample_id) ? body.sample_id : undefined;
  const suffix = sampleId ?? "ephemeral-diy-table";
  const contract = sampleId ? sampleContracts[sampleId] : "answer_directly";
  const approvalRequired = contract === "approval_required";
  const memoryRead = contract === "answer_with_reviewed_memory";
  const toolPrep = contract === "prepare_tool_or_action";
  return {
    ok: true,
    result: {
      contract_ref: "contract-ref:turn-router-preview:v1",
      preview_ref: `turn-router-preview:smoke:${suffix}`,
      request_ref: sampleId
        ? `turn-router-preview-request:sample:${suffix}`
        : "turn-router-preview-request:ephemeral-text",
      request_kind: sampleId ? "sample" : "ephemeral_text",
      sample_id: sampleId ?? null,
      selected_turn_contract: contract,
      confidence: 0.96,
      reason_refs: [`reason-ref:turn-router-smoke:${suffix}`],
      risk_flags: approvalRequired ? ["risk-flag:approval-boundary"] : [],
      policy_summary: {
        turn_contract: contract,
        memory_scope: memoryRead ? "reviewed_refs_only" : "none",
        memory_read_allowed: memoryRead,
        memory_write_allowed: false,
        tool_policy: toolPrep ? "read_only_tool_prep" : "none",
        tool_choice: "none",
        tool_execution_allowed: false,
        action_execution_allowed: false,
        workflow_execution_allowed: false,
        context_injection_allowed: false,
        approval_policy: approvalRequired ? "approval_required" : "not_required",
        approval_required: approvalRequired,
        planner: contract === "draft_or_plan",
        durable_state: false,
        state_policy: "none",
        prompt_profile: "diagnostic_preview",
        output_contract: "safe_summary_only",
        runtime_model_call_allowed: false,
        provider_call_allowed: false,
        shell_subprocess_allowed: false,
        browser_network_allowed: false,
        connector_write_allowed: false,
        side_effects_allowed: false,
        execution_ready: false,
      },
      no_effect_proof: noEffectProof(),
      blocked_authority_refs: [
        "blocked-state:turn-router-preview:no-runtime-model-call",
        "blocked-state:turn-router-preview:no-provider-call",
        "blocked-state:turn-router-preview:no-tool-execution",
        "blocked-state:turn-router-preview:no-action-execution",
        "blocked-state:turn-router-preview:no-memory-write",
        "blocked-state:turn-router-preview:no-shell-subprocess",
        "blocked-state:turn-router-preview:no-browser-network",
        "blocked-state:turn-router-preview:no-connector-write",
      ],
      lane_result_refs: [`turn-preflight-lane-result:smoke:${suffix}`],
      source_refs: ["source-ref:turn-router-smoke:fixture"],
      evidence_refs: ["evidence-ref:turn-router-smoke:fixture"],
      route_refs: ["/control-center/turn-router/preview"],
      redactions_applied: ["ephemeral_request_text_omitted"],
      safe_summary: "Smoke fixture preview returns safe refs only.",
      raw_content_included: false,
      ephemeral_request_text_omitted: true,
    },
  };
}

function turnHarnessBinding() {
  return {
    contract_ref: "contract-ref:turn-contract-router:harness-binding:v1",
    binding_ref: bindingRef,
    decision_ref: "turn-decision:v1-chat:v1-chat-completions-uaa-safe-local",
    policy_ref: "policy-ref:turn-contract-router:invocation-policy-compiler:v1",
    turn_contract: "answer_directly",
    safe_summary:
      "Turn harness binding read model prepared safe capability refs without execution.",
    reason_refs: [
      "reason-ref:turn-contract:default-direct-answer",
      "reason-ref:turn-harness-binding:compiled-policy",
    ],
    evidence_refs: ["evidence:turn-contract:deterministic-rules"],
    risk_flags: ["low_risk"],
    memory_scope: "none",
    memory_touched: false,
    reviewed_memory_refs_allowed: false,
    memory_content_retrieved: false,
    memory_write_allowed: false,
    memory_write_performed: false,
    tool_policy: "none",
    tools_exposed_count: 0,
    tool_refs: [],
    execution_tools_exposed_count: 0,
    planner: false,
    durable_state: false,
    approval_policy: "not_required",
    approval_required: false,
    approval_envelope_required: false,
    side_effects_allowed: false,
    execution_ready: false,
    receipt_required: false,
    raw_prompt_persisted: false,
    raw_response_persisted: false,
    raw_memory_body_persisted: false,
    raw_local_path_persisted: false,
    credential_persisted: false,
    safe_refs_only: true,
    blocked_authority_refs: [
      "blocked-authority:no-runtime-model-call",
      "blocked-authority:no-tool-execution",
      "blocked-authority:no-action-execution",
    ],
    no_effect_scope: "turn_harness_binding_compilation_only",
    no_runtime_model_call_performed: true,
    no_provider_call_performed: true,
    no_tool_execution_performed: true,
    no_action_execution_performed: true,
    no_shell_subprocess_performed: true,
    no_browser_network_performed: true,
    no_connector_write_performed: true,
  };
}

function chatReceipt(requestBody: Record<string, unknown> = {}) {
  const binding =
    asRecord(requestBody.turn_harness_binding) ?? turnHarnessBinding();
  return {
    contract_ref: "contract-ref:founder-loop-chat-durable-receipt:v1",
    turn_ref: stringValue(requestBody.turn_ref, chatTurnRef),
    route_ref: stringValue(requestBody.route_ref, "/v1/chat/completions"),
    model_ref: stringValue(requestBody.model_ref, "model-ref:uaa-safe-local"),
    runtime_truth: stringValue(
      requestBody.runtime_truth,
      "local-chat-route-answered",
    ),
    auth_truth: stringValue(requestBody.auth_truth, "local-bearer-accepted"),
    tool_denial_truth: stringValue(
      requestBody.tool_denial_truth,
      "tools-functions-streaming-denied",
    ),
    safe_summary_ref: stringValue(
      requestBody.safe_summary_ref,
      "safe-summary-ref:control-center-chat-probe",
    ),
    turn_harness_binding: turnHarnessReceiptBinding(binding),
    handoff_refs: [
      "handoff-ref:chat-to-actions:uaa-safe-local",
      "handoff-ref:chat-to-plans:uaa-safe-local",
    ],
    receipt_ref: "receipt:chat-turn:control-center-smoke",
    evidence_ref: "evidence-ref:chat-turn:control-center-smoke",
    idempotency_key_ref: "idempotency-ref:control-center-chat-turn:smoke",
    payload_fingerprint_ref:
      "payload-fingerprint:chat-durable-receipt:smoke",
    evidence_refs: [
      "evidence-ref:founder-loop:chat-turn-receipt",
      "evidence-ref:chat-turn:control-center-smoke",
    ],
    blocked_state_refs: [
      "blocked-state:no-model-output-authority",
      "blocked-state:no-tool-execution",
      "blocked-state:no-memory-write",
      "blocked-state:no-action-execution",
    ],
    response_visible: false,
    prompt_body_visible: false,
    completion_body_visible: false,
    model_output_authority: false,
    tool_execution_enabled: false,
    memory_write_authorized: false,
    context_injection_authorized: false,
    provider_sdk_call_enabled: false,
    web_fetch_enabled: false,
    connector_write_enabled: false,
    shell_subprocess_execution_enabled: false,
    action_execution_enabled: false,
    approval_grant_capture_enabled: false,
    production_authority_enabled: false,
    replayed: false,
    created_at: "2026-01-01T00:00:00.000Z",
  };
}

function turnHarnessReceiptBinding(source: Record<string, unknown>) {
  return {
    contract_ref: stringValue(
      source.contract_ref,
      "contract-ref:turn-contract-router:harness-binding:v1",
    ),
    binding_ref: stringValue(source.binding_ref, bindingRef),
    decision_ref: stringValue(
      source.decision_ref,
      "turn-decision:v1-chat:v1-chat-completions-uaa-safe-local",
    ),
    policy_ref: stringValue(
      source.policy_ref,
      "policy-ref:turn-contract-router:invocation-policy-compiler:v1",
    ),
    turn_contract: stringValue(source.turn_contract, "answer_directly"),
    safe_summary: stringValue(
      source.safe_summary,
      "Turn harness binding read model prepared safe capability refs without execution.",
    ),
    reason_refs: stringArrayValue(source.reason_refs, [
      "reason-ref:turn-contract:default-direct-answer",
      "reason-ref:turn-harness-binding:compiled-policy",
    ]),
    evidence_refs: stringArrayValue(source.evidence_refs, [
      "evidence:turn-contract:deterministic-rules",
    ]),
    risk_flags: stringArrayValue(source.risk_flags, ["low_risk"]),
    memory_scope: stringValue(source.memory_scope, "none"),
    tool_policy: stringValue(source.tool_policy, "none"),
    no_effect_scope: stringValue(
      source.no_effect_scope,
      "turn_harness_binding_compilation_only",
    ),
    blocked_authority_refs: stringArrayValue(source.blocked_authority_refs, [
      "blocked-authority:no-runtime-model-call",
      "blocked-authority:no-tool-execution",
      "blocked-authority:no-action-execution",
    ]),
    safe_refs_only: true,
    prompt_body_persisted: false,
    response_body_persisted: false,
    memory_body_persisted: false,
    local_path_body_persisted: false,
    sensitive_material_persisted: false,
    authority_granted: false,
    execution_ready: false,
    side_effects_allowed: false,
    approval_required: false,
    no_runtime_model_call_performed: true,
    no_provider_call_performed: true,
    no_tool_execution_performed: true,
    no_action_execution_performed: true,
    no_shell_subprocess_performed: true,
    no_browser_network_performed: true,
    no_connector_write_performed: true,
  };
}

function noEffectProof() {
  return {
    authority_granted: false,
    execution_permitted: false,
    no_runtime_model_call_performed: true,
    no_provider_call_performed: true,
    no_tool_execution_performed: true,
    no_action_execution_performed: true,
    no_workflow_execution_performed: true,
    no_context_injection_performed: true,
    no_memory_content_retrieved: true,
    no_memory_write_performed: true,
    no_durable_state_write_performed: true,
    no_shell_subprocess_performed: true,
    no_browser_network_performed: true,
    no_connector_write_performed: true,
    invocation_policy_compiled_only: true,
    raw_request_text_persisted: false,
  };
}

function jsonResponse(body: unknown, status = 200) {
  return {
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  };
}

function parseBody(postData: string | null): Record<string, unknown> {
  if (!postData) {
    return {};
  }
  try {
    const parsed = JSON.parse(postData);
    return isRecord(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return isRecord(value) ? value : undefined;
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function stringArrayValue(value: unknown, fallback: string[]): string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string")
    ? value
    : fallback;
}

function isSampleId(value: unknown): value is SampleId {
  return typeof value === "string" && value in sampleContracts;
}
