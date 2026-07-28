import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "119-politics-longform-capcut" / "SKILL.md"
SKILL_DIR = SKILL.parent


class PoliticsLongformEmbeddedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL.read_text(encoding="utf-8-sig")

    def test_skill_embeds_common_longform_boundaries(self):
        for token in (
            "## 정치 롱폼 공통 제작 계약",
            "22factory_20260628",
            "Stage 1",
            "Stage 2",
            "1920x1080",
            "jungchilong_v3_intro15_CAPCUT_20260715.zip",
            "template_manifest_v3_intro15.json",
            "jungchilong_base_v3_intro15",
            "promotion_state: READY",
            "archive_sha256: B461A07FF18E1491E837E56A0681A35CCB0A25CBF9D7BFA2B6004C6D32CC878A",
            "packaged_file_count: 39",
            "intro_sha256: E899A65CC6C089FF116CBB6175B6A43B8580A69C523720B093FBE259F05717B9",
            "commentary_review_packet_sent.md",
            "commentary_review_packet_returned.md",
            "commentary_review_packet_manifest.json",
            "external_review_gate.json",
            "commentary_decisions.json",
            "timeline_design_approved.json",
            "speech_boundary_lock.json",
            "roughcut_edl_locked.json",
            "source_labels_locked.json",
            "locked_clips_manifest.json",
            "POLITICS_LONGFORM_MEDIA_ROOT",
            "roughcut_edl_sha256",
            "복원본 전 파일",
            "timeline_design_approved.json`과 locked clips만",
            "active_writer_machine",
            "raw_capcut_sync: false",
            "audio_track_count == 0",
            "materials.audios == []",
            "harness",
            "ffprobe",
            "frame QA",
        ):
            self.assertIn(token, self.skill_text)

    def test_jungchilong_is_the_only_root_and_yp007_is_legacy_only(self):
        self.assertIn("jungchilong_base_v3_intro15", self.skill_text)
        self.assertIn("YP007, YP005, YM007", self.skill_text)
        self.assertIn("legacy", self.skill_text.lower())
        self.assertNotIn("Default CapCut base priority 1: YP007", self.skill_text)
        self.assertNotIn("canvas: 1280x720", self.skill_text)

    def test_derived_politics_shorts_use_shrtjungchi_and_locked_stage_one_plans(self):
        for token in (
            "## 파생 정치 쇼츠 계약",
            "SHRTJUNGCHI",
            "canvas: 1080x1920",
            "60~100초",
            "target_shorts_count=3",
            "valid_shorts_count=0~3",
            "갈등 → 분석 → 결론",
            "longform_entry_point",
            "20_script/shorts/SHxx/edit_plan_approved.json",
            "design_lock_manifest.json",
            "approved_short_ids",
            "WAIT_SHRTJUNGCHI_ROOT_REQUIRED",
            "근본 무결성",
            "CapCut 화면",
            "하네스",
        ):
            self.assertIn(token, self.skill_text)
        self.assertIn(
            "Stage 2는 SHRTJUNGCHI를 승인된 쇼츠마다 복제",
            self.skill_text,
        )
        self.assertIn(
            "일반 `shrt white`를 정치 롱폼 파생 쇼츠의 근본으로 사용하지 않는다",
            self.skill_text,
        )
        self.assertIn(
            "`jungchilong_base_v3_intro15`는 롱폼 근본이며 쇼츠 근본이 아니다",
            self.skill_text,
        )

    def test_stage_one_owns_rough_design_and_one_review_packet(self):
        for token in (
            "source_manifest.json",
            "design_blueprint_draft.md",
            "timeline_design_draft.json",
            "commentary_review_packet_sent.md",
            "segment_id",
            "Stage 1 초벌 평론",
            "외부 제안 평론",
            "flow_id",
            "timeline_start_sec",
            "timeline_end_sec",
            "[비판 동기]",
        ):
            self.assertIn(token, self.skill_text)

    def test_stage_two_invalidates_review_when_immutable_design_changes(self):
        for token in (
            "SOURCE_TRANSCRIPT_VERIFIED=WAIT",
            "EXTERNAL_REVIEW_REFLECTED=WAIT",
            "DESIGN_APPROVED=WAIT",
            "timeline_design_draft.json`을 조립에 사용하지 않는다",
        ):
            self.assertIn(token, self.skill_text)

    def test_skill_does_not_depend_on_retired_common_skill(self):
        self.assertNotIn("22utube-production-agent", self.skill_text)

    def test_skill_uses_portable_workspace_roots(self):
        self.assertIn(r"${env:WORKSPACE_ROOT}\22factory_20260628", self.skill_text)
        self.assertIn(r"${env:UTUBE_ROOT}", self.skill_text)
        self.assertIn(r"docs\YOUTUBE_PRODUCTION_WORK_ORDER.md", self.skill_text)
        self.assertNotIn(r"C:\Users\arajun", self.skill_text)

    def test_new_source_evidence_prefers_factory_lane_and_legacy_is_read_only(self):
        self.assertIn(r"02_politics_longform\episodes\{episode_id}", self.skill_text)
        self.assertIn("legacy read-only fallback", self.skill_text)
        self.assertNotIn(
            "For source evidence, prefer the episode folder under `22utube\\11utube\\yellow\\episodes\\...`.",
            self.skill_text,
        )

    def test_source_intake_accepts_720p_and_1080p_while_canvas_stays_1080p(self):
        for token in (
            "preferred_source_resolution=1920x1080",
            "required_accepted_source_resolutions=1920x1080|1280x720",
            "final_canvas_resolution=1920x1080",
            "source_dimensions_preserved_from_ffprobe=true",
            "thumbnail_resolution_contract=1280x720",
            "SOURCE_RESOLUTION_ACCEPTED",
        ):
            self.assertIn(token, self.skill_text)

    def test_capcut_backups_stay_outside_active_draft_and_cleanup_is_fail_closed(self):
        self.assertIn("outside the active CapCut draft tree", self.skill_text)
        self.assertIn("WAIT_PROJECT_CLEANUP", self.skill_text)
        self.assertIn("FAIL_PROJECT_CLEANUP", self.skill_text)

    def test_skill_embeds_adversarial_gate_hardening(self):
        for token in (
            "파일에 `ffprobe`를 다시 실행",
            "상태 문자열만 있는 빈 PASS/CANDIDATE 파일",
            "원본 송신 SHA-256",
            "공개 우회 옵션이 없다",
            "POLITICS_WRITER_MACHINE",
            "CapCut GUI 열림, 타임라인 표시, CapCut 프로세스 종료 여부는 자동 확인하지",
            "사용자가 프로젝트 문제를 알린 경우에만 해당 문제를 진단",
            "원래 바이트로 원복",
            "개수와 간격만 맞는 다른 문장은 FAIL",
        ):
            self.assertIn(token, self.skill_text)

    def test_skill_requires_editable_small_source_caption_track(self):
        for token in (
            "source_caption",
            "editability=editable",
            "TTS font size: 8.0",
            "max lines: 1줄",
            "speech boundary lock 후",
            "자연스러운 자막 공백",
            "박힌 자막",
            "NEEDS_VISUAL_REVIEW",
            "original_transcript: episode-relative SRT/TXT path",
            "unique consecutive",
        ):
            self.assertIn(token, self.skill_text)

    def test_intro15_root_promotion_is_fail_closed_and_portable(self):
        for token in (
            "jungchilong_base_v3_intro15",
            "content_start_sec=15.083333",
            "INTRO_MEDIA_FFPROBE=PASS",
            "INTRO_MEDIA_SHA256=PASS",
            "INTRO_TEXT_COVERAGE=PASS",
            "OVERLAY_OFFSET=PASS",
            "NO_FOREIGN_ABSOLUTE_PATHS=PASS",
            "새 근본 승격은 별도 staging 사본에서 수행",
            "*.bak",
            "Resources/media",
        ):
            self.assertIn(token, self.skill_text)
        for removed in (
            "jungchilong_gui_restore_gate.json",
            "gui_opened=true",
            "timeline_visible=true",
            "status=DEFERRED_TO_USER",
        ):
            self.assertNotIn(removed, self.skill_text)
        self.assertNotIn("intro jounchilong.mp4", self.skill_text)

    def test_intro_copy_is_reviewed_in_stage_two_and_printed_in_final_outputs(self):
        for token in (
            "정확히 2개 cue",
            "각 cue는 실제 2줄",
            "오늘 다룰 쟁점",
            "감상·검증 포인트",
            "final_intro_text",
            "INTRO_TEXT_OUTPUT=PASS",
            "70~90자",
        ):
            self.assertIn(token, self.skill_text)

    def test_lower_commentary_uses_two_synchronized_template_tracks(self):
        for token in (
            "__LOWER_T1_A__",
            "__LOWER_T1_B__",
            "LOWER_COMMENTARY_ACTIVE_PAIR_COUNT=1",
            "FAIL_DUPLICATE_LOWER_COMMENTARY",
            "같은 시작·종료",
            "공백 제외 최대 15자",
        ):
            self.assertIn(token, self.skill_text)
        self.assertNotIn("lower_commentary_active_track_count == 1", self.skill_text)

    def test_tts_fidelity_flow_external_review_thumbnail_and_api_contracts(self):
        for token in (
            "FAIL_SOURCE_CAPTION_FIDELITY",
            "정규화 연결 문자열",
            "원문을 축약·요약·의역하지 않는다",
            "topic1 > topic2 > topic3",
            "숫자 접두사를 붙이지 않는다",
            "너는 민주진영 관점의 정치 평론가다",
            "review_origin=user_return|external_model",
            "commentary_review_receipt.json",
            "recorded_by=user|external_adapter",
            "recorded_by=agent_self",
            "politics-external-review-hash-receipt-v1",
            "공개키를 요구하지 않는다",
            "인물 3명",
            "빨간 줄 후킹 1",
            "하단 2줄 후킹 2",
            "minju_decoder",
            "OAUTH_PROFILE_RESOLVED",
            "EXPECTED_CHANNEL_MATCH",
            "API_UPLOAD",
            "THUMBNAIL_SET",
            "REMOTE_METADATA_VERIFY",
            "privacyStatus=private",
            "selfDeclaredMadeForKids=false",
            "containsSyntheticMedia=true",
            "promotion_state: READY",
            "audio_normalization_target: -14 LUFS",
            "AUDIO_LOUDNESS_NORMALIZATION=PASS",
            "thumbnail.delivery=TEXT_GUIDE_ONLY",
            "tools/youtube_profile_upload.py",
            "--require-thumbnail",
        ):
            self.assertIn(token, self.skill_text)

    def test_skill_folder_does_not_ship_stale_duplicate_contract(self):
        duplicates = [path.name for path in SKILL_DIR.glob("SKILL*.md") if path.name != "SKILL.md"]
        self.assertEqual(duplicates, [])


if __name__ == "__main__":
    unittest.main()
