#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.decision_router import (  # noqa: E402
    ROUTE_DECISION_BINDING_ALLOWED_SIDE_EFFECT_CLASSES,
    TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS,
    TurnRouterPreviewRequest,
    build_route_decision_binding,
    build_sample_prepared_turns,
    build_turn_router_preview,
    classify_turn_contract,
    compile_invocation_policy,
    context_from_route_decision_binding,
    safe_content_fingerprint_ref,
    validate_route_decision_binding,
    prepare_turn,
)


def preview(args: argparse.Namespace) -> int:
    request = (
        TurnRouterPreviewRequest(sample_id=args.sample)
        if args.sample is not None
        else TurnRouterPreviewRequest(text=args.text)
    )
    payload = build_turn_router_preview(request).model_dump(mode="json")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def golden_cases(args: argparse.Namespace) -> int:
    payload = {
        sample_id: build_turn_router_preview(
            TurnRouterPreviewRequest(sample_id=sample_id)
        ).model_dump(mode="json")
        for sample_id in sorted(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS)
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def route_binding(args: argparse.Namespace) -> int:
    request_text = TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS[args.sample]
    decision = classify_turn_contract(
        request_text,
        decision_ref=f"turn-decision:route-binding:{args.sample}",
    )
    policy = compile_invocation_policy(decision)
    binding = build_route_decision_binding(
        policy,
        actor_ref=args.actor_ref,
        session_ref=args.session_ref,
        turn_ref=args.turn_ref,
        route_ref=args.route_ref,
        side_effect_class=args.side_effect_class,
        idempotency_key=args.idempotency_key,
        content_fingerprint_ref=safe_content_fingerprint_ref(request_text),
        provider_ref=args.provider_ref,
        model_ref=args.model_ref,
        resource_refs=args.resource_refs,
    )
    context = context_from_route_decision_binding(binding)
    result = validate_route_decision_binding(binding, context)
    payload = {
        "binding": binding.model_dump(mode="json"),
        "validation": result.model_dump(mode="json"),
        "operator_note": (
            "Route decision binding validation is inspection-only; it is not approval "
            "and grants no runtime/model/provider/tool authority."
        ),
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def prepare_turn_command(args: argparse.Namespace) -> int:
    if args.all_samples:
        payload: dict[str, object] = {
            "schema_version": "prepared_turn_cli.v1",
            "prepared_turns": [
                item.model_dump(mode="json") for item in build_sample_prepared_turns()
            ],
            "raw_prompt_persisted": False,
            "raw_model_output_persisted": False,
            "execution_performed": False,
        }
    else:
        prepared = prepare_turn(sample_id=args.sample, text=args.text)
        payload = {
            "schema_version": "prepared_turn_cli.v1",
            "prepared_turn": prepared.model_dump(mode="json"),
            "raw_prompt_persisted": False,
            "raw_model_output_persisted": False,
            "execution_performed": False,
        }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect UAA Turn Contract Router no-effect previews."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    preview_parser = subparsers.add_parser(
        "preview",
        help="Print a backend-owned no-effect router preview.",
    )
    preview_source = preview_parser.add_mutually_exclusive_group(required=True)
    preview_source.add_argument(
        "--sample",
        choices=sorted(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS),
        help="Preview a protected sample prompt without printing raw prompt text.",
    )
    preview_source.add_argument(
        "--text",
        help="Preview ephemeral text. The output omits the raw submitted text.",
    )
    preview_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    preview_parser.set_defaults(func=preview)
    golden = subparsers.add_parser(
        "golden-cases",
        help="Print all protected sample previews as safe read models.",
    )
    golden.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read models.",
    )
    golden.set_defaults(func=golden_cases)
    route_binding_parser = subparsers.add_parser(
        "route-binding",
        help="Build and validate a no-effect route decision binding for a protected sample.",
    )
    route_binding_parser.add_argument(
        "--sample",
        choices=sorted(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS),
        required=True,
        help="Protected sample prompt. Output omits raw prompt text.",
    )
    route_binding_parser.add_argument(
        "--route-ref",
        default="/v1/chat/completions",
        help="Route or surface ref to bind. Defaults to the local chat completion surface.",
    )
    route_binding_parser.add_argument(
        "--side-effect-class",
        choices=ROUTE_DECISION_BINDING_ALLOWED_SIDE_EFFECT_CLASSES,
        default="validation_only",
        help="Expected route side-effect class.",
    )
    route_binding_parser.add_argument(
        "--actor-ref",
        default="actor-ref:local-operator",
        help="Safe actor ref for binding inspection.",
    )
    route_binding_parser.add_argument(
        "--session-ref",
        default="session-ref:turn-router-cli",
        help="Safe session ref for binding inspection.",
    )
    route_binding_parser.add_argument(
        "--turn-ref",
        default="turn-ref:turn-router-cli",
        help="Safe turn ref for binding inspection.",
    )
    route_binding_parser.add_argument(
        "--idempotency-key",
        default="idempotency-key:turn-router-cli-route-binding",
        help="Safe idempotency key for binding inspection.",
    )
    route_binding_parser.add_argument(
        "--provider-ref",
        default=None,
        help="Optional safe provider choice ref. Does not grant provider authority.",
    )
    route_binding_parser.add_argument(
        "--model-ref",
        default=None,
        help="Optional safe model choice ref. Does not grant model authority.",
    )
    route_binding_parser.add_argument(
        "--resource-refs",
        nargs="*",
        default=[],
        help="Optional safe tool/action/resource refs to bind.",
    )
    route_binding_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    route_binding_parser.set_defaults(func=route_binding)
    prepared_parser = subparsers.add_parser(
        "prepare-turn",
        help="Prepare a turn through routing, binding, run, and readiness refs.",
    )
    prepared_source = prepared_parser.add_mutually_exclusive_group(required=True)
    prepared_source.add_argument(
        "--sample",
        choices=sorted(TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS),
        help="Prepare a protected sample prompt without printing raw prompt text.",
    )
    prepared_source.add_argument(
        "--text",
        help="Prepare ephemeral text. Output omits the raw submitted text.",
    )
    prepared_source.add_argument(
        "--all-samples",
        action="store_true",
        help="Emit prepared-turn read models for the representative protected samples.",
    )
    prepared_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the safe JSON read model.",
    )
    prepared_parser.set_defaults(func=prepare_turn_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
