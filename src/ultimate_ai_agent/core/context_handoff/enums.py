from enum import Enum


class ContextHandoffApprovalKind(str, Enum):
    approve_handoff_review_only = "approve_handoff_review_only"
    deny_handoff_review = "deny_handoff_review"


class ContextHandoffApprovalDecisionStatus(str, Enum):
    approved_for_handoff_review_only = "approved_for_handoff_review_only"
    denied_for_handoff_review = "denied_for_handoff_review"
    requires_context_proposal = "requires_context_proposal"
    denied = "denied"
