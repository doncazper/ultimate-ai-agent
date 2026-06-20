from enum import Enum


class MattermostRoleCreationMode(str, Enum):
    predefined = "predefined"
    proposal_then_approve = "proposal_then_approve"
    auto_create = "auto_create"


class MattermostTriggerMode(str, Enum):
    mention_command = "mention_command"
    enabled_room = "enabled_room"
    always_on_by_role = "always_on_by_role"


class MattermostDecisionStatus(str, Enum):
    ignored = "ignored"
    reply_proposed = "reply_proposed"
    approval_required = "approval_required"
    duplicate = "duplicate"
    blocked = "blocked"


class MattermostRoleSuggestionStatus(str, Enum):
    predefined = "predefined"
    proposed = "proposed"
    auto_created = "auto_created"
    blocked = "blocked"
