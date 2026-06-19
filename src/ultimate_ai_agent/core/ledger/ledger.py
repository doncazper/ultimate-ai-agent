import json
from collections import defaultdict
from typing import List, Optional, Set
from pathlib import Path

from ultimate_ai_agent.core.ledger.events import EventLedgerEvent
from ultimate_ai_agent.core.ledger.enums import RunState
from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.ledger.replay import replay_run_events
from ultimate_ai_agent.core.ledger.receipts import RunReceipt, generate_receipt_from_events

class EventLedger:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = Path(filepath) if filepath else None
        self._events: List[EventLedgerEvent] = []
        self._event_ids: Set[str] = set()
        self._events_by_id: dict[str, EventLedgerEvent] = {}
        self._events_by_run: dict[str, list[EventLedgerEvent]] = defaultdict(list)
        self._idempotency_keys_by_run: dict[str, set[str]] = defaultdict(set)

        if self.filepath:
            self._load_from_file()

    def _load_from_file(self) -> None:
        if self.filepath.exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        event_dict = json.loads(line)
                        event = EventLedgerEvent.model_validate(event_dict)
                        if scan_payload_for_secrets(event.model_dump()):
                            raise ValueError("Event load blocked: raw secrets/credentials detected in payload")
                        self._append_in_memory(event)

    def append_event(self, event: EventLedgerEvent) -> None:
        # Rule 1: Reject duplicate event_id
        if event.event_id in self._event_ids:
            raise ValueError(f"Duplicate event_id detected: {event.event_id}")

        # Rule 2: Reject duplicate idempotency_key for the same run
        if event.idempotency_key and event.idempotency_key in self._idempotency_keys_by_run[event.run_id]:
            raise ValueError(f"Duplicate idempotency_key detected for run_id '{event.run_id}': {event.idempotency_key}")

        # Rule 3: Scan event payload and metadata for secrets
        if scan_payload_for_secrets(event.model_dump()):
            raise ValueError("Event append blocked: raw secrets/credentials detected in payload")

        # Save to memory
        self._append_in_memory(event)

        # Write to JSONL
        if self.filepath:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

    def _append_in_memory(self, event: EventLedgerEvent) -> None:
        if event.event_id in self._event_ids:
            raise ValueError(f"Duplicate event_id detected: {event.event_id}")
        if event.idempotency_key and event.idempotency_key in self._idempotency_keys_by_run[event.run_id]:
            raise ValueError(f"Duplicate idempotency_key detected for run_id '{event.run_id}': {event.idempotency_key}")
        self._events.append(event)
        self._event_ids.add(event.event_id)
        self._events_by_id[event.event_id] = event
        self._events_by_run[event.run_id].append(event)
        if event.idempotency_key:
            self._idempotency_keys_by_run[event.run_id].add(event.idempotency_key)

    def list_events(self, run_id: Optional[str] = None) -> List[EventLedgerEvent]:
        if run_id:
            return list(self._events_by_run.get(run_id, []))
        return list(self._events)

    def get_event(self, event_id: str) -> Optional[EventLedgerEvent]:
        return self._events_by_id.get(event_id)

    def replay_run(self, run_id: str) -> RunState:
        run_state = replay_run_events(run_id, self.list_events(run_id))
        return run_state.current_state

    def generate_receipt(self, run_id: str) -> RunReceipt:
        return generate_receipt_from_events(run_id, self.list_events(run_id))

    def validate_trace_integrity(self, run_id: str, allow_external_parent_spans: bool = True) -> bool:
        """Validate trace details and chronological ordering of trace spans.

        Policy:
        - If allow_external_parent_spans is True (default), a parent_span_id that is not in the run's span IDs
          is considered an external parent span (e.g. from an external systems call) and is allowed.
          This is common at API and worker boundaries.
        - If allow_external_parent_spans is False (internal-only mode), all parent_span_ids must correspond to
          a span_id defined within the run's events, otherwise verification fails.
        """
        run_events = self.list_events(run_id)
        if not run_events:
            return True

        # Check chronological consistency of the stored (append-order) trace.
        # NOTE: do NOT sort here. The ledger is append-only and events are recorded
        # in the order they occur, so the stored order must already be chronologically
        # non-decreasing. Sorting first would make the check below unreachable and
        # silently accept out-of-order traces.
        last_time = run_events[0].occurred_at
        for event in run_events:
            if event.occurred_at < last_time:
                return False
            last_time = event.occurred_at

        # Verify trace IDs match
        first_trace = run_events[0].trace_id
        for event in run_events:
            if event.trace_id != first_trace:
                return False

        # Verify parent span connections exist if parent_span_id is provided
        span_ids = {e.span_id for e in run_events}
        for event in run_events:
            if event.parent_span_id and event.parent_span_id not in span_ids:
                if not allow_external_parent_spans:
                    return False

        return True
