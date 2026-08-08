from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_audio_caption import validate_audio_caption
import test_vocal_stem_contract as vocal_fixtures
from test_vocal_stem_contract import sha256


SRT = (
    "ST01\n00:00:00,000 --> 00:00:00,120\n상황 하나\n\n"
    "SP01\n00:00:00,000 --> 00:00:00,200\n화자 발언\n\n"
    "ST02\n00:00:00,120 --> 00:00:00,300\n상황 둘\n"
)
CUES = [
    {"cue_id": "ST01", "start_us": 0, "end_us": 120000, "text": "상황 하나", "layer": "STATE"},
    {"cue_id": "SP01", "start_us": 0, "end_us": 200000, "text": "화자 발언", "layer": "A10_TEXT"},
    {"cue_id": "ST02", "start_us": 120000, "end_us": 300000, "text": "상황 둘", "layer": "STATE"},
]


class CaptionCueLayerTest(unittest.TestCase):
    def _locks(self, root: Path, cues: list[dict], srt_text: str = SRT) -> tuple[Path, Path]:
        _, vocals, manifest = vocal_fixtures.VocalStemContractTest()._fixture(root)
        duration = json.loads(manifest.read_text(encoding="utf-8"))["vocals_duration_us"]
        audio_lock = root / "audio_lock.json"
        audio_lock.write_text(json.dumps({
            "schema_version": "001short-audio-lock-v3", "episode_id": "SH_VOCAL_TEST",
            "status": "PASS", "audio_source": "SOURCE_VOCAL_STEM", "audio_path": vocals.name,
            "audio_sha256": sha256(vocals), "measured_duration_us": duration,
            "audio_codec": "pcm_s16le", "ffprobe_verified": True,
            "vocal_stem_manifest_path": manifest.name, "vocal_stem_manifest_sha256": sha256(manifest),
            "role_files": [{
                "role": "A10", "audio_path": vocals.name, "audio_sha256": sha256(vocals),
                "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
            }],
        }), encoding="utf-8")
        srt = root / "final.srt"
        srt.write_text(srt_text, encoding="utf-8")
        caption = root / "caption_lock.json"
        caption.write_text(json.dumps({
            "schema_version": "001short-caption-lock-v1", "episode_id": "SH_VOCAL_TEST",
            "status": "PASS", "audio_lock_path": audio_lock.name,
            "audio_lock_sha256": sha256(audio_lock), "final_srt_path": srt.name,
            "final_srt_sha256": sha256(srt), "final_cue_count": len(cues), "cues": cues,
            "all_cues_within_measured_audio": True, "no_overlap_verified": True,
        }), encoding="utf-8")
        return audio_lock, caption

    def test_cues_on_distinct_layers_may_overlap(self):
        with tempfile.TemporaryDirectory() as temporary:
            audio_lock, caption = self._locks(Path(temporary), CUES)
            self.assertEqual(validate_audio_caption(audio_lock, caption)["status"], "PASS")

    def test_cues_on_same_layer_still_reject_overlap(self):
        with tempfile.TemporaryDirectory() as temporary:
            cues = [dict(cue, layer="STATE") for cue in CUES]
            audio_lock, caption = self._locks(Path(temporary), cues)
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_CUE_OVERLAP", {row["code"] for row in result["errors"]})

    def test_cues_without_layer_keep_single_sequence_behaviour(self):
        with tempfile.TemporaryDirectory() as temporary:
            cues = [{k: v for k, v in cue.items() if k != "layer"} for cue in CUES]
            audio_lock, caption = self._locks(Path(temporary), cues)
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_CUE_OVERLAP", {row["code"] for row in result["errors"]})

    def test_arbitrary_layer_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            cues = [dict(CUES[0], layer="FAKE_LAYER"), *CUES[1:]]
            audio_lock, caption = self._locks(Path(temporary), cues)
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_CAPTION_LOCK_SCHEMA", {row["code"] for row in result["errors"]})

    def test_available_caption_role_must_match_layer(self):
        with tempfile.TemporaryDirectory() as temporary:
            cues = [dict(cue) for cue in CUES]
            cues[1]["caption_role"] = "STATE"
            audio_lock, caption = self._locks(Path(temporary), cues)
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_CUE_LAYER_ROLE_MISMATCH", {row["code"] for row in result["errors"]})

    def test_caption_role_without_layer_keeps_legacy_sequence(self):
        with tempfile.TemporaryDirectory() as temporary:
            cue = {k: v for k, v in CUES[0].items() if k != "layer"}
            cue["caption_role"] = "STATE"
            srt = "ST01\n00:00:00,000 --> 00:00:00,120\n상황 하나\n"
            cue["text"] = "상황 하나"
            audio_lock, caption = self._locks(Path(temporary), [cue], srt)
            self.assertEqual(validate_audio_caption(audio_lock, caption)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
