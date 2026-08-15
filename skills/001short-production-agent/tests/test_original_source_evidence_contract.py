import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_capcut_grids import validate_grid, validate_grids


SCRIPT = SCRIPTS / "validate_capcut_grids.py"
ORIGINAL = SKILL / "tests" / "fixtures" / "original_grid_8.pass.md"
URAKKAI = SKILL / "tests" / "fixtures" / "urakkai_grid_8.pass.md"
CONTRACT_VERSION = "001short-original-source-transcript-v1"
RANGES = (
    ("B01", 0, 3_900_000, "케이크를 비춘다. 화면 OCR: 없음", "없음", '"케이크 상태가 이상해"', "없음"),
    ("B02", 3_900_000, 7_200_000, "팬케이크를 비춘다. 화면 OCR: PANCAKE", "없음", '"팬케이크에 분유"', "PANCAKE"),
    ("B03", 7_200_000, 10_400_000, "점심을 비춘다. 화면 OCR: 없음", "없음", '"점심도 분유 시리얼"', "없음"),
    ("B04", 10_400_000, 13_900_000, "질환을 설명한다. 화면 OCR: 없음", "없음", '"희귀면역질환 때문"', "없음"),
    ("B05", 13_900_000, 16_900_000, "장보기를 보여준다. 화면 OCR: 없음", "없음", '"한 달 장보기 공개"', "없음"),
    ("B06", 17_700_000, 21_600_000, "영양소를 보여준다. 화면 OCR: 없음", "없음", '"생존에 필요한 영양"', "없음"),
    ("B07", 21_600_000, 26_700_000, "식비를 보여준다. 화면 OCR: 50만원", "없음", '"한 달 50만원 식비"', "50만원"),
    ("B08", 26_700_000, 30_200_000, "두 음식으로 끝난다. 화면 OCR: 없음", "없음", '"이제 두 음식만 가능"', "없음"),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def versioned_episode(root: Path, *, write_evidence: bool = True) -> tuple[Path, Path]:
    episode = root / "260815_test_SOURCE"
    script_root = episode / "20_script"
    input_root = episode / "00_input"
    analysis_root = episode / "10_analysis"
    workflow_root = episode / "90_workflow"
    for directory in (script_root, input_root, analysis_root, workflow_root):
        directory.mkdir(parents=True, exist_ok=True)
    original = script_root / "original-capcut-grid.md"
    original.write_text(ORIGINAL.read_text(encoding="utf-8"), encoding="utf-8")
    (script_root / "urakkai-capcut-grid.md").write_text(URAKKAI.read_text(encoding="utf-8"), encoding="utf-8")

    source = input_root / "source.mp4"
    identity = input_root / "source_identity.json"
    transcript = analysis_root / "source-transcript.txt"
    audio = analysis_root / "source-audio.wav"
    source.write_bytes(b"source-media")
    transcript.write_text("verified source transcript", encoding="utf-8")
    audio.write_bytes(b"verified-source-audio")
    write_json(identity, {
        "schema_version": "source-identity-v1",
        "episode_id": episode.name,
        "source_id": "SOURCE",
        "source_fingerprint": sha(source),
        "media_path": "source.mp4",
        "media_sha256": sha(source),
    })
    receipt = input_root / "source_intake_receipt.json"
    write_json(receipt, {
        "schema_version": "001short-source-intake-receipt-v2",
        "episode_id": episode.name,
        "source_id": "SOURCE",
        "intake_kind": "DESKTOP",
        "source_locator": str(source.resolve()),
        "local_media_path": "source.mp4",
        "local_media_sha256": sha(source),
        "local_media_duration_us": 30_200_000,
        "source_identity_path": "source_identity.json",
        "source_identity_sha256": sha(identity),
        "original_analysis_contract_version": CONTRACT_VERSION,
    })

    evidence_path = analysis_root / "original-source-evidence.json"
    segments = []
    for segment_id, start, end, situation, speaker, narration, literal_ocr in RANGES:
        frame = analysis_root / f"{segment_id}.png"
        frame.write_bytes((segment_id + "-frame").encode("utf-8"))
        segments.append({
            "segment_id": segment_id,
            "source_range_us": [start, end],
            "keyframes": [{
                "path": f"10_analysis/{frame.name}",
                "sha256": sha(frame),
                "timestamp_us": start,
                "literal_ocr": literal_ocr,
            }],
            "transcript_evidence_path": "10_analysis/source-transcript.txt",
            "transcript_evidence_sha256": sha(transcript),
            "audio_evidence_path": "10_analysis/source-audio.wav",
            "audio_evidence_sha256": sha(audio),
            "classified_fields": {
                "situation_description": situation,
                "speaker_statement": speaker,
                "narration": narration,
                "tts_speaker_statement": "없음",
                "tts_narration": "없음",
            },
        })
    if write_evidence:
        write_json(evidence_path, {
            "schema_version": "001short-original-source-evidence-v1",
            "contract_version": CONTRACT_VERSION,
            "episode_id": episode.name,
            "source_identity_path": "00_input/source_identity.json",
            "source_identity_sha256": sha(identity),
            "source_media_path": "00_input/source.mp4",
            "source_media_sha256": sha(source),
            "segments": segments,
        })
    state = workflow_root / "state.json"
    state_payload = {
        "episode_id": episode.name,
        "current_stage": "02",
        "status": "SOURCE_OCR_VERIFIED",
        "original_analysis_contract_version": CONTRACT_VERSION,
    }
    if write_evidence:
        state_payload.update({
            "original_source_evidence_path": "10_analysis/original-source-evidence.json",
            "original_source_evidence_sha256": sha(evidence_path),
        })
    write_json(state, state_payload)
    return original, state


class OriginalSourceEvidenceContractTest(unittest.TestCase):
    def test_a_unresolved_situation_is_rejected_even_when_ocr_is_none(self):
        text = ORIGINAL.read_text(encoding="utf-8").replace(
            "(상황설명) 케이크를 비춘다. 화면 OCR: 없음",
            "(상황설명) 미확인. 화면 OCR: 없음",
            1,
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "original.md"
            path.write_text(text, encoding="utf-8")
            _grid, errors = validate_grid(path, "original")
        self.assertIn("ORIGINAL_TRANSCRIPT_UNVERIFIED", {row["code"] for row in errors})

    def test_b_versioned_stage02_rejects_transcript_text_not_bound_to_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            original, _state = versioned_episode(Path(td))
            original.write_text(
                original.read_text(encoding="utf-8").replace(
                    "화면 OCR: PANCAKE", "화면 OCR: TOTALLY INVENTED", 1
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--original", str(original), "--original-only"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ORIGINAL_TRANSCRIPT_EVIDENCE_MISMATCH", completed.stdout)

    def test_b_versioned_stage02_rejects_invented_speaker_statement(self):
        with tempfile.TemporaryDirectory() as td:
            original, _state = versioned_episode(Path(td))
            original.write_text(
                original.read_text(encoding="utf-8").replace(
                    '"화자발언" 없음', '"화자발언" "TOTALLY INVENTED"', 1
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--original", str(original), "--original-only"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ORIGINAL_TRANSCRIPT_EVIDENCE_MISMATCH", completed.stdout)

    def test_b_versioned_stage02_accepts_sha_bound_matching_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            original, _state = versioned_episode(Path(td))
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--original", str(original), "--original-only"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_b_versioned_stage02_rejects_tampered_keyframe(self):
        with tempfile.TemporaryDirectory() as td:
            original, _state = versioned_episode(Path(td))
            (original.parent.parent / "10_analysis" / "B01.png").write_bytes(b"tampered")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--original", str(original), "--original-only"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ORIGINAL_SOURCE_KEYFRAME_INVALID", completed.stdout)

    def test_c_legacy_grid_without_version_or_transcript_still_validates(self):
        source = ORIGINAL.read_text(encoding="utf-8")
        legacy = "# 원본표\n\n" + source[source.index("| 레이어 \\ 원본 시간 |") :]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "original.md"
            path.write_text(legacy, encoding="utf-8")
            result = validate_grids(path, URAKKAI)
        self.assertEqual(result["status"], "PASS", result)
        self.assertNotIn("원본 5분류 대본", result["original"].markdown())

    def test_c_versioned_stage02_cannot_omit_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            original, _state = versioned_episode(Path(td), write_evidence=False)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--original", str(original), "--original-only"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ORIGINAL_SOURCE_EVIDENCE_REQUIRED", completed.stdout)

    def test_c_intake_v2_and_state_must_share_contract_version(self):
        with tempfile.TemporaryDirectory() as td:
            original, _state = versioned_episode(Path(td))
            receipt = original.parent.parent / "00_input" / "source_intake_receipt.json"
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            del payload["original_analysis_contract_version"]
            write_json(receipt, payload)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--original", str(original), "--original-only"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ORIGINAL_ANALYSIS_CONTRACT_VERSION_MISMATCH", completed.stdout)


if __name__ == "__main__":
    unittest.main()
