from typing import Dict, List, Optional

from ultimate_ai_agent.core.remote_workers.enums import PrivateMeshProviderKind, RemoteNodeStatus, RemoteTransportKind, RemoteTransportStatus
from ultimate_ai_agent.core.remote_workers.nodes import NodeCapabilitySet, NodeIdentity, RemoteNode
from ultimate_ai_agent.core.remote_workers.status import RemotePolicyDecision, allowed_decision, denied_decision
from ultimate_ai_agent.core.remote_workers.transports import RemoteTransportDescriptor


class RemoteTransportRegistry:
    def __init__(self):
        self._transports: dict[str, RemoteTransportDescriptor] = {}

    def register_transport(self, descriptor: RemoteTransportDescriptor) -> RemoteTransportDescriptor:
        self._transports[descriptor.transport_id] = descriptor
        return descriptor

    def get_transport(self, transport_id: str) -> Optional[RemoteTransportDescriptor]:
        return self._transports.get(transport_id)

    def list_transports(self) -> List[RemoteTransportDescriptor]:
        return list(self._transports.values())

    def validate_transport(self, transport_id: str) -> RemotePolicyDecision:
        descriptor = self.get_transport(transport_id)
        if descriptor is None:
            return denied_decision(["REMOTE_TRANSPORT_UNKNOWN"], "Remote transport is unknown.")
        reasons: list[str] = []
        if descriptor.status in {RemoteTransportStatus.disabled, RemoteTransportStatus.denied, RemoteTransportStatus.not_configured}:
            reasons.append("REMOTE_TRANSPORT_DISABLED")
        if descriptor.planned_only or descriptor.status == RemoteTransportStatus.planned:
            reasons.append("REMOTE_TRANSPORT_PLANNED_ONLY")
        if not descriptor.enabled:
            reasons.append("REMOTE_TRANSPORT_NOT_ENABLED")
        if descriptor.requires_network:
            reasons.append("REMOTE_TRANSPORT_NETWORK_DENIED")
        if descriptor.requires_credentials:
            reasons.append("REMOTE_TRANSPORT_CREDENTIALS_DENIED")
        if descriptor.supports_dispatch:
            reasons.append("REMOTE_TRANSPORT_DISPATCH_DENIED")
        if descriptor.supports_file_transfer:
            reasons.append("REMOTE_TRANSPORT_FILE_TRANSFER_DENIED")
        if descriptor.supports_subagents:
            reasons.append("REMOTE_TRANSPORT_SUBAGENT_DENIED")
        if reasons:
            return denied_decision(reasons, "Remote transport is blocked by M10.5 policy.", transport_id=transport_id)
        return allowed_decision(["REMOTE_TRANSPORT_METADATA_ALLOWED"], "Remote transport metadata is valid.", transport_id=transport_id)

    def status_summary(self) -> Dict[str, object]:
        planned_by_provider = {
            transport.transport_id: transport.provider_kind
            for transport in self._transports.values()
            if transport.planned_only
        }
        return {
            "transport_ids": sorted(self._transports),
            "live_network_enabled": False,
            "dispatch_enabled": False,
            "open_source_first": True,
            "self_hosted_control_plane_first": True,
            "planned_private_mesh_providers": planned_by_provider,
            "planned_transports": sorted(
                transport.transport_id for transport in self._transports.values() if transport.planned_only
            ),
        }


class RemoteNodeRegistry:
    def __init__(self):
        self._nodes: dict[str, RemoteNode] = {}

    def register_node(self, node: RemoteNode) -> RemoteNode:
        self._nodes[node.node_id] = node
        return node

    def get_node(self, node_id: str) -> Optional[RemoteNode]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[RemoteNode]:
        return list(self._nodes.values())

    def validate_node(self, node_id: str) -> RemotePolicyDecision:
        node = self.get_node(node_id)
        if node is None:
            return denied_decision(["REMOTE_NODE_UNKNOWN"], "Remote node is unknown.")
        reasons: list[str] = []
        if node.status in {RemoteNodeStatus.unknown, RemoteNodeStatus.disabled, RemoteNodeStatus.denied, RemoteNodeStatus.planned}:
            reasons.append("REMOTE_NODE_NOT_AVAILABLE")
        if node.capabilities.can_approve_actions:
            reasons.append("REMOTE_APPROVAL_DENIED")
        if node.capabilities.can_run_critical:
            reasons.append("REMOTE_CRITICAL_DENIED")
        if reasons:
            return denied_decision(reasons, "Remote node is blocked by M10.5 policy.", node_id=node_id)
        return allowed_decision(["REMOTE_NODE_METADATA_ALLOWED"], "Remote node metadata is valid.", node_id=node_id)

    def status_summary(self) -> Dict[str, object]:
        return {
            "node_ids": sorted(self._nodes),
            "live_workers_enabled": False,
            "remote_approvals_enabled": False,
        }


def default_remote_transport_registry() -> RemoteTransportRegistry:
    registry = RemoteTransportRegistry()
    for descriptor in [
        RemoteTransportDescriptor(
            transport_id="local_metadata",
            kind=RemoteTransportKind.local,
            status=RemoteTransportStatus.available,
            display_name="Local Metadata",
            description="Local metadata only; no job transfer.",
            planned_only=False,
            enabled=True,
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="mock_metadata",
            kind=RemoteTransportKind.mock,
            status=RemoteTransportStatus.available,
            display_name="Mock Metadata",
            description="Mock metadata only; dry-run validation.",
            planned_only=False,
            enabled=True,
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="private_mesh_planned",
            kind=RemoteTransportKind.private_mesh_planned,
            provider_kind=PrivateMeshProviderKind.none,
            status=RemoteTransportStatus.planned,
            display_name="Private Mesh Planned",
            description="Vendor-neutral private mesh metadata only; no network transport.",
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="headscale_planned",
            kind=RemoteTransportKind.headscale_planned,
            provider_kind=PrivateMeshProviderKind.headscale_planned,
            status=RemoteTransportStatus.planned,
            display_name="Headscale Planned",
            description="Planned self-hosted private mesh control-plane metadata only.",
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="generic_wireguard_planned",
            kind=RemoteTransportKind.generic_wireguard_planned,
            provider_kind=PrivateMeshProviderKind.generic_wireguard_planned,
            status=RemoteTransportStatus.planned,
            display_name="Generic WireGuard Planned",
            description="Planned generic private mesh metadata only.",
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="tailscale_planned",
            kind=RemoteTransportKind.tailscale_planned,
            provider_kind=PrivateMeshProviderKind.tailscale_planned,
            status=RemoteTransportStatus.planned,
            display_name="Tailscale Planned",
            description="Planned proprietary control-plane private mesh metadata only.",
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="tailnet_planned",
            kind=RemoteTransportKind.tailnet_planned,
            provider_kind=PrivateMeshProviderKind.none,
            status=RemoteTransportStatus.planned,
            display_name="Tailnet Planned",
            description="Deprecated generic tailnet/private mesh metadata only.",
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
        RemoteTransportDescriptor(
            transport_id="lan_planned",
            kind=RemoteTransportKind.lan_planned,
            provider_kind=PrivateMeshProviderKind.manual_lan_planned,
            status=RemoteTransportStatus.planned,
            display_name="LAN Planned",
            description="Planned LAN transport metadata only.",
            owner="system",
            source="default_remote_transport_registry",
            version="0.0.0",
        ),
    ]:
        registry.register_transport(descriptor)
    return registry


def default_remote_node_registry() -> RemoteNodeRegistry:
    registry = RemoteNodeRegistry()
    registry.register_node(
        RemoteNode(
            node_id="mock_node",
            identity=NodeIdentity(
                node_id="mock_node",
                display_name="Mock Remote Node",
                owner="system",
                source="default_remote_node_registry",
                version="0.0.0",
            ),
            status=RemoteNodeStatus.mock_available,
            capabilities=NodeCapabilitySet(),
            allowed_transport_ids=["mock_metadata", "local_metadata"],
        )
    )
    return registry
