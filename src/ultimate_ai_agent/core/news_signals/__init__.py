"""Backend-owned News and Signals contracts.

The module consumes already-redacted artifacts from separately admitted read-only
source lanes.  It does not fetch, authenticate, summarize, or execute actions.
"""

from ultimate_ai_agent.core.news_signals.read_model import (
    NEWS_SIGNALS_ADAPTER_REF,
    NEWS_SIGNALS_CONTRACT_REF,
    NEWS_SIGNALS_SCHEMA_VERSION,
    NewsSignalArtifact,
    NewsSignalPreference,
    NewsSignalSource,
    NewsSignalsRepository,
    build_news_signals_summary,
)

__all__ = [
    "NEWS_SIGNALS_ADAPTER_REF",
    "NEWS_SIGNALS_CONTRACT_REF",
    "NEWS_SIGNALS_SCHEMA_VERSION",
    "NewsSignalArtifact",
    "NewsSignalPreference",
    "NewsSignalSource",
    "NewsSignalsRepository",
    "build_news_signals_summary",
]
