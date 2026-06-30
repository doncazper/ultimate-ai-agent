import type {
  ProviderCatalog,
  ProviderSetupCard,
  TokenCostExample,
} from "../api/types";

type ProviderCatalogMode = "setup" | "settings" | "models";

const MODE_COPY: Record<
  ProviderCatalogMode,
  { eyebrow: string; title: string; summary: string; status: string }
> = {
  setup: {
    eyebrow: "Provider account guidance",
    title: "Provider Catalog",
    status: "guidance only",
    summary:
      "Reviewed provider setup, docs, pricing, and env-var style labels are visible as static metadata. UAA does not collect secrets, validate providers, call providers, or refresh pricing here.",
  },
  settings: {
    eyebrow: "Providers and Credentials",
    title: "Provider Guidance",
    status: "metadata only",
    summary:
      "Settings shows provider readiness and cost blockers as posture. Catalog visibility does not configure a provider or grant runtime authority.",
  },
  models: {
    eyebrow: "Cost and token literacy",
    title: "Provider Cost Literacy",
    status: "cost blocked",
    summary:
      "Models shows token billing concepts, synthetic examples, and budget requirements for future frontier providers without quoting live prices or authorizing model use.",
  },
};

export function ProviderCatalogPanel({
  catalog,
  mode,
}: {
  catalog: ProviderCatalog;
  mode: ProviderCatalogMode;
}) {
  const copy = MODE_COPY[mode];
  const visibleCards =
    mode === "models"
      ? catalog.provider_cards.slice(0, 8)
      : catalog.provider_cards;
  const visibleExamples =
    mode === "models" ? catalog.token_cost_examples : catalog.token_cost_examples.slice(0, 3);

  return (
    <section className="page-section" aria-labelledby={`provider-catalog-${mode}`}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{copy.eyebrow}</p>
          <h2 id={`provider-catalog-${mode}`}>{copy.title}</h2>
        </div>
        <span className="status-pill compact">{copy.status}</span>
      </div>
      <p className="section-copy">{copy.summary}</p>

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Authority posture</h3>
            <span>{catalog.catalog_ref}</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Last reviewed</dt>
              <dd>{catalog.last_verified_at}</dd>
            </div>
            <div>
              <dt>Catalog grants authority</dt>
              <dd>{catalog.catalog_visibility_grants_authority ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Provider SDK calls</dt>
              <dd>{catalog.no_provider_sdk_calls ? "blocked" : "enabled"}</dd>
            </div>
            <div>
              <dt>Model invocation</dt>
              <dd>{catalog.no_model_invocation ? "blocked" : "enabled"}</dd>
            </div>
            <div>
              <dt>Runtime web fetching</dt>
              <dd>{catalog.no_runtime_web_fetching ? "blocked" : "enabled"}</dd>
            </div>
            <div>
              <dt>Automatic pricing refresh</dt>
              <dd>{catalog.no_automatic_pricing_fetch ? "blocked" : "enabled"}</dd>
            </div>
            <div>
              <dt>Secret entry controls</dt>
              <dd>{catalog.no_credential_input ? "not available" : "available"}</dd>
            </div>
          </dl>
          <div className="note-list" aria-label="Provider catalog blocked authorities">
            {catalog.blocked_authorities.map((authority) => (
              <span key={authority}>{authority}</span>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h3>Budget posture</h3>
            <span>{catalog.budget_posture.state}</span>
          </div>
          <p>{catalog.budget_posture.safe_summary}</p>
          <dl className="metadata-list">
            <div>
              <dt>Unknown paid cost</dt>
              <dd>
                {catalog.budget_posture.unknown_paid_cost_requires_explicit_approval
                  ? "approval required"
                  : "not required"}
              </dd>
            </div>
            <div>
              <dt>Above-budget estimate</dt>
              <dd>
                {catalog.budget_posture.estimated_cost_above_budget_blocks_use
                  ? "blocked"
                  : "not blocked"}
              </dd>
            </div>
            <div>
              <dt>Provider/model refs</dt>
              <dd>{catalog.budget_posture.provider_model_refs_required ? "required" : "optional"}</dd>
            </div>
            <div>
              <dt>Receipt refs</dt>
              <dd>{catalog.budget_posture.receipt_ref_required ? "required" : "optional"}</dd>
            </div>
            <div>
              <dt>CostGovernor binding</dt>
              <dd>
                {catalog.budget_posture.cost_governor_binding_required
                  ? "required"
                  : "optional"}
              </dd>
            </div>
          </dl>
        </article>
      </div>

      {visibleExamples.length > 0 ? (
        <article className="panel">
          <div className="panel-heading">
            <h3>Token cost examples</h3>
            <span>synthetic</span>
          </div>
          <div className="provider-readiness-list">
            {visibleExamples.map((example) => (
              <TokenCostExampleCard key={example.example_ref} example={example} />
            ))}
          </div>
        </article>
      ) : null}

      <article className="panel">
        <div className="panel-heading">
          <h3>Provider setup cards</h3>
          <span>{visibleCards.length} shown</span>
        </div>
        <div className="provider-readiness-list" aria-label="Provider catalog setup cards">
          {visibleCards.map((card) => (
            <ProviderSetupCardView key={card.provider_ref} card={card} />
          ))}
        </div>
      </article>
    </section>
  );
}

function TokenCostExampleCard({ example }: { example: TokenCostExample }) {
  return (
    <section className="provider-readiness-item">
      <div className="panel-heading compact-heading">
        <h4>{example.label}</h4>
        <span>{example.synthetic_only ? "synthetic only" : "unsafe"}</span>
      </div>
      <p>{example.safe_summary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Workload</dt>
          <dd>{example.workload_kind}</dd>
        </div>
        <div>
          <dt>Live price quote</dt>
          <dd>{example.no_live_price_amounts ? "no" : "yes"}</dd>
        </div>
        <div>
          <dt>Unknown paid cost</dt>
          <dd>
            {example.approval_required_for_paid_use
              ? "approval required"
              : "not required"}
          </dd>
        </div>
      </dl>
      <div className="note-list" aria-label={`${example.label} cost driver notes`}>
        {example.cost_driver_notes.map((note) => (
          <span key={note}>{note}</span>
        ))}
      </div>
    </section>
  );
}

function ProviderSetupCardView({ card }: { card: ProviderSetupCard }) {
  return (
    <section className="provider-readiness-item">
      <div className="panel-heading compact-heading">
        <h4>{card.provider_label}</h4>
        <span>{card.authority_state}</span>
      </div>
      <p>{card.authority_posture.safe_summary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Provider class</dt>
          <dd>{card.provider_class}</dd>
        </div>
        <div>
          <dt>Env-var style</dt>
          <dd>{card.env_var_styles.join(", ")}</dd>
        </div>
        <div>
          <dt>Billing prerequisite</dt>
          <dd>{card.billing_prerequisite}</dd>
        </div>
        <div>
          <dt>Pricing may change</dt>
          <dd>{card.pricing_may_change ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Billing authority</dt>
          <dd>{card.not_billing_authority ? "not claimed" : "claimed"}</dd>
        </div>
        <div>
          <dt>Provider validation</dt>
          <dd>{card.credential_validation_enabled ? "enabled" : "blocked"}</dd>
        </div>
        <div>
          <dt>Provider SDK calls</dt>
          <dd>{card.provider_sdk_call_enabled ? "enabled" : "blocked"}</dd>
        </div>
        <div>
          <dt>Model invocation</dt>
          <dd>{card.model_invocation_enabled ? "enabled" : "blocked"}</dd>
        </div>
      </dl>
      <div className="note-list" aria-label={`${card.provider_label} source links`}>
        <SourceRefLabel href={card.setup_link} label="Setup docs" />
        <SourceRefLabel href={card.api_docs_link} label="API docs" />
        <SourceRefLabel href={card.pricing_link} label="Pricing docs" />
      </div>
      <div className="note-list" aria-label={`${card.provider_label} token notes`}>
        {card.token_cost_notes.map((note) => (
          <span key={note}>{note}</span>
        ))}
      </div>
      <div className="note-list" aria-label={`${card.provider_label} blockers`}>
        {card.authority_posture.blocker_codes.slice(0, 6).map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
    </section>
  );
}

function SourceRefLabel({ href, label }: { href: string; label: string }) {
  // Explicitly block javascript:, data:, vbscript: protocols to prevent XSS
  if (/^https:\/\//i.test(href)) {
    return (
      <a href={href} rel="noreferrer noopener" target="_blank">
        {label}
      </a>
    );
  }
  return <span>{label}</span>;
}
