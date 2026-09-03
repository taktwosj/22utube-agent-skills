from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import assembly_type_matrix as assembly
import audio_policy_matrix as audio
import build_episode_capcut as builder
import build_episode_locks as generator
import production_profile
import track_template_matrix as templates
import validate_executable_protocol
from schema_runtime import validate_schema


EXPECTED_TYPES = {
    "1": {
        "execution_strategy": "caption_only",
        "required_roles": {"STATE"},
        "optional_roles": set(),
        "cleared_roles": ("A9", "A9_TEXT", "A10", "A10_TEXT"),
        "allowed_mode_policies": {
            ("URAKKAI", "CAPTION_ONLY_MUTE_SOURCE"),
        },
        "placement_rules": set(),
    },
    "2": {
        "execution_strategy": "full_tts",
        "required_roles": {"A9", "A9_TEXT"},
        "optional_roles": {"STATE"},
        "cleared_roles": ("A10", "A10_TEXT", "STATE_LASER"),
        "allowed_mode_policies": {
            ("URAKKAI", "TTS_ONLY_MUTE_SOURCE"),
        },
        "placement_rules": set(),
    },
    "3": {
        "execution_strategy": "original_audio_caption",
        "required_roles": {"A10", "A10_TEXT"},
        "optional_roles": {"STATE"},
        "cleared_roles": ("A9", "A9_TEXT"),
        "allowed_mode_policies": {
            ("SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_ORDER_CLEAN_AUDIO"),
            ("SOURCE_ORDER_UNCHANGED_A10_RETAINED", "A10_RETAINED_SYNC"),
            ("URAKKAI", "A10_REASSEMBLED_SYNC"),
            ("URAKKAI", "SOURCE_ORDER_CLEAN_AUDIO"),
        },
        "placement_rules": set(),
    },
    "4": {
        "execution_strategy": "tts_intro_original_body",
        "required_roles": {"A9", "A9_TEXT", "A10", "A10_TEXT"},
        "optional_roles": {"STATE"},
        "cleared_roles": (),
        "allowed_mode_policies": {
            ("URAKKAI", "A9_TTS_PLUS_A10_REASSEMBLED"),
            ("URAKKAI", "A9_TTS_PLUS_A10_SOURCE_CLIP"),
        },
        "placement_rules": {
            "A9_FIRST_VIDEO_ONLY",
            "A10_TEXT_AFTER_FIRST_VIDEO",
        },
    },
    "5": {
        "execution_strategy": "narration_plus_speaker",
        "required_roles": {"A9", "A9_TEXT", "A10", "A10_TEXT"},
        "optional_roles": {"STATE"},
        "cleared_roles": (),
        "allowed_mode_policies": {
            ("URAKKAI", "A9_TTS_PLUS_A10_REASSEMBLED"),
            ("URAKKAI", "A9_TTS_PLUS_A10_SOURCE_CLIP"),
        },
        "placement_rules": {"A9_AFTER_FIRST_VIDEO_REQUIRED"},
    },
}

SELECTOR_FIELDS = {
    "schema_version",
    "profile_id",
    "assembly_type",
    "template_profile",
    "production_mode",
    "audio_policy",
}
SELECTOR_ORDER = (
    "schema_version",
    "profile_id",
    "assembly_type",
    "template_profile",
    "production_mode",
    "audio_policy",
)

ALWAYS_CLEARED = ("A11", "A12", "A12_RESERVED_EMPTY", "STATE_GLITCH")


def _selector(**overrides: str) -> dict[str, str]:
    payload = {
        "schema_version": "001short-production-profile-v1",
        "profile_id": "fixture-caption-only",
        "assembly_type": "1",
        "template_profile": templates.V3_TEMPLATE_PROFILE,
        "production_mode": "URAKKAI",
        "audio_policy": "CAPTION_ONLY_MUTE_SOURCE",
    }
    payload.update(overrides)
    return payload


class AssemblyTypeMatrixContractTest(unittest.TestCase):
    def test_current_five_types_match_the_approved_layer_and_audio_contract(self):
        self.assertEqual(set(assembly.ASSEMBLY_TYPE_DEFINITIONS), set(EXPECTED_TYPES))

        canonical_mode_policies = {
            (mode, policy) for mode, policy, _source in audio.CANONICAL_MODE_MATRIX
        }
        for type_id, expected in EXPECTED_TYPES.items():
            with self.subTest(type_id=type_id):
                definition = assembly.assembly_type_definition(type_id)
                self.assertIs(
                    definition,
                    assembly.ASSEMBLY_TYPE_DEFINITIONS[type_id],
                )
                self.assertEqual(definition.type_id, type_id)
                self.assertEqual(
                    definition.execution_strategy,
                    expected["execution_strategy"],
                )
                self.assertEqual(set(definition.required_roles), expected["required_roles"])
                self.assertEqual(set(definition.optional_roles), expected["optional_roles"])
                self.assertEqual(definition.cleared_roles, expected["cleared_roles"])
                self.assertEqual(
                    set(definition.allowed_mode_policies),
                    expected["allowed_mode_policies"],
                )
                self.assertEqual(
                    set(definition.placement_rules),
                    expected["placement_rules"],
                )
                self.assertLessEqual(
                    set(definition.allowed_mode_policies),
                    canonical_mode_policies,
                )

    def test_type_roles_are_disjoint_and_unknown_type_fails_closed(self):
        for definition in assembly.ASSEMBLY_TYPE_DEFINITIONS.values():
            with self.subTest(type_id=definition.type_id):
                required = set(definition.required_roles)
                optional = set(definition.optional_roles)
                cleared = set(definition.cleared_roles)
                self.assertTrue(required.isdisjoint(optional))
                self.assertTrue(required.isdisjoint(cleared))
                self.assertTrue(optional.isdisjoint(cleared))

        with self.assertRaisesRegex(ValueError, "ASSEMBLY_TYPE_UNKNOWN:missing"):
            assembly.assembly_type_definition("missing")

    def test_future_type_rejects_physical_aliases_that_are_not_placement_anchors(self):
        for role in ("A10_TEXT_WHITE", "STATE_LASER"):
            with self.subTest(role=role):
                with self.assertRaisesRegex(
                    ValueError, "ASSEMBLY_TYPE_PLACEMENT_ROLE_UNKNOWN"
                ):
                    assembly.AssemblyTypeDefinition(
                        type_id="future",
                        execution_strategy="future",
                        required_roles=frozenset({role}),
                        optional_roles=frozenset(),
                        cleared_roles=(),
                        allowed_mode_policies=frozenset({
                            ("URAKKAI", "CAPTION_ONLY_MUTE_SOURCE"),
                        }),
                    )

    def test_lock_generator_consumes_the_matrix_instead_of_copying_type_branches(self):
        self.assertIs(
            generator.assembly_type_definition,
            assembly.assembly_type_definition,
        )
        source = Path(generator.__file__).read_text(encoding="utf-8")
        self.assertNotIn("CLEARED_BY_TYPE = {", source)

    def test_v_plan_type_strategy_and_audio_route_are_checked_together(self):
        plan = {
            "type": "1",
            "execution_strategy": "caption_only",
            "audio_policy": "CAPTION_ONLY_MUTE_SOURCE",
        }
        self.assertIs(
            generator.resolve_v_plan_type(plan),
            assembly.ASSEMBLY_TYPE_DEFINITIONS["1"],
        )
        with self.assertRaisesRegex(ValueError, "V_PLAN_EXECUTION_STRATEGY_MISMATCH"):
            generator.resolve_v_plan_type({**plan, "execution_strategy": "full_tts"})
        with self.assertRaisesRegex(ValueError, "V_PLAN_ASSEMBLY_AUDIO_ROUTE_MISMATCH"):
            generator.resolve_v_plan_type({**plan, "audio_policy": "TTS_ONLY_MUTE_SOURCE"})

    def test_legacy_type_two_tts_only_alias_is_reassembly_only(self):
        legacy = {
            "type": "2",
            "execution_strategy": "tts_only",
            "audio_policy": "TTS_ONLY_MUTE_SOURCE",
        }
        self.assertIs(
            generator.resolve_v_plan_type(legacy),
            assembly.ASSEMBLY_TYPE_DEFINITIONS["2"],
        )
        resolved = production_profile.resolve_production_profile(_selector(
            assembly_type="2",
            audio_policy="TTS_ONLY_MUTE_SOURCE",
        ))
        with self.assertRaisesRegex(ValueError, "V_PLAN_PRODUCTION_PROFILE_MISMATCH"):
            generator.resolve_v_plan_type(legacy, resolved)

    def test_generator_derives_audio_source_without_a_type_two_branch(self):
        self.assertIs(
            generator.audio_source_for_route,
            production_profile.audio_source_for_route,
        )
        self.assertEqual(
            generator.audio_source_for_route("URAKKAI", "TTS_ONLY_MUTE_SOURCE"),
            "GENERATED_TTS",
        )
        source = Path(generator.__file__).read_text(encoding="utf-8")
        self.assertNotIn('plan["type"] == "2"', source)


class ProductionProfileContractTest(unittest.TestCase):
    def test_selector_has_exactly_six_authored_fields_and_derives_the_rest(self):
        payload = _selector()
        resolved = production_profile.resolve_production_profile(payload)

        self.assertEqual(set(resolved.selector), SELECTOR_FIELDS)
        self.assertEqual(production_profile.SELECTOR_FIELDS, SELECTOR_ORDER)
        self.assertEqual(tuple(resolved.selector), SELECTOR_ORDER)
        self.assertEqual(resolved.selector, payload)
        self.assertEqual(resolved.execution_strategy, "caption_only")
        self.assertEqual(resolved.audio_source, "SILENCE")
        self.assertEqual(resolved.track_layout, templates.V3_TRACK_LAYOUT)
        self.assertEqual(set(resolved.required_roles), {"STATE"})
        self.assertEqual(set(resolved.optional_roles), set())
        self.assertEqual(
            resolved.cleared_roles,
            ALWAYS_CLEARED + ("A9", "A9_TEXT", "A10", "A10_TEXT"),
        )

    def test_audio_source_is_derived_from_the_existing_audio_matrix(self):
        payload = _selector(
            profile_id="fixture-type-three",
            assembly_type="3",
            production_mode="SOURCE_ORDER_UNCHANGED_A10_RETAINED",
            audio_policy="A10_RETAINED_SYNC",
        )
        resolved = production_profile.resolve_production_profile(payload)

        self.assertEqual(resolved.execution_strategy, "original_audio_caption")
        self.assertEqual(resolved.audio_source, "SOURCE_VOCAL_STEM")
        self.assertEqual(set(resolved.required_roles), {"A10", "A10_TEXT"})
        self.assertEqual(set(resolved.optional_roles), {"STATE"})

    def test_future_type_resolves_by_registry_data_without_a_new_code_branch(self):
        future = assembly.AssemblyTypeDefinition(
            type_id="6",
            execution_strategy="future_tts_fixture",
            required_roles=frozenset({"A9", "A9_TEXT"}),
            optional_roles=frozenset({"STATE"}),
            cleared_roles=("A10", "A10_TEXT"),
            allowed_mode_policies=frozenset({
                ("URAKKAI", "TTS_ONLY_MUTE_SOURCE"),
            }),
        )
        with patch.dict(
            assembly.ASSEMBLY_TYPE_DEFINITIONS,
            {future.type_id: future},
            clear=False,
        ):
            resolved = production_profile.resolve_production_profile(
                _selector(
                    profile_id="fixture-future-type",
                    assembly_type="6",
                    audio_policy="TTS_ONLY_MUTE_SOURCE",
                )
            )

        self.assertEqual(resolved.execution_strategy, "future_tts_fixture")
        self.assertEqual(resolved.audio_source, "GENERATED_TTS")
        self.assertEqual(set(resolved.required_roles), {"A9", "A9_TEXT"})
        self.assertEqual(set(resolved.optional_roles), {"STATE"})
        self.assertEqual(
            resolved.cleared_roles,
            ALWAYS_CLEARED + ("A10", "A10_TEXT"),
        )

    def test_unknown_type_policy_mismatch_and_extra_fields_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "ASSEMBLY_TYPE_UNKNOWN:missing"):
            production_profile.resolve_production_profile(
                _selector(assembly_type="missing")
            )

        with self.assertRaisesRegex(
            ValueError,
            "PRODUCTION_PROFILE_AUDIO_ROUTE_INCOMPATIBLE",
        ):
            production_profile.resolve_production_profile(
                _selector(audio_policy="TTS_ONLY_MUTE_SOURCE")
            )

        with self.assertRaisesRegex(ValueError, "PRODUCTION_PROFILE_FIELDS_INVALID"):
            production_profile.resolve_production_profile(
                {**_selector(), "execution_strategy": "caption_only"}
            )

    def test_missing_field_and_unknown_schema_fail_closed(self):
        missing = _selector()
        missing.pop("template_profile")
        with self.assertRaisesRegex(ValueError, "PRODUCTION_PROFILE_FIELDS_INVALID"):
            production_profile.resolve_production_profile(missing)

        with self.assertRaisesRegex(ValueError, "PRODUCTION_PROFILE_SCHEMA_UNSUPPORTED"):
            production_profile.resolve_production_profile(
                _selector(schema_version="001short-production-profile-v999")
            )

    def test_profile_json_schema_keeps_only_selector_fields(self):
        schema = json.loads(
            (SKILL_ROOT / "schemas" / "production_profile.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(schema["required"]), SELECTOR_FIELDS)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(validate_schema(_selector(), schema), [])
        self.assertTrue(
            validate_schema({**_selector(), "audio_source": "SILENCE"}, schema)
        )
        plan_schema = json.loads(
            (SKILL_ROOT / "schemas" / "executable_production_plan.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            plan_schema["properties"]["production_profile"],
            {"type": "object"},
        )

    def test_validator_and_generator_consume_the_same_profile_resolver(self):
        self.assertIs(
            validate_executable_protocol.resolve_production_profile,
            production_profile.resolve_production_profile,
        )
        self.assertIs(
            generator.resolve_production_profile,
            production_profile.resolve_production_profile,
        )
        self.assertIs(
            builder.resolve_production_profile,
            production_profile.resolve_production_profile,
        )

    def test_profile_selector_must_match_the_v_plan(self):
        resolved = production_profile.resolve_production_profile(_selector())
        valid = {
            "type": "1",
            "execution_strategy": "caption_only",
            "audio_policy": "CAPTION_ONLY_MUTE_SOURCE",
        }
        self.assertIs(generator.resolve_v_plan_type(valid, resolved), assembly.ASSEMBLY_TYPE_DEFINITIONS["1"])
        with self.assertRaisesRegex(ValueError, "V_PLAN_PRODUCTION_PROFILE_MISMATCH"):
            generator.resolve_v_plan_type({**valid, "type": "2"}, resolved)

    def test_builder_rejects_root_template_that_differs_from_profile(self):
        config = {
            "workspace_root": "C:/workspace",
            "root_profile": "fixture",
            "root_contract_path": "root.json",
            "production_profile": _selector(
                template_profile=templates.V2_TEMPLATE_PROFILE
            ),
        }
        resolved_root = {
            "archive": "C:/workspace/root.zip",
            "archive_sha256": "a" * 64,
            "profile": "fixture",
            "template_profile": templates.V3_TEMPLATE_PROFILE,
        }
        with patch.object(
            builder.resolve_shorts_capcut_root,
            "resolve_root_contract",
            return_value=resolved_root,
        ):
            with self.assertRaisesRegex(
                ValueError, "ROOT_CONTRACT_PRODUCTION_PROFILE_MISMATCH"
            ):
                builder._bind_portable_root_contract(config)

    def test_required_logical_role_must_be_supported_by_selected_template(self):
        future = assembly.AssemblyTypeDefinition(
            type_id="future-source-credit",
            execution_strategy="source_credit_required",
            required_roles=frozenset({"SOURCE_CREDIT"}),
            optional_roles=frozenset(),
            cleared_roles=(),
            allowed_mode_policies=frozenset({
                ("URAKKAI", "CAPTION_ONLY_MUTE_SOURCE"),
            }),
        )
        with patch.dict(
            assembly.ASSEMBLY_TYPE_DEFINITIONS,
            {future.type_id: future},
        ):
            with self.assertRaisesRegex(
                ValueError, "PRODUCTION_PROFILE_TEMPLATE_ROLE_UNSUPPORTED"
            ):
                production_profile.resolve_production_profile(
                    _selector(
                        assembly_type=future.type_id,
                        template_profile=templates.V2_TEMPLATE_PROFILE,
                    )
                )
            resolved = production_profile.resolve_production_profile(
                _selector(
                    assembly_type=future.type_id,
                    template_profile=templates.V3_TEMPLATE_PROFILE,
                )
            )
            self.assertEqual(resolved.required_roles, frozenset({"SOURCE_CREDIT"}))


if __name__ == "__main__":
    unittest.main()
