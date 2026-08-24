from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import track_template_matrix as matrix
import track_contract
import build_episode_capcut as builder
import user_provided_media_overlay
import validate_capcut_grids
import validate_capcut_project
import validate_design_lock


EXPECTED_PHYSICAL_TRACKS = (
    "VIDEO",
    "SCREEN_EFFECT",
    "SCREEN_WHITE",
    "SOURCE_CREDIT",
    "STATE_GLITCH",
    "STATE_LASER",
    "A10_TEXT_WHITE",
    "A10_TEXT_YELLOW",
    "A9_TEXT",
    "T2",
    "T1",
    "A9",
    "A10",
    "A11",
    "A12_RESERVED_EMPTY",
)
EXPECTED_HUMAN_GRID_ROWS = (
    "T1",
    "T2",
    "A9_TEXT",
    "A10_TEXT_YELLOW",
    "A10_TEXT_WHITE",
    "STATE_LASER",
    "STATE_GLITCH",
    "SOURCE_CREDIT",
    "SCREEN_WHITE",
    "SCREEN_EFFECT",
    "VIDEO",
    "A9",
    "A10",
    "A11",
    "A12_RESERVED_EMPTY",
)
BASE_REQUIRED_SEEDS = ("VIDEO", "A9", "A10")
SEED_PRESERVED_ROLES = frozenset(
    {"VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "T2", "T1"}
)
EXPECTED_CLEAR_TRACK_INDICES = (3, 4, 5, 6, 7, 8, 11, 12, 13, 14)


class TrackTemplateMatrixContractTest(unittest.TestCase):
    def test_physical_track_order_is_exactly_fifteen_tracks(self):
        self.assertEqual(matrix.CANONICAL_TRACKS, EXPECTED_PHYSICAL_TRACKS)
        self.assertEqual(len(matrix.CANONICAL_TRACKS), 15)
        self.assertEqual(matrix.TRACK_INDEX["SOURCE_CREDIT"], 3)
        self.assertEqual(matrix.A12_INDEX, 14)
        self.assertEqual(matrix.TRACK_INDEX["A12_RESERVED_EMPTY"], 14)

    def test_human_grid_order_is_distinct_from_physical_order(self):
        self.assertNotEqual(matrix.HUMAN_GRID_ROWS, matrix.CANONICAL_TRACKS)
        self.assertEqual(matrix.HUMAN_GRID_ROWS, EXPECTED_HUMAN_GRID_ROWS)
        self.assertEqual(
            matrix.HUMAN_GRID_ROWS,
            tuple(reversed(matrix.CANONICAL_TRACKS[: matrix.VISUAL_TRACK_COUNT]))
            + matrix.CANONICAL_TRACKS[matrix.VISUAL_TRACK_COUNT :],
        )

    def test_v2_and_v3_keep_track_three_physically_stable_but_logically_distinct(self):
        v2 = matrix.track_template_profile(matrix.V2_TEMPLATE_PROFILE)
        v3 = matrix.track_template_profile(matrix.V3_TEMPLATE_PROFILE)

        self.assertEqual(v2.physical_tracks, EXPECTED_PHYSICAL_TRACKS)
        self.assertEqual(v3.physical_tracks, EXPECTED_PHYSICAL_TRACKS)
        self.assertIsNone(v2.logical_role_by_track[3])
        self.assertEqual(v3.logical_role_by_track[3], "SOURCE_CREDIT")
        self.assertFalse(
            matrix.profile_supports_role(matrix.V2_TEMPLATE_PROFILE, "SOURCE_CREDIT")
        )
        self.assertTrue(
            matrix.profile_supports_role(matrix.V3_TEMPLATE_PROFILE, "SOURCE_CREDIT")
        )

    def test_required_seeds_and_clear_indices_are_profile_data(self):
        v2 = matrix.track_template_profile(matrix.V2_TEMPLATE_PROFILE)
        v3 = matrix.track_template_profile(matrix.V3_TEMPLATE_PROFILE)

        self.assertEqual(v2.required_seed_roles, BASE_REQUIRED_SEEDS)
        self.assertEqual(
            v3.required_seed_roles,
            BASE_REQUIRED_SEEDS + ("SOURCE_CREDIT",),
        )
        self.assertEqual(v2.seed_preserved_roles, SEED_PRESERVED_ROLES)
        self.assertEqual(v3.seed_preserved_roles, SEED_PRESERVED_ROLES)
        self.assertEqual(v2.clear_track_indices, EXPECTED_CLEAR_TRACK_INDICES)
        self.assertEqual(v3.clear_track_indices, EXPECTED_CLEAR_TRACK_INDICES)

    def test_capabilities_and_layout_lookup_support_a_third_profile_by_data(self):
        v3 = matrix.track_template_profile(matrix.V3_TEMPLATE_PROFILE)
        future = matrix.TrackTemplateProfile(
            name="fixture_source_credit_profile",
            track_layout=v3.track_layout,
            physical_tracks=v3.physical_tracks,
            logical_role_by_track=v3.logical_role_by_track,
            visual_track_count=v3.visual_track_count,
            required_seed_roles=v3.required_seed_roles,
            seed_preserved_roles=v3.seed_preserved_roles,
            full_span_roles=v3.full_span_roles,
            optional_full_span_roles=v3.optional_full_span_roles,
            role_line_budgets=v3.role_line_budgets,
            grid_line_budgets=v3.grid_line_budgets,
            pinned_assets=v3.pinned_assets,
        )

        with patch.dict(
            matrix.TRACK_TEMPLATE_PROFILES,
            {future.name: future},
            clear=False,
        ):
            self.assertIs(matrix.track_template_profile(future.name), future)
            self.assertTrue(matrix.profile_supports_role(future.name, "SOURCE_CREDIT"))
            self.assertEqual(future.clear_track_indices, EXPECTED_CLEAR_TRACK_INDICES)
            self.assertIn(
                future.name,
                matrix.template_profiles_for_layout(matrix.V3_TRACK_LAYOUT),
            )

    def test_unknown_profile_and_layout_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "TEMPLATE_PROFILE_UNKNOWN:missing-profile"):
            matrix.track_template_profile("missing-profile")
        with self.assertRaisesRegex(ValueError, "TRACK_LAYOUT_UNKNOWN:missing-layout"):
            matrix.template_profiles_for_layout("missing-layout")

    def test_noncanonical_physical_track_order_fails_closed(self):
        v3 = matrix.track_template_profile(matrix.V3_TEMPLATE_PROFILE)
        reordered = list(v3.physical_tracks)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        with self.assertRaisesRegex(
            ValueError, "TRACK_TEMPLATE_PROFILE_PHYSICAL_ORDER_UNSUPPORTED"
        ):
            matrix.TrackTemplateProfile(
                name="fixture_reordered",
                track_layout="fixture_reordered_15",
                physical_tracks=tuple(reordered),
                logical_role_by_track=v3.logical_role_by_track,
                visual_track_count=v3.visual_track_count,
                required_seed_roles=v3.required_seed_roles,
                seed_preserved_roles=v3.seed_preserved_roles,
                full_span_roles=v3.full_span_roles,
                optional_full_span_roles=v3.optional_full_span_roles,
                role_line_budgets=v3.role_line_budgets,
                grid_line_budgets=v3.grid_line_budgets,
                pinned_assets=v3.pinned_assets,
            )

    def test_design_lock_uses_selected_profile_text_budget(self):
        v3 = matrix.track_template_profile(matrix.V3_TEMPLATE_PROFILE)
        strict = matrix.TrackTemplateProfile(
            name="fixture_strict_budget",
            track_layout=v3.track_layout,
            physical_tracks=v3.physical_tracks,
            logical_role_by_track=v3.logical_role_by_track,
            visual_track_count=v3.visual_track_count,
            required_seed_roles=v3.required_seed_roles,
            seed_preserved_roles=v3.seed_preserved_roles,
            full_span_roles=v3.full_span_roles,
            optional_full_span_roles=v3.optional_full_span_roles,
            role_line_budgets={
                **v3.role_line_budgets,
                "STATE": matrix.LineBudget(2, 5),
            },
            grid_line_budgets=v3.grid_line_budgets,
            pinned_assets=v3.pinned_assets,
        )
        rows = [
            {"segment_id": "video", "role": "VIDEO", "start": 0, "duration": 100},
            {"segment_id": "screen-effect", "role": "SCREEN_EFFECT", "start": 0, "duration": 100},
            {"segment_id": "screen-white", "role": "SCREEN_WHITE", "start": 0, "duration": 100},
            {"segment_id": "t1", "role": "T1", "start": 0, "duration": 100, "text": "title", "content_type": "TITLE"},
            {"segment_id": "t2", "role": "T2", "start": 0, "duration": 100, "text": "title", "content_type": "TITLE"},
            {
                "segment_id": "state", "role": "STATE", "start": 0,
                "duration": 100, "text": "123456", "content_type": "STATE",
                "caption_role": "STATE", "state_effect": "LASER_CUT",
            },
        ]
        with patch.dict(
            matrix.TRACK_TEMPLATE_PROFILES, {strict.name: strict}, clear=False
        ):
            codes = {
                row["code"]
                for row in validate_design_lock.validate_role_contract(
                    {"segments": rows}, template_profile=strict.name
                )
            }
        self.assertIn("CAPTION_LINE_TOO_LONG", codes)

    def test_grid_validator_uses_selected_profile_text_budget(self):
        v3 = matrix.track_template_profile(matrix.V3_TEMPLATE_PROFILE)
        strict_grid = matrix.TrackTemplateProfile(
            name="fixture_strict_grid_budget",
            track_layout=v3.track_layout,
            physical_tracks=v3.physical_tracks,
            logical_role_by_track=v3.logical_role_by_track,
            visual_track_count=v3.visual_track_count,
            required_seed_roles=v3.required_seed_roles,
            seed_preserved_roles=v3.seed_preserved_roles,
            full_span_roles=v3.full_span_roles,
            optional_full_span_roles=v3.optional_full_span_roles,
            role_line_budgets=v3.role_line_budgets,
            grid_line_budgets={
                **v3.grid_line_budgets,
                ("original", "STATE_LASER"): matrix.LineBudget(2, 1),
                ("urakkai", "STATE_LASER"): matrix.LineBudget(2, 1),
            },
            pinned_assets=v3.pinned_assets,
        )
        fixtures = SKILL_ROOT / "tests" / "fixtures"
        with patch.dict(
            matrix.TRACK_TEMPLATE_PROFILES,
            {strict_grid.name: strict_grid},
            clear=False,
        ):
            result = validate_capcut_grids.validate_grids(
                fixtures / "original_grid_8.pass.md",
                fixtures / "urakkai_grid_8.pass.md",
                template_profile=strict_grid.name,
            )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "TABLE_TEXT_LINE_TOO_LONG",
            {row["code"] for row in result["errors"]},
        )

    def test_track_contract_is_an_identity_preserving_compatibility_facade(self):
        for name in (
            "CANONICAL_TRACKS",
            "HUMAN_GRID_ROWS",
            "TRACK_INDEX",
            "TRACK_LAYOUT_BY_TEMPLATE_PROFILE",
            "LOGICAL_ROLE_BY_LAYOUT",
            "STATE_TRACK_BY_EFFECT",
            "A10_TEXT_TRACK_BY_COLOR",
        ):
            with self.subTest(name=name):
                self.assertIs(getattr(track_contract, name), getattr(matrix, name))

    def test_direct_consumers_share_matrix_owned_contract_views(self):
        self.assertIs(validate_design_lock.FULL_SPAN_ROLES, matrix.FULL_SPAN_ROLES)
        self.assertIs(
            validate_design_lock.OPTIONAL_FULL_SPAN_ROLES,
            matrix.OPTIONAL_FULL_SPAN_ROLES,
        )
        self.assertIs(
            validate_design_lock.MAX_LINE_LENGTH_BY_ROLE,
            matrix.MAX_LINE_LENGTH_BY_ROLE,
        )
        self.assertIs(
            validate_design_lock.MAX_LINE_COUNT_BY_ROLE,
            matrix.MAX_LINE_COUNT_BY_ROLE,
        )
        self.assertIs(validate_capcut_grids.LINE_LIMITS, matrix.LINE_LIMITS)
        self.assertEqual(
            user_provided_media_overlay.BASE_TRACK_COUNT,
            len(matrix.CANONICAL_TRACKS),
        )

    def test_source_credit_is_gated_by_capability_not_v3_name(self):
        self.assertIs(builder.profile_supports_role, matrix.profile_supports_role)
        self.assertIs(
            validate_capcut_project.profile_supports_role,
            matrix.profile_supports_role,
        )
        builder_source = Path(builder.__file__).read_text(encoding="utf-8")
        validator_source = Path(validate_capcut_project.__file__).read_text(encoding="utf-8")
        self.assertNotIn("== V3_TEMPLATE_PROFILE", builder_source)
        self.assertNotIn("!= V3_TEMPLATE_PROFILE", builder_source)
        self.assertNotIn("== V3_TRACK_LAYOUT", validator_source)
        self.assertNotIn("!= V3_TRACK_LAYOUT", validator_source)

    def test_build_contract_schema_defers_profile_allowlist_to_matrix(self):
        schema = json.loads(
            (SKILL_ROOT / "schemas" / "build_contract.schema.json").read_text(
                encoding="utf-8"
            )
        )
        for property_name in ("track_layout_version", "root_template_profile"):
            contract = schema["properties"][property_name]
            self.assertNotIn("enum", contract)
            self.assertEqual(contract["type"], "string")
            self.assertEqual(contract["minLength"], 1)

    def test_provisional_builder_propagates_resolved_template_profile(self):
        source = (
            SCRIPTS / "build_root_provisional_short.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '_extract_template(\n            Path(contract["archive"]), authority, contract["template_profile"]',
            source,
        )
        self.assertIn('"_resolved_root_contract": contract', source)


if __name__ == "__main__":
    unittest.main()
