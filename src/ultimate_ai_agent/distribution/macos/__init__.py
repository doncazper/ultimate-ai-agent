"""First-class macOS installation, update, rollback, and runtime contracts."""

from .contracts import (
    BUNDLE_MANIFEST_SCHEMA,
    PRODUCT_LINE,
    RELEASE_DESCRIPTOR_SCHEMA,
    ReleaseCandidate,
    ReleaseDescriptor,
    ReleaseSelection,
    select_release,
)

__all__ = [
    "BUNDLE_MANIFEST_SCHEMA",
    "PRODUCT_LINE",
    "RELEASE_DESCRIPTOR_SCHEMA",
    "ReleaseCandidate",
    "ReleaseDescriptor",
    "ReleaseSelection",
    "select_release",
]
