from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_capcut_media_links.py"
)


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MediaLinkGateTests(unittest.TestCase):
    def test_active_source_video_must_link_existing_source(self):
        module = load_source_module_no_bytecode("media_link_valid", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            write_json(
                root / "50_capcut_project" / "draft_content.json",
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )

            result = module.validate_capcut_media_links(
                root,
                Path("50_capcut_project/draft_content.json"),
                Path("00_source/source.mp4"),
            )

            self.assertEqual(result["capcut_media_links_status"], "PASS")

    def test_missing_active_source_path_fails(self):
        module = load_source_module_no_bytecode("media_link_missing", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            write_json(
                root / "50_capcut_project" / "draft_content.json",
                {
                    "active_materials": [
                        {"role": "source_video", "path": "missing.mp4", "active": True}
                    ]
                },
            )

            with self.assertRaisesRegex(module.GateFail, "FAIL_MEDIA_LINK"):
                module.validate_capcut_media_links(
                    root,
                    Path("50_capcut_project/draft_content.json"),
                    Path("00_source/source.mp4"),
                )

    def test_external_capcut_draft_resolves_relative_media_from_project_folder(self):
        module = load_source_module_no_bytecode("media_link_capcut_runtime", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            capcut_project = Path(tmp) / "capcut-project"
            write(root / "00_source" / "source.mp4", "video")
            draft_path = capcut_project / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )
            write_json(
                capcut_project / "draft_meta_info.json",
                {
                    "draft_materials": [
                        {
                            "type": 8,
                            "value": [
                                {
                                    "file_Path": "missing/non-media-effect.bin",
                                }
                            ],
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_CAPCUT_RUNTIME_MEDIA_LINK",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_external_capcut_draft_validates_meta_info_media_paths(self):
        module = load_source_module_no_bytecode("media_link_capcut_meta", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            capcut_project = Path(tmp) / "capcut-project"
            source = root / "00_source" / "source.mp4"
            write(source, "video")
            write(root / "00_source" / "source_audio.wav", "audio")
            draft_path = capcut_project / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": str(source),
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )
            write_json(
                capcut_project / "draft_meta_info.json",
                {
                    "draft_materials": [
                        {
                            "type": 1,
                            "value": [
                                {
                                    "extra_info": "source_audio.wav",
                                    "file_Path": "00_source/source_audio.wav",
                                }
                            ],
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_CAPCUT_RUNTIME_MEDIA_LINK",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_external_capcut_copied_source_matches_absolute_source_declaration(self):
        module = load_source_module_no_bytecode("media_link_capcut_absolute_source", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            capcut_project = Path(tmp) / "capcut-project"
            source = root / "00_source" / "source.mp4"
            copied_source = capcut_project / "00_source" / "source.mp4"
            write(source, "video")
            write(copied_source, "video")
            draft_path = capcut_project / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )
            write_json(
                capcut_project / "draft_meta_info.json",
                {
                    "draft_materials": [
                        {
                            "type": 8,
                            "value": [
                                {
                                    "file_Path": "missing/non-media-effect.bin",
                                }
                            ],
                        }
                    ]
                },
            )

            try:
                result = module.validate_capcut_media_links(
                    root,
                    draft_path,
                    source,
                )
            except module.GateFail as exc:
                self.fail(f"copied original source was not recognized: {exc}")

            self.assertEqual(result["original_source_media_bin_status"], "PASS")

    def test_external_capcut_declared_source_copy_must_match_original_bytes(self):
        module = load_source_module_no_bytecode("media_link_capcut_source_hash", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            capcut_project = Path(tmp) / "capcut-project"
            source = root / "00_source" / "source.mp4"
            write(source, "original")
            write(capcut_project / "00_source" / "source.mp4", "different")
            draft_path = capcut_project / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )
            write_json(capcut_project / "draft_meta_info.json", {"draft_materials": []})

            with self.assertRaisesRegex(
                module.GateFail,
                "original source media is not listed by exact path",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    source,
                )

    def test_native_capcut_non_media_materials_do_not_require_paths(self):
        module = load_source_module_no_bytecode("media_link_native_groups", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "materials": {
                        "videos": [
                            {
                                "type": "video",
                                "role": "source_video",
                                "path": "00_source/source.mp4",
                                "active": True,
                                "audio_enabled": False,
                            }
                        ],
                        "texts": [
                            {
                                "type": "text",
                                "name": "caption",
                                "path": "missing/non-media-caption.txt",
                            }
                        ],
                        "canvases": [
                            {
                                "type": "canvas_color",
                                "file_path": "missing/non-media-canvas.bin",
                            }
                        ],
                        "speeds": [{"type": "speed"}],
                    }
                },
            )

            try:
                result = module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )
            except module.GateFail as exc:
                self.fail(f"native non-media material was treated as imported media: {exc}")

            self.assertEqual(result["capcut_media_links_status"], "PASS")

    def test_external_capcut_draft_requires_sibling_meta_info(self):
        module = load_source_module_no_bytecode("media_link_capcut_meta_required", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            capcut_project = Path(tmp) / "capcut-project"
            source = root / "00_source" / "source.mp4"
            copied_source = capcut_project / "00_source" / "source.mp4"
            write(source, "video")
            write(copied_source, "video")
            draft_path = capcut_project / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_CAPCUT_RUNTIME_MEDIA_LINK.*draft_meta_info",
            ):
                module.validate_capcut_media_links(root, draft_path, source)

    def test_native_capcut_source_video_segment_volume_must_be_zero(self):
        module = load_source_module_no_bytecode("media_link_native_segment_mute", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            write(source, "video")
            draft_path = root / "50_capcut_project" / "draft_content.json"
            draft = {
                "materials": {
                    "videos": [
                        {
                            "id": "source-video",
                            "type": "video",
                            "path": "00_source/source.mp4",
                        }
                    ]
                },
                "tracks": [
                    {
                        "type": "video",
                        "segments": [
                            {
                                "material_id": "source-video",
                                "volume": 1.0,
                            }
                        ],
                    }
                ],
            }
            write_json(draft_path, draft)

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            draft["tracks"][0]["segments"][0]["volume"] = 0.0
            write_json(draft_path, draft)
            result = module.validate_capcut_media_links(
                root,
                draft_path,
                Path("00_source/source.mp4"),
            )
            self.assertEqual(result["capcut_media_links_status"], "PASS")

    def test_source_video_audio_must_always_be_muted(self):
        module = load_source_module_no_bytecode("media_link_audio_mute", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": True,
                            "caption_type": "tts_narration",
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(module.GateFail, "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED"):
                module.validate_capcut_media_links(root, draft_path, Path("00_source/source.mp4"))

            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": True,
                            "caption_type": "speaker_quote",
                        }
                    ]
                },
            )
            with self.assertRaisesRegex(module.GateFail, "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED"):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_clean_visual_can_be_active_while_original_source_stays_in_media_bin(self):
        module = load_source_module_no_bytecode("media_link_dual_source", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "original")
            write(root / "00_source" / "clean_visual.mp4", "clean")
            write(root / "00_source" / "clean_visual_capcut.mp4", "clean")
            write_json(
                root / "00_source" / "source_manifest.json",
                {
                    "status": "PASS",
                    "sources": [
                        {
                            "source_id": "CLEAN_VISUAL",
                            "local_source_path": "00_source/clean_visual.mp4",
                            "role": "capcut_visual_only",
                            "embedded_audio_policy": "MUTED",
                        }
                    ],
                },
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video_CLEAN_VISUAL",
                            "is_source_video": True,
                            "path": "00_source/clean_visual_capcut.mp4",
                            "active": True,
                            "audio_enabled": False,
                        },
                    ],
                    "materials": {
                        "videos": [
                            {
                                "type": "video",
                                "path": "00_source/clean_visual_capcut.mp4",
                            },
                            {
                                "type": "video",
                                "path": "00_source/source.mp4",
                            },
                        ]
                    },
                },
            )

            result = module.validate_capcut_media_links(
                root,
                draft_path,
                Path("00_source/source.mp4"),
            )

            self.assertEqual(result["capcut_media_links_status"], "PASS")
            self.assertEqual(result["original_source_media_bin_status"], "PASS")
            self.assertEqual(result["dual_source_binding_status"], "PASS")

    def test_native_clean_visual_rejects_active_original_source_segment(self):
        module = load_source_module_no_bytecode("media_link_native_dual_source_mute", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            clean = root / "00_source" / "clean_visual.mp4"
            write(source, "original")
            write(clean, "clean")
            write_json(
                root / "00_source" / "source_manifest.json",
                {
                    "sources": [
                        {
                            "role": "capcut_visual_only",
                            "local_source_path": "00_source/clean_visual.mp4",
                        }
                    ]
                },
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "materials": {
                        "videos": [
                            {
                                "id": "clean-video",
                                "type": "video",
                                "path": "00_source/clean_visual.mp4",
                            },
                            {
                                "id": "original-video",
                                "type": "video",
                                "path": "00_source/source.mp4",
                            },
                        ]
                    },
                    "tracks": [
                        {
                            "type": "video",
                            "segments": [
                                {"material_id": "clean-video", "volume": 0.0},
                                {"material_id": "original-video", "volume": 1.0},
                            ],
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_ORIGINAL_SOURCE_VIDEO_ACTIVE|FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_unrecognized_active_original_video_cannot_bypass_mute_gate(self):
        module = load_source_module_no_bytecode("media_link_overlay_mute", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "original")
            write(root / "00_source" / "clean_visual.mp4", "clean")
            write_json(
                root / "00_source" / "source_manifest.json",
                {
                    "sources": [
                        {
                            "role": "capcut_visual_only",
                            "local_source_path": "00_source/clean_visual.mp4",
                        }
                    ]
                },
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video_CLEAN_VISUAL",
                            "is_source_video": True,
                            "path": "00_source/clean_visual.mp4",
                            "active": True,
                            "audio_enabled": False,
                        },
                        {
                            "role": "overlay",
                            "type": "video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": True,
                        },
                    ],
                    "materials": {
                        "videos": [
                            {"type": "video", "path": "00_source/source.mp4"}
                        ]
                    },
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_byte_identical_clean_copy_does_not_prove_original_media_bin_entry(self):
        module = load_source_module_no_bytecode("media_link_exact_bin_path", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "same-bytes")
            write(root / "00_source" / "clean_visual.mp4", "same-bytes")
            write_json(
                root / "00_source" / "source_manifest.json",
                {
                    "sources": [
                        {
                            "role": "capcut_visual_only",
                            "local_source_path": "00_source/clean_visual.mp4",
                        }
                    ]
                },
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video_CLEAN_VISUAL",
                            "is_source_video": True,
                            "path": "00_source/clean_visual.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ],
                    "materials": {
                        "videos": [
                            {"type": "video", "path": "00_source/clean_visual.mp4"}
                        ]
                    },
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "original source media is not listed by exact path",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_speaker_q_materials_are_bound_to_validated_vocals_hash(self):
        module = load_source_module_no_bytecode("media_link_q_provenance", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            vocals = root / "10_analysis" / "audio" / "vocals.wav"
            q_asset = root / "30_audio_srt" / "speaker_q" / "E1.wav"
            write(source, "original")
            write(vocals, "demucs-vocals")
            write(q_asset, "derived-q")
            write_json(
                root / "10_analysis" / "source_voice_separation.json",
                {
                    "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
                    "status": "PASS",
                    "vocals_path": "10_analysis/audio/vocals.wav",
                    "vocals_sha256": sha256(vocals),
                },
            )
            write_json(
                root / "20_script" / "timeline_design.json",
                {
                    "segments": [
                        {"edit_id": "E1", "caption_type": "speaker_quote"}
                    ]
                },
            )
            write_json(
                root / "30_audio_srt" / "audio_asset_manifest.json",
                {
                    "status": "PASS",
                    "speaker_q_lane": [
                        {
                            "edit_id": "E1",
                            "path": "30_audio_srt/speaker_q/E1.wav",
                            "source_audio_ref": "10_analysis/audio/vocals.wav",
                            "source_audio_provenance": "demucs_full_source_vocals",
                            "source_voice_vocals_sha256": sha256(vocals),
                            "asset_sha256": sha256(q_asset),
                        }
                    ],
                },
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        },
                        {
                            "role": "speaker_q_E1",
                            "path": "30_audio_srt/speaker_q/E1.wav",
                            "active": True,
                        },
                    ],
                    "materials": {
                        "videos": [
                            {"type": "video", "path": "00_source/source.mp4"}
                        ],
                        "audios": [
                            {
                                "type": "audio",
                                "path": "30_audio_srt/speaker_q/E1.wav",
                            }
                        ],
                    },
                },
            )

            result = module.validate_capcut_media_links(
                root,
                draft_path,
                Path("00_source/source.mp4"),
            )
            self.assertEqual(result["speaker_q_provenance_status"], "PASS")

            manifest_path = root / "30_audio_srt" / "audio_asset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["speaker_q_lane"][0]["source_voice_vocals_sha256"] = "0" * 64
            write_json(manifest_path, manifest)
            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

    def test_empty_speaker_q_lane_is_not_required_for_tts_only_draft(self):
        module = load_source_module_no_bytecode("media_link_q_not_required", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            vocals = root / "10_analysis" / "audio" / "vocals.wav"
            write(source, "video")
            write(vocals, "demucs-vocals")
            write_json(
                root / "10_analysis" / "source_voice_separation.json",
                {
                    "status": "PASS",
                    "vocals_path": "10_analysis/audio/vocals.wav",
                    "vocals_sha256": sha256(vocals),
                },
            )
            write_json(
                root / "30_audio_srt" / "audio_asset_manifest.json",
                {"status": "PASS", "speaker_q_lane": []},
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )

            result = module.validate_capcut_media_links(
                root,
                draft_path,
                Path("00_source/source.mp4"),
            )

            self.assertEqual(result["speaker_q_provenance_status"], "NOT_REQUIRED")

    def test_speaker_quote_requires_manifest_lane_and_runtime_q_reference(self):
        module = load_source_module_no_bytecode("media_link_q_required", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            vocals = root / "10_analysis" / "audio" / "vocals.wav"
            q_asset = root / "30_audio_srt" / "speaker_q" / "E2.wav"
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write(source, "video")
            write(vocals, "demucs-vocals")
            write(q_asset, "derived-q")
            write_json(
                root / "10_analysis" / "source_voice_separation.json",
                {
                    "status": "PASS",
                    "vocals_path": "10_analysis/audio/vocals.wav",
                    "vocals_sha256": sha256(vocals),
                },
            )
            write_json(
                root / "20_script" / "timeline_design.json",
                {
                    "segments": [
                        {
                            "edit_id": "E2",
                            "caption_type": "speaker_quote",
                        }
                    ]
                },
            )
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*audio_asset_manifest",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            write_json(
                root / "30_audio_srt" / "audio_asset_manifest.json",
                {
                    "status": "PASS",
                    "speaker_q_lane": [],
                },
            )
            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*speaker_q_lane is empty",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            write_json(
                root / "30_audio_srt" / "audio_asset_manifest.json",
                {
                    "status": "PASS",
                    "speaker_q_lane": [
                        {
                            "edit_id": "E2",
                            "path": "30_audio_srt/speaker_q/E2.wav",
                            "source_audio_ref": "10_analysis/audio/vocals.wav",
                            "source_audio_provenance": "demucs_full_source_vocals",
                            "source_voice_vocals_sha256": sha256(vocals),
                            "asset_sha256": sha256(q_asset),
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*active audio",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            draft["active_materials"].append(
                {
                    "role": "speaker_q_E2",
                    "path": "30_audio_srt/speaker_q/E2.wav",
                    "active": True,
                }
            )
            write_json(draft_path, draft)
            result = module.validate_capcut_media_links(
                root,
                draft_path,
                Path("00_source/source.mp4"),
            )
            self.assertEqual(result["speaker_q_provenance_status"], "PASS")

    def test_speaker_q_lane_must_be_exact_unique_and_active_on_audio_track(self):
        module = load_source_module_no_bytecode("media_link_q_exact_active", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            vocals = root / "10_analysis" / "audio" / "vocals.wav"
            q_asset = root / "30_audio_srt" / "speaker_q" / "E2_demucs.wav"
            write(source, "video")
            write(vocals, "demucs-vocals")
            write(q_asset, "derived-q")
            write_json(
                root / "10_analysis" / "source_voice_separation.json",
                {
                    "status": "PASS",
                    "vocals_path": "10_analysis/audio/vocals.wav",
                    "vocals_sha256": sha256(vocals),
                },
            )
            write_json(
                root / "20_script" / "timeline_design.json",
                {
                    "segments": [
                        {"edit_id": "E2", "caption_type": "speaker_quote"}
                    ]
                },
            )
            lane_item = {
                "edit_id": "E2",
                "path": "30_audio_srt/speaker_q/E2_demucs.wav",
                "source_audio_ref": "10_analysis/audio/vocals.wav",
                "source_audio_provenance": "demucs_full_source_vocals",
                "source_voice_vocals_sha256": sha256(vocals),
                "asset_sha256": sha256(q_asset),
            }
            manifest_path = root / "30_audio_srt" / "audio_asset_manifest.json"
            write_json(
                manifest_path,
                {
                    "status": "PASS",
                    "speaker_q_lane": [lane_item, dict(lane_item)],
                },
            )
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "materials": {
                        "videos": [
                            {
                                "id": "source-video",
                                "type": "video",
                                "path": "00_source/source.mp4",
                            }
                        ],
                        "audios": [
                            {
                                "id": "speaker-q-E2",
                                "type": "audio",
                                "path": "30_audio_srt/speaker_q/E2_demucs.wav",
                            }
                        ],
                    },
                    "tracks": [
                        {
                            "type": "video",
                            "segments": [
                                {"material_id": "source-video", "volume": 0.0}
                            ],
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*duplicate",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            extra_item = {
                **lane_item,
                "edit_id": "E9",
            }
            write_json(
                manifest_path,
                {
                    "status": "PASS",
                    "speaker_q_lane": [lane_item, extra_item],
                },
            )
            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*unexpected",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            write_json(
                manifest_path,
                {
                    "status": "PASS",
                    "speaker_q_lane": [lane_item],
                },
            )
            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*active audio",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            draft["tracks"].append(
                {
                    "type": "audio",
                    "segments": [
                        {
                            "material_id": "speaker-q-E2",
                            "volume": 1.0,
                        }
                    ],
                }
            )
            write_json(draft_path, draft)
            draft["tracks"][-1]["segments"].append(
                {
                    "material_id": "speaker-q-E2",
                    "volume": 1.0,
                }
            )
            write_json(draft_path, draft)
            with self.assertRaisesRegex(
                module.GateFail,
                "FAIL_SPEAKER_Q_PROVENANCE.*duplicate active audio",
            ):
                module.validate_capcut_media_links(
                    root,
                    draft_path,
                    Path("00_source/source.mp4"),
                )

            draft["tracks"][-1]["segments"].pop()
            write_json(draft_path, draft)
            result = module.validate_capcut_media_links(
                root,
                draft_path,
                Path("00_source/source.mp4"),
            )
            self.assertEqual(result["speaker_q_provenance_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
