from __future__ import annotations

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


def _service(args) -> TaskDecompositionService:
    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(
            registry_path=args.registry,
            create_if_missing=True,
        )
    )
    return TaskDecompositionService(registry_store=store)


def _cmd_init_examples(args) -> int:
    service = _service(args)
    catalog = service.ensure_examples()
    print(dump_json({"registered": [card["id"] for card in catalog], "registry_path": args.registry}))
    return 0


def _cmd_catalog(args) -> int:
    service = _service(args)
    print(dump_json(service.catalog()))
    return 0


def _cmd_decompose(args) -> int:
    service = _service(args)
    result = service.decompose(TaskDecompositionRequest(raw_request=args.request, context={}))
    print(dump_json(result))
    return 0 if result.validation.valid else 2


def _cmd_run(args) -> int:
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


def _cmd_serve_api(args) -> int:
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
