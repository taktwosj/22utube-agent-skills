import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from capcut_material_paths import enforce_material_paths


class CapcutMaterialPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary.name) / "P0_ROOT"
        self.project_root.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def document(material: dict) -> dict:
        return {"materials": {"videos": [material]}, "outside": {"path": "D:/ignored.mp4"}}

    def enforce(self, document: dict, **overrides) -> dict:
        values = {
            "project_root": self.project_root,
            "rebase_legacy_resources": False,
        }
        values.update(overrides)
        return enforce_material_paths(document, **values)

    def assert_rejected(self, value, code: str, *, key: str = "path") -> None:
        document = self.document({key: value})
        original = copy.deepcopy(document)
        with self.assertRaisesRegex(RuntimeError, code) as raised:
            self.enforce(document)
        self.assertIn(f"$.materials.videos[0].{key}", str(raised.exception))
        self.assertIn(repr(value), str(raised.exception))
        self.assertEqual(document, original)

    def test_walks_only_materials_and_recognized_path_keys(self) -> None:
        document = self.document(
            {
                "path": "Resources/media/main.mp4",
                "nested": {"proxy_path": "Resources/media/proxy.mp4"},
                "filepath": "D:/not-a-recognized-key.mp4",
                "name": "D:/display-only.mp4",
            }
        )

        self.assertEqual(self.enforce(document), document)

    def test_rejects_non_string_nul_drive_relative_and_unsafe_relative_paths(self) -> None:
        cases = (
            (123, "NON_STRING"),
            ("Resources/media/bad\0.mp4", "NUL"),
            (r"C:old\Resources\media\main.mp4", "DRIVE_RELATIVE"),
            ("Resources/../escape.mp4", "TRAVERSAL"),
            ("Resources/./escape.mp4", "TRAVERSAL"),
            ("Resources/D:/escape.mp4", "COLON"),
        )
        for value, code in cases:
            with self.subTest(value=value):
                self.assert_rejected(value, code)

    def test_rejects_foreign_absolute_and_lexical_root_prefix_collision(self) -> None:
        self.assert_rejected("D:/foreign/audio.wav", "FOREIGN")
        collision = self.project_root.with_name(self.project_root.name + "-evil") / "leak.mp4"
        self.assert_rejected(collision.as_posix(), "FOREIGN")

    def test_accepts_contained_absolute_and_safe_relative_paths(self) -> None:
        contained = (self.project_root / "Resources" / "media" / "main.mp4").as_posix()
        for value in (contained, "Resources/media/main.mp4", ""):
            with self.subTest(value=value):
                document = self.document({"path": value})
                self.assertEqual(self.enforce(document), document)

    def test_rebases_only_safe_absolute_legacy_resources_paths(self) -> None:
        legacy = r"C:\old\CapCut\P0_OLD\Resources\media\main.png"
        document = self.document({"path": legacy})

        result = self.enforce(document, rebase_legacy_resources=True)

        self.assertEqual(
            result["materials"]["videos"][0]["path"],
            (self.project_root / "Resources" / "media" / "main.png").as_posix(),
        )
        self.assertEqual(document["materials"]["videos"][0]["path"], legacy)

    def test_rebase_rejects_drive_relative_empty_and_unsafe_resources_suffixes(self) -> None:
        cases = (
            (r"C:old\Resources\media\main.mp4", "DRIVE_RELATIVE"),
            (r"C:\old\Resources", "FOREIGN"),
            (r"C:\old\Resources\..\escape.mp4", "TRAVERSAL"),
            (r"C:\old\Resources\D:\escape.mp4", "COLON"),
        )
        for value, code in cases:
            with self.subTest(value=value):
                document = self.document({"path": value})
                with self.assertRaisesRegex(RuntimeError, code):
                    self.enforce(document, rebase_legacy_resources=True)

    def test_exact_rewrites_apply_only_to_an_exact_path_value(self) -> None:
        cached = "C:/Users/test/AppData/Local/CapCut/User Data/Cache/item.png"
        target = (self.project_root / "Resources" / "media" / "item.png").as_posix()
        document = self.document({"path": cached})

        result = self.enforce(document, exact_rewrites={cached: target})

        self.assertEqual(result["materials"]["videos"][0]["path"], target)
        with self.assertRaisesRegex(RuntimeError, "FOREIGN"):
            self.enforce(self.document({"path": cached + ".suffix"}), exact_rewrites={cached: target})

    def test_recurses_through_physical_material_metadata(self) -> None:
        document = self.document({"metadata": {"nested": {"local_path": "D:/foreign/audio.wav"}}})

        with self.assertRaisesRegex(RuntimeError, "FOREIGN") as raised:
            self.enforce(document)

        self.assertIn("$.materials.videos[0].metadata.nested.local_path", str(raised.exception))

    def test_decodes_single_and_double_encoded_recognized_wrappers(self) -> None:
        for encoded in (
            json.dumps({"nested": {"local_path": "D:/foreign/audio.wav"}}),
            json.dumps(json.dumps({"nested": {"local_path": "D:/foreign/audio.wav"}})),
        ):
            with self.subTest(encoded=encoded):
                document = self.document({"metadata": encoded})
                with self.assertRaisesRegex(RuntimeError, "FOREIGN") as raised:
                    self.enforce(document)
                self.assertIn("metadata", str(raised.exception))
                self.assertIn(repr("D:/foreign/audio.wav"), str(raised.exception))

    def test_rejects_third_encoded_container_and_malformed_recognized_wrapper(self) -> None:
        three_layers = json.dumps(json.dumps(json.dumps({"path": "Resources/media/main.mp4"})))
        for value, code in ((three_layers, "DEPTH_EXCEEDED"), ('{"path":', "JSON_INVALID")):
            with self.subTest(code=code):
                document = self.document({"metadata": value})
                with self.assertRaisesRegex(RuntimeError, code) as raised:
                    self.enforce(document)
                self.assertIn("$.materials.videos[0].metadata", str(raised.exception))
                self.assertIn(repr(value), str(raised.exception))

    def test_does_not_decode_arbitrary_display_strings(self) -> None:
        document = self.document(
            {
                "path": "Resources/media/main.mp4",
                "name": "[Intro]",
                "text": "{literal display text",
                "visible": json.dumps({"local_path": "D:/display-only.wav"}),
            }
        )

        self.assertEqual(self.enforce(document), document)

    def test_decoded_wrapper_ignores_display_text_but_rewrites_path_slots(self) -> None:
        original_wrapper = {
            "text": "{literal display text",
            "name": "[Intro]",
            "asset_path": "Resources/media/main.mp4",
        }
        document = self.document({"content": json.dumps(original_wrapper)})

        result = self.enforce(document)

        self.assertEqual(result, document)

    def test_nested_recognized_wrappers_share_the_two_layer_budget(self) -> None:
        two_layers = json.dumps(
            {"content": json.dumps({"asset_path": "D:/foreign/nested.wav"})}
        )
        document = self.document({"metadata": two_layers})

        with self.assertRaisesRegex(RuntimeError, "FOREIGN"):
            self.enforce(document)

        three_layers = json.dumps(
            {"content": json.dumps({"metadata": json.dumps({"asset_path": "Resources/a"})})}
        )
        with self.assertRaisesRegex(RuntimeError, "DEPTH_EXCEEDED"):
            self.enforce(self.document({"metadata": three_layers}))

    def test_allowed_root_requires_true_normalized_containment(self) -> None:
        allowed = ("C:/__CAPCUT_RELINK_REQUIRED__",)
        accepted = self.document({"path": "C:/__CAPCUT_RELINK_REQUIRED__/C027.mp4"})
        self.assertEqual(self.enforce(accepted, allowed_roots=allowed), accepted)
        for value in (
            "D:/foreign/__CAPCUT_RELINK_REQUIRED__/C027.mp4",
            "C:/__CAPCUT_RELINK_REQUIRED__-evil/C027.mp4",
            "C:/__CAPCUT_RELINK_REQUIRED__/../escape.mp4",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    self.enforce(self.document({"path": value}), allowed_roots=allowed)


if __name__ == "__main__":
    unittest.main()
