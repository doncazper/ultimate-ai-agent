import json
from pathlib import Path

PLUGIN_ROOT = Path("integrations/mattermost-plugin")


def test_mattermost_plugin_manifest_declares_server_component_and_safe_settings() -> None:
    manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "com.ultimateaiagent.mattermost-agent-rooms"
    assert manifest["server"]["executables"]["linux-amd64"] == "server/dist/plugin-linux-amd64"
    settings = {setting["key"]: setting for setting in manifest["settings_schema"]["settings"]}
    assert settings["UAABridgeBearer"]["secret"] is True
    assert settings["AllowedChannelIDs"]["default"] == ""
    assert settings["ReplyEnabled"]["default"] is False
    assert settings["TriggerMode"]["default"] == "mention_command"
    assert settings["PlannerBotUserID"]["default"] == ""
    assert settings["SafetyReviewerBotUserID"]["default"] == ""


def test_mattermost_plugin_scaffold_contains_server_hooks_and_commands() -> None:
    plugin_go = (PLUGIN_ROOT / "server/plugin.go").read_text(encoding="utf-8")
    commands_go = (PLUGIN_ROOT / "server/commands.go").read_text(encoding="utf-8")

    assert "MessageHasBeenPosted" in plugin_go
    assert "RegisterCommand" in plugin_go
    assert "CreatePost" in plugin_go
    assert "channelAllowed" in plugin_go
    assert "LoadOrStore" in plugin_go
    assert "role add" in commands_go
    assert "role suggest" in commands_go
    assert "trigger" in commands_go


def test_mattermost_plugin_redacts_secrets_and_bounds_message_preview() -> None:
    redaction_go = (PLUGIN_ROOT / "server/redaction.go").read_text(encoding="utf-8")
    client_go = (PLUGIN_ROOT / "server/uaa_client.go").read_text(encoding="utf-8")

    assert "REDACTED_SECRET" in redaction_go
    assert "MaxPreviewChars" in client_go
    assert "message_sha256" in client_go
    assert "/integrations/mattermost/events/message" in client_go
