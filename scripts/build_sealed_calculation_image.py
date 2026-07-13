#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "packaging" / "sealed-calculation"
BASE_IMAGE = "python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
LOCAL_TAG = "uaa-sealed-calculation:local"


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
        timeout=180,
    )


def main() -> int:
    runner_sha256 = hashlib.sha256((CONTEXT / "runner.py").read_bytes()).hexdigest()
    probe_sha256 = hashlib.sha256(
        (CONTEXT / "isolation_probe.py").read_bytes()
    ).hexdigest()
    _run(
        [
            "/usr/local/bin/docker",
            "build",
            "--pull=false",
            "--network=none",
            "--build-arg",
            f"BASE_IMAGE={BASE_IMAGE}",
            "--build-arg",
            f"RUNNER_SHA256={runner_sha256}",
            "--build-arg",
            f"ISOLATION_PROBE_SHA256={probe_sha256}",
            "--tag",
            LOCAL_TAG,
            "--file",
            str(CONTEXT / "Dockerfile"),
            str(CONTEXT),
        ]
    )
    inspection = _run(
        [
            "/usr/local/bin/docker",
            "image",
            "inspect",
            LOCAL_TAG,
            "--format",
            "{{json .}}",
        ]
    )
    payload = json.loads(inspection.stdout)
    image_id = payload.get("Id")
    if not isinstance(image_id, str) or not image_id.startswith("sha256:"):
        raise RuntimeError("SEALED_CALCULATION_IMAGE_ID_REQUIRED")
    config = payload.get("Config", {})
    expected_entrypoint = [
        "/usr/local/bin/python3.13",
        "-I",
        "-S",
        "/opt/uaa-sealed-calculation/runner.py",
    ]
    if config.get("Entrypoint") != expected_entrypoint:
        raise RuntimeError("SEALED_CALCULATION_IMAGE_ENTRYPOINT_INVALID")
    labels = config.get("Labels") or {}
    expected_labels = {
        "com.ultimate-ai-agent.sealed-calculation": "v1",
        "com.ultimate-ai-agent.sealed-calculation.base-image": BASE_IMAGE,
        "com.ultimate-ai-agent.sealed-calculation.runner-sha256": runner_sha256,
        "com.ultimate-ai-agent.sealed-calculation.probe-sha256": probe_sha256,
    }
    if any(labels.get(key) != value for key, value in expected_labels.items()):
        raise RuntimeError("SEALED_CALCULATION_IMAGE_LABEL_BINDING_INVALID")
    print(
        json.dumps(
            {
                "schema_version": "uaa-sealed-calculation-image-build.v1",
                "image_id": image_id,
                "runner_source_ref": f"runner-source-ref:sha256:{runner_sha256}",
                "tag_ref": "local-image-tag-ref:uaa-sealed-calculation",
                "pull_during_invocation": False,
                "safe_summary": "Sealed calculation image built and pinned locally.",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
