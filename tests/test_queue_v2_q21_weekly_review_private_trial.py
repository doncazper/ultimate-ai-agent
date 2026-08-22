from __future__ import annotations

from scripts import verify_product_loop_008_weekly_ceo_review as weekly_verifier
from scripts import verify_queue_v2_q21_weekly_review_private_trial as q21


def test_q21_completion_report_is_safe_complete_and_owned() -> None:
    assert q21.verify() == []


def test_weekly_review_verifier_ignores_unrelated_shared_client_adapters() -> None:
    failures: list[str] = []
    client_source = q21.ROOT.joinpath(
        "apps/control-center/src/api/client.ts"
    ).read_text(encoding="utf-8")
    scoped = "\n".join(
        [
            weekly_verifier._bounded_source_slice(
                client_source,
                start="const WEEKLY_CEO_REVIEW_V1_DENIED_FLAGS",
                end="const FOUNDER_LOOP_PRODUCT_PROOF_DENIED_FLAGS",
                label="Weekly CEO Review client constants",
                failures=failures,
            ),
            weekly_verifier._bounded_source_slice(
                client_source,
                start="function isSafeWeeklyCeoReviewV1ReadModel",
                end="function isSafeFounderLoopProductProofReadModel",
                label="Weekly CEO Review client validator",
                failures=failures,
            ),
        ]
    )

    assert failures == []
    assert "isSafeWeeklyCeoReviewV1ReadModel" in scoped
    assert "firecrawl" not in scoped.lower()
    assert weekly_verifier.main() == 0
