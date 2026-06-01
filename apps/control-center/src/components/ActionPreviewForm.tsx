import { FormEvent, useState } from "react";
import { containsSecretLike, sanitizeForDisplay } from "../api/redaction";
import { submitActionPreview } from "../api/client";
import type { ActionPreviewDecision, ActionPreviewRequest } from "../api/types";
import { SafeAlert } from "./SafeAlert";

const actionKindOptions: Array<{ label: string; value: ActionPreviewRequest["action_kind"] }> = [
  { label: "View status", value: "view_status" },
  { label: "View receipt", value: "view_receipt" },
  { label: "View event summary", value: "view_event_summary" },
  { label: "Preview action", value: "preview_action" },
  { label: "Preview approval", value: "preview_approval" },
  { label: "Preview runtime", value: "preview_runtime" },
  { label: "Preview remote worker", value: "preview_remote_worker" },
  { label: "Preview mobile capability", value: "preview_mobile_capability" }
];

const defaultRequest: ActionPreviewRequest = {
  request_id: "frontend_preview_request",
  actor_context: { actor_type: "user", actor_id: "local_operator" },
  action_kind: "view_status",
  target_ref: "dashboard",
  purpose: "Review read-only Control Center status.",
  risk_level: "safe",
  data_classification: "system_internal",
  consent_refs: [],
  metadata: { frontend_shell: true, preview_only: true }
};

export function ActionPreviewForm() {
  const [actionKind, setActionKind] = useState<ActionPreviewRequest["action_kind"]>(defaultRequest.action_kind);
  const [purpose, setPurpose] = useState(defaultRequest.purpose);
  const [targetRef, setTargetRef] = useState(defaultRequest.target_ref);
  const [decision, setDecision] = useState<ActionPreviewDecision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setDecision(null);
    const request = { ...defaultRequest, action_kind: actionKind, purpose, target_ref: targetRef };
    if (containsSecretLike(request)) {
      setPurpose("");
      setTargetRef(defaultRequest.target_ref);
      setError("Secret-like input was redacted before display and not submitted.");
      return;
    }
    setSubmitting(true);
    try {
      setDecision(await submitActionPreview(request));
    } catch (err) {
      setError(sanitizeForDisplay(err instanceof Error ? err.message : "Preview request failed safely."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Action Preview</h2>
        <span>POST /control-center/actions/preview</span>
      </div>
      <SafeAlert
        title="Preview only action request"
        message="This form asks the backend for a policy preview only. It never runs, enables, grants, deploys, or dispatches anything."
      />
      <form className="preview-form" onSubmit={handleSubmit}>
        <label>
          Action kind
          <select value={actionKind} onChange={(event) => setActionKind(event.target.value as ActionPreviewRequest["action_kind"])}>
            {actionKindOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
            <option disabled value="disabled_execute">
              Blocked execution action
            </option>
          </select>
        </label>
        <label>
          Target reference
          <input value={targetRef} onChange={(event) => setTargetRef(event.target.value)} />
        </label>
        <label>
          Purpose
          <textarea value={purpose} onChange={(event) => setPurpose(event.target.value)} rows={3} />
        </label>
        <button disabled={submitting} type="submit">
          {submitting ? "Previewing..." : "Preview action"}
        </button>
      </form>
      {error ? <SafeAlert title="Safe rejection" message={error} tone="warning" /> : null}
      {decision ? (
        <section className="decision" aria-label="Action preview decision">
          <strong>{decision.status}</strong>
          <p>{decision.safe_message}</p>
          <p>{decision.preview_summary}</p>
          <small>{decision.reason_codes.join(", ")}</small>
        </section>
      ) : null}
    </section>
  );
}
