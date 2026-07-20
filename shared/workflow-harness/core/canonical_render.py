"""Canonical JSON -> human Markdown renderer with lossless record codec.

V2 design section 37: machine JSON is canonical. Human MD is rendered from
it deterministically (no LLM — section 44.2). The two are never edited
independently. If a hand-edited MD diverges from the canonical projection,
reconciliation raises HUMAN_MD_CANONICAL_JSON_MISMATCH.

RW-P04-03 round 6 (segment-kind-aware lossless codec):
- Each tracked scalar is encoded as a single JSON array record of two
  elements: ``[path_segments, value]`` where ``path_segments`` is a list
  of ``[kind, name]`` pairs. ``kind`` is ``"key"`` (object property) or
  ``"idx"`` (array index). This disambiguates an array element
  ``foo[0].bar`` from an object property literally named ``[0]`` — the
  two never collide because the kind tag differs. ``value`` is the
  original JSON scalar (bool/number/string/null with full type, newline,
  and whitespace fidelity).
- Records are emitted one per line, prefixed with ``R ``. The MD therefore
  round-trips losslessly: parsing the record lines yields exactly the
  canonical scalars.
- reconcile_human_md compares the canonical record list against the
  human-MD-parsed record list as a SORTED MULTIPLICITY-PRESERVING list
  (NOT a set). Duplicate record lines, dot-bearing keys, and
  array-index-vs-bracket-key collisions can no longer hide changes.

IN_SYNC vs COSMETIC_DIFF_ONLY:
- IN_SYNC: the rendered MD is byte-identical to a fresh canonical render.
- COSMETIC_DIFF_ONLY: the record lists are identical (same scalars) but
  the surrounding MD text differs (whitespace, comments, prose).
- Otherwise: HUMAN_MD_CANONICAL_JSONMismatch.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


class HumanMdCanonicalJsonMismatch(Exception):
    def __init__(self, kind: str, detail: str):
        super().__init__(f"HUMAN_MD_CANONICAL_JSON_MISMATCH kind={kind} {detail}")
        self.kind = kind
        self.detail = detail


RECORD_PREFIX = "R "


def _hash_canonical(canonical: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            canonical,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest().upper()


def _collect_records(
    value: Any,
    segments: list[list[str]] | None = None,
) -> list[tuple[list[list[str]], Any]]:
    """Walk canonical recursively and return [(segments, value)] for every
    scalar leaf plus explicit markers for empty containers.

    Each segment is a ``[kind, name]`` pair where ``kind`` is ``"key"``
    (object property) or ``"idx"`` (array index, name is ``"[i]"``). This
    disambiguates ``foo[0].bar`` (idx "[0]") from an object property
    literally named ``"[0]"`` (key "[0]") — the two never collide because
    the kind tag differs (RW-P04-03 round 6).

    Containers (dict / non-empty list) produce no record of their own but
    their children carry the parent segments. Empty containers emit a
    synthetic record so adding/removing them is detectable.
    """
    if segments is None:
        segments = []
    out: list[tuple[list[list[str]], Any]] = []
    if isinstance(value, dict):
        if not value:
            out.append((list(segments), {"__empty__": "object"}))
            return out
        for k in sorted(value.keys()):
            child = [list(s) for s in segments]
            child.append(["key", str(k)])
            out.extend(_collect_records(value[k], child))
        return out
    if isinstance(value, list):
        if not value:
            out.append((list(segments), {"__empty__": "list"}))
            return out
        for i, item in enumerate(value):
            child = [list(s) for s in segments]
            child.append(["idx", f"[{i}]"])
            out.extend(_collect_records(item, child))
        return out
    # Scalar leaf — keep the original Python value so json.dumps preserves
    # the JSON type exactly (bool vs number vs string).
    out.append((list(segments), value))
    return out


def _serialize_record(segments: list[str], value: Any) -> str:
    """Encode one record as a single JSON array line."""
    return RECORD_PREFIX + json.dumps(
        [segments, value],
        ensure_ascii=False,
        allow_nan=False,
    )


def _reject_nonfinite_json_constant(constant: str) -> None:
    raise ValueError(f"non-standard JSON constant: {constant}")


def _parse_record_line(line: str) -> tuple[list[list[str]], Any] | None:
    """Parse a single record line. Returns (segments, value) or None if
    the line is not a record line.

    Each segment must be a ``[kind, name]`` pair where ``kind`` is
    ``"key"`` or ``"idx"``. Round-6 requirement: kind tag is mandatory so
    an array index never collides with an object key of the same text.
    """
    s = line.strip()
    if not s.startswith(RECORD_PREFIX):
        return None
    payload = s[len(RECORD_PREFIX):]
    try:
        rec = json.loads(
            payload,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(rec, list) or len(rec) != 2:
        return None
    segments, value = rec
    if not isinstance(segments, list):
        return None
    for seg in segments:
        if (
            not isinstance(seg, list)
            or len(seg) != 2
            or seg[0] not in ("key", "idx")
            or not isinstance(seg[1], str)
        ):
            return None
    return segments, value


def _parse_records_from_md(md: str) -> list[tuple[list[list[str]], Any]]:
    """Parse every record line in the MD, preserving multiplicity and order."""
    out: list[tuple[list[list[str]], Any]] = []
    for raw in md.splitlines():
        rec = _parse_record_line(raw)
        if rec is not None:
            out.append(rec)
    return out


def _assert_json_compatible(value: Any, path: str = "<root>") -> None:
    """Reject values that Python can serialize to JSON but that are NOT
    themselves JSON-native. This catches:

    - tuples (Python tuple serializes to JSON array; if the caller passed
      a tuple they meant something JSON cannot represent faithfully)
    - non-string dict keys (JSON keys MUST be strings; an int/bool/None
      key would silently coerce to a string key on json.dumps and could
      collide with a real string key)

    Anything that json.dumps cannot serialize is already rejected by the
    subsequent json.dumps call (set, object, cyclic refs, etc.).
    """
    if isinstance(value, tuple):
        raise TypeError(
            f"CANONICAL_NOT_JSON_NATIVE: tuple at {path} — JSON has no tuple type"
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise TypeError(
            f"CANONICAL_NOT_JSON_NATIVE: non-finite float {value!r} at {path} — "
            "JSON numbers must be finite"
        )
    if isinstance(value, dict):
        for k in value.keys():
            if not isinstance(k, str):
                raise TypeError(
                    f"CANONICAL_NOT_JSON_NATIVE: non-string dict key {k!r} at {path} — "
                    "JSON keys must be strings"
                )
        for k, v in value.items():
            _assert_json_compatible(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _assert_json_compatible(item, f"{path}[{i}]")


def render_markdown(canonical: Any) -> str:
    """Render canonical JSON to deterministic markdown with lossless record
    encoding."""
    # Round 8: reject Python-native-but-not-JSON-native inputs (tuples,
    # non-string dict keys) BEFORE they silently coerce through json.dumps.
    _assert_json_compatible(canonical)
    # Round-trip through json for deterministic key ordering and to reject
    # non-JSON-serializable input early.
    serialized = json.dumps(
        canonical,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    canonical_norm = json.loads(serialized)
    sha = _hash_canonical(canonical_norm)

    records = _collect_records(canonical_norm)
    # Sort records by (segments, json(value)) for deterministic output that
    # is independent of insertion order.
    records.sort(
        key=lambda r: (
            r[0],
            json.dumps(
                r[1],
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            ),
        )
    )

    title = (
        canonical_norm.get("schema_version")
        if isinstance(canonical_norm, dict)
        else None
    ) or "canonical-json"

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("<!-- Rendered from canonical JSON. Do not edit. -->")
    lines.append("<!-- Each 'R ' line below is one JSON record [segments, value].")
    lines.append("     Reconciliation parses those records and compares them")
    lines.append("     losslessly as a sorted, multiplicity-preserving list. -->")
    lines.append("")
    lines.append("## Records")
    lines.append("")
    for segments, value in records:
        lines.append(_serialize_record(segments, value))
    lines.append("")
    lines.append(f"<!-- CANONICAL_SHA256: {sha} -->")
    lines.append("")
    return "\n".join(lines)


def reconcile_human_md(*, canonical: Any, human_md: str) -> dict:
    """Compare a hand-edited MD against the canonical JSON projection.

    Strategy (RW-P04-03 round 5, lossless codec):
    - Build the canonical record list (segments, value) preserving type
      and multiplicity.
    - Parse the human MD's R-lines into the same shape.
    - Sort both lists (canonical key for sorted order) and compare element
      by element. Set semantics are explicitly forbidden: duplicate lines
      and structural collisions must be caught.

    Outcomes:
    - IN_SYNC: the human MD is byte-identical to a fresh canonical render.
    - COSMETIC_DIFF_ONLY: the record lists are identical (same scalars,
      same multiplicity) but the surrounding MD text differs.
    - HumanMdCanonicalJsonMismatch: the record lists differ.
    """
    # Round 8: reject non-JSON-native canonical inputs on this path too.
    _assert_json_compatible(canonical)
    canonical_norm = json.loads(
        json.dumps(
            canonical,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    canonical_records = _collect_records(canonical_norm)
    human_records = _parse_records_from_md(human_md)

    # Comparison key: canonical-form JSON of (segments, value). We compare
    # the JSON-serialized form rather than the Python objects so that
    # distinct JSON values that compare equal in Python (e.g. int 1 and
    # float 1.0, or 0 and False) are correctly distinguished. The key is
    # also hashable for the multiplicity counter below.
    def _key(rec: tuple[list[list[str]], Any]) -> tuple:
        segments, value = rec
        segments_tuple = tuple(tuple(s) for s in segments)
        return (
            segments_tuple,
            json.dumps(
                value,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            ),
        )

    canonical_keys = sorted(_key(r) for r in canonical_records)
    human_keys = sorted(_key(r) for r in human_records)

    if canonical_keys == human_keys:
        # Record lists identical at the JSON-fidelity level. Now decide
        # IN_SYNC vs COSMETIC_DIFF_ONLY by comparing the surrounding MD
        # text against a fresh render.
        fresh = render_markdown(canonical)
        if human_md.strip() == fresh.strip():
            return {"status": "IN_SYNC", "action": "NONE"}
        return {"status": "COSMETIC_DIFF_ONLY", "action": "RE_RENDER_RECOMMENDED"}

    # Record lists differ. Classify the difference for the error message.
    canonical_count: dict[tuple, int] = {}
    for k in canonical_keys:
        canonical_count[k] = canonical_count.get(k, 0) + 1
    human_count: dict[tuple, int] = {}
    for k in human_keys:
        human_count[k] = human_count.get(k, 0) + 1

    missing = [
        k for k, n in canonical_count.items() if human_count.get(k, 0) < n
    ]
    extra = [
        k for k, n in human_count.items() if canonical_count.get(k, 0) < n
    ]
    # Render a short readable preview of the first few diffs.
    def _preview(key_tuple: tuple) -> str:
        segments_tuple, value_json = key_tuple
        # segments_tuple is a tuple of (kind, name) tuples.
        path = "/".join(
            f"{kind}:{name}" for kind, name in segments_tuple
        ) if segments_tuple else "<root>"
        return f"{path}={value_json}"

    detail = (
        f"missing_or_underrepresented={[ _preview(k) for k in missing[:5] ]} "
        f"extra_or_overrepresented={[ _preview(k) for k in extra[:5] ]} "
        f"(canonical_records={len(canonical_keys)} "
        f"human_records={len(human_keys)})"
    )
    raise HumanMdCanonicalJsonMismatch("STRUCTURAL_OR_VALUE_CHANGE", detail)
