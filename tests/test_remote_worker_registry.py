from ultimate_ai_agent.core.remote_workers import (
    RemoteTransportDescriptor,
    RemoteTransportKind,
    RemoteTransportRegistry,
    RemoteTransportStatus,
    default_remote_transport_registry,
)


def test_default_registry_loads_mock_local_and_planned_transports():
    registry = default_remote_transport_registry()
    summary = registry.status_summary()

    assert "local_metadata" in summary["transport_ids"]
    assert "mock_metadata" in summary["transport_ids"]
    assert "tailnet_planned" in summary["transport_ids"]
    assert "lan_planned" in summary["transport_ids"]
    assert registry.validate_transport("tailnet_planned").allowed is False
    assert registry.validate_transport("lan_planned").allowed is False


def test_unknown_and_network_or_dispatch_transports_are_denied():
    registry = RemoteTransportRegistry()
    registry.register_transport(
        RemoteTransportDescriptor(
            transport_id="network_transport",
            kind=RemoteTransportKind.manual,
            status=RemoteTransportStatus.available,
            display_name="Network Transport",
            description="Should be denied in M10.5.",
            enabled=True,
            requires_network=True,
            supports_dispatch=True,
            owner="tests",
            source="fixture",
            version="0.0.0",
        )
    )

    unknown = registry.validate_transport("missing_transport")
    denied = registry.validate_transport("network_transport")

    assert unknown.allowed is False
    assert "REMOTE_TRANSPORT_UNKNOWN" in unknown.reason_codes
    assert denied.allowed is False
    assert "REMOTE_TRANSPORT_NETWORK_DENIED" in denied.reason_codes
    assert "REMOTE_TRANSPORT_DISPATCH_DENIED" in denied.reason_codes

