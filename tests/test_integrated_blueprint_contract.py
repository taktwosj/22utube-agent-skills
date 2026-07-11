import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "000short-production-agent" / "scripts" / "validate_integrated_blueprint.py"


def load_module():
    if not SCRIPT.is_file():
        raise AssertionError("integrated blueprint validator is missing")
    return load_source_module_no_bytecode("integrated_blueprint_contract", SCRIPT)


VALID = """# 설계도
## 기본 정보
## 제작 판단
## 자막 레이아웃 기준
caption_beat_map.json
TTS (T3): y=-900, max_chars_per_line=10, max_lines=1
화자발언 (T4/T5): y=-500, max_chars_per_line=10, max_lines=1
( ) 상황설명 (T6): y=700, max_chars_per_line=10, max_lines=1
video_scale=1.20
face_avoidance=fixed_lower_safe_zone_v1
## 상단 고정 문구
## 조립 역할 순서
| 편집 | 원본 | 편집 구간 |
|---|---|---|
| E1 | S1 | 00:00-00:03 |
## 트랙별 타임라인
| 트랙 / 시간 | 00:00 |
|---|---|
| V1 | 00:00-00:03 |
## TTS 복사용 문구
[E1]
## 승인 전 점검
status: PASS
## 조립도
보고서2 시작: 예
최종보고서: 예
상태: CAPCUT_EDIT_READY
CapCut 프로젝트명: TEST_PROJECT
CapCut 열어보기 필요: 예
사용자 확인 대기: 예
업로드 준비 완료: 아니오
최종 잠금: 아니오
## 프로젝트 실체
## 설계도 반영 결과
| 설계 편집 | 실제 CapCut 구간 |
|---|---|
| E1 | 00:00-00:03 |
## 실제 CapCut 트랙 구성
| 실제 트랙 | 역할 |
|---|---|
| V1 | source |
## TTS 실제 길이 대조
| 편집 | 계획 길이 | 실제 WAV 길이 |
|---|---:|---:|
| E1 | 3.0 | 3.0 |
## 검증 결과
- Stage 2 handoff: PASS
## 남은 사람 작업
- CapCut 미리보기
## 업로드 패키지
제목: 테스트 제목
상세설명: 테스트 상세 설명
출처: https://example.com/source
해시태그: #테스트 #쇼츠
추천 업로드채널: 테스트채널
"""


class IntegratedBlueprintContractTest(unittest.TestCase):
    def test_assembly_report_requires_canonical_status_fields(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design_blueprint.md"
            path.write_text(VALID.replace("보고서2 시작: 예\n", ""), encoding="utf-8")
            with self.assertRaises(module.BlueprintGateFail) as ctx:
                module.validate_integrated_blueprint(path, phase="production")
        self.assertIn("FAIL_ASSEMBLY_REPORT_FORMAT", str(ctx.exception))

    def test_report_requires_fixed_caption_profile_contract(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design_blueprint.md"
            path.write_text(VALID.replace("video_scale=1.20\n", ""), encoding="utf-8")
            with self.assertRaises(module.BlueprintGateFail) as ctx:
                module.validate_integrated_blueprint(path, phase="production")
        self.assertIn("FAIL_CAPTION_PROFILE_CONTRACT", str(ctx.exception))

    def test_valid_design_assembly_upload_contract_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design_blueprint.md"
            path.write_text(VALID, encoding="utf-8")
            result = module.validate_integrated_blueprint(path, phase="production")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["last_section"], "업로드 패키지")

    def test_missing_final_upload_package_fails_closed(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design_blueprint.md"
            path.write_text(VALID.replace("## 업로드 패키지", "## 누락"), encoding="utf-8")
            with self.assertRaises(module.BlueprintGateFail) as ctx:
                module.validate_integrated_blueprint(path, phase="production")
        self.assertIn("FAIL_UPLOAD_PACKAGE", str(ctx.exception))

    def test_table_requires_header_separator_and_data_row(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design_blueprint.md"
            path.write_text(VALID.replace("| 트랙 / 시간 | 00:00 |", "prose | weak"), encoding="utf-8")
            with self.assertRaises(module.BlueprintGateFail) as ctx:
                module.validate_integrated_blueprint(path, phase="production")
        self.assertIn("FAIL_DESIGN_BLUEPRINT", str(ctx.exception))

    def test_upload_source_and_hashtags_must_be_in_their_own_fields(self):
        module = load_module()
        bad = VALID.replace("제목: 테스트 제목", "제목: https://example.com/not-source #wrong")
        bad = bad.replace("출처: https://example.com/source", "출처: 없음")
        bad = bad.replace("해시태그: #테스트 #쇼츠", "해시태그: 없음")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "design_blueprint.md"
            path.write_text(bad, encoding="utf-8")
            with self.assertRaises(module.BlueprintGateFail) as ctx:
                module.validate_integrated_blueprint(path, phase="production")
        self.assertIn("FAIL_UPLOAD_PACKAGE", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
