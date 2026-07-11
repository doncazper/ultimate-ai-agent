from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.productization import (
    REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS,
    PublicDocsWikiReadinessRequest,
)


def _request(**overrides: Any) -> PublicDocsWikiReadinessRequest:
    data = {
        "request_ref": "public-docs-wiki-readiness-request:m147",
        "public_doc_ref": "public-docs-wiki-readiness:m147",
        "baseline_ref": "baseline:v1.7.2",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS),
        "public_doc_refs": [
            "public-doc:m147:readme",
            "public-doc:m147:safety-overview",
        ],
        "wiki_readiness_refs": [
            "wiki-readiness:m147:landing-index",
            "wiki-readiness:m147:no-upload",
        ],
        "docs_index_refs": [
            "docs-index:m147:canonical-map-entry",
            "docs-index:m147:no-generated-site",
        ],
        "canonical_map_refs": [
            "canonical-map:m147:public-docs",
            "canonical-map:m147:wiki-readiness",
        ],
        "release_note_refs": [
            "release-note:m147:checkpoint",
            "release-note:m147:no-release-publish",
        ],
        "disclosure_review_refs": [
            "disclosure-review:m147:authority-boundary",
            "disclosure-review:m147:no-sensitive-content",
        ],
        "publishing_checklist_refs": [
            "publishing-checklist:m147:manual-review",
            "publishing-checklist:m147:no-automation",
        ],
        "audit_ref": "audit:m147:public-docs-wiki-readiness",
        "replay_ref": "replay:m147:public-docs-wiki-readiness",
        "revocation_ref": "revocation:m147:public-docs-wiki-readiness",
        "kill_switch_ref": "kill-switch:m147:public-docs-wiki-readiness",
        "no_effect_receipt_plan_ref": (
            "receipt-plan:m147:public-docs-wiki-readiness:no-effect"
        ),
        "safe_summary": "Record public docs and wiki readiness refs without publishing authority.",
    }
    data.update(overrides)
    return PublicDocsWikiReadinessRequest(**data)
