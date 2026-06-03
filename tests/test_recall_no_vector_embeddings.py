from pathlib import Path

from ultimate_ai_agent.core.recall import GroundedRecallManifest


def test_recall_manifest_disables_vector_embedding_and_external_retrieval():
    manifest = GroundedRecallManifest(baseline_version="0.30.1")

    assert manifest.vector_search_enabled is False
    assert manifest.embeddings_enabled is False
    assert manifest.semantic_search_enabled is False
    assert manifest.external_retrieval_enabled is False
    assert manifest.web_search_enabled is False


def test_recall_source_has_no_vector_embedding_or_provider_imports():
    recall_root = Path("src/ultimate_ai_agent/core/recall")
    forbidden = [
        "import chromadb",
        "import faiss",
        "import pgvector",
        "import qdrant",
        "import weaviate",
        "import pinecone",
        "import tokenizers",
        "import tiktoken",
        "requests.get(",
        "httpx.get(",
        "import openai",
        "import anthropic",
        "import ollama",
    ]

    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in recall_root.glob("*.py"))

    for fragment in forbidden:
        assert fragment not in source
