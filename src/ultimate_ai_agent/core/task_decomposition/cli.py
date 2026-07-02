from __future__ import annotations
from typing import Any

import argparse
import sys

from ultimate_ai_agent.core.task_decomposition.contracts import CapabilityCallContext
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskDecompositionRequest,
    TaskDecompositionRunRequest,
    TaskDecompositionService,
    dump_json,
)


def _service(args: Any) -> TaskDecompositionService:
    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(
            registry_path=args.registry,
            create_if_missing=True,
        )
    )
    return TaskDecompositionService(registry_store=store)


def _cmd_init_examples(args: Any) -> int:
    service = _service(args)
    catalog = service.ensure_examples()
    print(dump_json({"registered": [card["id"] for card in catalog], "registry_path": args.registry}))
    return 0


def _cmd_catalog(args: Any) -> int:
    service = _service(args)
    print(dump_json(service.catalog()))
    return 0


def _cmd_decompose(args: Any) -> int:
    service = _service(args)
    result = service.decompose(TaskDecompositionRequest(raw_request=args.request, context={}))
    print(dump_json(result))
    return 0 if result.validation.valid else 2


def _cmd_run(args: Any) -> int:
    service = _service(args)
    approval_refs = {}
    for value in args.approval_ref or []:
        capability_id, _, approval_ref = value.partition("=")
        if capability_id and approval_ref:
            approval_refs[capability_id] = approval_ref
    result = service.run_sync(
        TaskDecompositionRunRequest(
            raw_request=args.request,
            call_context=CapabilityCallContext(
                run_id=args.run_id,
                actor_id=args.actor_id,
                approval_refs=approval_refs,
            ),
        )
    )
    print(dump_json(result))
    return 0 if result.execution is not None and result.execution.status == "succeeded" else 2


def _cmd_inspect_run(args: Any) -> int:
    service = _service(args)
    lifecycle = service.durable_run_lifecycle(
        args.run_id,
        include_receipts=not args.omit_receipts,
        limit=args.limit,
    )
    if lifecycle is None:
        print(
            dump_json(
                {
                    "schema_version": "task-decomposition-cli-inspect-run.v1",
                    "command_ref": "cli:task-decomposition:inspect-run",
                    "safe_refs_only": True,
                    "raw_content_omitted": True,
                    "success": False,
                    "error_ref": "error-ref:task-decomposition:durable-run-not-found",
                }
            )
        )
        return 1
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-run.v1",
                "command_ref": "cli:task-decomposition:inspect-run",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "success": True,
                "lifecycle": lifecycle,
            }
        )
    )
    return 0


def _cmd_inspect_approvals(args: Any) -> int:
    service = _service(args)
    queue = service.run_attached_approval_queue(args.run_id, limit=args.limit)
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-approvals.v1",
                "command_ref": "cli:task-decomposition:inspect-approvals",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "approval_authority_enabled": False,
                "execution_authority_enabled": False,
                "success": True,
                "approval_queue": queue,
            }
        )
    )
    return 0


def _cmd_inspect_approval_review(args: Any) -> int:
    service = _service(args)
    review = service.approval_review(args.run_id, limit=args.limit)
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-approval-review.v1",
                "command_ref": "cli:task-decomposition:inspect-approval-review",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "approval_refs_are_identifiers_only": True,
                "approval_authority_enabled": False,
                "execution_authority_enabled": False,
                "provider_model_calls_enabled": False,
                "tool_execution_enabled": False,
                "connector_writes_enabled": False,
                "background_worker_enabled": False,
                "scheduler_enabled": False,
                "success": True,
                "approval_review": review,
            }
        )
    )
    return 0


def _cmd_inspect_run_progress(args: Any) -> int:
    service = _service(args)
    progress = service.durable_run_progress(args.run_id, limit=args.limit)
    if progress is None:
        print(
            dump_json(
                {
                    "schema_version": "task-decomposition-cli-inspect-run-progress.v1",
                    "command_ref": "cli:task-decomposition:inspect-run-progress",
                    "safe_refs_only": True,
                    "raw_content_omitted": True,
                    "success": False,
                    "error_ref": "error-ref:task-decomposition:durable-run-progress-not-found",
                }
            )
        )
        return 1
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-run-progress.v1",
                "command_ref": "cli:task-decomposition:inspect-run-progress",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "live_streaming_runtime_enabled": False,
                "provider_model_calls_enabled": False,
                "execution_authority_enabled": False,
                "success": True,
                "progress": progress,
            }
        )
    )
    return 0


def _cmd_inspect_run_observability(args: Any) -> int:
    service = _service(args)
    observability = service.run_observability(
        args.run_id,
        lifecycle_limit=args.lifecycle_limit,
        related_limit=args.related_limit,
    )
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-run-observability.v1",
                "command_ref": "cli:task-decomposition:inspect-run-observability",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "read_only": True,
                "cancel_resume_controls_enabled": False,
                "live_streaming_runtime_enabled": False,
                "provider_model_calls_enabled": False,
                "tool_execution_enabled": False,
                "connector_writes_enabled": False,
                "connector_sends_enabled": False,
                "background_worker_enabled": False,
                "scheduler_enabled": False,
                "autonomous_execution_enabled": False,
                "success": True,
                "run_observability": observability,
            }
        )
    )
    return 0


def _cmd_inspect_coworker_workers(args: Any) -> int:
    service = _service(args)
    workers = service.background_coworker_workers(args.run_id, limit=args.limit)
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-coworker-workers.v1",
                "command_ref": "cli:task-decomposition:inspect-coworker-workers",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "background_execution_enabled": False,
                "scheduler_enabled": False,
                "worker_runtime_started": False,
                "queue_consumer_enabled": False,
                "execution_authority_enabled": False,
                "success": True,
                "coworker_workers": workers,
            }
        )
    )
    return 0


def _cmd_inspect_connector_deliveries(args: Any) -> int:
    service = _service(args)
    deliveries = service.connector_deliveries(args.run_id, limit=args.limit)
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-connector-deliveries.v1",
                "command_ref": "cli:task-decomposition:inspect-connector-deliveries",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "connector_write_enabled": False,
                "connector_send_enabled": False,
                "account_sync_enabled": False,
                "oauth_enabled": False,
                "credential_collection_enabled": False,
                "background_delivery_worker_enabled": False,
                "scheduler_enabled": False,
                "delivery_authority_enabled": False,
                "success": True,
                "connector_deliveries": deliveries,
            }
        )
    )
    return 0


def _cmd_inspect_connector_delivery_review(args: Any) -> int:
    service = _service(args)
    review_queue = service.connector_delivery_review_queue(args.run_id, limit=args.limit)
    print(
        dump_json(
            {
                "schema_version": "task-decomposition-cli-inspect-connector-delivery-review.v1",
                "command_ref": "cli:task-decomposition:inspect-connector-delivery-review",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "connector_write_enabled": False,
                "connector_send_enabled": False,
                "account_sync_enabled": False,
                "oauth_enabled": False,
                "credential_collection_enabled": False,
                "provider_model_calls_enabled": False,
                "live_web_runtime_enabled": False,
                "browser_runtime_enabled": False,
                "shell_runtime_enabled": False,
                "background_delivery_worker_enabled": False,
                "scheduler_enabled": False,
                "delivery_authority_enabled": False,
                "success": True,
                "connector_delivery_review_queue": review_queue,
            }
        )
    )
    return 0


def _cmd_serve_api(args: Any) -> int:
    import uvicorn

    uvicorn.run(
        "ultimate_ai_agent.core.task_decomposition.dev_api:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local/dev task decomposition registry CLI.")
    parser.add_argument("--registry", default=".uaa/task_decomposition_registry.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_examples = subparsers.add_parser("init-examples", help="Register the built-in safe example capabilities.")
    init_examples.set_defaults(func=_cmd_init_examples)

    catalog = subparsers.add_parser("catalog", help="List compact capability routing cards.")
    catalog.set_defaults(func=_cmd_catalog)

    decompose = subparsers.add_parser("decompose", help="Decompose a request without executing it.")
    decompose.add_argument("request")
    decompose.set_defaults(func=_cmd_decompose)

    run = subparsers.add_parser("run", help="Decompose and execute using registered local handlers.")
    run.add_argument("request")
    run.add_argument("--run-id", default="task-decomposition-run:cli")
    run.add_argument("--actor-id", default="local_cli_user")
    run.add_argument("--approval-ref", action="append", help="Bind capability_id=approval_ref for LocalApprovalAuthority.")
    run.set_defaults(func=_cmd_run)

    inspect_run = subparsers.add_parser("inspect-run", help="Inspect a durable run lifecycle read model.")
    inspect_run.add_argument("run_id")
    inspect_run.add_argument("--limit", type=int, default=50)
    inspect_run.add_argument("--omit-receipts", action="store_true")
    inspect_run.set_defaults(func=_cmd_inspect_run)

    inspect_approvals = subparsers.add_parser(
        "inspect-approvals",
        help="Inspect run-attached approval queue refs without granting authority.",
    )
    inspect_approvals.add_argument("run_id", nargs="?")
    inspect_approvals.add_argument("--limit", type=int, default=50)
    inspect_approvals.set_defaults(func=_cmd_inspect_approvals)

    inspect_approval_review = subparsers.add_parser(
        "inspect-approval-review",
        help="Inspect the unified approval review without granting authority.",
    )
    inspect_approval_review.add_argument("run_id", nargs="?")
    inspect_approval_review.add_argument("--limit", type=int, default=50)
    inspect_approval_review.set_defaults(func=_cmd_inspect_approval_review)

    inspect_run_progress = subparsers.add_parser(
        "inspect-run-progress",
        help="Inspect a durable run progress read model without live streaming authority.",
    )
    inspect_run_progress.add_argument("run_id")
    inspect_run_progress.add_argument("--limit", type=int, default=50)
    inspect_run_progress.set_defaults(func=_cmd_inspect_run_progress)

    inspect_run_observability = subparsers.add_parser(
        "inspect-run-observability",
        help="Inspect aggregate run observability refs without runtime authority.",
    )
    inspect_run_observability.add_argument("run_id", nargs="?")
    inspect_run_observability.add_argument("--lifecycle-limit", type=int, default=50)
    inspect_run_observability.add_argument("--related-limit", type=int, default=50)
    inspect_run_observability.set_defaults(func=_cmd_inspect_run_observability)

    inspect_coworker_workers = subparsers.add_parser(
        "inspect-coworker-workers",
        help="Inspect metadata-only coworker worker refs without background execution authority.",
    )
    inspect_coworker_workers.add_argument("run_id", nargs="?")
    inspect_coworker_workers.add_argument("--limit", type=int, default=100)
    inspect_coworker_workers.set_defaults(func=_cmd_inspect_coworker_workers)

    inspect_connector_deliveries = subparsers.add_parser(
        "inspect-connector-deliveries",
        help="Inspect contract-only connector delivery refs without send or write authority.",
    )
    inspect_connector_deliveries.add_argument("run_id", nargs="?")
    inspect_connector_deliveries.add_argument("--limit", type=int, default=100)
    inspect_connector_deliveries.set_defaults(func=_cmd_inspect_connector_deliveries)

    inspect_connector_delivery_review = subparsers.add_parser(
        "inspect-connector-delivery-review",
        help="Inspect the connector delivery review queue without send or write authority.",
    )
    inspect_connector_delivery_review.add_argument("run_id", nargs="?")
    inspect_connector_delivery_review.add_argument("--limit", type=int, default=100)
    inspect_connector_delivery_review.set_defaults(func=_cmd_inspect_connector_delivery_review)

    serve = subparsers.add_parser("serve-api", help="Serve the local/dev task decomposition API.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.set_defaults(func=_cmd_serve_api)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
