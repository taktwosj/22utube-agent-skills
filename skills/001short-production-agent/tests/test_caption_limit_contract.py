import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_design_lock
from validate_capcut_grids import LINE_LIMITS

from schema_runtime import validate_schema

PROTOCOL_PATH = SKILL_ROOT / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
GRID_HARNESS = PROTOCOL["grid_harness"]
ORIGINAL_TEMPLATE = SKILL_ROOT / "templates" / "original-capcut-grid.md"
URAKKAI_TEMPLATE = SKILL_ROOT / "templates" / "urakkai-capcut-grid.md"


class CaptionLimitContractTest(unittest.TestCase):
    """protocol.json, the grid harness and the design lock each keep their own copy
    of the caption budgets.  A9_TEXT was once 10 in protocol.json while both
    validators still enforced 15, so the operator's decision never reached the
    build.  These assertions fail the moment one copy moves without the others."""

    def test_grid_harness_matches_protocol(self):
        self.assertEqual(
            LINE_LIMITS[("urakkai", "A9_TEXT")],
            (
                GRID_HARNESS["target_a9_text_max_lines"],
                GRID_HARNESS["target_a9_text_max_chars_per_line"],
            ),
        )
        self.assertEqual(
            LINE_LIMITS[("original", "A9_TEXT")],
            (
                GRID_HARNESS["original_a9_text_max_lines"],
                GRID_HARNESS["original_a9_text_max_chars_per_line"],
            ),
        )
        for table in ("original", "urakkai"):
            self.assertEqual(
                LINE_LIMITS[(table, "STATE_LASER")],
                (
                    GRID_HARNESS["state_laser_max_lines"],
                    GRID_HARNESS["state_laser_max_chars_per_line"],
                ),
            )

    def test_design_lock_matches_protocol(self):
        # The design lock inspects the assembled project, which carries the
        # urakkai A9_TEXT, so it follows the target budget rather than the
        # original one.
        self.assertEqual(
            validate_design_lock.MAX_LINE_LENGTH_BY_ROLE["A9_TEXT"],
            GRID_HARNESS["target_a9_text_max_chars_per_line"],
        )
        self.assertEqual(
            validate_design_lock.MAX_LINE_COUNT_BY_ROLE["A9_TEXT"],
            GRID_HARNESS["target_a9_text_max_lines"],
        )
        self.assertEqual(
            validate_design_lock.MAX_LINE_LENGTH_BY_ROLE["STATE"],
            GRID_HARNESS["state_laser_max_chars_per_line"],
        )
        self.assertEqual(
            validate_design_lock.MAX_LINE_COUNT_BY_ROLE["STATE"],
            GRID_HARNESS["state_laser_max_lines"],
        )

    def test_templates_quote_the_enforced_numbers(self):
        target = GRID_HARNESS["target_a9_text_max_chars_per_line"]
        original = GRID_HARNESS["original_a9_text_max_chars_per_line"]
        urakkai_text = URAKKAI_TEMPLATE.read_text(encoding="utf-8")
        original_text = ORIGINAL_TEMPLATE.read_text(encoding="utf-8")
        self.assertRegex(urakkai_text, rf"`A9_TEXT`는 \*\*한 줄 {target}자 이하")
        self.assertRegex(original_text, rf"`A9_TEXT`와 `STATE_LASER`는 한 줄 {original}자 이하")

    def _a9_text_codes(self, length: int) -> set[str]:
        rows = validate_design_lock.validate_role_contract(
            {
                "segments": [
                    {
                        "segment_id": "S",
                        "role": "A9_TEXT",
                        "start": 0,
                        "duration": 10,
                        "text": "가" * length,
                        "content_type": "A9_TEXT",
                        "caption_role": "A9_TEXT",
                    }
                ]
            },
            10,
        )
        return {row["code"] for row in rows}

    def test_a9_text_budget_is_enforced_at_the_protocol_number(self):
        limit = GRID_HARNESS["target_a9_text_max_chars_per_line"]
        self.assertNotIn("CAPTION_LINE_TOO_LONG", self._a9_text_codes(limit))
        self.assertIn("CAPTION_LINE_TOO_LONG", self._a9_text_codes(limit + 1))



class ProtocolSchemaContractTest(unittest.TestCase):
    """Nothing validated protocol.json against schemas/executable_protocol.schema.json,
    so the schema quietly fell three changes behind: it never learned the
    source_intake_receipt and vocal_stem_manifest pointers, it still required the
    old cloud_row_required_fields name, and its URAKKAI policy enum was missing
    SOURCE_ORDER_CLEAN_AUDIO - a policy protocol.json has been allowing all along."""

    def _schema(self) -> dict:
        return json.loads(
            (SKILL_ROOT / "schemas" / "executable_protocol.schema.json").read_text(encoding="utf-8")
        )

    def test_protocol_validates_against_its_own_schema(self):
        self.assertEqual(validate_schema(PROTOCOL, self._schema()), [])

    def test_the_schema_still_refuses_what_it_is_meant_to_refuse(self):
        """A schema that passes because it stopped constraining anything is worse
        than no schema, so check it rejects as well as accepts."""
        import copy

        unknown_policy = copy.deepcopy(PROTOCOL)
        unknown_policy["production_modes"]["URAKKAI"]["allowed_audio_policies"].append(
            "NOT_A_REAL_POLICY"
        )
        self.assertTrue(validate_schema(unknown_policy, self._schema()))

        stray_pointer = copy.deepcopy(PROTOCOL)
        stray_pointer["schemas"]["not_a_real_schema"] = "schemas/nope.schema.json"
        self.assertTrue(validate_schema(stray_pointer, self._schema()))

        missing_field = copy.deepcopy(PROTOCOL)
        del missing_field["completion_report"]["cloud_sync_row_required_fields"]
        self.assertTrue(validate_schema(missing_field, self._schema()))


class LegacyV1PolicyRewriteTest(unittest.TestCase):
    """A v1 plan may name a RETAINED policy under URAKKAI, which no current URAKKAI
    combination allows, so validate_executable_protocol rewrites it before
    validating.  That mapping used to be a bare dict inside the validator while
    the matrix declared its own partial copy of the same idea."""

    def _matrix(self):
        import audio_policy_matrix
        return audio_policy_matrix

    def _validator(self):
        import validate_executable_protocol
        return validate_executable_protocol

    def test_the_validator_uses_the_shared_map(self):
        self.assertIs(
            self._validator().LEGACY_V1_URAKKAI_POLICY_REWRITES,
            self._matrix().LEGACY_V1_URAKKAI_POLICY_REWRITES,
        )

    def test_every_rewrite_maps_a_v1_name_onto_a_current_urakkai_policy(self):
        rewrites = self._matrix().LEGACY_V1_URAKKAI_POLICY_REWRITES
        self.assertTrue(rewrites)
        v1_schema = json.loads(
            (SKILL_ROOT / "schemas" / "executable_production_plan_v1.schema.json")
            .read_text(encoding="utf-8")
        )
        v1_policies = v1_schema["properties"]["audio_policy"]["enum"]
        allowed_urakkai = PROTOCOL["production_modes"]["URAKKAI"]["allowed_audio_policies"]
        for old_name, current in rewrites.items():
            # Rewriting anything a v1 plan cannot carry would be dead code.
            self.assertIn(old_name, v1_policies)
            # And rewriting onto a name URAKKAI still refuses would fix nothing.
            self.assertNotIn(old_name, allowed_urakkai)
            self.assertIn(current, allowed_urakkai)

    def test_a_v1_urakkai_plan_is_not_rejected_for_its_legacy_policy(self):
        """The rewrite has to actually run: without it the plan below fails
        URAKKAI_AUDIO_POLICY_INVALID before any real check is reached."""
        validator = self._validator()
        for old_name in self._matrix().LEGACY_V1_URAKKAI_POLICY_REWRITES:
            plan = {
                "schema_version": "001short-production-plan-v1",
                "episode_id": "EP", "root_profile": "test", "project_name": "EP",
                "production_mode": "URAKKAI", "total_duration_us": 2_000_000,
                "audio_policy": old_name,
                "order_signature": ["B02", "B01"],
                "original_order": ["B01", "B02"],
                "timeline": [
                    {"segment_key": "B02", "target_range_us": [0, 1_000_000], "placements": []},
                    {"segment_key": "B01", "target_range_us": [1_000_000, 2_000_000], "placements": []},
                ],
            }
            errors = validator.validate_production_plan(plan, validator.load_protocol())
            self.assertNotIn("URAKKAI_AUDIO_POLICY_INVALID", errors, old_name)


class DerivedPolicySetTest(unittest.TestCase):
    """The protocol validator kept its own hand-listed copy of the URAKKAI policies
    that retain A10.  Missing a new policy there drops the VIDEO-to-A10 count and
    range checks without any failure to notice."""

    def test_the_urakkai_a10_set_is_derived_not_listed(self):
        import audio_policy_matrix
        import validate_executable_protocol
        self.assertEqual(
            set(validate_executable_protocol.A10_AUDIO_POLICIES),
            set(audio_policy_matrix.URAKKAI_AUDIO_POLICIES) & audio_policy_matrix.A10_POLICIES,
        )
        # Every URAKKAI policy that keeps A10 has to be in it, or its episodes skip
        # the mapping gate entirely.
        for mode, policy, _source in audio_policy_matrix.CANONICAL_MODE_MATRIX:
            if mode == "URAKKAI" and policy in audio_policy_matrix.A10_POLICIES:
                self.assertIn(policy, validate_executable_protocol.A10_AUDIO_POLICIES)


if __name__ == "__main__":
    unittest.main()
