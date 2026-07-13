from __future__ import annotations


FOUNDER_LOOP_EXACT_ATTENTION_ROUTES = frozenset(
    {
        "/control-center/today/exact-action/{today_item_ref}/status",
        "/control-center/today/exact-action/source-review",
        "/control-center/today/exact-action/prepare",
        "/control-center/today/exact-action/approve",
        "/control-center/today/exact-action/execute",
    }
)
