from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.founder_loop_schema import FOUNDER_LOOP_SCHEMA_VERSION


BUILD_IDENTITY_SCHEMA_VERSION = "uaa-build-identity.v1"
CAPABILITY_PROFILE_VERSION = "governed_product_pilot_authority_profile.v1"
BUILD_ID_ENV = "UAA_BUILD_ID"
BUILD_COMMIT_ENV = "UAA_BUILD_COMMIT"
_SAFE_BUILD_ID = re.compile(r"^build-ref:[a-zA-Z0-9][a-zA-Z0-9._:-]{0,189}$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


class UpgradeCompatibility(BaseModel):
    minimum_storage_schema_version: str
    maximum_storage_schema_version: str
    automatic_unknown_schema_upgrade: Literal[False] = False
    rollback_requires_verified_backup: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class BuildIdentity(BaseModel):
    schema_version: Literal["uaa-build-identity.v1"] = BUILD_IDENTITY_SCHEMA_VERSION
    package_version: str
    build_id: str
    commit_ref: str
    source_revision_bound: bool
    storage_schema_version: str
    capability_profile_version: str
    upgrade_compatibility: UpgradeCompatibility

    model_config = ConfigDict(extra="forbid")


def build_identity(
    *,
    env: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> BuildIdentity:
    values = os.environ if env is None else env
    # A mutable source checkout cannot prove that its executing files still
    # match HEAD without invoking Git or reimplementing the index. Only an
    # explicit build/launcher binding is therefore authoritative.
    _ = repo_root
    sha = _validated_sha(values.get(BUILD_COMMIT_ENV))
    commit_ref = f"commit-ref:git:{sha}" if sha else "commit-ref:git:unbound"
    configured_build_id = (values.get(BUILD_ID_ENV) or "").strip()
    if configured_build_id and _SAFE_BUILD_ID.fullmatch(configured_build_id):
        build_id = configured_build_id
    elif sha:
        build_id = f"build-ref:uaa:{__version__}:{sha[:12]}"
    else:
        build_id = f"build-ref:uaa:{__version__}:source-unbound"
    return BuildIdentity(
        package_version=__version__,
        build_id=build_id,
        commit_ref=commit_ref,
        source_revision_bound=sha is not None,
        storage_schema_version=FOUNDER_LOOP_SCHEMA_VERSION,
        capability_profile_version=CAPABILITY_PROFILE_VERSION,
        upgrade_compatibility=UpgradeCompatibility(
            minimum_storage_schema_version=FOUNDER_LOOP_SCHEMA_VERSION,
            maximum_storage_schema_version=FOUNDER_LOOP_SCHEMA_VERSION,
        ),
    )


def _validated_sha(value: str | None) -> str | None:
    candidate = (value or "").strip().lower()
    return candidate if _GIT_SHA.fullmatch(candidate) else None


def verified_clean_source_commit(repo_root: Path) -> str:
    """Return HEAD only when the exact repository worktree is clean."""
    try:
        top_level = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        head = subprocess.run(
            ("git", "rev-parse", "--verify", "HEAD"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = subprocess.run(
            ("git", "status", "--porcelain", "--untracked-files=all"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        resolved_top_level = Path(top_level.stdout.strip()).resolve()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise RuntimeError(
            "source revision could not be verified; use a clean exact checkout"
        ) from exc
    commit = head.stdout.strip().lower()
    if (
        top_level.returncode != 0
        or head.returncode != 0
        or status.returncode != 0
        or resolved_top_level != repo_root.resolve()
        or status.stdout.strip()
        or _validated_sha(commit) is None
    ):
        raise RuntimeError(
            "source revision could not be verified; use a clean exact checkout"
        )
    return commit
