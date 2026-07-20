"""Shared deterministic-only workflow runner policy."""

from __future__ import annotations


FORBIDDEN_ADVANCE_CLASSES = {
    "LLM_CALL_ALLOWED",
    "PAID_ACTION_ALLOWED",
    "UPLOAD_ALLOWED",
}
FORBIDDEN_ACTION_MARKERS = (
    "LLM",
    "MODEL",
    "CAPCUT",
    "GUI",
    "UPLOAD",
    "RELEASE",
    "RETRY",
    "TRANSPORT",
)


def _stop(reason_code: str, detail: str | None = None) -> dict:
    result = {
        "status": "STOP",
        "reason_code": reason_code,
        "next_action": "NONE",
        "max_auto_retries": 0,
    }
    if detail is not None:
        result["detail"] = detail
    return result


def decide_runner_action(
    *,
    validator_result: dict,
    allowed_deterministic_actions: set[str],
    wait_actions: set[str],
    episode_id: str | None = None,
    paid_action: dict | None = None,
    cost_guard=None,
    ledger_events: list[dict] | None = None,
) -> dict:
    """Evaluate a validator result; never execute its next action."""
    if validator_result.get("schema_version") != "gate-result-v1":
        return _stop("INVALID_VALIDATOR_RESULT")
    advance_class = validator_result.get("auto_advance_class")
    if advance_class in FORBIDDEN_ADVANCE_CLASSES or advance_class not in {
        "NONE",
        "DETERMINISTIC_ONLY",
    }:
        return _stop("FORBIDDEN_ADVANCE_CLASS", str(advance_class))

    action = str(validator_result.get("next_action", "NONE"))
    status = validator_result.get("status")
    if action in wait_actions and status != "FAIL":
        return {
            "status": "WAIT",
            "reason_code": action,
            "next_action": action,
            "max_auto_retries": 0,
        }
    if status not in ("PASS", "NOT_REQUIRED"):
        return _stop("VALIDATOR_NOT_PASS", str(status))

    if paid_action is not None:
        if cost_guard is None or episode_id is None:
            return _stop("PAID_ACTION_POLICY_REQUIRED")
        normalized_events = getattr(ledger_events, "events", ledger_events) or []
        decision = cost_guard.authorize_paid_action(
            episode_id=episode_id,
            action_id=paid_action.get("action_id", ""),
            cost_usd=paid_action.get("cost_usd"),
            chars=paid_action.get("chars"),
            ledger_events=normalized_events,
        )
        if decision.get("status") != "AUTHORIZED":
            return _stop(decision.get("reason_code", "PAID_ACTION_REJECTED"))
        return {
            "status": "WAIT",
            "reason_code": "PAID_ACTION_AUTHORIZED_MANUAL_EXECUTION_ONLY",
            "next_action": "WAIT_PAID_ACTION_EXECUTION",
            "max_auto_retries": 0,
            "authorization": decision,
        }

    if any(marker in action.upper() for marker in FORBIDDEN_ACTION_MARKERS) or action.startswith(
        ("PAID_", "COST_")
    ):
        return _stop("FORBIDDEN_AUTO_ACTION", action)
    if action == "NONE":
        return _stop("NO_NEXT_ACTION")
    if action not in allowed_deterministic_actions:
        return _stop("ACTION_NOT_ALLOWLISTED", action)
    if validator_result.get("auto_advance_allowed") is not True:
        return _stop("AUTO_ADVANCE_NOT_ALLOWED")
    return {
        "status": "EXECUTE_DETERMINISTIC",
        "reason_code": "DETERMINISTIC_ACTION_ALLOWED",
        "next_action": action,
        "auto_advance_class": "DETERMINISTIC_ONLY",
        "max_auto_retries": 0,
    }
