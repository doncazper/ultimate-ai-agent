from __future__ import annotations
from typing import Any

from ultimate_ai_agent.core.context_proposal.contracts import SafeContextProposalPolicy


def build_safe_context_proposal_policy(**overrides: Any) -> SafeContextProposalPolicy:
    if not overrides:
        return SafeContextProposalPolicy()
    return SafeContextProposalPolicy().model_copy(update=overrides)
