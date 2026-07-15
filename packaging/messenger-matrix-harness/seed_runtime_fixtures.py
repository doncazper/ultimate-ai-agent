#!/usr/bin/env python3
"""Create synthetic disposable Matrix fixtures and print counts only."""

from __future__ import annotations

import hashlib
import hmac
import http.client
import json
from pathlib import Path
import re
import secrets
from urllib.parse import quote


HOST = "127.0.0.1"
PORT = 8008
SERVER_NAME = "uaa-matrix-harness.invalid"
CONFIG_PATH = Path("/data/homeserver.yaml")
SECRET_PATTERN = re.compile(r'^registration_shared_secret: "([0-9a-f]{64})"$', re.MULTILINE)


def _request(
    method: str,
    path: str,
    *,
    payload: dict[str, object] | None = None,
    access_token: str | None = None,
) -> dict[str, object]:
    connection = http.client.HTTPConnection(HOST, PORT, timeout=10)
    try:
        body = (
            json.dumps(payload, separators=(",", ":"))
            if payload is not None
            else None
        )
        headers = {"Content-Type": "application/json"}
        if access_token is not None:
            headers["Authorization"] = f"Bearer {access_token}"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read(65537)
    finally:
        connection.close()
    if len(raw) > 65536:
        raise RuntimeError("MATRIX_HARNESS_FIXTURE_RESPONSE_OVERSIZED")
    if response.status < 200 or response.status >= 300:
        raise RuntimeError("MATRIX_HARNESS_FIXTURE_REQUEST_FAILED")
    result = json.loads(raw.decode("utf-8")) if raw else {}
    if not isinstance(result, dict):
        raise RuntimeError("MATRIX_HARNESS_FIXTURE_RESPONSE_INVALID")
    return result


def _registration_secret() -> bytes:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = handle.read(4097)
    if len(config) > 4096:
        raise RuntimeError("MATRIX_HARNESS_CONFIG_OVERSIZED")
    match = SECRET_PATTERN.search(config)
    if match is None:
        raise RuntimeError("MATRIX_HARNESS_REGISTRATION_SECRET_UNAVAILABLE")
    return match.group(1).encode("ascii")


def _register(username: str, password: str, secret: bytes) -> tuple[str, str]:
    nonce = str(_request("GET", "/_synapse/admin/v1/register")["nonce"])
    mac = hmac.new(secret, digestmod=hashlib.sha1)
    mac.update(nonce.encode("utf-8"))
    mac.update(b"\x00")
    mac.update(username.encode("utf-8"))
    mac.update(b"\x00")
    mac.update(password.encode("utf-8"))
    mac.update(b"\x00notadmin")
    created = _request(
        "POST",
        "/_synapse/admin/v1/register",
        payload={
            "nonce": nonce,
            "username": username,
            "password": password,
            "admin": False,
            "mac": mac.hexdigest(),
        },
    )
    return str(created["user_id"]), str(created["access_token"])


def _create_room(
    token: str,
    *,
    is_space: bool = False,
    invite: list[str] | None = None,
) -> str:
    payload: dict[str, object] = {
        "preset": "private_chat",
        "visibility": "private",
        "invite": invite or [],
    }
    if is_space:
        payload["creation_content"] = {"type": "m.space"}
    result = _request(
        "POST",
        "/_matrix/client/v3/createRoom",
        payload=payload,
        access_token=token,
    )
    return str(result["room_id"])


def _send(
    token: str,
    room_id: str,
    event_type: str,
    txn: str,
    content: dict[str, object],
) -> str:
    path = (
        "/_matrix/client/v3/rooms/"
        f"{quote(room_id, safe='')}/send/{quote(event_type, safe='')}/{txn}"
    )
    return str(
        _request("PUT", path, payload=content, access_token=token)["event_id"]
    )


def _runtime_body(index: int) -> str:
    return f"synthetic-runtime-fixture-v1-{index}"


def main() -> int:
    secret = _registration_secret()
    first_user, first_token = _register(
        "uaa_fixture_alpha_v1", secrets.token_urlsafe(32), secret
    )
    second_user, _second_token = _register(
        "uaa_fixture_beta_v1", secrets.token_urlsafe(32), secret
    )
    space_id = _create_room(first_token, is_space=True)
    room_id = _create_room(first_token, invite=[second_user])
    direct_id = _create_room(first_token, invite=[second_user])
    _request(
        "PUT",
        "/_matrix/client/v3/user/"
        f"{quote(first_user, safe='')}/account_data/m.direct",
        payload={second_user: [direct_id]},
        access_token=first_token,
    )
    _request(
        "PUT",
        "/_matrix/client/v3/rooms/"
        f"{quote(space_id, safe='')}/state/m.space.child/{quote(room_id, safe='')}",
        payload={"via": [SERVER_NAME]},
        access_token=first_token,
    )
    first_event = _send(
        first_token,
        room_id,
        "m.room.message",
        "fixture-v1-1",
        {"msgtype": "m.text", "body": _runtime_body(1)},
    )
    _send(
        first_token,
        room_id,
        "m.room.message",
        "fixture-v1-2",
        {
            "msgtype": "m.text",
            "body": _runtime_body(2),
            "m.relates_to": {"m.in_reply_to": {"event_id": first_event}},
        },
    )
    _send(
        first_token,
        room_id,
        "m.reaction",
        "fixture-v1-3",
        {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": first_event,
                "key": "fixture-reaction",
            }
        },
    )
    _send(
        first_token,
        direct_id,
        "m.room.message",
        "fixture-v1-4",
        {"msgtype": "m.text", "body": _runtime_body(3)},
    )
    print(
        json.dumps(
            {"account_count": 2, "room_count": 3, "event_count": 5},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
