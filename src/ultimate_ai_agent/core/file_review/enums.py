from enum import Enum


class FileReviewPacketStatus(str, Enum):
    ready_for_review = "ready_for_review"
    denied = "denied"


class FileReviewDecisionStatus(str, Enum):
    packet_valid_for_review = "packet_valid_for_review"
    review_allowed = "review_allowed"
    denied = "denied"
    expired = "expired"
    revoked = "revoked"
    replay_detected = "replay_detected"


class FileReviewApprovalDecisionKind(str, Enum):
    approve_review_only = "approve_review_only"
    deny_review_only = "deny_review_only"


class FileReviewApprovalCaptureDecisionStatus(str, Enum):
    approved_for_review_only = "approved_for_review_only"
    denied_for_review = "denied_for_review"
    rejected = "rejected"
