from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_capcut_project import validate_audio_material_registration
import build_episode_capcut as builder


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


class AudioMaterialRegistrationTest(unittest.TestCase):
    def _registered_bundle(self, project: Path) -> None:
        media = project / "Resources" / "media"
        media.mkdir(parents=True)
        audios = []
        for index, (name, role, seconds) in enumerate((
            ("a10_vocal_stem.wav", "A10", 0.40),
            ("user_overlay_15.wav", "USER_PROVIDED_AUDIO", 0.15),
            ("user_overlay_16.wav", "USER_PROVIDED_AUDIO", 0.20),
            ("user_overlay_17.wav", "USER_PROVIDED_AUDIO", 0.25),
        )):
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", f"sine=frequency={440 + index}:duration={seconds}",
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(media / name),
            ], check=True)
            audios.append({
                "id": f"audio-{index}", "role": role, "type": "music", "name": name,
                "path": f"##_draftpath_placeholder_fixture_##/Resources/media/{name}",
                "duration": 716_666, "local_material_id": "", "music_id": "seed-cloud-id",
            })
        _write(project / "draft_content.json", {
            "materials": {"audios": audios}, "tracks": [{"segments": [
                {"id": f"segment-{index}", "material_id": row["id"]}
                for index, row in enumerate(audios)
            ]}],
        })
        _write(project / "draft_meta_info.json", {"draft_materials": []})
        builder.register_project_local_audio_materials(project)

    def test_cloud_prepare_scopes_local_audio_ids_while_music_id_tracks_material_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "template"
            media = template / "Resources" / "media"
            media.mkdir(parents=True)
            audio = media / "a10_vocal_stem.wav"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2",
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(audio),
            ], check=True)
            material = {
                "id": "a10-material", "role": "A10", "type": "music",
                "name": audio.name,
                "path": "##_draftpath_placeholder_fixture_##/Resources/media/a10_vocal_stem.wav",
                "duration": 200_000, "local_material_id": "", "music_id": "",
            }
            _write(template / "draft_content.json", {
                "materials": {"audios": [material]},
                "tracks": [{"segments": [{"material_id": material["id"]}]}],
            })
            _write(template / "draft_meta_info.json", {
                "draft_id": "shared-template-draft-id", "draft_materials": [],
            })

            observed = []
            for revision, draft_id in (("revision-a", "draft-a"), ("revision-b", "draft-b")):
                project = root / revision
                shutil.copytree(template, project)
                builder._prepare_cloud_project(
                    project, project_name=revision, capcut_root=root,
                    draft_id=draft_id, duration_us=200_000,
                )
                payload = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
                row = payload["materials"]["audios"][0]
                observed.append({
                    "id": row["id"],
                    "local_material_id": row["local_material_id"],
                    "music_id": row["music_id"],
                })

            self.assertNotEqual(observed[0]["local_material_id"], observed[1]["local_material_id"])
            self.assertTrue(all(row["music_id"] == row["id"] for row in observed))

    def test_builder_registers_each_local_audio_as_one_unique_unit(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            media = project / "Resources" / "media"
            media.mkdir(parents=True)
            audios = []
            for index, (name, role, seconds) in enumerate((
                ("a10_vocal_stem.wav", "A10", 0.40),
                ("user_overlay_15.wav", "USER_PROVIDED_AUDIO", 0.15),
                ("user_overlay_16.wav", "USER_PROVIDED_AUDIO", 0.20),
                ("user_overlay_17.wav", "USER_PROVIDED_AUDIO", 0.25),
            )):
                subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"sine=frequency={440 + index}:duration={seconds}",
                    "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(media / name),
                ], check=True)
                audios.append({
                    "id": f"audio-{index}", "role": role, "type": "music", "name": name,
                    "path": f"##_draftpath_placeholder_fixture_##/Resources/media/{name}",
                    "duration": 716_666, "local_material_id": "", "music_id": "seed-cloud-id",
                    "resource_id": "seed-resource-id", "remote_url": "https://seed.invalid/audio",
                })
            _write(project / "draft_content.json", {
                "materials": {"audios": audios}, "tracks": [{"segments": [
                    {"material_id": row["id"]} for row in audios
                ]}],
            })
            _write(project / "draft_meta_info.json", {
                "draft_materials": [{"type": 0, "value": [{
                    "id": "audio-0", "file_Path": "stale/path.wav",
                }]}, {"type": 18, "value": [{
                    "id": "unrelated-template-combination", "extra_info": "template preset",
                }]}],
            })

            builder.register_project_local_audio_materials(project)

            content = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            meta = json.loads((project / "draft_meta_info.json").read_text(encoding="utf-8"))
            registered = content["materials"]["audios"]
            material_ids = [row["id"] for row in registered]
            music_ids = [row["music_id"] for row in registered]
            local_ids = [row["local_material_id"] for row in registered]
            self.assertEqual(len(material_ids), len(set(material_ids)))
            self.assertEqual(music_ids, material_ids)
            self.assertEqual(len(music_ids), len(set(music_ids)))
            self.assertEqual(len(local_ids), len(set(local_ids)))
            self.assertNotIn("", local_ids)
            self.assertTrue(all(
                material["local_material_id"] != material["id"]
                for material in registered
            ))
            self.assertEqual(len({row["path"] for row in registered}), 4)
            self.assertTrue(all(row["resource_id"] == "" for row in registered))
            self.assertTrue(all(row["remote_url"] is None for row in registered))
            meta_rows = next(row["value"] for row in meta["draft_materials"] if row["type"] == 0)
            self.assertEqual({row["id"] for row in meta_rows}, set(material_ids))
            self.assertEqual(len(meta_rows), 4)
            for material in registered:
                row = next(row for row in meta_rows if row["id"] == material["id"])
                measured_duration = builder._measured_audio_duration_us(media / material["name"])
                self.assertEqual(row["file_Path"], (media / material["name"]).resolve().as_posix())
                self.assertNotIn("\\", row["file_Path"])
                self.assertEqual(row["metetype"], "music")
                self.assertEqual(row["item_source"], 1)
                self.assertEqual(row["type"], 0)
                self.assertEqual(material["duration"], measured_duration)
                self.assertEqual(row["duration"], measured_duration)
                self.assertEqual(row["roughcut_time_range"], {
                    "start": 0, "duration": measured_duration,
                })
            self.assertEqual(validate_audio_material_registration(project), [])

    def test_cloud_prepare_preserves_existing_subdrafts(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "subdraft" / "template-combination").mkdir(parents=True)
            marker = project / "subdraft" / "template-combination" / "sub_draft_config.json"
            marker.write_text("{}", encoding="utf-8")
            _write(project / "draft_content.json", {"materials": {"audios": []}, "tracks": []})
            _write(project / "draft_meta_info.json", {"draft_materials": []})

            builder._prepare_cloud_project(
                project, project_name="fixture", capcut_root=project.parent,
                draft_id="fixture-id", duration_us=1_000_000,
            )

            self.assertTrue(marker.is_file())

    def test_rejects_the_observed_postopen_audio_rewrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            combination = project / "Resources" / "combination"
            combination.mkdir(parents=True)
            shared = combination / "collapsed_audio.aac"
            shared.write_bytes(b"not-decodable-aac")
            a10 = combination / "a10_audio.aac"
            a10.write_bytes(b"not-decodable-aac")
            audios = [
                {
                    "id": "a10", "role": "A10", "type": "music",
                    "name": "a10_vocal_stem.wav", "duration": 34_273_000,
                    "path": "Resources/combination/a10_audio.aac",
                    "local_material_id": "",
                },
                *[
                    {
                        "id": f"overlay-{index}", "role": "USER_PROVIDED_AUDIO",
                        "type": "music", "name": f"user_overlay_{index}.wav",
                        "duration": 1_600_000,
                        "path": "Resources/combination/collapsed_audio.aac",
                        "local_material_id": "",
                    }
                    for index in (15, 16, 17)
                ],
            ]
            _write(project / "draft_content.json", {
                "materials": {"audios": audios},
                "tracks": [{"segments": [
                    {
                        "id": audio["id"], "material_id": audio["id"],
                        "role": audio["role"], "source_timerange": {"start": 0, "duration": audio["duration"]},
                        "target_timerange": {"start": 0, "duration": audio["duration"]},
                    }
                    for audio in audios
                ]}],
            })
            _write(project / "draft_meta_info.json", {
                "draft_materials": [{"type": 18, "value": [{
                    "id": "bad-a10-subdraft", "extra_info": "a10_vocal_stem.wav",
                    "duration": 716_666,
                    "roughcut_time_range": {"start": 0, "duration": 716_666},
                    "metetype": "combination",
                }]}],
            })

            errors = validate_audio_material_registration(project)
            codes = {row["code"] for row in errors}
            self.assertIn("COMBINATION_AUDIO_DECODE_FAILED", codes)
            self.assertIn("A10_SUBDRAFT_DURATION_MISMATCH", codes)
            self.assertIn("USER_AUDIO_OVERLAY_COLLAPSED", codes)
            self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_rejects_a10_hidden_in_material_items(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            a10 = content["materials"]["audios"].pop(0)
            a10["type"] = "music"
            content["materials"]["items"] = [a10]
            _write(content_path, content)

            codes = {row["code"] for row in validate_audio_material_registration(project)}
            self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_exact_four_bundle_rejects_id_and_path_aliases(self):
        for mutation in ("id_alias", "path_alias"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                self._registered_bundle(project)
                content_path = project / "draft_content.json"
                content = json.loads(content_path.read_text(encoding="utf-8"))
                rows = content["materials"]["audios"]
                if mutation == "id_alias":
                    old_id = rows[2]["id"]
                    rows[2]["id"] = rows[1]["id"]
                    rows[2]["music_id"] = rows[1]["id"]
                    content["tracks"][0]["segments"][2]["material_id"] = rows[1]["id"]
                    meta = json.loads((project / "draft_meta_info.json").read_text(encoding="utf-8"))
                    meta_row = next(
                        row for group in meta["draft_materials"] if group["type"] == 0
                        for row in group["value"] if row["id"] == old_id
                    )
                    meta_row["id"] = rows[1]["id"]
                    _write(project / "draft_meta_info.json", meta)
                else:
                    rows[2]["path"] = rows[1]["path"]
                _write(content_path, content)

                codes = {row["code"] for row in validate_audio_material_registration(project)}
                self.assertIn("USER_AUDIO_OVERLAY_COLLAPSED", codes)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "media tools required")
    def test_declared_user_audio_count_includes_each_valid_a9_and_a10_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            media = project / "Resources" / "media"
            media.mkdir(parents=True)
            audios = []
            for index, (name, role) in enumerate((
                ("a9_narration_1.wav", "A9"),
                ("a9_narration_2.wav", "A9"),
                ("a10_vocal_stem.wav", "A10"),
                ("user_overlay_15.wav", "USER_PROVIDED_AUDIO"),
            )):
                subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"sine=frequency={440 + index}:duration=0.2",
                    "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(media / name),
                ], check=True)
                audios.append({
                    "id": f"audio-{index}", "role": role, "type": "music", "name": name,
                    "path": f"##_draftpath_placeholder_fixture_##/Resources/media/{name}",
                    "duration": 200_000, "local_material_id": "", "music_id": "",
                })
            _write(project / "draft_content.json", {
                "materials": {"audios": audios},
                "tracks": [{"segments": [
                    {"id": f"segment-{index}", "material_id": row["id"]}
                    for index, row in enumerate(audios)
                ]}],
            })
            _write(project / "draft_meta_info.json", {"draft_materials": []})
            builder.register_project_local_audio_materials(project)

            errors = validate_audio_material_registration(
                project,
                declared_items=[{"track_index": 15, "media_kind": "audio"}],
                declared_role_segment_ids={
                    "A9": {"segment-0", "segment-1"},
                    "A10": {"segment-2"},
                },
            )

            self.assertEqual(errors, [])

            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            content["tracks"][0]["segments"][1]["material_id"] = "audio-0"
            _write(content_path, content)
            collapsed_errors = validate_audio_material_registration(
                project,
                declared_items=[{"track_index": 15, "media_kind": "audio"}],
                declared_role_segment_ids={
                    "A9": {"segment-0", "segment-1"},
                    "A10": {"segment-2"},
                },
            )

            self.assertIn(
                "A9_MATERIAL_MAPPING_INVALID",
                {row["code"] for row in collapsed_errors},
            )

    def test_out_of_project_managed_audio_path_fails_closed_without_crashing(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            content["materials"]["audios"][0]["path"] = str(project.parent / "outside.wav")
            _write(content_path, content)

            errors = validate_audio_material_registration(project)

            self.assertIn(
                "AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID",
                {row["code"] for row in errors},
            )

    def test_registration_schema_and_combination_refs_are_hard_gates(self):
        schema_mutations = {
            "material_type": lambda content, meta: content["materials"]["audios"][1].update(type="music"),
            "music_id": lambda content, meta: content["materials"]["audios"][1].update(music_id="wrong"),
            "meta_metetype": lambda content, meta: meta["draft_materials"][0]["value"][1].update(metetype="combination"),
            "meta_item_source": lambda content, meta: meta["draft_materials"][0]["value"][1].update(item_source=0),
            "meta_type": lambda content, meta: meta["draft_materials"][0]["value"][1].update(type=18),
            "meta_file_path": lambda content, meta: meta["draft_materials"][0]["value"][1].update(file_Path="C:\\bad\\overlay.wav"),
            "meta_extra_info": lambda content, meta: meta["draft_materials"][0]["value"][1].update(extra_info="wrong.wav"),
            "meta_sub_time_range": lambda content, meta: meta["draft_materials"][0]["value"][1].update(sub_time_range={"start": 0, "duration": 1}),
            "meta_width": lambda content, meta: meta["draft_materials"][0]["value"][1].update(width=1),
            "roughcut": lambda content, meta: meta["draft_materials"][0]["value"][1]["roughcut_time_range"].update(duration=1),
            "roughcut_plus_one": lambda content, meta: meta["draft_materials"][0]["value"][1]["roughcut_time_range"].update(
                duration=content["materials"]["audios"][1]["duration"] + 1
            ),
        }
        for name, mutate in schema_mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                self._registered_bundle(project)
                content_path = project / "draft_content.json"
                meta_path = project / "draft_meta_info.json"
                content = json.loads(content_path.read_text(encoding="utf-8"))
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                mutate(content, meta)
                _write(content_path, content)
                _write(meta_path, meta)
                codes = {row["code"] for row in validate_audio_material_registration(project)}
                self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_extra_managed_meta_row_is_rejected_but_unrelated_row_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            meta_path = project / "draft_meta_info.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            rows = meta["draft_materials"][0]["value"]
            rows.append({
                "id": "legitimate-image", "extra_info": "logo.png",
                "metetype": "photo", "type": 0,
            })
            _write(meta_path, meta)
            self.assertEqual(validate_audio_material_registration(project), [])

            rows.append({
                "id": "stale-audio", "extra_info": "user_overlay_18.wav",
                "metetype": "music", "item_source": 1, "type": 0,
            })
            _write(meta_path, meta)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            stale_material = dict(content["materials"]["audios"][1])
            stale_material.update({
                "id": "stale-audio", "name": "user_overlay_18.wav",
                "role": "USER_PROVIDED_AUDIO", "music_id": "stale-audio",
            })
            content["materials"]["audios"].append(stale_material)
            content["tracks"][0]["segments"].append({
                "id": "stale-segment", "material_id": "stale-audio",
            })
            _write(content_path, content)
            declared = [
                {"track_index": index, "media_kind": "audio"}
                for index in (15, 16, 17)
            ]
            codes = {row["code"] for row in validate_audio_material_registration(
                project, declared_items=declared,
                declared_role_segment_ids={"A9": set(), "A10": {"segment-0"}},
            )}
            self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_unrelated_local_music_meta_and_referenced_bgm_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            meta_path = project / "draft_meta_info.json"
            content_path = project / "draft_content.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            content = json.loads(content_path.read_text(encoding="utf-8"))
            rows = meta["draft_materials"][0]["value"]

            unrelated = dict(rows[0])
            unrelated.update({"id": "unrelated-local-music", "extra_info": "bgm.wav"})
            rows.append(unrelated)
            _write(meta_path, meta)
            self.assertEqual(validate_audio_material_registration(project), [])

            bgm_material = dict(content["materials"]["audios"][0])
            bgm_material.update({
                "id": "bgm-a12", "role": "A12", "name": "bgm.wav",
                "music_id": "bgm-a12",
            })
            content["materials"]["audios"].append(bgm_material)
            content["tracks"][0]["segments"].append({
                "id": "bgm-segment", "material_id": "bgm-a12", "role": "A12",
            })
            bgm_meta = dict(rows[0])
            bgm_meta.update({"id": "bgm-a12", "extra_info": "bgm.wav"})
            rows.append(bgm_meta)
            _write(content_path, content)
            _write(meta_path, meta)

            self.assertEqual(validate_audio_material_registration(project), [])

        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            content["materials"]["items"] = [{"id": "combo", "type": "combination"}]
            content["tracks"][0]["segments"][1]["extra_material_refs"] = ["combo"]
            _write(content_path, content)
            codes = {row["code"] for row in validate_audio_material_registration(project)}
            self.assertIn("AUDIO_MATERIAL_COMBINATION_REFERENCE_FORBIDDEN", codes)

    def test_identical_mirrored_material_rows_are_canonicalized_by_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            content["materials"]["items"] = [
                dict(row) for row in content["materials"]["audios"]
            ]
            _write(content_path, content)

            self.assertEqual(validate_audio_material_registration(project), [])

    def test_conflicting_mirrored_material_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            conflict = dict(content["materials"]["audios"][1])
            conflict["path"] = content["materials"]["audios"][2]["path"]
            conflict["local_material_id"] = "conflicting-local-id"
            content["materials"]["items"] = [conflict]
            _write(content_path, content)

            codes = {row["code"] for row in validate_audio_material_registration(project)}
            self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_nested_effect_combination_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            content_path = project / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            content["materials"]["items"] = [{"id": "combo", "type": "combination"}]
            content["tracks"][0]["segments"][1]["effects"] = [
                {"binding": {"material_id": "combo"}}
            ]
            _write(content_path, content)

            codes = {row["code"] for row in validate_audio_material_registration(project)}
            self.assertIn("AUDIO_MATERIAL_COMBINATION_REFERENCE_FORBIDDEN", codes)

    def test_duplicate_managed_meta_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self._registered_bundle(project)
            meta_path = project / "draft_meta_info.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            rows = meta["draft_materials"][0]["value"]
            rows.append(dict(rows[1]))
            _write(meta_path, meta)

            codes = {row["code"] for row in validate_audio_material_registration(project)}
            self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_required_ui_meta_fields_cannot_be_deleted(self):
        required_fields = (
            "ai_group_type", "create_time", "enter_from", "import_time",
            "import_time_ms", "material_color_tag", "md5",
        )
        for field in required_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                self._registered_bundle(project)
                meta_path = project / "draft_meta_info.json"
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                del meta["draft_materials"][0]["value"][1][field]
                _write(meta_path, meta)

                codes = {row["code"] for row in validate_audio_material_registration(project)}
                self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)

    def test_builder_written_material_fields_are_exact(self):
        mutations = {
            "resource_id": "stale", "third_resource_id": "stale",
            "remote_url": "https://stale.invalid", "source_platform": 1,
            "category_id": "preset", "category_name": "preset",
            "request_id": "stale", "team_id": "stale", "check_flag": 0,
            "copyright_limit_type": "limited",
        }
        for field, value in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                self._registered_bundle(project)
                content_path = project / "draft_content.json"
                content = json.loads(content_path.read_text(encoding="utf-8"))
                content["materials"]["audios"][1][field] = value
                _write(content_path, content)

                codes = {row["code"] for row in validate_audio_material_registration(project)}
                self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", codes)


if __name__ == "__main__":
    unittest.main()
