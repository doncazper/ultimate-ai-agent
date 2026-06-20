from __future__ import annotations

import hmac
import os
from typing import Mapping

MATTERMOST_BRIDGE_ENV = "UAA_MATTERMOST_BRIDGE_ENABLED"
MATTERMOST_BRIDGE_BEARER_ENV = "UAA_MATTERMOST_BRIDGE_BEARER"
MATTERMOST_BRIDGE_STORAGE_DIR_ENV = "UAA_MATTERMOST_BRIDGE_STORAGE_DIR"
MATTERMOST_REPLY_ENABLED_ENV = "UAA_MATTERMOST_REPLY_ENABLED"
MATTERMOST_AUTO_CREATE_ROLES_ENV = "UAA_MATTERMOST_AUTO_CREATE_ROLES_ENABLED"
DEFAULT_MATTERMOST_BRIDGE_STORAGE_DIR = ".uaa/mattermost_bridge"

TRUE_VALUES = {"1", "true", "yes", "on"}


def mattermost_bridge_enabled(values: Mapping[str, str] | None = None) -> bool:
    env = values or os.environ
    return env.get(MATTERMOST_BRIDGE_ENV, "").strip().lower() in TRUE_VALUES


def mattermost_reply_enabled(values: Mapping[str, str] | None = None) -> bool:
    env = values or os.environ
    return env.get(MATTERMOST_REPLY_ENABLED_ENV, "").strip().lower() in TRUE_VALUES


def mattermost_auto_create_roles_enabled(values: Mapping[str, str] | None = None) -> bool:
    env = values or os.environ
    return env.get(MATTERMOST_AUTO_CREATE_ROLES_ENV, "").strip().lower() in TRUE_VALUES


def mattermost_bridge_storage_dir(values: Mapping[str, str] | None = None) -> str:
    env = values or os.environ
    return env.get(MATTERMOST_BRIDGE_STORAGE_DIR_ENV, DEFAULT_MATTERMOST_BRIDGE_STORAGE_DIR).strip() or (
        DEFAULT_MATTERMOST_BRIDGE_STORAGE_DIR
    )


def mattermost_bridge_authority_error(
    authorization: str | None,
    values: Mapping[str, str] | None = None,
) -> tuple[int, str] | None:
    env = values or os.environ
    if not mattermost_bridge_enabled(env):
        return 403, "Mattermost bridge is disabled. Set UAA_MATTERMOST_BRIDGE_ENABLED=1 for local self-hosted use."
    expected = env.get(MATTERMOST_BRIDGE_BEARER_ENV, "").strip()
    if not expected:
        return 401, "Mattermost bridge requires an explicit local bearer."
    if not hmac.compare_digest(authorization or "", f"Bearer {expected}"):
        return 401, "Mattermost bridge bearer was not accepted."
    return None
