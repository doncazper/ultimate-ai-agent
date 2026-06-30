#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from ultimate_ai_agent.core.control_center.dashboard import (
    build_provider_credential_readiness_summary,
)
from ultimate_ai_agent.core.providers import (
    ProviderRouterDryRunNeed,
    ProviderRouterDryRunRequest,
    evaluate_provider_router_dry_run,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect proposal-only provider router dry-run posture."
    )
    parser.add_argument(
        "--router-run-ref",
        default="provider-router-run-ref:dry-run:local-cli",
        help="Safe router run ref to show in the inspection output.",
    )
    parser.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:provider-router:dry-run:local-cli",
        help="Safe idempotency ref for the dry-run proposal output.",
    )
    parser.add_argument(
        "--task-ref",
        default="task-ref:provider-router:local-cli",
        help="Safe task ref; raw task text is not accepted by this inspector.",
    )
    parser.add_argument(
        "--model-need-ref",
        default="model-need-ref:provider-router:text-generation",
        help="Safe model-need ref; raw prompt/model payloads are not accepted.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    readiness = build_provider_credential_readiness_summary()
    request = ProviderRouterDryRunRequest(
        router_run_ref=args.router_run_ref,
        idempotency_ref=args.idempotency_ref,
        need=ProviderRouterDryRunNeed(
            task_ref=args.task_ref,
            model_need_ref=args.model_need_ref,
        ),
    )
    proposal = evaluate_provider_router_dry_run(
        request,
        provider_readiness_items=readiness.providers,
    )
    print(json.dumps(proposal.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
