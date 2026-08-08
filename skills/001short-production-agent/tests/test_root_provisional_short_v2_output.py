import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_root_builder():
    spec = importlib.util.spec_from_file_location("build_root_provisional_short", SCRIPTS / "build_root_provisional_short.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RootProvisionalShortV2OutputTest(unittest.TestCase):
    def test_main_builds_and_reads_back_v2_root_and_timeline(self):
        builder = load_root_builder()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, sfx, bgm = root / "source.mp4", root / "sfx.wav", root / "bgm.wav"
            for path in (source, sfx, bgm):
                path.write_bytes(b"media")
            assembly = root / "assembly.json"
            assembly.write_text(json.dumps({"timeline": {
                "target_duration_us": 1_000, "audio_policy": "A10_RETAINED_SYNC",
                "clips": [{"clip_id": "video", "source_start_us": 0, "source_duration_us": 1_000, "target_start_us": 0, "target_duration_us": 1_000}],
                "a11_placements": [{"segment_id": "sfx", "source_start_us": 0, "source_duration_us": 100, "target_start_us": 100, "target_duration_us": 100}],
            }}), encoding="utf-8")
            template = root / "template"

            def make_template(destination):
                destination.mkdir(parents=True)
                documents = [destination / "draft_content.json", destination / "Timelines" / "timeline" / "draft_content.json"]
                for document in documents:
                    document.parent.mkdir(parents=True, exist_ok=True)
                    tracks = [{"segments": []} for _ in range(15)]
                    tracks[14]["segments"] = [{"id": "template-a12", "material_id": "m-a12", "target_timerange": {"start": 0, "duration": 1}, "source_timerange": {"start": 0, "duration": 1}}]
                    document.write_text(json.dumps({"tracks": tracks, "materials": {"items": [{"id": "m-a12", "type": "music", "path": "##_draftpath_placeholder_test_##/Resources/media/template.wav"}]}}), encoding="utf-8")
                (destination / "draft_meta_info.json").write_text(json.dumps({"draft_id": "template"}), encoding="utf-8")

            def extract_template(_archive, destination):
                make_template(destination)
                return destination

            def normalize(working, config, _audio, _manifest):
                approved = json.loads(Path(config["approved_timeline_path"]).read_text(encoding="utf-8"))["segments"]
                (working / "Resources" / "media").mkdir(parents=True, exist_ok=True)
                for document, payload in builder.build_episode_capcut._documents(working):
                    tracks = [{"segments": []} for _ in range(15)]
                    materials = [{"id": "m-a12", "type": "music", "path": "##_draftpath_placeholder_test_##/Resources/media/template.wav"}]
                    for row in approved:
                        role = row["role"]
                        index = {"VIDEO": 0, "SCREEN_EFFECT": 1, "SCREEN_WHITE": 2, "T2": 9, "T1": 10, "A11": 13}.get(role)
                        if index is None:
                            continue
                        segment = {"id": row["segment_id"], "role": role, "target_timerange": {"start": row["start"], "duration": row["duration"]}}
                        if role == "VIDEO":
                            segment["volume"] = 0.0
                        if role == "A11":
                            segment["volume"] = 1.0
                        if role in {"T1", "T2"}:
                            material_id = f"m-{role}"
                            segment["material_id"] = material_id
                            materials.append({"id": material_id, "type": "text", "content": json.dumps({"text": config[role], "styles": [{"range": [0, len(config[role])]}]})})
                        tracks[index]["segments"].append(segment)
                    payload["tracks"], payload["materials"] = tracks, {"items": materials}
                    document.write_text(json.dumps(payload), encoding="utf-8")

            evidence, capcut_root, report = root / "evidence", root / "capcut", root / "report.json"
            capcut_root.mkdir()
            argv = ["build_root_provisional_short.py", "--workspace-root", str(root), "--root-contract", str(root / "contract.json"), "--assembly-input", str(assembly), "--source-video", str(source), "--sfx-audio", str(sfx), "--bgm-audio", str(bgm), "--episode-evidence-root", str(evidence), "--episode-id", "EP", "--title1", "title", "--title2", "sub", "--capcut-root", str(capcut_root), "--project-name", "project", "--report", str(report)]
            output = io.StringIO()
            with patch.object(builder, "_capcut_open", return_value=False), \
                 patch.object(builder.resolve_shorts_capcut_root, "resolve_root_contract", return_value={"archive": str(template)}), \
                 patch.object(builder.build_episode_capcut, "_extract_template", side_effect=extract_template), \
                 patch.object(builder.clone_and_sync, "hash_project_core", return_value={}), \
                 patch.object(builder.clone_and_sync, "clone_project", side_effect=lambda source_root, working: (shutil.copytree(source_root, working), {"status": "PASS"})[1]), \
                 patch.object(builder.clone_and_sync, "sync_project_ids", return_value={"status": "PASS", "evidence": {"draft_id": "draft"}}), \
                 patch.object(builder.build_episode_capcut, "_normalize_source", side_effect=normalize), \
                 patch.object(builder.apply_capcut_polish_profile, "apply_project", return_value={"status": "PASS"}), \
                 patch.object(builder.validate_capcut_polish_profile, "validate_project", return_value={"status": "PASS", "errors": []}), \
                 patch.object(builder.build_episode_capcut, "_prepare_cloud_project", return_value={}), \
                 patch.object(builder.build_episode_capcut, "_register_capcut_project", return_value=None), \
                 patch.object(sys, "argv", argv), redirect_stdout(output):
                self.assertEqual(builder.main(), 0, output.getvalue())
            for document in (capcut_root / "project" / "draft_content.json", capcut_root / "project" / "Timelines" / "timeline" / "draft_content.json"):
                tracks = json.loads(document.read_text(encoding="utf-8"))["tracks"]
                self.assertEqual(tracks[0]["segments"][0]["volume"], 0.0)
                self.assertEqual(tracks[11]["segments"], [])
                self.assertEqual(tracks[12]["segments"], [])
                self.assertEqual(tracks[13]["segments"][0]["volume"], 1.0)
                self.assertEqual(tracks[14]["segments"][0]["volume"], 1.0)

    def test_cli_rejects_missing_required_bgm_audio(self):
        builder = load_root_builder()
        with patch.object(sys, "argv", [
            "build_root_provisional_short.py", "--workspace-root", "work", "--root-contract", "contract",
            "--assembly-input", "assembly", "--source-video", "source", "--episode-evidence-root", "evidence",
            "--episode-id", "EP", "--title1", "one", "--title2", "two", "--capcut-root", "capcut",
            "--project-name", "project", "--report", "report",
        ]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                builder.main()
        self.assertEqual(raised.exception.code, 2)

    def test_output_readback_keeps_v2_audio_tracks(self):
        builder = load_root_builder()
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            mirror = project / "Timelines" / "timeline"
            mirror.mkdir(parents=True)
            materials = {
                "items": [
                    {"id": "t2", "type": "text", "content": json.dumps({"text": "sub", "styles": [{"range": [0, 3]}]})},
                    {"id": "t1", "type": "text", "content": json.dumps({"text": "title", "styles": [{"range": [0, 5]}]})},
                ]
            }
            tracks = [{"segments": []} for _ in range(15)]
            tracks[0]["segments"] = [{"id": "video", "role": "VIDEO", "volume": 0.0, "target_timerange": {"start": 0, "duration": 1_000}}]
            for index, material_id in ((1, "screen-effect"), (2, "screen-white"), (9, "t2"), (10, "t1")):
                tracks[index]["segments"] = [{"id": f"fixed-{index}", "material_id": material_id, "target_timerange": {"start": 0, "duration": 1_000}}]
            tracks[13]["segments"] = [
                {"id": "a11-1", "role": "A11", "volume": 1.0, "target_timerange": {"start": 100, "duration": 100}},
                {"id": "a11-2", "role": "A11", "volume": 1.0, "target_timerange": {"start": 500, "duration": 50}},
            ]
            tracks[14]["segments"] = [{"id": "A12_BGM_FULL", "role": "A12", "volume": 1.0, "target_timerange": {"start": 0, "duration": 1_000}, "source_timerange": {"start": 0, "duration": 1_000}}]
            payload = {"tracks": tracks, "materials": materials}
            for path in (project / "draft_content.json", mirror / "draft_content.json"):
                path.write_text(json.dumps(payload), encoding="utf-8")
            kwargs = {
                "audio_policy": "A10_RETAINED_SYNC", "tts_cues": [],
                "a11_placements": [{"target_range_us": [100, 200]}, {"target_range_us": [500, 550]}],
                "has_a12_bgm": True,
            }
            payload["tracks"][13]["segments"][0]["volume"] = 0.0
            for path in (project / "draft_content.json", mirror / "draft_content.json"):
                path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ROOT_A11_NOT_NORMAL_VOLUME"):
                builder._validate_root_timeline(project, 1_000, 1, "title", "sub", **kwargs)
            payload["tracks"][13]["segments"][0]["volume"] = 1.0
            payload["tracks"][14]["segments"][0]["volume"] = 0.0
            for path in (project / "draft_content.json", mirror / "draft_content.json"):
                path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ROOT_A12_NOT_NORMAL_VOLUME"):
                builder._validate_root_timeline(project, 1_000, 1, "title", "sub", **kwargs)
            payload["tracks"][14]["segments"][0]["volume"] = 1.0
            for path in (project / "draft_content.json", mirror / "draft_content.json"):
                path.write_text(json.dumps(payload), encoding="utf-8")
            result = builder._validate_root_timeline(
                project, 1_000, 1, "title", "sub", **kwargs,
            )
            self.assertEqual(result["a10_segments"], 0)
            self.assertEqual(result["a11_segments"], 2)
            self.assertEqual(result["a12_segments"], 1)


if __name__ == "__main__":
    unittest.main()
