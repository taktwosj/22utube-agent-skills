"""Deterministic gate validator.

The validator validates the current gate only and returns a gate_result
document. It never:
- calls an external model
- calls another skill
- opens CapCut
- generates creative text
- performs paid TTS
- uploads
- silently advances authority

Pass authority is DETERMINISTIC_VALIDATOR_ONLY.
"""

from __future__ import annotations


SCHEMA_VERSION = "gate-result-v1"

ALLOWED_AUTO_ADVANCE_CLASSES = {
    "NONE",
    "DETERMINISTIC_ONLY",
    "LLM_CALL_FORBIDDEN",
    "PAID_ACTION_FORBIDDEN",
    "UPLOAD_FORBIDDEN",
}

# Any class value outside the allowed set is treated as a forbidden attempt
# to authorize automatic LLM / paid / upload work.
FORBIDDEN_AUTO_ADVANCE_CLASSES = {
    "LLM_CALL_ALLOWED",
    "PAID_ACTION_ALLOWED",
    "UPLOAD_ALLOWED",
}


class ForbiddenAdvanceClass(Exception):
    """Raised when a validator result asks the runner to perform automatic
    LLM / paid / upload work — which the validator is never allowed to do."""

    def __init__(self, auto_advance_class: str):
        super().__init__(
            f"FORBIDDEN_ADVANCE_CLASS auto_advance_class={auto_advance_class}"
        )
        self.auto_advance_class = auto_advance_class


class PassWithErrorsForbidden(Exception):
    """Raised when a caller asks validate_gate to emit PASS while the errors
    list is non-empty. PASS is the deterministic validator's positive verdict
    and must never coexist with recorded errors."""

    def __init__(self):
        super().__init__(
            "PASS_WITH_ERRORS_FORBIDDEN: status=PASS requires empty errors"
        )


def validate_gate(
    *,
    lane: str,
    gate: str,
    subgate: str | None,
    validated_inputs: list[dict],
    evidence: list[dict],
    errors: list[dict],
    warnings: list[dict],
    next_action: str,
    auto_advance_allowed: bool,
    auto_advance_class: str,
    status: str | None = None,
    reason_code: str | None = None,
) -> dict:
    """Construct a gate_result document.

    The validator itself never executes any next action; the runner does.
    The runner must reject any result whose auto_advance_class requests
    automatic LLM, paid, or upload work.

    Authority rule: if `errors` is non-empty the status can never be PASS.
    An explicit status=PASS with non-empty errors raises
    PassWithErrorsForbidden. When status is None, it is derived as FAIL
    when errors exist and PASS otherwise.
    """
    if auto_advance_class in FORBIDDEN_AUTO_ADVANCE_CLASSES:
        raise ForbiddenAdvanceClass(auto_advance_class)
    if auto_advance_class not in ALLOWED_AUTO_ADVANCE_CLASSES:
        raise ForbiddenAdvanceClass(auto_advance_class)

    has_errors = bool(errors)
    if status == "PASS" and has_errors:
        raise PassWithErrorsForbidden()

    derived_status = status
    if derived_status is None:
        derived_status = "FAIL" if has_errors else "PASS"

    result = {
        "schema_version": SCHEMA_VERSION,
        "status": derived_status,
        "reason_code": reason_code,
        "lane": lane,
        "gate": gate,
        "subgate": subgate,
        "validated_inputs": list(validated_inputs),
        "evidence": list(evidence),
        "errors": list(errors),
        "warnings": list(warnings),
        "next_action": next_action,
        "auto_advance_allowed": bool(auto_advance_allowed),
        "auto_advance_class": auto_advance_class,
    }
    return result
