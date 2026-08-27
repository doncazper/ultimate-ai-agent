#!/usr/bin/env python3
"""Inspect deterministic FIN-002 synthetic CSV fixtures without mutation."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from ultimate_ai_agent.core.finance.import_preview import (
    FinanceImportPreviewError,
    load_synthetic_import_fixture_manifest,
    preview_synthetic_csv_fixture,
    synthetic_import_fixture_manifest_ref,
)


def _print(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("manifest")
    preview = commands.add_parser("preview")
    preview.add_argument("--fixture-ref", required=True)
    preview.add_argument("--existing-fingerprint-ref", action="append", default=[])
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "manifest":
            fixtures = load_synthetic_import_fixture_manifest()
            _print(
                {
                    "schema_version": "uaa-finance-synthetic-import-manifest.v1",
                    "manifest_ref": synthetic_import_fixture_manifest_ref(),
                    "fixture_refs": [item.fixture_ref for item in fixtures],
                    "synthetic_only": True,
                    "raw_source_content_included": False,
                    "arbitrary_operator_input_allowed": False,
                    "mutation_performed": False,
                    "real_financial_data_allowed": False,
                }
            )
            return 0
        preview = preview_synthetic_csv_fixture(
            args.fixture_ref,
            existing_fingerprint_refs=tuple(args.existing_fingerprint_ref),
        )
        _print(preview.redacted_read_model())
        return 0
    except (FinanceImportPreviewError, ValueError) as exc:
        _print(
            {
                "schema_version": "uaa-finance-synthetic-import-error.v1",
                "ok": False,
                "error_code": str(exc).split(":", 1)[0],
                "raw_source_content_included": False,
                "mutation_performed": False,
                "real_financial_data_allowed": False,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
