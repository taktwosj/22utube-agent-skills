import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_politics_card_project as builder
import capture_politics_relink_readback as readback


MICROS = 1_000_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def make_media(path: Path, duration: int, *, audio: bool) -> None:
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=30",
    ]
    if audio:
        command += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000"]
    command += ["-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio:
        command += ["-c:a", "aac", "-shortest"]
    else:
        command += ["-an"]
    command += [str(path)]
    subprocess.run(command, check=True, capture_output=True, text=True)


def make_audio(path: Path, duration: int) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
            "-t", str(duration), "-c:a", "pcm_s16le", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def make_image(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=gray:s=320x180", "-frames:v", "1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def template_document() -> dict:
    def text_material(material_id: str, value: str) -> dict:
        return {"id": material_id, "content": json.dumps({"text": value, "styles": []}, ensure_ascii=False)}

    def segment(segment_id: str, material_id: str, duration: int = 20 * MICROS) -> dict:
        return {
            "id": segment_id,
            "material_id": material_id,
            "source_timerange": {"start": 0, "duration": duration},
            "target_timerange": {"start": 0, "duration": duration},
            "clip": {"alpha": 1.0},
            "extra_material_refs": [],
            "volume": 1.0,
            "last_nonzero_volume": 1.0,
        }

    texts = [
        text_material("TINTRO", "__INTRO_HOOK_LINE_1__\n__INTRO_HOOK_LINE_2__"),
        text_material("TCHAPTER", "__CHAPTER__"),
        text_material("TSOURCE", "출처 __SOURCE__\n__DATE__"),
        text_material("TLOWER", "__LOWER_LINE_1__\n__LOWER_LINE_2__"),
        text_material("TCTA", "구독은 다음 취재를 만듭니다"),
    ]
    video = {"id": "VINTRO", "type": "video", "duration": 20 * MICROS, "width": 1920, "height": 1080}
    photo = {"id": "VPHOTO", "type": "photo", "duration": 20 * MICROS, "width": 1920, "height": 1080}
    return {
        "duration": 20 * MICROS,
        "name": "ROOT",
        "materials": {"texts": texts, "videos": [video, photo], "audios": []},
        "tracks": [
            {"id": "VPRIMARY", "type": "video", "segments": [segment("SVINTRO", "VINTRO")]},
            {"id": "VOVERLAY", "type": "video", "segments": [segment("SVPHOTO", "VPHOTO")]},
            {"id": "TINTRO_TRACK", "type": "text", "segments": [segment("STINTRO", "TINTRO")]},
            {"id": "TCHAPTER_TRACK", "type": "text", "segments": [segment("STCHAPTER", "TCHAPTER")]},
            {"id": "TSOURCE_TRACK", "type": "text", "segments": [segment("STSOURCE", "TSOURCE")]},
            {"id": "TLOWER_TRACK", "type": "text", "segments": [segment("STLOWER", "TLOWER")]},
            {"id": "TCTA_TRACK", "type": "text", "segments": [segment("STCTA", "TCTA")]},
        ],
    }


class NarrationCardFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root / "source.mp4"
        cls.narration_video = cls.root / "narration-video.mp4"
        cls.narration_wav = cls.root / "narration.wav"
        cls.narration_m4a = cls.root / "narration.m4a"
        cls.image = cls.root / "image.png"
        cls.srt = cls.root / "narration.srt"
        make_media(cls.source, 9, audio=True)
        make_media(cls.narration_video, 4, audio=True)
        make_audio(cls.narration_wav, 4)
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(cls.narration_wav), "-c:a", "aac", str(cls.narration_m4a)],
            check=True,
            capture_output=True,
            text=True,
        )
        make_image(cls.image)
        cls.srt.write_text("1\n00:00:05,000 --> 00:00:06,000\ntechnical fixture\n", encoding="utf-8")
        cls.hashes = {name: sha256(getattr(cls, name)) for name in ("source", "narration_video", "narration_wav", "narration_m4a", "image", "srt")}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.srt.write_text("1\n00:00:05,000 --> 00:00:06,000\ntechnical fixture\n", encoding="utf-8")

    def cards(self, *, narration_duration_us: int = MICROS, card_type: str = "NARRATION_IMAGE") -> dict:
        source_duration = 10 * MICROS - narration_duration_us
        narration = {
            "card_id": "C002",
            "card_type": card_type,
            "target_start_us": 5 * MICROS,
            "target_duration_us": narration_duration_us,
            "narration_audio_file": str(self.narration_wav),
            "narration_audio_sha256": self.hashes["narration_wav"],
            "audio_start_us": 0,
            "audio_duration_us": narration_duration_us,
            "narration_srt_file": str(self.srt),
            "narration_srt_sha256": self.hashes["srt"],
            "fact_source_refs": ["TECHNICAL_FIXTURE_SOURCE"],
            "lower_mode": "NONE",
        }
        if card_type == "NARRATION_IMAGE":
            narration.update({
                "image_file": str(self.image),
                "image_sha256": self.hashes["image"],
                "motion_profile": "SLOW_ZOOM_IN",
                "asset_origin": "LOCAL",
            })
        else:
            narration.update({
                "video_file": str(self.narration_video),
                "video_sha256": self.hashes["narration_video"],
                "video_start_us": 0,
                "video_duration_us": narration_duration_us,
                "source_audio_mode": "MUTE",
            })
        return {
            "schema": "politics-longform-episode-cards.v1",
            "episode_id": "P1_TECHNICAL_FIXTURE",
            "project_name": "P1_TECHNICAL_FIXTURE",
            "cards": [
                {"card_id": "C001", "card_type": "INTRO", "target_start_us": 0, "target_duration_us": 5 * MICROS, "intro_text": "technical\nfixture", "lower_mode": "NONE"},
                narration,
                {
                    "card_id": "C003", "card_type": "SOURCE_VIDEO", "target_start_us": 5 * MICROS + narration_duration_us,
                    "target_duration_us": source_duration, "source_file": str(self.source), "source_sha256": self.hashes["source"],
                    "source_start_us": 0, "source_duration_us": source_duration, "source_identity_ref": "TECH_SOURCE",
                    "source_channel": "TECHNICAL", "source_date": "2026.08.08", "original_audio_mode": "embedded", "lower_mode": "NONE",
                },
            ],
        }

    def validate(self, cards: dict) -> dict:
        validator = getattr(builder, "validate_narration_contract", None)
        if validator is None:
            self.fail("P1 narration contract validation is not implemented")
        return validator(cards)

    def test_01_existing_source_video_only_episode_remains_valid(self):
        cards = self.cards()
        cards["cards"] = [cards["cards"][0], cards["cards"][2]]
        cards["cards"][1]["target_start_us"] = 5 * MICROS
        cards["cards"][1]["target_duration_us"] = 5 * MICROS
        cards["cards"][1]["source_duration_us"] = 5 * MICROS
        self.assertEqual(builder.normalize_cards(cards)[1], 10 * MICROS)

    def test_02_ratio_exactly_ten_percent_passes_from_ffprobe_duration(self):
        result = self.validate(self.cards(narration_duration_us=MICROS))
        self.assertEqual(result["narration_duration_us"], MICROS)
        self.assertEqual(result["editorial_duration_us"], 10 * MICROS)
        self.assertEqual(result["narration_ratio"], 0.10)

    def test_03_ratio_exactly_forty_percent_passes_from_ffprobe_duration(self):
        result = self.validate(self.cards(narration_duration_us=4 * MICROS))
        self.assertEqual(result["narration_ratio"], 0.40)

    def test_04_requested_narration_below_ten_percent_is_accepted(self):
        cards = self.cards()
        cards["cards"][1]["audio_duration_us"] = 999_999
        self.assertEqual(self.validate(cards)["status"], "PASS")

    def test_05_requested_narration_above_forty_percent_is_accepted(self):
        cards = self.cards(narration_duration_us=4 * MICROS)
        cards["cards"][2]["target_duration_us"] = 1
        cards["cards"][2]["source_duration_us"] = 1
        self.assertEqual(self.validate(cards)["status"], "PASS")

    def test_06_duplicate_audio_sha_and_range_are_counted_once(self):
        cards = self.cards()
        duplicate = copy.deepcopy(cards["cards"][1])
        duplicate.update({"card_id": "C003", "target_start_us": 5 * MICROS})
        source = cards["cards"][2]
        source.update({"card_id": "C004", "target_start_us": 7 * MICROS, "target_duration_us": 8 * MICROS, "source_duration_us": 8 * MICROS})
        cards["cards"] = [cards["cards"][0], cards["cards"][1], duplicate, source]
        result = self.validate(cards)
        self.assertEqual(result["narration_duration_us"], MICROS)
        self.assertEqual(result["narration_ratio"], 0.10)

    def test_07_override_with_user_reason_passes(self):
        cards = self.cards(narration_duration_us=4 * MICROS)
        cards["cards"][2].update({"target_duration_us": 1, "source_duration_us": 1})
        cards["narration_ratio_override"] = True
        cards["narration_ratio_override_reason"] = "user requested a separate narration ratio"
        self.assertTrue(self.validate(cards)["override"])

    def test_08_legacy_override_without_reason_does_not_gate_requested_narration(self):
        cards = self.cards(narration_duration_us=4 * MICROS)
        cards["narration_ratio_override"] = True
        self.assertEqual(self.validate(cards)["status"], "PASS")

    def test_09_valid_narration_image_middle_card_passes_contract(self):
        self.assertEqual(self.validate(self.cards())["status"], "PASS")

    def test_10_narration_image_is_embedded_in_resources_not_media_relink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = builder.copy_card_media(self.cards()["cards"], root / "Media", "P1_TECHNICAL_FIXTURE")
            builder.embed_design_images(root / "draft", root / "project", records)
            record = records["C002"]
            embedded = root / "draft" / record["embedded_relpath"]
            self.assertEqual(record["storage"], "embedded")
            self.assertEqual(sha256(embedded), self.hashes["image"])
            self.assertFalse((root / "Media" / record["filename"]).exists())
            self.assertEqual(list((root / "Media").glob("*.png")), [])

    def test_11_valid_narration_video_cut_passes_contract(self):
        self.assertEqual(self.validate(self.cards(card_type="NARRATION_VIDEO"))["status"], "PASS")

    def test_12_narration_video_range_past_ffprobe_duration_fails(self):
        cards = self.cards(card_type="NARRATION_VIDEO")
        cards["cards"][1].update({"video_start_us": 3_500_000, "video_duration_us": MICROS})
        with self.assertRaisesRegex(RuntimeError, "NARRATION_VIDEO_RANGE_INVALID"):
            self.validate(cards)

    def test_13_narration_video_target_duration_difference_over_250ms_fails(self):
        cards = self.cards(card_type="NARRATION_VIDEO")
        cards["cards"][1]["video_duration_us"] = 1_300_000
        with self.assertRaisesRegex(RuntimeError, "NARRATION_VIDEO_TARGET_DURATION_INVALID"):
            self.validate(cards)

    def test_14_narration_audio_target_duration_difference_over_250ms_fails(self):
        cards = self.cards()
        cards["cards"][1]["audio_duration_us"] = 1_300_000
        with self.assertRaisesRegex(RuntimeError, "NARRATION_AUDIO_TARGET_DURATION_INVALID"):
            self.validate(cards)

    def test_15_narration_video_source_audio_is_marked_muted_for_builder(self):
        with tempfile.TemporaryDirectory() as temporary:
            records = builder.copy_card_media(
                self.cards(card_type="NARRATION_VIDEO")["cards"], Path(temporary) / "Media", "P1_TECHNICAL_FIXTURE"
            )
        self.assertIn("C002", records)
        self.assertEqual(records["C002"]["source_audio_mode"], "MUTE")

    def test_16_duplicate_source_and_narration_audio_fails(self):
        cards = self.cards(card_type="NARRATION_VIDEO")
        cards["cards"][1]["source_audio_mode"] = "embedded"
        with self.assertRaisesRegex(RuntimeError, "FAIL_DUPLICATE_AUDIO"):
            self.validate(cards)

    def test_17_narration_audio_sha_mismatch_fails(self):
        cards = self.cards()
        cards["cards"][1]["narration_audio_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "NARRATION_AUDIO_SHA256_INVALID"):
            self.validate(cards)

    def test_18_narration_srt_outside_used_audio_range_fails(self):
        self.srt.write_text("1\n00:00:05,000 --> 00:00:06,300\ntechnical fixture\n", encoding="utf-8")
        cards = self.cards()
        cards["cards"][1]["narration_srt_sha256"] = sha256(self.srt)
        with self.assertRaisesRegex(RuntimeError, "NARRATION_SRT_RANGE_INVALID"):
            self.validate(cards)

    def test_19_image_sha_mismatch_fails(self):
        cards = self.cards()
        cards["cards"][1]["image_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "IMAGE_SHA256_INVALID"):
            self.validate(cards)

    def test_20_missing_fact_source_refs_do_not_gate_requested_narration(self):
        cards = self.cards()
        cards["cards"][1].update({"asset_origin": "GENERATED", "fact_source_refs": []})
        self.assertEqual(self.validate(cards)["status"], "PASS")

    def test_21_readback_requires_narration_video_and_audio_sha_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            media = Path(temporary) / "Media"
            media.mkdir()
            video = media / "C002_narration-video.mp4"
            audio = media / "C002_narration.wav"
            video.write_bytes(self.narration_video.read_bytes())
            audio.write_bytes(self.narration_wav.read_bytes())
            build = {
                "media": {
                    "C002": {
                        "filename": video.name,
                        "sha256": self.hashes["narration_video"],
                        "storage": "relink",
                        "narration_audio": {
                            "filename": audio.name,
                            "sha256": self.hashes["narration_wav"],
                            "storage": "relink",
                        },
                    }
                }
            }
            document = {
                "materials": {
                    "videos": [{"material_name": video.name, "path": str(video)}],
                    "audios": [{"material_name": audio.name, "path": str(audio)}],
                }
            }
            rows, persisted = readback.readback_media(document, build, media, "LOCAL_MEDIA_FOLDER/test/Media")
        self.assertTrue(persisted)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["filename"] for row in rows}, {video.name, audio.name})

    def test_22_four_source_video_cards_start_at_zero_without_intro_or_optional_assets(self):
        cards = []
        for index in range(4):
            cards.append({
                "card_id": f"C{index + 1:03d}", "card_type": "SOURCE_VIDEO",
                "target_start_us": index * 2 * MICROS, "target_duration_us": 2 * MICROS,
                "source_file": str(self.source), "source_sha256": self.hashes["source"],
                "source_start_us": index * 2 * MICROS, "source_duration_us": 2 * MICROS,
                "source_identity_ref": f"TECH_SOURCE_{index}", "source_channel": "TECHNICAL",
                "source_date": "2026.08.08", "original_audio_mode": "embedded", "lower_mode": "NONE",
            })
        normalized, total = builder.normalize_cards({"cards": cards})
        with tempfile.TemporaryDirectory() as temporary:
            records = builder.copy_card_media(normalized, Path(temporary) / "Media", "TECH")
            document = builder.build_document(template_document(), normalized, total, records, "TECH")
        primary = document["tracks"][0]["segments"]
        self.assertEqual([row["target_timerange"]["start"] for row in primary], [0, 2 * MICROS, 4 * MICROS, 6 * MICROS])
        self.assertTrue(all(row["volume"] == 1.0 for row in primary))
        self.assertEqual(document["materials"]["audios"], [])
        self.assertEqual(len(records), 4)

    def test_23_public_lower_choices_map_by_active_audio_and_keep_internal_modes_compatible(self):
        source = self.cards()["cards"][2]
        source.update({"target_start_us": 0, "target_duration_us": MICROS, "source_duration_us": MICROS,
                       "lower_mode": "SRT", "source_srt_file": str(self.srt), "source_srt_sha256": self.hashes["srt"]})
        self.srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nsource cue\n", encoding="utf-8")
        source["source_srt_sha256"] = sha256(self.srt)
        normalized, _ = builder.normalize_cards({"cards": [source]})
        self.assertEqual(normalized[0]["lower_mode"], "SOURCE_TTS")
        narration = self.cards()["cards"][1]
        narration["target_start_us"] = 0
        narration["lower_mode"] = "SRT"
        narration["narration_srt_sha256"] = sha256(self.srt)
        source_first = copy.deepcopy(source)
        source_first["lower_mode"] = "NONE"
        source_first["target_duration_us"] = MICROS
        source_first["source_duration_us"] = MICROS
        narration["target_start_us"] = MICROS
        self.srt.write_text("1\n00:00:01,000 --> 00:00:02,000\nnarration cue\n", encoding="utf-8")
        narration["narration_srt_sha256"] = sha256(self.srt)
        normalized, _ = builder.normalize_cards({"cards": [source_first, narration]})
        self.assertEqual(normalized[1]["lower_mode"], "NARRATION_TTS")
        source["lower_mode"] = "COMMENTARY_2LINE"
        source["lower_text"] = "first line\nsecond line"
        normalized, _ = builder.normalize_cards({"cards": [source]})
        self.assertEqual(normalized[0]["lower_mode"], "VIDEO100_EXPLAINER")
        source["lower_mode"] = "NONE"
        self.assertEqual(builder.normalize_cards({"cards": [source]})[0][0]["lower_mode"], "NONE")

    def test_24_narration_video_builds_muted_video_one_audio_segment_and_srt_lower(self):
        cards = self.cards(card_type="NARRATION_VIDEO")
        source, narration = cards["cards"][2], cards["cards"][1]
        source.update({"target_start_us": 0, "target_duration_us": 5 * MICROS, "source_duration_us": 5 * MICROS})
        narration.update({"target_start_us": 5 * MICROS, "lower_mode": "SRT"})
        cards["cards"] = [source, narration]
        self.srt.write_text("1\n00:00:05,000 --> 00:00:06,000\nnarration cue\n", encoding="utf-8")
        narration["narration_srt_sha256"] = sha256(self.srt)
        normalized, total = builder.normalize_cards(cards)
        with tempfile.TemporaryDirectory() as temporary:
            records = builder.copy_card_media(normalized, Path(temporary) / "Media", "TECH")
            document = builder.build_document(template_document(), normalized, total, records, "TECH")
        video_segment = document["tracks"][0]["segments"][1]
        audio_tracks = [row for row in document["tracks"] if row.get("type") == "audio"]
        self.assertEqual(video_segment["volume"], 0.0)
        self.assertEqual(len(document["materials"]["audios"]), 1)
        self.assertEqual(len(audio_tracks), 1)
        self.assertEqual(audio_tracks[0]["segments"][0]["target_timerange"], {"start": 5 * MICROS, "duration": MICROS})
        self.assertEqual(records["C002"]["narration_audio"]["sha256"], self.hashes["narration_wav"])
        lowers = builder.capture_presentation_contract(document, normalized)["lower_slots"]
        self.assertEqual([(row["text"], row["target_timerange"]) for row in lowers], [("narration cue", {"start": 5 * MICROS, "duration": MICROS})])

    def test_25_narration_image_builds_image_one_audio_segment_and_srt_lower(self):
        cards = self.cards()
        source, narration = cards["cards"][2], cards["cards"][1]
        source.update({"target_start_us": 0, "target_duration_us": 5 * MICROS, "source_duration_us": 5 * MICROS})
        narration.update({"target_start_us": 5 * MICROS, "lower_mode": "SRT"})
        cards["cards"] = [source, narration]
        self.srt.write_text("1\n00:00:05,000 --> 00:00:06,000\nimage narration\n", encoding="utf-8")
        narration["narration_srt_sha256"] = sha256(self.srt)
        normalized, total = builder.normalize_cards(cards)
        with tempfile.TemporaryDirectory() as temporary:
            records = builder.copy_card_media(normalized, Path(temporary) / "Media", "TECH")
            document = builder.build_document(template_document(), normalized, total, records, "TECH")
        self.assertEqual(document["tracks"][0]["segments"][1]["volume"], 0.0)
        self.assertEqual(len(document["materials"]["audios"]), 1)
        self.assertEqual(len([row for row in document["tracks"] if row.get("type") == "audio"][0]["segments"]), 1)
        self.assertEqual(builder.capture_presentation_contract(document, normalized)["lower_slots"][0]["text"], "image narration")

    def test_26_narration_srt_cue_cannot_escape_card_when_audio_has_nonzero_source_offset(self):
        cards = self.cards()
        cards["cards"][1].update({"audio_start_us": MICROS, "audio_duration_us": MICROS})
        self.srt.write_text("1\n00:00:06,100 --> 00:00:06,200\noutside card\n", encoding="utf-8")
        cards["cards"][1]["narration_srt_sha256"] = sha256(self.srt)
        with self.assertRaisesRegex(RuntimeError, "NARRATION_SRT_RANGE_INVALID"):
            self.validate(cards)

    def test_27_source_srt_mode_requires_at_least_one_parsed_cue(self):
        source = self.cards()["cards"][2]
        source.update({
            "target_start_us": 0, "target_duration_us": MICROS, "source_duration_us": MICROS,
            "lower_mode": "SRT", "source_srt_file": str(self.srt),
        })
        self.srt.write_text("", encoding="utf-8")
        source["source_srt_sha256"] = sha256(self.srt)
        with self.assertRaisesRegex(RuntimeError, "SRT_CUES_REQUIRED"):
            builder.normalize_cards({"cards": [source]})

    def test_28_narration_srt_mode_requires_at_least_one_parsed_cue(self):
        cards = self.cards()
        source, narration = cards["cards"][2], cards["cards"][1]
        source.update({"target_start_us": 0, "target_duration_us": 5 * MICROS, "source_duration_us": 5 * MICROS})
        narration.update({"target_start_us": 5 * MICROS, "lower_mode": "SRT"})
        self.srt.write_text("malformed subtitle without timing", encoding="utf-8")
        narration["narration_srt_sha256"] = sha256(self.srt)
        with self.assertRaisesRegex(RuntimeError, "SRT_CUES_REQUIRED"):
            builder.normalize_cards({"cards": [source, narration]})

    def test_29_timing_only_srt_is_rejected_for_source_and_narration_modes(self):
        source = self.cards()["cards"][2]
        source.update({
            "target_start_us": 0, "target_duration_us": MICROS, "source_duration_us": MICROS,
            "lower_mode": "SRT", "source_srt_file": str(self.srt),
        })
        self.srt.write_text("1\n00:00:00,000 --> 00:00:01,000\n\n", encoding="utf-8")
        source["source_srt_sha256"] = sha256(self.srt)
        with self.subTest(mode="SOURCE_TTS"), self.assertRaisesRegex(RuntimeError, "SRT_CUES_REQUIRED"):
            builder.normalize_cards({"cards": [source]})

        cards = self.cards()
        source, narration = cards["cards"][2], cards["cards"][1]
        source.update({"target_start_us": 0, "target_duration_us": 5 * MICROS, "source_duration_us": 5 * MICROS})
        narration.update({"target_start_us": 5 * MICROS, "lower_mode": "SRT"})
        self.srt.write_text("1\n00:00:05,000 --> 00:00:06,000\n\n", encoding="utf-8")
        narration["narration_srt_sha256"] = sha256(self.srt)
        with self.subTest(mode="NARRATION_TTS"), self.assertRaisesRegex(RuntimeError, "SRT_CUES_REQUIRED"):
            builder.normalize_cards({"cards": [source, narration]})


if __name__ == "__main__":
    unittest.main()
