from __future__ import annotations

import json
from pathlib import Path

from ultimate_ai_agent.core.local_model_management.inventory import (
    inspect_local_model_inventory,
    inspect_local_model_ref,
    local_model_inventory_as_json,
)


def _write_hf_model(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "config.json").write_text('{"model_type":"test"}\n', encoding="utf-8")
    (path / "tokenizer.json").write_text("{}\n", encoding="utf-8")
    (path / "model-00001-of-00001.safetensors").write_bytes(b"safe metadata fixture")


def test_inventory_detects_supported_local_model_candidates(tmp_path: Path) -> None:
    gguf_root = tmp_path / "gguf-root"
    gguf_root.mkdir()
    (gguf_root / "qwen-coder-q4.gguf").write_bytes(b"gguf fixture")

    hf_root = tmp_path / "huggingface"
    _write_hf_model(hf_root / "models--org--chat-instruct" / "snapshots" / "abc")

    mlx_root = tmp_path / "mlx"
    mlx_model = mlx_root / "qwen3-coder-mlx"
    _write_hf_model(mlx_model)
    (mlx_model / "chat_template.jinja").write_text("{{ messages }}\n", encoding="utf-8")

    ollama_root = tmp_path / "ollama"
    manifest = ollama_root / "manifests" / "registry.ollama.ai" / "library" / "llama" / "latest"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"schemaVersion":2,"layers":[]}\n', encoding="utf-8")
    blob = ollama_root / "blobs" / "sha256-abc123"
    blob.parent.mkdir(parents=True)
    blob.write_bytes(b"blob fixture")

    lm_studio_root = tmp_path / "lm-studio"
    _write_hf_model(lm_studio_root / "publisher" / "model")

    missing_root = tmp_path / "missing"

    report = inspect_local_model_inventory(
        [gguf_root, hf_root, mlx_root, ollama_root, lm_studio_root, missing_root]
    )

    assert report.schema_version == "uaa_local_model_inventory.v1"
    assert len(report.models) == 6
    by_kind = {(item.runtime_family, item.artifact_kind): item for item in report.models}

    gguf = by_kind[("llama_cpp", "gguf")]
    assert gguf.runnable_status == "runnable_now"
    assert gguf.adapter_requirement == "llama_cpp"
    assert "coding" in gguf.role_hints

    assert by_kind[("huggingface", "safetensors_directory")].adapter_requirement == "huggingface_runtime"
    assert by_kind[("mlx", "safetensors_directory")].adapter_requirement == "mlx_runtime"
    assert by_kind[("ollama", "ollama_manifest")].adapter_requirement == "ollama_runtime"
    assert by_kind[("ollama", "ollama_blob")].adapter_requirement == "ollama_runtime"
    assert by_kind[("lm_studio", "model_directory")].adapter_requirement == "lm_studio_runtime"

    blocked_roots = [root for root in report.roots if root.status == "blocked"]
    assert blocked_roots[0].blocked_reason_code == "root_missing"


def test_inventory_refs_are_deterministic_and_redacted(tmp_path: Path) -> None:
    root = tmp_path / "models"
    root.mkdir()
    (root / "private-name.gguf").write_bytes(b"fixture")

    first = inspect_local_model_inventory([root])
    second = inspect_local_model_inventory([root])

    assert [item.model_ref for item in first.models] == [item.model_ref for item in second.models]
    rendered = local_model_inventory_as_json(first)
    assert str(tmp_path) not in rendered
    assert "private-name.gguf" not in rendered
    assert "/Users/" not in rendered
    assert "raw_path" not in rendered

    data = json.loads(rendered)
    assert data["models"][0]["model_ref"].startswith("local-model:gguf:")
    assert data["models"][0]["summary_ref"].startswith("local-model-summary:")


def test_inventory_deduplicates_overlapping_configured_roots(tmp_path: Path) -> None:
    parent = tmp_path / "Models"
    child = parent / "llama.cpp" / "model-cache"
    child.mkdir(parents=True)
    (child / "one.gguf").write_bytes(b"fixture")

    report = inspect_local_model_inventory([parent, child])

    assert len(report.models) == 1
    assert report.models[0].artifact_kind == "gguf"


def test_inventory_inspect_returns_safe_model_ref(tmp_path: Path) -> None:
    root = tmp_path / "models"
    root.mkdir()
    (root / "assistant.gguf").write_bytes(b"fixture")
    report = inspect_local_model_inventory([root])
    model_ref = report.models[0].model_ref

    item = inspect_local_model_ref(model_ref, [root])

    assert item is not None
    assert item.model_ref == model_ref
    assert item.runtime_family == "llama_cpp"


def test_inventory_blocks_unsupported_weight_without_crashing(tmp_path: Path) -> None:
    root = tmp_path / "models"
    root.mkdir()
    (root / "unknown.bin").write_bytes(b"fixture")

    report = inspect_local_model_inventory([root])

    assert report.models[0].runnable_status == "blocked"
    assert report.models[0].blocked_reason_code == "unsupported_artifact"
    assert report.models[0].adapter_requirement == "unsupported"
