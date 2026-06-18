from __future__ import annotations

from ultimate_ai_agent.core.capabilities.models import CapabilityCatalogEntry


def render_compact_catalog(entries: list[CapabilityCatalogEntry], *, max_entries: int | None = None) -> str:
    selected = entries[:max_entries] if max_entries is not None else entries
    lines: list[str] = []
    for entry in selected:
        modes = ",".join(mode.value for mode in entry.allowed_coordination_modes)
        tags = ",".join(entry.tags[:6])
        lines.append(
            " | ".join(
                [
                    f"id={entry.id}",
                    f"kind={entry.kind.value}",
                    f"risk={entry.risk_level.value}",
                    f"side_effects={entry.side_effects.value}",
                    f"modes={modes}",
                    f"tags={tags}",
                    f"desc={entry.description}",
                ]
            )
        )
    return "\n".join(lines)
