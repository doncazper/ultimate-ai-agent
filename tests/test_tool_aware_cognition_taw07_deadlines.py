from __future__ import annotations

import json
from itertools import count
from pathlib import Path
from types import SimpleNamespace

import pytest

from ultimate_ai_agent.core.capabilities import retrieval
from ultimate_ai_agent.core.capabilities.chat_shadow import ShadowChatAction
from ultimate_ai_agent.core.evals import tool_aware_hardening as hardening
from ultimate_ai_agent.core.evals.tool_aware_corpus import (
    DevelopmentCorpusManifest,
    reconstruct_development_case_payload,
)


def _set_retrieval_elapsed_clock(
    monkeypatch: pytest.MonkeyPatch, *, elapsed_ms: int = 1
) -> None:
    ticks = count(0, elapsed_ms * 1_000_000)
    # Replace only retrieval's clock binding, not the shared time module.
    monkeypatch.setattr(
        retrieval, "time", SimpleNamespace(perf_counter_ns=lambda: next(ticks))
    )


@pytest.mark.parametrize(
    ("boundary", "budget_ms", "failure_message"),
    [
        (
            "build_progressive_capability_cache",
            300,
            "compact cache build latency budget exceeded",
        ),
        (
            "discover_capabilities",
            100,
            "candidate hydration did not bind the selected operation",
        ),
        (
            "hydrate_capability_manifests",
            200,
            "candidate hydration did not bind the selected operation",
        ),
    ],
)
@pytest.mark.parametrize("overrun_ms", [0, 1])
def test_source_decision_enforces_real_retrieval_deadlines(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    budget_ms: int,
    failure_message: str,
    overrun_ms: int,
) -> None:
    _set_retrieval_elapsed_clock(monkeypatch)
    original_boundary = getattr(hardening, boundary)
    invocations = 0

    def measured_boundary(*args, **kwargs):
        nonlocal invocations
        invocations += 1
        with monkeypatch.context() as measurement:
            _set_retrieval_elapsed_clock(
                measurement, elapsed_ms=budget_ms + overrun_ms
            )
            return original_boundary(*args, **kwargs)

    monkeypatch.setattr(hardening, boundary, measured_boundary)
    corpus_path = (
        Path(__file__).resolve().parents[1]
        / "docs/evals/tool_aware_cognition_taw07_development_corpus_v1.json"
    )
    corpus = DevelopmentCorpusManifest.model_validate(
        json.loads(corpus_path.read_text(encoding="utf-8"))
    )
    case = next(
        item
        for item in corpus.cases
        if "parameter-ref:taw07:reviewed-read-operation" in item.parameter_refs
    )

    def decide():
        return hardening.build_taw07_source_decision(
            case_payload=reconstruct_development_case_payload(corpus, case.case_ref),
            catalog_state=hardening.CatalogState.healthy,
            replay_mode=hardening.ReplayMode.candidate_shadow,
        )

    if overrun_ms:
        with pytest.raises(ValueError, match=failure_message):
            decide()
    else:
        decision = decide()
        assert decision.action == ShadowChatAction.record_capability_candidate
        assert decision.execution_performed is False
        assert decision.provider_call_performed is False
        assert decision.authority_granted is False
    assert invocations == 1
