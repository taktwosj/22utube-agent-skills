"""Append-only gate ledger.

Authority model:
- gate_ledger.jsonl is the single source of truth.
- manual_gate_state.json is a projection only; rebuilt from the ledger.
- A new event must reference an existing previous_event_id (or null only
  for the genesis WORKFLOW_CREATED event). A broken chain is rejected.

This module is pure: it never performs I/O on episode runtime paths.
Callers pass events in; the store validates and retains them in memory.
Persistence (jsonl append) is the caller's responsibility.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterable


class BrokenChainError(Exception):
    """Raised when an appended event references a non-existent
    previous_event_id, or when the event_id collides with an existing one."""

    def __init__(self, event_id: str, previous_event_id: str | None):
        super().__init__(
            f"BROKEN_CHAIN event_id={event_id} "
            f"previous_event_id={previous_event_id}"
        )
        self.event_id = event_id
        self.previous_event_id = previous_event_id


class DuplicateEventError(Exception):
    def __init__(self, event_id: str):
        super().__init__(f"DUPLICATE_EVENT event_id={event_id}")
        self.event_id = event_id


@dataclass
class LedgerStore:
    """In-memory append-only event log.

    Validations performed on append:
    - event_id must be unique within the store.
    - previous_event_id must reference an existing event, or be None only
      when the store is empty (genesis).
    """

    events: list[dict] = field(default_factory=list)
    _by_id: dict[str, dict] = field(default_factory=dict)

    def append(self, event: dict) -> dict:
        if not isinstance(event, dict):
            raise TypeError("ledger event must be a dict")
        event_id = event.get("event_id")
        prev = event.get("previous_event_id")
        if not event_id:
            raise BrokenChainError(None, prev)
        if event_id in self._by_id:
            raise DuplicateEventError(event_id)
        # Genesis rule: the very first event must have previous_event_id=None.
        if not self.events:
            if prev is not None:
                raise BrokenChainError(event_id, prev)
        else:
            if prev is None:
                raise BrokenChainError(event_id, None)
            if prev not in self._by_id:
                raise BrokenChainError(event_id, prev)
        # Freeze a shallow copy to avoid callers mutating history.
        stored = dict(event)
        self.events.append(stored)
        self._by_id[event_id] = stored
        return stored

    def extend(self, events: Iterable[dict]) -> None:
        for e in events:
            self.append(e)

    def latest_event_id(self) -> str | None:
        return self.events[-1]["event_id"] if self.events else None

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps(e, ensure_ascii=False) for e in self.events)

    @classmethod
    def from_jsonl(cls, text: str) -> "LedgerStore":
        store = cls()
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            store.append(json.loads(line))
        return store
