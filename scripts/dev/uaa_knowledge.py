#!/usr/bin/env python3
"""Inspect and operate the local, rights-gated UAA Knowledge Dump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.knowledge_dump import (
    KnowledgeDumpStore,
    KnowledgeRightsBasis,
    KnowledgeSourceKind,
)


def _actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_knowledge_operator",
        authority_source=AuthoritySource.manual_operator_action,
    )


def _dump(value: object) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")  # type: ignore[union-attr]
    print(json.dumps(value, indent=2, sort_keys=True))


def _prepare(store: KnowledgeDumpStore, args: argparse.Namespace):  # type: ignore[no-untyped-def]
    return store.prepare_ingest(
        args.source,
        title=args.title,
        rights_basis=KnowledgeRightsBasis(args.rights_basis),
        rights_evidence_ref=args.rights_evidence_ref,
        idempotency_key=args.idempotency_key,
        catalog_source_id=args.catalog_source_id,
        source_kind=KnowledgeSourceKind(args.source_kind),
        category=args.category,
        collection=args.collection,
        tags=args.tag,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--store", default=".uaa/knowledge_dump", help="Local Knowledge Dump directory."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("source", type=Path)
    shared.add_argument("--title", required=True)
    shared.add_argument(
        "--rights-basis",
        required=True,
        choices=[item.value for item in KnowledgeRightsBasis],
    )
    shared.add_argument("--rights-evidence-ref", required=True)
    shared.add_argument("--idempotency-key", required=True)
    shared.add_argument("--catalog-source-id")
    shared.add_argument(
        "--source-kind",
        choices=[item.value for item in KnowledgeSourceKind],
        default="reference",
    )
    shared.add_argument("--category", default="uncategorized")
    shared.add_argument("--collection")
    shared.add_argument("--tag", action="append", default=[])

    subparsers.add_parser(
        "plan-ingest", parents=[shared], help="Build a content-free exact ingest plan."
    )
    ingest = subparsers.add_parser(
        "ingest", parents=[shared], help="Approve and apply one exact local ingest."
    )
    ingest.add_argument(
        "--approve-exact-scope",
        metavar="EXACT_SCOPE_REF",
        help=(
            "Explicitly attest rights and approve only the exact scope ref printed "
            "by plan-ingest."
        ),
    )

    listing = subparsers.add_parser(
        "list", help="List and sort stored source metadata without source text."
    )
    listing.add_argument(
        "--source-kind", choices=[item.value for item in KnowledgeSourceKind]
    )
    listing.add_argument("--category")
    listing.add_argument("--collection")
    listing.add_argument("--tag")
    listing.add_argument(
        "--sort-by",
        choices=["newest", "oldest", "title", "category", "source_kind"],
        default="newest",
    )
    subparsers.add_parser(
        "inventory", help="Show category, collection, tag, type, and format counts."
    )
    categorize = subparsers.add_parser(
        "categorize", help="Exact-approved navigation metadata update."
    )
    categorize.add_argument("document_ref")
    categorize.add_argument(
        "--source-kind",
        choices=[item.value for item in KnowledgeSourceKind],
        required=True,
    )
    categorize.add_argument("--category", required=True)
    categorize.add_argument("--collection")
    categorize.add_argument("--tag", action="append", default=[])
    categorize.add_argument("--idempotency-key", required=True)
    categorize.add_argument("--approve-exact-scope", metavar="EXACT_SCOPE_REF")
    search = subparsers.add_parser(
        "search", help="Lexically search and return cited local chunks."
    )
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument(
        "--source-kind", choices=[item.value for item in KnowledgeSourceKind]
    )
    search.add_argument("--category")
    search.add_argument("--collection")
    search.add_argument("--tag")
    context = subparsers.add_parser(
        "prepare-context", help="Prepare an explicit cited Chat context pack."
    )
    context.add_argument("query")
    context.add_argument("--limit", type=int, default=8)
    context.add_argument("--max-characters", type=int, default=8000)
    context.add_argument(
        "--source-kind", choices=[item.value for item in KnowledgeSourceKind]
    )
    context.add_argument("--category")
    context.add_argument("--collection")
    context.add_argument("--tag")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = KnowledgeDumpStore(args.store)
    if args.command == "plan-ingest":
        _dump(_prepare(store, args).plan)
        return 0
    if args.command == "ingest":
        prepared = _prepare(store, args)
        if args.approve_exact_scope != prepared.plan.exact_scope_ref:
            _dump(prepared.plan)
            reason = (
                "the provided exact scope does not match the current plan"
                if args.approve_exact_scope
                else "inspect the plan and provide its exact scope ref"
            )
            raise SystemExit(
                "Refusing mutation: "
                f"{reason} with --approve-exact-scope EXACT_SCOPE_REF."
            )
        actor = _actor()
        run_id = prepared.plan.plan_ref
        authority = LocalApprovalAuthority()
        request = store.approval_request_for_ingest(
            prepared, actor_context=actor, run_id=run_id
        )
        authority.create_request(request)
        grant = authority.grant(
            request.approval_request_id,
            approved_by_actor_id=actor.actor_id,
            approved_actions=[request.requested_action],
            approved_resource_refs=request.resource_refs,
            approval_ref=f"approval:{prepared.plan.exact_scope_ref}",
        )
        receipt = store.ingest(
            prepared,
            approval_authority=authority,
            approval_ref=grant.approval_ref,
            actor_context=actor,
            run_id=run_id,
        )
        _dump(receipt)
        return 0
    if args.command == "list":
        _dump(
            [
                item.model_dump(mode="json")
                for item in store.list_documents(
                    source_kind=KnowledgeSourceKind(args.source_kind)
                    if args.source_kind
                    else None,
                    category=args.category,
                    collection=args.collection,
                    tag=args.tag,
                    sort_by=args.sort_by,
                )
            ]
        )
        return 0
    if args.command == "inventory":
        _dump(store.inventory())
        return 0
    if args.command == "categorize":
        prepared = store.prepare_metadata_update(
            args.document_ref,
            source_kind=KnowledgeSourceKind(args.source_kind),
            category=args.category,
            collection=args.collection,
            tags=args.tag,
            idempotency_key=args.idempotency_key,
        )
        if args.approve_exact_scope != prepared.plan.exact_scope_ref:
            _dump(prepared.plan)
            reason = (
                "the provided exact scope does not match the current plan"
                if args.approve_exact_scope
                else "inspect the plan and provide its exact scope ref"
            )
            raise SystemExit(
                "Refusing mutation: "
                f"{reason} with --approve-exact-scope EXACT_SCOPE_REF."
            )
        actor = _actor()
        run_id = prepared.plan.plan_ref
        authority = LocalApprovalAuthority()
        request = store.approval_request_for_metadata_update(
            prepared, actor_context=actor, run_id=run_id
        )
        authority.create_request(request)
        grant = authority.grant(
            request.approval_request_id,
            approved_by_actor_id=actor.actor_id,
            approved_actions=[request.requested_action],
            approved_resource_refs=request.resource_refs,
            approval_ref=f"approval:{prepared.plan.exact_scope_ref}",
        )
        _dump(
            store.update_metadata(
                prepared,
                approval_authority=authority,
                approval_ref=grant.approval_ref,
                actor_context=actor,
                run_id=run_id,
            )
        )
        return 0
    if args.command == "search":
        _dump(
            [
                item.model_dump(mode="json")
                for item in store.search(
                    args.query,
                    limit=args.limit,
                    source_kind=KnowledgeSourceKind(args.source_kind)
                    if args.source_kind
                    else None,
                    category=args.category,
                    collection=args.collection,
                    tag=args.tag,
                )
            ]
        )
        return 0
    if args.command == "prepare-context":
        _dump(
            store.prepare_context(
                args.query,
                limit=args.limit,
                max_characters=args.max_characters,
                source_kind=KnowledgeSourceKind(args.source_kind)
                if args.source_kind
                else None,
                category=args.category,
                collection=args.collection,
                tag=args.tag,
            )
        )
        return 0
    raise SystemExit("Unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
