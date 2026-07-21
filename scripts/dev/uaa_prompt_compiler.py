#!/usr/bin/env python3
"""Inspect, compile, and drift-check a UAA prompt-module dependency graph."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.prompt_compiler import (  # noqa: E402
    PromptCompilationError,
    PromptCompilationReceipt,
    PromptModuleCompiler,
)


def _load_variables(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromptCompilationError(
            "PROMPT_VARIABLE_FILE_INVALID",
            "Prompt variable file validation failed safely.",
        ) from exc
    if not isinstance(payload, dict):
        raise PromptCompilationError(
            "PROMPT_VARIABLE_FILE_INVALID",
            "Prompt variable file must contain one JSON object.",
        )
    return payload


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _load_expected_receipt(path: Path) -> PromptCompilationReceipt:
    try:
        return PromptCompilationReceipt.model_validate_json(
            path.read_bytes(),
            strict=True,
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise PromptCompilationError(
            "PROMPT_GOLDEN_RECEIPT_INVALID",
            "Golden prompt compilation receipt validation failed safely.",
        ) from exc


def _receipt_json(receipt: PromptCompilationReceipt) -> str:
    return json.dumps(receipt.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"


def _add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--entry",
        action="append",
        default=None,
        help="select an entry module; repeat to select more than one",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="show safe graph metadata and optional reverse-dependency impact",
    )
    _add_shared_arguments(inspect_parser)
    inspect_parser.add_argument(
        "--changed",
        action="append",
        default=[],
        help="module changed for reverse-dependency analysis; repeat as needed",
    )

    compile_parser = subparsers.add_parser(
        "compile",
        help="compile selected entries without executing the result",
    )
    _add_shared_arguments(compile_parser)
    compile_parser.add_argument("--variables", type=Path)
    compile_parser.add_argument("--output", type=Path)
    compile_parser.add_argument("--receipt", type=Path)
    compile_parser.add_argument(
        "--check-receipt",
        type=Path,
        help="fail if the deterministic receipt differs from this golden receipt",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    compiler = PromptModuleCompiler(ROOT)
    try:
        manifest = compiler.load_manifest(args.manifest)
        if args.command == "inspect":
            inspection = compiler.inspect(
                manifest,
                entry_module_ids=args.entry,
                changed_module_ids=args.changed,
            )
            print(
                json.dumps(inspection.model_dump(mode="json"), indent=2, sort_keys=True)
            )
            return 0

        artifact = compiler.compile(
            manifest,
            variables=_load_variables(args.variables),
            entry_module_ids=args.entry,
        )
        if args.check_receipt is not None:
            expected = _load_expected_receipt(args.check_receipt)
            if artifact.receipt != expected:
                raise PromptCompilationError(
                    "PROMPT_COMPILATION_DRIFT",
                    "Prompt compilation differs from its reviewed golden receipt.",
                )
        if args.output is not None:
            _write_atomic(args.output, artifact.content)
        if args.receipt is not None:
            _write_atomic(args.receipt, _receipt_json(artifact.receipt))
        print(
            json.dumps(
                {
                    "bundle_id": artifact.receipt.bundle_id,
                    "bundle_version": artifact.receipt.bundle_version,
                    "entry_module_ids": artifact.receipt.entry_module_ids,
                    "ordered_module_ids": artifact.receipt.ordered_module_ids,
                    "compiled_artifact_hash": artifact.receipt.compiled_artifact_hash,
                    "compiled_bytes": artifact.receipt.compiled_bytes,
                    "manifest_contract_hash": artifact.receipt.manifest_contract_hash,
                    "dependency_graph_hash": artifact.receipt.dependency_graph_hash,
                    "golden_receipt_verified": args.check_receipt is not None,
                    "output_written": args.output is not None,
                    "receipt_written": args.receipt is not None,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except PromptCompilationError as exc:
        print(f"ERROR [{exc.reason_code}]: {exc.safe_message}", file=sys.stderr)
        return 1
    except OSError:
        print(
            "ERROR [PROMPT_COMPILER_OUTPUT_FAILED]: "
            "Prompt compiler output could not be written safely.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
