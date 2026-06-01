from ultimate_ai_agent.core.truth import RetrievalLogEntry


def test_retrieval_log_stores_refs_not_raw_payloads():
    entry = RetrievalLogEntry(
        retrieval_id="ret_123",
        run_id="run_123",
        query="M4.5 truth router",
        source_ids_considered=["src_canonical", "src_memory"],
        source_ids_selected=["src_canonical"],
        chunks_or_refs=["docs/canonical/60_truth_source_router.md:1"],
        filters_applied=["authority_rank", "freshness"],
        reranker_ref="reranker_contract_only",
        result_count=1,
        redactions_applied=["private_source_summary"],
    )

    assert entry.reranker_ref == "reranker_contract_only"
    assert entry.result_count == 1
