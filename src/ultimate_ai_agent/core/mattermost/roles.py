from __future__ import annotations

import hashlib
import re

from ultimate_ai_agent.core.mattermost.contracts import MattermostRoleCard


PREDEFINED_ROLE_CARDS: tuple[MattermostRoleCard, ...] = (
    MattermostRoleCard(
        role_id="planner",
        display_name="Planner",
        bot_username="uaa-planner",
        summary="Breaks room requests into safe, reviewable plans.",
        instructions=[
            "Decompose goals into steps.",
            "Name assumptions and approval boundaries.",
        ],
        use_when=["A room needs a task plan or sequencing."],
        do_not_use_when=["The room asks for immediate unapproved execution."],
    ),
    MattermostRoleCard(
        role_id="summarizer",
        display_name="Summarizer",
        bot_username="uaa-summarizer",
        summary="Summarizes thread state and extracts safe action items.",
        instructions=["Summarize only visible safe context.", "Avoid storing raw transcript content."],
        use_when=["A thread needs a compact recap."],
        do_not_use_when=["The room asks for private-data export."],
    ),
    MattermostRoleCard(
        role_id="critic",
        display_name="Critic",
        bot_username="uaa-critic",
        summary="Checks assumptions, risks, and missing evidence.",
        instructions=["Challenge weak plans constructively.", "Point out unclear authority boundaries."],
        use_when=["A proposal needs review."],
        do_not_use_when=["The room needs a final answer without critique."],
    ),
    MattermostRoleCard(
        role_id="implementer",
        display_name="Implementer",
        bot_username="uaa-implementer",
        summary="Turns approved plans into UAA capability proposals.",
        instructions=["Propose capability actions.", "Require approval before any tool or connector action."],
        use_when=["A task may map to UAA capabilities."],
        do_not_use_when=["The request needs unapproved external mutation."],
    ),
    MattermostRoleCard(
        role_id="safety-reviewer",
        display_name="Safety Reviewer",
        bot_username="uaa-safety",
        summary="Reviews policy, approval, privacy, and rollback concerns.",
        instructions=["Prefer safe denial over ambiguous authority.", "Name receipt and rollback expectations."],
        use_when=["The room discusses tools, data, writes, or external actions."],
        do_not_use_when=["The room only needs a light recap."],
    ),
    MattermostRoleCard(
        role_id="facilitator",
        display_name="Facilitator",
        bot_username="uaa-facilitator",
        summary="Coordinates which role should respond and prevents noisy pile-ons.",
        instructions=["Select the smallest useful role set.", "Reduce duplicate responses."],
        use_when=["Multiple roles are available in a busy room."],
        do_not_use_when=["A single role was explicitly mentioned."],
    ),
)

PREDEFINED_ROLE_CATALOG: dict[str, MattermostRoleCard] = {
    role.role_id: role for role in PREDEFINED_ROLE_CARDS
}


def get_predefined_role(role_id: str) -> MattermostRoleCard | None:
    return PREDEFINED_ROLE_CATALOG.get(role_id)


def list_predefined_roles() -> list[MattermostRoleCard]:
    return list(PREDEFINED_ROLE_CARDS)


def suggest_predefined_role_ids(prompt_preview: str, desired_count: int) -> list[str]:
    lowered = prompt_preview.lower()
    scored: list[tuple[int, str]] = []
    keyword_map = {
        "planner": ("plan", "roadmap", "break down", "sequence", "task"),
        "summarizer": ("summary", "summarize", "recap", "notes", "action items"),
        "critic": ("risk", "review", "critique", "assumption", "evidence"),
        "implementer": ("build", "implement", "code", "execute", "tool", "ship"),
        "safety-reviewer": ("approval", "policy", "safe", "rollback", "privacy"),
        "facilitator": ("coordinate", "decide", "moderate", "room", "roles"),
    }
    for role_id, keywords in keyword_map.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        scored.append((score, role_id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = [role_id for score, role_id in scored if score > 0]
    if not selected:
        selected = ["planner", "summarizer", "safety-reviewer"]
    for fallback in ("planner", "summarizer", "critic", "implementer", "safety-reviewer", "facilitator"):
        if len(selected) >= desired_count:
            break
        if fallback not in selected:
            selected.append(fallback)
    return selected[:desired_count]


def build_custom_role_from_prompt(prompt_preview: str, index: int) -> MattermostRoleCard:
    normalized = " ".join(re.findall(r"[a-z0-9]+", prompt_preview.lower()))
    digest = hashlib.sha256(f"{normalized}:{index}".encode("utf-8")).hexdigest()[:12]
    role_id = f"custom-role-{digest}"
    return MattermostRoleCard(
        role_id=role_id,
        display_name=f"Custom {index}",
        bot_username=f"uaa-custom-{digest}",
        summary="Custom low-risk speak-only room role derived from approved user input.",
        instructions=[
            "Speak only in enabled Mattermost rooms.",
            "Ask for UAA approval before any tool or connector action.",
        ],
        use_when=["The user asked for a custom room role."],
        do_not_use_when=["The role would require unapproved authority."],
    )
