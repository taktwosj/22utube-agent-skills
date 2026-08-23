import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
GRID_ORIGINAL = SKILL / "tests" / "fixtures" / "original_grid_8.pass.md"
GRID_URAKKAI = SKILL / "tests" / "fixtures" / "urakkai_grid_8.pass.md"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import validate_design_lock


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def install_valid_grids(episode: Path, *, mixed: bool = False) -> None:
    script_root = episode / "20_script"
    script_root.mkdir(parents=True, exist_ok=True)
    a9 = ("narration", "비움") if mixed else ("비움", "비움")
    yellow = ("비움", "there") if mixed else ("비움", "비움")
    rows = (
        ("T1", "title", "title"),
        ("T2", "subtitle", "subtitle"),
        ("A9_TEXT", *a9),
        ("A10_TEXT_YELLOW", *yellow),
        ("A10_TEXT_WHITE", "hello", "비움"),
        ("STATE_LASER", "비움", "비움"),
        ("STATE_GLITCH", "비움", "비움"),
        ("SOURCE_CREDIT", "비움", "비움"),
        ("SCREEN_WHITE", "템플릿 유지", "템플릿 유지"),
        ("SCREEN_EFFECT", "W Flash", "W Flash"),
        ("VIDEO", "장면2", "장면1"),
        ("A9", *a9),
        ("A10", "분리 음성", "분리 음성"),
        ("A11", "비움", "비움"),
        ("A12_RESERVED_EMPTY", "비움", "비움"),
    )
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    transcript = """## 원본 5분류 대본

### B01 0.0–1.0
(상황설명) 첫 장면. 화면 OCR: 없음
\"화자발언\" \"hello\"
<나레이션> 없음
TTS화자발언 없음
TTS나레이션 없음

### B02 1.0–2.0
(상황설명) 둘째 장면. 화면 OCR: 없음
\"화자발언\" \"there\"
<나레이션> 없음
TTS화자발언 없음
TTS나레이션 없음

"""
    original = transcript + "| 레이어 \\ 원본 시간 | B01 0.0–1.0 | B02 1.0–2.0 |\n|---|---|---|\n" + body + "\n"
    urakkai = "| 레이어 \\ 목표 시간 | V01 0.0–1.0 B02 | V02 1.0–2.0 B01 |\n|---|---|---|\n" + body + "\n"
    (script_root / "original-capcut-grid.md").write_text(original, encoding="utf-8")
    (script_root / "urakkai-capcut-grid.md").write_text(urakkai, encoding="utf-8")


def bind_state_artifacts(
    state: Path,
    *,
    timeline: Path,
    build_manifest: Path,
    design_evidence: Path,
    audio_lock: Path,
    caption_lock: Path,
) -> None:
    episode = build_manifest.parent
    manifest_payload = json.loads(build_manifest.read_text(encoding="utf-8"))
    audio_payload = json.loads(audio_lock.read_text(encoding="utf-8"))
    caption_payload = json.loads(caption_lock.read_text(encoding="utf-8"))
    timeline_payload = json.loads(timeline.read_text(encoding="utf-8"))
    timeline_cues = {row.get("cue_id"): row for row in timeline_payload["segments"] if row.get("cue_id")}
    for cue in caption_payload.get("cues", []):
        row = timeline_cues[cue["cue_id"]]
        cue["start_us"], cue["end_us"] = row["start"], row["start"] + row["duration"]
    def srt_stamp(value: int) -> str:
        milliseconds = value // 1000
        hours, milliseconds = divmod(milliseconds, 3_600_000)
        minutes, milliseconds = divmod(milliseconds, 60_000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    srt_path = audio_lock.parent / caption_payload["final_srt_path"]
    srt_path.write_text("\n\n".join(
        f"{cue['cue_id']}\n{srt_stamp(cue['start_us'])} --> {srt_stamp(cue['end_us'])}\n{cue['text']}"
        for cue in caption_payload.get("cues", [])
    ) + "\n", encoding="utf-8")
    caption_payload["final_srt_sha256"] = sha(srt_path)
    clips = manifest_payload["urakkai"]["video_clips"]
    mixed = any(row.get("role") == "A9" for row in audio_payload.get("role_files", []))
    policy = "A9_TTS_PLUS_A10_REASSEMBLED" if mixed else "A10_REASSEMBLED_SYNC"
    asset_key = "source_video" if manifest_payload["visual_asset_mode"] == "SOURCE_VIDEO_PROVISIONAL" else "clean_video"
    plan_rows = []
    for index, clip in enumerate(clips):
        placements = [
            {"anchor": "VIDEO", "operation": "replace_media_and_range", "asset_key": asset_key, "source_range_us": clip["source_range_us"], "target_range_us": clip["target_range_us"], "volume": 1},
            {"anchor": "A10", "operation": "replace_media_and_range", "asset_key": "reassembled_vocals", "source_range_us": clip["source_range_us"], "target_range_us": clip["target_range_us"], "volume": 0 if mixed and index == 0 else 1},
        ]
        if mixed and index == 0:
            placements.append({"anchor": "A9", "operation": "replace_media_and_range", "asset_key": "tts", "source_range_us": [0, 1_000_000], "target_range_us": [0, 1_000_000], "volume": 1})
        plan_rows.append({"segment_key": clip["clip_id"], "source_beat_id": "B02" if index == 0 else "B01", "target_segment_id": f"V{index + 1:02d}", "target_range_us": clip["target_range_us"], "placements": placements})
    plan = episode / "production_plan.json"
    write(plan, {
        "schema_version": "001short-production-plan-v2", "episode_id": "EP", "root_profile": "home_windows",
        "project_name": "project", "production_mode": "URAKKAI", "audio_policy": policy,
        "audio_source": "REASSEMBLED_VOCAL_STEM", "visual_asset_mode": manifest_payload["visual_asset_mode"],
        "total_duration_us": manifest_payload["urakkai"]["target_duration_us"],
        "original_order": ["V1", "V2"], "order_signature": [clip["clip_id"] for clip in clips], "timeline": plan_rows,
    })
    reassembled = episode / "reassembled_stem_manifest.json"
    write(reassembled, {
        "schema_version": "001short-reassembled-stem-manifest-v2", "status": "PASS", "episode_id": "EP",
        "full_stem_manifest_path": audio_payload["vocal_stem_manifest_path"],
        "full_stem_manifest_sha256": audio_payload["vocal_stem_manifest_sha256"],
        "build_manifest_path": str(build_manifest), "build_manifest_sha256": sha(build_manifest),
        "production_plan_path": str(plan), "production_plan_sha256": sha(plan),
        "production_plan_path": str(plan), "production_plan_sha256": sha(plan),
        "reassembled_audio_path": audio_payload["audio_path"], "reassembled_audio_sha256": audio_payload["audio_sha256"],
        "target_duration_us": audio_payload["measured_duration_us"],
        "mapping": [{"source_beat_id": "B02" if index == 0 else "B01", "target_segment_id": f"V{index + 1:02d}", "source_range_us": clip["source_range_us"], "target_range_us": clip["target_range_us"]} for index, clip in enumerate(clips)],
    })
    identity = episode / "source_identity.json"
    audio_payload.update({
        "schema_version": "001short-audio-lock-v4", "production_mode": "URAKKAI", "audio_policy": policy,
        "audio_source": "REASSEMBLED_VOCAL_STEM", "source_identity_path": str(identity),
        "source_identity_sha256": sha(identity), "reassembled_stem_manifest_path": str(reassembled),
        "reassembled_stem_manifest_sha256": sha(reassembled),
    })
    write(audio_lock, audio_payload)
    original_grid = episode / "20_script" / "original-capcut-grid.md"
    urakkai_grid = episode / "20_script" / "urakkai-capcut-grid.md"
    timing = episode / "caption_timing_evidence.json"
    mapping = [{"mapping_id": f"M{index + 1}", "source_beat_id": "B02" if index == 0 else "B01", "target_segment_id": f"V{index + 1:02d}", "source_range_us": clip["source_range_us"], "target_range_us": clip["target_range_us"]} for index, clip in enumerate(clips)]
    cue_receipts = []
    for cue in caption_payload.get("cues", []):
        map_index = 0 if cue["start_us"] < 1_000_000 else 1
        selected_mapping = mapping[map_index]
        source_start = selected_mapping["source_range_us"][0] + cue["start_us"] - selected_mapping["target_range_us"][0]
        source_range = [source_start, source_start + cue["end_us"] - cue["start_us"]]
        cue_receipts.append({
            "cue_id": cue["cue_id"], "text": cue["text"],
            "authority": "TTS" if cue.get("layer") == "A9_TEXT" else "SPEECH_AUDIO",
            "mapping_id": mapping[map_index]["mapping_id"], "source_range_us": source_range,
            "target_range_us": [cue["start_us"], cue["end_us"]],
            "bound_file_path": audio_payload["audio_path"], "bound_file_sha256": audio_payload["audio_sha256"],
        })
    write(timing, {
        "schema_version": "001short-caption-timing-evidence-v2", "status": "PASS", "episode_id": "EP",
        "source_identity_path": str(identity), "source_identity_sha256": sha(identity),
        "approved_timeline_path": str(timeline), "approved_timeline_sha256": sha(timeline),
        "build_manifest_path": str(build_manifest), "build_manifest_sha256": sha(build_manifest),
        "production_plan_path": str(plan), "production_plan_sha256": sha(plan),
        "original_grid_path": str(original_grid), "original_grid_sha256": sha(original_grid),
        "urakkai_grid_path": str(urakkai_grid), "urakkai_grid_sha256": sha(urakkai_grid),
        "tolerance_us": 0, "zero_caption": not caption_payload.get("cues"), "mapping": mapping, "cues": cue_receipts,
    })
    caption_payload.update({
        "schema_version": "001short-caption-lock-v2", "audio_lock_sha256": sha(audio_lock),
        "caption_timing_evidence_path": str(timing), "caption_timing_evidence_sha256": sha(timing),
    })
    write(caption_lock, caption_payload)
    receipt = state.parent / "production_plan_validation.json"
    write(receipt, {"status": "PASS", "errors": [], "evidence": {"episode_id": "EP", "production_plan_path": str(plan), "production_plan_sha256": sha(plan)}})
    payload = json.loads(state.read_text(encoding="utf-8"))
    payload.update({
        "approved_timeline_path": str(timeline),
        "approved_timeline_sha256": sha(timeline),
        "build_manifest_path": str(build_manifest),
        "build_manifest_sha256": sha(build_manifest),
        "design_lock_evidence_path": str(design_evidence),
        "design_lock_evidence_sha256": sha(design_evidence),
        "audio_lock_path": str(audio_lock),
        "audio_lock_sha256": sha(audio_lock),
        "caption_lock_path": str(caption_lock),
        "caption_lock_sha256": sha(caption_lock),
        "production_plan_path": str(plan),
        "production_plan_sha256": sha(plan),
        "production_plan_validation_receipt_path": str(receipt),
        "production_plan_validation_receipt_sha256": sha(receipt),
    })
    write(state, payload)


def media(root: Path) -> tuple[Path, Path]:
    source, vocals = root / "source.mp4", root / "vocals.wav"
    subprocess.run([
        # Deliberately not the template's 1080x1920, so a stale material size shows up.
        "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=540x960:r=30:d=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-shortest", "-y", str(source),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", "-y", str(vocals),
    ], check=True)
    return source, vocals


def template_archive(root: Path) -> tuple[Path, Path, Path]:
    template = root / "template"
    resources = template / "Resources" / "media"
    resources.mkdir(parents=True)
    (resources / "transparent_center_white_1080x1920.png").write_bytes(b"png")
    rich = json.dumps({"text": "seed", "styles": [{"range": [0, 4]}]})
    materials = []
    tracks = []
    for index, role in enumerate(builder.ROLE_BY_TRACK):
        material_id = f"material-{index}"
        if role == "VIDEO":
            material = {"id": material_id, "type": "video", "path": "##_draftpath_placeholder_test_##/Resources/media/transparent_center_white_1080x1920.png"}
        elif role == "SCREEN_WHITE":
            # Real shrt_white_base_v2 points here at CapCut's cache before the
            # builder must replace it with the project-local PNG.
            material = {"id": material_id, "type": "photo", "path": "C:/Users/test/AppData/Local/CapCut/User Data/Cache/onlineMaterial/white.png"}
        elif role == "SCREEN_EFFECT":
            material = {"id": material_id, "type": "video_effect", "path": ""}
        elif role in {"A9", "A10", "A11", "A12_RESERVED_EMPTY"}:
            material = {"id": material_id, "type": "music", "path": ""}
        else:
            material = {"id": material_id, "type": "text", "content": rich}
        materials.append(material)
        segments = [{
            "id": f"seed-{index}", "material_id": material_id,
            "target_timerange": {"start": 0, "duration": 2_000_000},
            "source_timerange": {"start": 0, "duration": 2_000_000},
        }]
        tracks.append({"id": f"track-{index}", "segments": segments})
    content = {
        "id": "timeline-template", "main_timeline_id": "timeline-template",
        "duration": 2_000_000, "tracks": tracks, "materials": {"items": materials},
    }
    write(template / "draft_content.json", content)
    write(template / "draft_meta_info.json", {"draft_id": "draft-template", "tm_duration": 2_000_000})
    write(template / "Timelines" / "project.json", {
        "id": "project-template", "project_id": "project-template", "draft_id": "draft-template",
        "main_timeline_id": "timeline-template", "timelines": [{"id": "timeline-template"}],
    })
    write(template / "Timelines" / "timeline-template" / "draft_content.json", content)
    archive = root / "root.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        for path in template.rglob("*"):
            if path.is_file():
                zipped.write(path, Path("template") / path.relative_to(template))
    manifest = root / "root_manifest.json"
    write(manifest, {"sha256": sha(archive), "template_profile": "shrt_white_base_v2"})
    contract = root / "root_contract.json"
    write(contract, {
        "schema_version": "shorts-capcut-root-contract-v1", "workspace_relative": True,
        "assembly_mode": "clean_staging_copy", "profiles": {"home_windows": {
            "archive_relative_path": archive.name, "manifest_relative_path": manifest.name,
            "archive_sha256": sha(archive), "template_profile": "shrt_white_base_v2",
        }},
    })
    return archive, manifest, contract


class PublicBuilderProvisionalTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "media tools required")
    def test_public_builder_finishes_source_provisional_with_real_gates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve(); episode = root / "episode"; episode.mkdir()
            install_valid_grids(episode)
            source, vocals = media(root)
            archive, _, contract = template_archive(root)
            identity = episode / "source_identity.json"
            write(identity, {
                "schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "SRC",
                "source_fingerprint": "fp", "media_path": str(source), "media_sha256": sha(source),
            })
            rows = [
                {"segment_id": "V2", "timeline_order": 0, "role": "VIDEO", "start": 0, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "V1", "timeline_order": 1, "role": "VIDEO", "start": 1_000_000, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "T2", "timeline_order": 2, "role": "T2", "start": 0, "duration": 2_000_000, "source_ref": "SRC", "text": "subtitle", "content_type": "TITLE"},
                {"segment_id": "T1", "timeline_order": 3, "role": "T1", "start": 0, "duration": 2_000_000, "source_ref": "SRC", "text": "title", "content_type": "TITLE"},
                {"segment_id": "SCR_FX", "timeline_order": 4, "role": "SCREEN_EFFECT", "start": 0, "duration": 2_000_000, "source_ref": "SRC"},
                {"segment_id": "SCR_WHITE", "timeline_order": 5, "role": "SCREEN_WHITE", "start": 0, "duration": 2_000_000, "source_ref": "SRC"},
                {"segment_id": "SP1", "timeline_order": 6, "role": "A10_TEXT", "start": 0, "duration": 1_000_000, "source_ref": "SRC", "source_range_us": [1_000_000, 2_000_000], "cue_id": "1", "text": "hello", "content_type": "SPEAKER", "caption_role": "A10_TEXT", "speaker_id": "P1", "color_role": "WHITE"},
                {"segment_id": "A10-1", "timeline_order": 7, "role": "A10", "start": 0, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "A10-2", "timeline_order": 8, "role": "A10", "start": 1_000_000, "duration": 1_000_000, "source_ref": "SRC"},
            ]
            timeline = episode / "approved_timeline.json"
            write(timeline, {"schema_version": "approved-timeline-v1", "episode_id": "EP", "source_fingerprint": "fp", "production_mode": "URAKKAI", "audio_policy": "A10_REASSEMBLED_SYNC", "primary_speaker_id": "P1", "segments": rows})
            handoff = episode / "design_handoff.json"
            write(handoff, {
                "schema_version": "tikitaka-design-handoff-v1", "episode_id": "EP", "status": "PASS",
                "source_identity_path": identity.name, "source_identity_sha256": sha(identity),
                "timeline_path": timeline.name, "timeline_sha256": sha(timeline), "source_fingerprint": "fp",
                "approved_timeline_order": [row["segment_id"] for row in rows],
            })
            evidence = episode / "design_evidence.json"
            self.assertEqual(validate_design_lock.validate_handoff(handoff, identity, timeline, evidence)["status"], "PASS")
            vocal_manifest = episode / "vocal_stem_manifest.json"
            write(vocal_manifest, {
                "schema_version": "001short-vocal-stem-manifest-v1", "status": "STEM_GENERATED", "episode_id": "EP",
                "source_path": str(source), "source_sha256": sha(source), "source_duration_us": 2_000_000,
                "separator": {"engine": "demucs", "model": "htdemucs", "python_executable": "python"},
                "vocals_path": str(vocals), "vocals_sha256": sha(vocals), "vocals_duration_us": 2_000_000,
                "vocals_codec": "pcm_s16le", "vocals_ffprobe_verified": True, "capcut_audio_role": "A10",
                "capcut_allowed_audio_path": str(vocals), "a12_policy": "EMPTY", "human_listen_qc_required": True,
            })
            audio_lock = episode / "audio_lock.json"
            audio_file = {"audio_path": str(vocals), "audio_sha256": sha(vocals), "measured_duration_us": 2_000_000, "audio_codec": "pcm_s16le", "ffprobe_verified": True}
            write(audio_lock, {"schema_version": "001short-audio-lock-v3", "episode_id": "EP", "status": "PASS", "audio_source": "SOURCE_VOCAL_STEM", **audio_file, "vocal_stem_manifest_path": vocal_manifest.name, "vocal_stem_manifest_sha256": sha(vocal_manifest), "role_files": [{"role": "A10", **audio_file}]})
            srt = episode / "final.srt"; srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")
            caption = episode / "caption_lock.json"
            write(caption, {"schema_version": "001short-caption-lock-v1", "episode_id": "EP", "status": "PASS", "audio_lock_path": audio_lock.name, "audio_lock_sha256": sha(audio_lock), "final_srt_path": srt.name, "final_srt_sha256": sha(srt), "final_cue_count": 1, "cues": [{"cue_id": "1", "start_us": 0, "end_us": 1_000_000, "text": "hello", "layer": "A10_TEXT", "caption_role": "A10_TEXT"}], "all_cues_within_measured_audio": True, "no_overlap_verified": True})
            state = episode / "90_workflow" / "state.json"
            write(state, {"episode_id": "EP", "current_stage": "08", "status": "AUDIO_CAPTION_VALIDATED", "audio_lock_path": str(audio_lock), "audio_lock_sha256": sha(audio_lock), "caption_lock_path": str(caption), "caption_lock_sha256": sha(caption)})
            build_manifest = episode / "build_manifest.json"
            write(build_manifest, {"schema_version": "001short-build-manifest-v1", "episode_id": "EP", "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL", "source": {"path": str(source), "sha256": sha(source), "duration_us": 2_000_000}, "template": {"root_name": "shrt white", "root_zip_path": str(archive), "root_zip_sha256": sha(archive)}, "urakkai": {"production_type": "URAKKAI", "target_duration_us": 2_000_000, "reorder_required": True, "locked_permutation": ["V2", "V1"], "video_clips": [{"clip_id": "V2", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]}, {"clip_id": "V1", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]}]}, "source_audio": [{"clip_id": "V2", "mode": "on", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]}, {"clip_id": "V1", "mode": "on", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]}]})
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            config = {"episode_id": "EP", "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL", "duration_us": 2_000_000, "T1": "title", "T2": "subtitle", "state_cues": [], "project_name": "project", "episode_root": str(episode), "work_root": str(root / "work"), "local_capcut_root": str(root / "capcut"), "source_identity_path": str(identity), "approved_timeline_path": str(timeline), "design_handoff_path": str(handoff), "design_lock_evidence_path": str(evidence), "build_manifest_path": str(build_manifest), "state_path": str(state), "production_mode": "URAKKAI", "audio_policy": "A10_REASSEMBLED_SYNC", "root_contract_path": contract.name, "workspace_root": str(root), "root_profile": "home_windows"}
            assembled = episode / "reassembled_stem_manifest.json"
            def rebind_tampered_assembled(payload: dict) -> None:
                write(assembled, payload)
                audio_payload = json.loads(audio_lock.read_text(encoding="utf-8")); audio_payload["reassembled_stem_manifest_sha256"] = sha(assembled); write(audio_lock, audio_payload)
                caption_payload = json.loads(caption.read_text(encoding="utf-8")); caption_payload["audio_lock_sha256"] = sha(audio_lock); write(caption, caption_payload)
                state_payload = json.loads(state.read_text(encoding="utf-8")); state_payload.update(audio_lock_sha256=sha(audio_lock), caption_lock_sha256=sha(caption)); write(state, state_payload)
            tampered = json.loads(assembled.read_text(encoding="utf-8"))
            tampered["mapping"][0].update(source_beat_id="B99", target_segment_id="V99")
            rebind_tampered_assembled(tampered)
            with self.assertRaisesRegex(ValueError, "AUDIO_CAPTION_REASSEMBLED_STEM_AUTHORITY_MISMATCH"):
                builder.validate_grid_harness(config)
            self.assertFalse((root / "work").exists())
            bind_state_artifacts(state, timeline=timeline, build_manifest=build_manifest, design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption)
            foreign_plan = episode / "foreign_plan.json"; write(foreign_plan, json.loads((episode / "production_plan.json").read_text(encoding="utf-8")))
            foreign = json.loads(assembled.read_text(encoding="utf-8")); foreign.update(production_plan_path=str(foreign_plan), production_plan_sha256=sha(foreign_plan))
            rebind_tampered_assembled(foreign)
            with self.assertRaisesRegex(ValueError, "AUDIO_CAPTION_REASSEMBLED_STEM_AUTHORITY_MISMATCH"):
                builder.validate_grid_harness(config)
            self.assertFalse((root / "work").exists())
            bind_state_artifacts(state, timeline=timeline, build_manifest=build_manifest, design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption)
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                result = builder.build_episode(config)
            normalized = json.loads((root / "capcut" / "project" / "draft_content.json").read_text(encoding="utf-8"))
            self.assertEqual(len(normalized["tracks"]), 15)
            self.assertEqual(normalized["tracks"][14]["segments"], [])
            self.assertFalse(any(
                row.get("role") in {"A12", "A12_RESERVED_EMPTY"}
                for row in normalized["materials"]["items"]
            ))
            self.assertTrue(normalized["config"]["video_mute"])
            self.assertTrue(all(row.get("volume") == 0.0 for row in normalized["tracks"][0]["segments"]))
            self.assertEqual(
                builder.validate_postbuild.validate_postbuild(build_manifest, root / "capcut" / "project")["status"],
                "PASS",
            )
            video_mute_disabled = json.loads(json.dumps(normalized))
            video_mute_disabled["config"]["video_mute"] = False
            write(root / "capcut" / "project" / "draft_content.json", video_mute_disabled)
            self.assertIn(
                {"code": "E_DRAFT_MISMATCH", "detail": "video_mute"},
                builder.validate_postbuild.validate_postbuild(build_manifest, root / "capcut" / "project")["errors"],
            )
            video_volume_enabled = json.loads(json.dumps(normalized))
            video_volume_enabled["tracks"][0]["segments"][0]["volume"] = 1.0
            write(root / "capcut" / "project" / "draft_content.json", video_volume_enabled)
            self.assertIn(
                {"code": "E_DRAFT_MISMATCH", "detail": "video_volume", "clip_id": "V2"},
                builder.validate_postbuild.validate_postbuild(build_manifest, root / "capcut" / "project")["errors"],
            )
            write(root / "capcut" / "project" / "draft_content.json", normalized)
            # A10 plays the timeline-aligned stem, so with no capcut_source_range_us
            # its source range must follow the target range, not the original media's.
            a10 = sorted(
                normalized["tracks"][12]["segments"],
                key=lambda row: row["target_timerange"]["start"],
            )
            self.assertEqual(
                [(row["source_timerange"]["start"], row["source_timerange"]["duration"]) for row in a10],
                [(0, 1_000_000), (1_000_000, 1_000_000)],
            )
            self.assertEqual(
                [(row["target_timerange"]["start"], row["target_timerange"]["duration"]) for row in a10],
                [(0, 1_000_000), (1_000_000, 1_000_000)],
            )
            materials = {
                row["id"]: row for container in normalized["materials"].values()
                if isinstance(container, list) for row in container if isinstance(row, dict)
            }
            a10_material = materials[a10[0]["material_id"]]
            self.assertEqual(a10_material["name"], "a10_vocal_stem.wav")
            self.assertTrue(a10_material["path"].endswith("/Resources/media/a10_vocal_stem.wav"))
            white = normalized["tracks"][2]["segments"]
            self.assertEqual(len(white), 1)
            white_material = materials[white[0]["material_id"]]
            self.assertEqual(white_material["path"], "##_draftpath_placeholder_test_##/Resources/media/transparent_center_white_1080x1920.png")
            self.assertTrue((root / "capcut" / "project" / "Resources" / "media" / "transparent_center_white_1080x1920.png").is_file())
            source_video = next(
                row
                for container in normalized["materials"].values() if isinstance(container, list)
                for row in container
                if isinstance(row, dict) and row.get("type") == "video"
                and str(row.get("path", "")).endswith("source.mp4")
            )
            self.assertEqual((source_video["width"], source_video["height"]), (540, 960))
            self.assertEqual(result["status"], "CAPCUT_STATIC_VALIDATED")
            self.assertEqual(result["visual_asset_mode"], "SOURCE_VIDEO_PROVISIONAL")
            self.assertFalse(result["upload_ready"])
            report = json.loads((episode / "50_capcut_project" / "build_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "CAPCUT_STATIC_VALIDATED")
            self.assertEqual(report["visual_asset_mode"], "SOURCE_VIDEO_PROVISIONAL")
            self.assertFalse(report["upload_ready"])
            self.assertEqual(Path(report["project_path"]), root / "capcut" / "project")
            self.assertEqual(Path(report["media_source_path"]), source.resolve())
            self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["current_stage"], "09")

            canonical_state_before_revisions = sha(state)
            canonical_build_manifest_before_revisions = sha(build_manifest)
            clean_root = episode / "40_assets_used"; clean_root.mkdir()
            user_clean_video = clean_root / "user_clean_video.mp4"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:s=360x640:r=30:d=2", "-y", str(user_clean_video)], check=True)
            user_override = clean_root / "user_clean_override.json"
            write(user_override, {
                "schema_version": "001short-user-clean-override-v1", "episode_id": "EP",
                "status": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                "episode_clean_source_path": user_clean_video.name,
                "clean_source_sha256": sha(user_clean_video), "clean_visual_ready_claim": False,
                "user_authority": {"evidence": "user supplied file", "exact_text": "use this clean video"},
            })
            revision_manifest = episode / "build_manifest.user-clean-v1.json"
            revision_manifest_payload = json.loads(build_manifest.read_text(encoding="utf-8"))
            revision_manifest_payload.update({
                "visual_asset_mode": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                "clean_source": {
                    "origin": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                    "output_path": str(user_clean_video), "output_sha256": sha(user_clean_video),
                    "user_clean_override_path": str(user_override),
                    "user_clean_override_sha256": sha(user_override),
                },
            })
            write(revision_manifest, revision_manifest_payload)
            revision_v1 = {
                **{key: value for key, value in config.items() if not key.startswith("_")},
                "revision_id": "v1",
                "visual_asset_mode": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                "clean_video": str(user_clean_video),
                "user_clean_override_path": str(user_override),
                "build_manifest_path": str(revision_manifest),
            }
            revision_config_path = root / "revision_v1_config.json"
            write(revision_config_path, revision_v1)
            output = io.StringIO()
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ), patch.object(sys, "argv", ["build_episode_capcut.py", "--config", str(revision_config_path)]), redirect_stdout(output):
                self.assertEqual(builder.main(), 0)
            v1_result = json.loads(output.getvalue())
            v1_project = root / "capcut" / "project_v1"
            v1_state = episode / "90_workflow" / "revisions" / "v1" / "state.json"
            self.assertEqual(Path(v1_result["project_path"]), v1_project)
            self.assertTrue(v1_state.is_file())
            v1_project_before_v2 = sha(v1_project / "draft_content.json")
            v1_state_before_v2 = sha(v1_state)
            self.assertEqual(sha(state), canonical_state_before_revisions)
            self.assertEqual(sha(build_manifest), canonical_build_manifest_before_revisions)

            invalid_revision = {
                **revision_v1, "revision_id": "v3",
                "user_clean_override_path": str(clean_root / "missing_override.json"),
            }
            with self.assertRaisesRegex((ValueError, RuntimeError), "USER_CLEAN_OVERRIDE"):
                builder.build_episode(invalid_revision)
            self.assertFalse((episode / "90_workflow" / "revisions" / "v3").exists())
            self.assertFalse((root / "capcut" / "project_v3").exists())

            bad_sha_manifest = episode / "build_manifest.bad-sha.json"
            bad_sha_payload = json.loads(revision_manifest.read_text(encoding="utf-8"))
            bad_sha_payload["clean_source"]["output_sha256"] = "0" * 64
            write(bad_sha_manifest, bad_sha_payload)
            bad_sha_revision = {
                **revision_v1, "revision_id": "v4",
                "build_manifest_path": str(bad_sha_manifest),
            }
            with self.assertRaisesRegex(RuntimeError, "STAGE08_PREBUILD"):
                builder.build_episode(bad_sha_revision)
            self.assertFalse((episode / "90_workflow" / "revisions" / "v4").exists())
            self.assertFalse((root / "capcut" / "project_v4").exists())

            bad_archive = root / "root_14_tracks.zip"
            with zipfile.ZipFile(archive) as source_zip, zipfile.ZipFile(bad_archive, "w") as target_zip:
                for info in source_zip.infolist():
                    data = source_zip.read(info.filename)
                    if info.filename.endswith("draft_content.json"):
                        payload = json.loads(data.decode("utf-8"))
                        payload["tracks"] = payload["tracks"][:-1]
                        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    target_zip.writestr(info, data)
            bad_root_manifest = root / "root_14_manifest.json"
            write(bad_root_manifest, {"sha256": sha(bad_archive), "template_profile": "shrt_white_base_v2"})
            bad_root_contract = root / "root_14_contract.json"
            write(bad_root_contract, {
                "schema_version": "shorts-capcut-root-contract-v1", "workspace_relative": True,
                "assembly_mode": "clean_staging_copy", "profiles": {"bad_windows": {
                    "archive_relative_path": bad_archive.name,
                    "manifest_relative_path": bad_root_manifest.name,
                    "archive_sha256": sha(bad_archive), "template_profile": "shrt_white_base_v2",
                }},
            })
            bad_track_manifest = episode / "build_manifest.bad-tracks.json"
            bad_track_payload = json.loads(revision_manifest.read_text(encoding="utf-8"))
            bad_track_payload["template"].update(
                root_zip_path=str(bad_archive), root_zip_sha256=sha(bad_archive),
            )
            write(bad_track_manifest, bad_track_payload)
            bad_track_revision = {
                **revision_v1, "revision_id": "v5", "root_profile": "bad_windows",
                "root_contract_path": bad_root_contract.name, "template_zip": str(bad_archive),
                "build_manifest_path": str(bad_track_manifest),
            }
            with self.assertRaisesRegex(RuntimeError, "PINNED_TRACK_LAYOUT_INVALID"):
                builder.build_episode(bad_track_revision)
            self.assertFalse((episode / "90_workflow" / "revisions" / "v5").exists())
            self.assertFalse((root / "capcut" / "project_v5").exists())

            revision_v2 = {**config, "revision_id": "v2"}
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                v2_result = builder.build_episode(revision_v2)
            v2_project = root / "capcut" / "project_v2"
            v2_state = episode / "90_workflow" / "revisions" / "v2" / "state.json"
            self.assertEqual(Path(v2_result["project_path"]), v2_project)
            self.assertTrue(v2_state.is_file())
            self.assertEqual(sha(v1_project / "draft_content.json"), v1_project_before_v2)
            self.assertEqual(sha(v1_state), v1_state_before_v2)
            self.assertEqual(sha(state), canonical_state_before_revisions)
            self.assertEqual(sha(build_manifest), canonical_build_manifest_before_revisions)

            clean_root = episode / "40_assets_used"
            clean_video = clean_root / "clean_video.mp4"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:s=1080x1920:r=30:d=2", "-y", str(clean_video)], check=True)
            clean_manifest = clean_root / "clean_visual_manifest.json"
            write(clean_manifest, {"schema_version": "001short-clean-visual-manifest-v1", "episode_id": "EP", "source_identity_path": str(identity), "source_identity_sha256": sha(identity), "design_lock_evidence_path": str(evidence), "design_lock_evidence_sha256": sha(evidence), "clean_source_path": clean_video.name, "clean_source_sha256": sha(clean_video), "clean_source_origin": "AGENT_PRIMARY_CLEAN_SOURCE", "expected_duration_us": 2_000_000, "expected_width": 1080, "expected_height": 1920})
            import validate_clean_visual
            clean_receipt = clean_root / "clean_visual_receipt.json"
            self.assertEqual(validate_clean_visual.validate_clean_visual(clean_manifest, identity, evidence, clean_receipt, clean_root)["status"], "PASS")
            vmake_receipt = clean_root / "vmake_receipt.json"
            write(vmake_receipt, {"provider": "vmake", "run_id": "run", "job_id": "job", "uploaded_source_sha256": sha(source), "downloaded_output_sha256": sha(clean_video), "final_download": True})
            clean_build_manifest = json.loads(build_manifest.read_text(encoding="utf-8"))
            clean_build_manifest.update({
                "visual_asset_mode": "CLEAN_VISUAL_READY",
                "clean_source": {"origin": "AGENT_PRIMARY_CLEAN_SOURCE", "output_path": str(clean_video), "output_sha256": sha(clean_video)},
                "vmake": {"receipt_path": str(vmake_receipt), "output_path": str(clean_video), "run_id": "run", "job_id": "job", "input_sha256": sha(source), "output_sha256": sha(clean_video), "final_download": True},
            })
            write(build_manifest, clean_build_manifest)
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            edit_lock = episode / "90_workflow" / "clean_swap_lock.json"
            write(edit_lock, {"episode_id": "EP", "action": "STAGE08_VIDEO_ONLY_SWAP", "project_path": str(root / "capcut" / "project")})
            before_nonvideo = json.loads((root / "capcut" / "project" / "draft_content.json").read_text(encoding="utf-8"))["tracks"][1:]
            swap_config = {**config, "visual_asset_mode": "CLEAN_VISUAL_READY", "clean_video": str(clean_video), "clean_asset_root": str(clean_root), "clean_evidence_root": str(clean_root), "edit_lock_path": str(edit_lock)}
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(builder, "_register_capcut_project", return_value=None):
                swapped = builder.swap_provisional_video_only(swap_config)
            after = json.loads((root / "capcut" / "project" / "draft_content.json").read_text(encoding="utf-8"))
            self.assertEqual(after["tracks"][1:], before_nonvideo)
            self.assertEqual(after["tracks"][14]["segments"], [])
            self.assertTrue((root / "capcut" / "project" / "Resources" / "media" / "clean_video.mp4").is_file())
            self.assertFalse((root / "capcut" / "project" / "Resources" / "media" / "source.mp4").exists())
            self.assertEqual(swapped["status"], "CAPCUT_STATIC_VALIDATED")
            self.assertEqual(swapped["next_action"], "WAIT_USER_CAPCUT_CHECK")
            self.assertFalse(swapped["upload_ready"])

            revision_edit_lock = episode / "90_workflow" / "clean_swap_lock_v2.json"
            write(revision_edit_lock, {"episode_id": "EP", "action": "STAGE08_VIDEO_ONLY_SWAP", "project_path": str(v2_project)})
            revision_swap = {
                **config,
                "revision_id": "v2",
                "visual_asset_mode": "CLEAN_VISUAL_READY",
                "clean_video": str(clean_video),
                "clean_asset_root": str(clean_root),
                "clean_evidence_root": str(clean_root),
                "edit_lock_path": str(revision_edit_lock),
                "T1": "mutable shared title",
            }
            bind_state_artifacts(
                v2_state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                revision_swapped = builder.swap_provisional_video_only(revision_swap)
            self.assertEqual(revision_swapped["status"], "CAPCUT_STATIC_VALIDATED")
            self.assertEqual(revision_swap["T1"], "title")
            self.assertTrue((v2_project / "Resources" / "media" / "clean_video.mp4").is_file())


if __name__ == "__main__":
    unittest.main()
