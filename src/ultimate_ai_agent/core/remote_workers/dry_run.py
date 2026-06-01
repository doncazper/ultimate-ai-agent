import uuid

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.remote_workers.audit import RemoteAuditContext
from ultimate_ai_agent.core.remote_workers.enums import RemoteJobStatus, RemoteOutputTrustLevel, RemoteRiskLevel
from ultimate_ai_agent.core.remote_workers.jobs import RemoteJobEnvelope
from ultimate_ai_agent.core.remote_workers.policy import RemoteExecutionPolicy, evaluate_remote_job_policy
from ultimate_ai_agent.core.remote_workers.registry import RemoteNodeRegistry, RemoteTransportRegistry
from ultimate_ai_agent.core.remote_workers.results import RemoteJobResult


class RemoteDryRunBuilder:
    def build_envelope(
        self,
        *,
        task_summary: str,
        node_id: str,
        transport_id: str,
        actor_context: ActorContext,
        policy: RemoteExecutionPolicy,
    ) -> RemoteJobEnvelope:
        correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
        return RemoteJobEnvelope(
            job_id=f"remote_job_{uuid.uuid4().hex[:12]}",
            correlation_id=correlation_id,
            node_id=node_id,
            transport_id=transport_id,
            task_summary=task_summary,
            requested_capabilities=["dry_run"],
            risk_level=RemoteRiskLevel.low,
            audit_context=RemoteAuditContext(
                run_id=f"run_{uuid.uuid4().hex[:12]}",
                correlation_id=correlation_id,
                actor_context=actor_context,
            ),
            policy_ref=policy.policy_id,
        )

    def dry_run(
        self,
        envelope: RemoteJobEnvelope,
        registry: RemoteNodeRegistry,
        transports: RemoteTransportRegistry,
        policy: RemoteExecutionPolicy,
    ) -> RemoteJobResult:
        decision = evaluate_remote_job_policy(envelope, registry, transports, policy)
        if decision.allowed:
            return RemoteJobResult(
                job_id=envelope.job_id,
                correlation_id=envelope.correlation_id,
                status=RemoteJobStatus.simulated_result,
                output_trust_level=RemoteOutputTrustLevel.untrusted_remote_output,
                output_summary="Remote worker dry-run completed; no remote work occurred and output is untrusted.",
                warnings=["REMOTE_FOUNDATION_ONLY"],
                metadata={"policy_decision_id": decision.decision_id, "foundation_only": True},
            )
        return RemoteJobResult(
            job_id=envelope.job_id,
            correlation_id=envelope.correlation_id,
            status=RemoteJobStatus.dispatch_blocked,
            output_trust_level=RemoteOutputTrustLevel.untrusted_remote_output,
            output_summary="Remote worker dry-run blocked before any remote work.",
            warnings=decision.reason_codes,
            metadata={"policy_decision_id": decision.decision_id, "foundation_only": True},
        )

