from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audio_policy_matrix as matrix
import track_contract
import validate_capcut_grids
import validate_executable_protocol


class AudioPolicyMatrixContractTest(unittest.TestCase):
    def test_matrix_rows_are_unique_v4_tuples(self):
        self.assertEqual(len(set(matrix.CANONICAL_MODE_MATRIX)), len(matrix.CANONICAL_MODE_MATRIX))
        for row in matrix.CANONICAL_MODE_MATRIX:
            self.assertEqual(len(row), 3)
        self.assertEqual(
            {mode for mode, _policy, _source in matrix.CANONICAL_MODE_MATRIX},
            {"URAKKAI", "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_ORDER_UNCHANGED_A10_RETAINED"},
        )

    def test_protocol_urakkai_policies_match_matrix(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        allowed = protocol["production_modes"]["URAKKAI"]["allowed_audio_policies"]
        self.assertEqual(set(allowed), set(matrix.URAKKAI_AUDIO_POLICIES))
        self.assertEqual(len(allowed), len(set(allowed)))

    def test_executable_protocol_constants_match_matrix(self):
        self.assertEqual(
            set(validate_executable_protocol.ALLOWED_URAKKAI_AUDIO_POLICIES),
            set(matrix.URAKKAI_AUDIO_POLICIES),
        )
        self.assertLessEqual(
            set(validate_executable_protocol.A10_AUDIO_POLICIES),
            set(matrix.URAKKAI_AUDIO_POLICIES),
        )

    def test_human_grid_rows_derive_from_canonical_tracks(self):
        self.assertEqual(len(track_contract.HUMAN_GRID_ROWS), 15)
        self.assertEqual(
            track_contract.HUMAN_GRID_ROWS,
            tuple(reversed(track_contract.CANONICAL_TRACKS[:track_contract.VISUAL_TRACK_COUNT]))
            + track_contract.CANONICAL_TRACKS[track_contract.VISUAL_TRACK_COUNT:],
        )
        self.assertIs(validate_capcut_grids.REQUIRED_ROWS, track_contract.HUMAN_GRID_ROWS)

    def test_clean_mode_matrix_covers_only_clean_modes(self):
        self.assertEqual(
            set(matrix.CLEAN_MODE_MATRIX),
            {"SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_ORDER_UNCHANGED_A10_RETAINED"},
        )


if __name__ == "__main__":
    unittest.main()
