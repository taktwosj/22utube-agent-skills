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
        if self.max_model_input_tokens_per_gate is not None:
            if self.spent_model_input_tokens + input_tokens > self.max_model_input_tokens_per_gate:
                return False
        if self.max_model_output_tokens_per_gate is not None:
            if self.spent_model_output_tokens + output_tokens > self.max_model_output_tokens_per_gate:
                return False
        return True
