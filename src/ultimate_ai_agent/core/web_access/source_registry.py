"""Source metadata registry helpers for WebAccessGateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from .contracts import SourceMetadata, utc_now


@dataclass
class SourceRegistry:
    """Small in-memory registry for first-slice source metadata normalization."""

    sources: dict[str, SourceMetadata] = field(default_factory=dict)

    def register(self, source: SourceMetadata) -> SourceMetadata:
        key = source.final_url or source.url
        if key:
            self.sources[key] = source
        return source

    def metadata_for_url(self, url: str, *, source_type: str = "web") -> SourceMetadata:
        parsed = urlparse(url)
        source = SourceMetadata(
            url=url,
            final_url=url,
            host=parsed.hostname,
            source_type=source_type,
            allowed_methods=("GET",),
            fetched_at=utc_now(),
            content_untrusted=True,
        )
        return self.register(source)
