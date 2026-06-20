from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ultimate_ai_agent.core.mattermost.contracts import (
    MattermostAuditEvent,
    MattermostBridgeReceipt,
    MattermostRoleBinding,
    safe_model_dump,
)
from ultimate_ai_agent.core.time import utc_now


class MattermostBridgeStore:
    def __init__(self, storage_dir: str | Path):
        self.storage_dir = Path(storage_dir)
        self.bindings_path = self.storage_dir / "bindings.json"
        self.audit_path = self.storage_dir / "audit.jsonl"
        self.receipts_path = self.storage_dir / "receipts.jsonl"
        self.idempotency_path = self.storage_dir / "idempotency.jsonl"
        self.cooldowns_path = self.storage_dir / "cooldowns.jsonl"

    @property
    def storage_ref(self) -> str:
        return "mattermost-bridge-storage:local"

    def list_bindings(self) -> list[MattermostRoleBinding]:
        payload = self._read_json_object(self.bindings_path)
        records = payload.get("bindings", [])
        bindings: list[MattermostRoleBinding] = []
        for record in records:
            try:
                bindings.append(MattermostRoleBinding(**record))
            except (TypeError, ValidationError):
                continue
        return bindings

    def save_binding(self, binding: MattermostRoleBinding) -> MattermostRoleBinding:
        bindings = [
            existing
            for existing in self.list_bindings()
            if not (
                existing.workspace_ref == binding.workspace_ref
                and existing.channel_ref == binding.channel_ref
            )
        ]
        bindings.append(binding)
        self._write_json_object(
            self.bindings_path,
            {"bindings": [item.model_dump(mode="json") for item in bindings]},
        )
        return binding

    def find_binding(self, workspace_ref: str, channel_ref: str) -> MattermostRoleBinding | None:
        for binding in self.list_bindings():
            if binding.workspace_ref == workspace_ref and binding.channel_ref == channel_ref:
                return binding
        return None

    def unbind_roles(self, workspace_ref: str, channel_ref: str, role_ids: list[str]) -> MattermostRoleBinding | None:
        binding = self.find_binding(workspace_ref, channel_ref)
        if binding is None:
            return None
        if role_ids:
            remaining = [role_id for role_id in binding.role_ids if role_id not in set(role_ids)]
        else:
            remaining = []
        updated = binding.model_copy(update={"role_ids": remaining, "enabled": bool(remaining)})
        return self.save_binding(updated)

    def idempotency_seen(self, idempotency_key: str) -> bool:
        return any(record.get("idempotency_key") == idempotency_key for record in self._read_jsonl(self.idempotency_path))

    def record_idempotency(self, idempotency_key: str, decision_ref: str) -> None:
        self._append_jsonl(
            self.idempotency_path,
            {"idempotency_key": idempotency_key, "decision_ref": decision_ref},
        )

    def latest_cooldown_at(self, scope_ref: str) -> datetime | None:
        latest: datetime | None = None
        for record in self._read_jsonl(self.cooldowns_path):
            if record.get("scope_ref") != scope_ref:
                continue
            created_at = record.get("created_at")
            if not isinstance(created_at, str):
                continue
            try:
                parsed = datetime.fromisoformat(created_at)
            except ValueError:
                continue
            if latest is None or parsed > latest:
                latest = parsed
        return latest

    def record_cooldown(self, scope_ref: str, decision_ref: str) -> None:
        self._append_jsonl(
            self.cooldowns_path,
            {
                "scope_ref": scope_ref,
                "decision_ref": decision_ref,
                "created_at": utc_now().isoformat(),
            },
        )

    def append_audit_event(self, event: MattermostAuditEvent) -> MattermostAuditEvent:
        self._append_jsonl(self.audit_path, event.model_dump(mode="json"))
        return event

    def append_receipt(self, receipt: MattermostBridgeReceipt) -> MattermostBridgeReceipt:
        self._append_jsonl(self.receipts_path, receipt.model_dump(mode="json"))
        return receipt

    def audit_events(self, limit: int = 100) -> list[MattermostAuditEvent]:
        records = self._read_jsonl(self.audit_path)[-max(1, min(limit, 500)) :]
        events: list[MattermostAuditEvent] = []
        for record in records:
            try:
                events.append(MattermostAuditEvent(**record))
            except ValidationError:
                continue
        return events

    def receipts(self, limit: int = 100) -> list[MattermostBridgeReceipt]:
        records = self._read_jsonl(self.receipts_path)[-max(1, min(limit, 500)) :]
        receipts: list[MattermostBridgeReceipt] = []
        for record in records:
            try:
                receipts.append(MattermostBridgeReceipt(**record))
            except ValidationError:
                continue
        return receipts

    def _ensure_dir(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _read_json_object(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _write_json_object(self, path: Path, payload: dict[str, Any]) -> None:
        self._ensure_dir()
        tmp_path = path.with_name(f".{path.name}.tmp")
        tmp_path.write_text(
            json.dumps(safe_model_dump(payload), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(path)

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(loaded, dict):
                records.append(loaded)
        return records

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        self._ensure_dir()
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
