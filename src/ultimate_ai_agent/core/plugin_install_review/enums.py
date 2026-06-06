from enum import Enum


class PluginInstallReviewDecisionStatus(str, Enum):
    install_review_ready_disabled = "install_review_ready_disabled"
    denied = "denied"
    blocked = "blocked"
