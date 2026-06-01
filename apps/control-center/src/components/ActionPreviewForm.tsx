import { FormEvent, useState } from "react";
import { containsSecretLike, sanitizeForDisplay } from "../api/redaction";
import { submitActionPreview } from "../api/client";
import type { ActionPreviewDecision, ActionPreviewRequest } from "../api/types";
import { SafeAlert } from "./SafeAlert";

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
  const [purpose, setPurpose] = useState(defaultRequest.purpose);
  const [targetRef, setTargetRef] = useState(defaultRequest.target_ref);
  const [decision, setDecision] = useState<ActionPreviewDecision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setDecision(null);
    const request = { ...defaultRequest, purpose, target_ref: targetRef };
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
      <form className="preview-form" onSubmit={handleSubmit}>
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
