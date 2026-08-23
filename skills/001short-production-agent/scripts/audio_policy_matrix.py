"""Canonical audio production matrix for 001short-audio-lock-v4.

Single source for the legal (production_mode, audio_policy, audio_source)
combinations.  validate_audio_caption, build_episode_capcut, and
validate_prebuild import their views from here, and
tests/test_audio_policy_matrix.py locks protocol.json and
validate_executable_protocol's ordered policy list to this table.
"""

from __future__ import annotations

CANONICAL_MODE_MATRIX = (
    ("SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_ORDER_CLEAN_AUDIO", "SOURCE_CLIP"),
    ("SOURCE_ORDER_UNCHANGED_A10_RETAINED", "A10_RETAINED_SYNC", "SOURCE_VOCAL_STEM"),
    ("URAKKAI", "A10_REASSEMBLED_SYNC", "REASSEMBLED_VOCAL_STEM"),
    ("URAKKAI", "A9_TTS_PLUS_A10_REASSEMBLED", "REASSEMBLED_VOCAL_STEM"),
    ("URAKKAI", "TTS_ONLY_MUTE_SOURCE", "GENERATED_TTS"),
    ("URAKKAI", "CAPTION_ONLY_MUTE_SOURCE", "SILENCE"),
    # Order-preserving trim: real original audio cut directly from the
    # untouched source clip (no Demucs stem involved).
    ("URAKKAI", "SOURCE_ORDER_CLEAN_AUDIO", "SOURCE_CLIP"),
)

ACCEPTED_MODE_TUPLES = frozenset(CANONICAL_MODE_MATRIX)

# A9 carries narration we generate; A10 carries the retained source speech.
# build_episode_capcut emits A10 segments only for A10_POLICIES, and
# build_episode_locks marks source_audio audible only for the same set, so
# the two must never drift apart - they live here, not in either builder.
TTS_POLICIES = frozenset({
    "TTS_ONLY_MUTE_SOURCE", "A9_TTS_PLUS_A10_RETAINED", "A9_TTS_PLUS_A10_REASSEMBLED",
})
A10_POLICIES = frozenset({
    "SOURCE_ORDER_CLEAN_AUDIO", "A10_RETAINED_SYNC", "A10_REASSEMBLED_SYNC",
    "A9_TTS_PLUS_A10_RETAINED", "A9_TTS_PLUS_A10_REASSEMBLED",
})
# SOURCE_ORDER_CLEAN_AUDIO plays the untouched source, so it is the one A10
# policy that needs no externally separated vocal stem.
STEM_POLICIES = A10_POLICIES - {"SOURCE_ORDER_CLEAN_AUDIO"}

URAKKAI_AUDIO_POLICIES = tuple(dict.fromkeys(
    policy for mode, policy, _source in CANONICAL_MODE_MATRIX if mode == "URAKKAI"
))

MODE_SOURCES_BY_POLICY: dict[str, set[tuple[str, str]]] = {}
for _mode, _policy, _source in CANONICAL_MODE_MATRIX:
    MODE_SOURCES_BY_POLICY.setdefault(_policy, set()).add((_mode, _source))

CLEAN_MODE_MATRIX = {
    mode: (policy, source)
    for mode, policy, source in CANONICAL_MODE_MATRIX
    if mode != "URAKKAI"
}
