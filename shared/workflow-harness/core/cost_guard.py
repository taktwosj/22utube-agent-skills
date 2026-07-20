"""Episode cost guard.

Locked at G00. Rules (V2 design section 7.4):
- No configured budget means no paid automatic action.
- No silent retry is allowed.
- A paid action must write a COST_AUTHORIZED ledger event before execution.
- Budget overrun triggers STOP.
"""

from __future__ import annotations

from dataclasses import dataclass


class CostOverrun(Exception):
    """Raised when a paid action would exceed the configured budget."""

    def __init__(self, kind: str, requested, limit):
        super().__init__(
            f"COST_OVERRUN kind={kind} requested={requested} limit={limit}"
        )
        self.kind = kind
        self.requested = requested
        self.limit = limit


@dataclass
class CostGuard:
    episode_budget_usd: float | None
    max_model_input_tokens_per_gate: int | None
    max_model_output_tokens_per_gate: int | None
    max_paid_tts_chars: int | None
    paid_tts_authorization: dict
    spent_tts_chars: int = 0
    spent_model_input_tokens: int = 0
    spent_model_output_tokens: int = 0
    spent_usd: float = 0.0

    def can_authorize_paid_action(self) -> bool:
        """A paid action requires both a non-zero episode budget AND an
        explicit authorization scope. No budget => no paid action."""
        if self.episode_budget_usd is None or self.episode_budget_usd <= 0:
            return False
        status = self.paid_tts_authorization.get("status")
        scope = self.paid_tts_authorization.get("scope")
        if status != "AUTHORIZED_FOR_EPISODE":
            return False
        if scope in (None, "none"):
            return False
        return True

    def can_spend_tts(self, *, chars: int) -> bool:
        """Check whether a paid TTS spend of `chars` fits within both the
        authorization limit and the episode budget."""
        if chars < 0:
            return False
        if not self.can_authorize_paid_action():
            return False
        limit = self.paid_tts_authorization.get("max_chars")
        if limit is not None and self.spent_tts_chars + chars > limit:
            return False
        if (
            self.max_paid_tts_chars is not None
            and self.spent_tts_chars + chars > self.max_paid_tts_chars
        ):
            return False
        return True

    def record_tts_spend(self, *, chars: int) -> None:
        if not self.can_spend_tts(chars=chars):
            raise CostOverrun("tts_chars", chars, self.max_paid_tts_chars)
        self.spent_tts_chars += chars

    def can_spend_model_tokens(self, *, input_tokens: int, output_tokens: int) -> bool:
        if input_tokens < 0 or output_tokens < 0:
            return False
        if self.max_model_input_tokens_per_gate is not None:
            if self.spent_model_input_tokens + input_tokens > self.max_model_input_tokens_per_gate:
                return False
        if self.max_model_output_tokens_per_gate is not None:
            if self.spent_model_output_tokens + output_tokens > self.max_model_output_tokens_per_gate:
                return False
        return True

    def authorize_paid_action(
        self,
        *,
        episode_id: str,
        action_id: str,
        cost_usd: float | None,
        chars: int | None,
        ledger_events: list[dict],
    ) -> dict:
        """Return a fail-closed authorization decision without executing.

        Authorization requires all three layers:
        1. G00 episode policy authorizes the paid scope.
        2. A USER COST_AUTHORIZED event matches the exact episode/action.
        3. The requested cost and optional character count fit both the
           event limit and remaining episode limits.
        """
        if (
            cost_usd is None
            or isinstance(cost_usd, bool)
            or not isinstance(cost_usd, (int, float))
            or cost_usd < 0
        ):
            return {"status": "STOP", "reason_code": "UNKNOWN_COST"}
        if not self.can_authorize_paid_action():
            return {"status": "STOP", "reason_code": "PAID_ACTION_NOT_AUTHORIZED"}
        if chars is not None and (
            isinstance(chars, bool) or not isinstance(chars, int) or chars < 0
        ):
            return {"status": "STOP", "reason_code": "INVALID_PAID_ACTION_SIZE"}

        matches = [
            event
            for event in ledger_events
            if event.get("event_type") == "COST_AUTHORIZED"
            and event.get("actor") == "USER"
            and event.get("episode_id") == episode_id
            and event.get("action_id") == action_id
        ]
        if not matches:
            return {
                "status": "STOP",
                "reason_code": "COST_AUTHORIZED_EVENT_REQUIRED",
            }
        event = matches[-1]
        event_limit = event.get("max_cost_usd")
        if (
            isinstance(event_limit, bool)
            or not isinstance(event_limit, (int, float))
            or event_limit < cost_usd
        ):
            return {"status": "STOP", "reason_code": "ACTION_LIMIT_EXCEEDED"}
        if self.spent_usd + cost_usd > float(self.episode_budget_usd or 0):
            return {"status": "STOP", "reason_code": "BUDGET_OVERRUN"}
        if chars is not None and not self.can_spend_tts(chars=chars):
            return {"status": "STOP", "reason_code": "TTS_CHAR_LIMIT_EXCEEDED"}
        return {
            "status": "AUTHORIZED",
            "reason_code": "COST_AUTHORIZED",
            "episode_id": episode_id,
            "action_id": action_id,
            "cost_usd": float(cost_usd),
            "chars": chars,
        }

    def record_paid_action(
        self,
        *,
        episode_id: str,
        action_id: str,
        cost_usd: float | None,
        chars: int | None,
        ledger_events: list[dict],
    ) -> dict:
        decision = self.authorize_paid_action(
            episode_id=episode_id,
            action_id=action_id,
            cost_usd=cost_usd,
            chars=chars,
            ledger_events=ledger_events,
        )
        if decision["status"] != "AUTHORIZED":
            raise CostOverrun(
                decision["reason_code"],
                cost_usd,
                self.episode_budget_usd,
            )
        self.spent_usd += float(cost_usd)
        if chars is not None:
            self.spent_tts_chars += chars
        return decision
