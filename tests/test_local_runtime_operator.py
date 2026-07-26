from __future__ import annotations

import scripts.dev.uaa_local_runtime as operator


SHA = "a" * 40
LOCAL_BEARER = "local-runtime-test-bearer"


def test_verified_operator_up_orders_source_proof_before_secret_handoff(
    monkeypatch,
    capsys,
) -> None:
    events: list[tuple[object, ...]] = []

    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda root: events.append(("verify", root)) or SHA,
    )
    monkeypatch.setattr(
        operator.secrets,
        "token_urlsafe",
        lambda length: events.append(("secret", length)) or LOCAL_BEARER,
    )
    monkeypatch.setattr(
        operator,
        "_write_private_text",
        lambda path, value: events.append(("write", path.name, value)),
    )
    monkeypatch.setattr(
        operator,
        "_run_compose",
        lambda arguments, *, commit: events.append(
            ("compose", arguments, commit)
        ),
    )
    monkeypatch.setattr(
        operator.webbrowser,
        "open",
        lambda url: events.append(("open", url)) or True,
    )

    operator._verified_up()

    assert events[0] == ("verify", operator.ROOT)
    compose_index = next(
        index for index, event in enumerate(events) if event[0] == "compose"
    )
    open_index = next(
        index for index, event in enumerate(events) if event[0] == "open"
    )
    assert open_index > compose_index > 0
    assert events[compose_index] == (
        "compose",
        ["up", "--build", "--detach", "--wait"],
        SHA,
    )
    opened_url = str(events[open_index][1])
    assert "#uaa-session-bearer=" in opened_url
    assert LOCAL_BEARER in opened_url
    assert LOCAL_BEARER not in capsys.readouterr().out
