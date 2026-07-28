#!/usr/bin/env python3
"""script_lock.schema.json 과 gate_lock.py 가 같은 계약을 말하는지 검사한다.

**스키마는 집행자가 아니다.** 집행자는 `gate_lock.py` 다. 스키마는 프로젝트
GPT·외부 도구에 넘기는 계약 문서다. 그래서 실제 위험은 "스키마가 틀렸다"가
아니라 **둘이 서로 다른 말을 하는 것**이다. 한쪽만 고치면 문서를 믿고 만든
잠금이 게이트에서 튕긴다.

jsonschema 패키지는 쓰지 않는다(표준 라이브러리 전용 정책). 대신 두 파일의
필수 키 집합을 직접 대조한다.
"""
import json
import re
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL / "references" / "script_lock.schema.json"

sys.path.insert(0, str(SKILL / "scripts"))
import gate_lock  # noqa: E402
from lock_preflight import REQUIRED_TTS_KEYS  # noqa: E402


class SchemaCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def props(self, *path):
        node = self.schema
        for key in path:
            node = node["properties"][key]
        return node

    # ------------------------------------------------------ 게이트와의 일치
    def test_schema_version_matches_gate(self):
        self.assertEqual(self.props("schema_version")["const"],
                         gate_lock.SCHEMA_VERSION)

    def test_audit_authorities_match_gate(self):
        authority = self.props("authority")
        self.assertEqual(
            set(authority["properties"]["audit_authority"]["enum"]),
            set(gate_lock.AUDIT_AUTHORITIES))
        self.assertIn("review_override", authority["required"])

    def test_locked_inputs_match_gate(self):
        self.assertEqual(set(self.props("locked_inputs")["required"]),
                         set(gate_lock.REQUIRED_INPUTS))

    def test_editorial_keys_match_gate(self):
        """게이트는 불리언 6개를 REQUIRED_EDITORIAL 로, lexicon_conflicts 는
        카운트(== 0)로 따로 검사한다. 스키마는 둘 다 required 다."""
        schema_keys = set(self.props("editorial_decisions")["required"])
        self.assertEqual(schema_keys,
                         set(gate_lock.REQUIRED_EDITORIAL) | {"lexicon_conflicts"})

    def test_editorial_flags_must_be_true(self):
        """false 를 허용하면 '검토 안 했음'이 잠금을 통과한다."""
        node = self.props("editorial_decisions")
        for key, spec in node["properties"].items():
            with self.subTest(key=key):
                self.assertEqual(spec["const"], 0 if key == "lexicon_conflicts"
                                 else True)

    def test_tts_keys_match_preflight(self):
        self.assertEqual(set(self.props("tts_params")["required"]),
                         set(REQUIRED_TTS_KEYS))

    def test_deferred_blocks_match_gate_stages(self):
        blocks = self.schema["$defs"]["deferredItem"]["properties"]["blocks"]
        self.assertEqual(set(blocks["items"]["enum"]),
                         set(gate_lock.STAGE_BLOCKER.values()))

    def test_unresolved_counters_are_pinned_to_zero(self):
        node = self.props("ruling_summary")["properties"]
        for key in ("unresolved", "unresolved_high",
                    "unresolved_quote_mismatch"):
            with self.subTest(key=key):
                self.assertEqual(node[key]["const"], 0)

    def test_rejected_no_change_is_not_pinned(self):
        """REJECTED_NO_CHANGE 는 해결된 것이다. 0으로 못박으면 SCA-011 같은
        '수정 안 함' 판정이 잠금을 영구히 막는다."""
        spec = self.props("ruling_summary")["properties"]["rejected_no_change"]
        self.assertNotIn("const", spec)

    def test_sha_pattern_matches_gate(self):
        self.assertEqual(self.schema["$defs"]["sha256"]["pattern"],
                         gate_lock.SHA_RE.pattern)

    # ------------------------------------------------------ 스키마 자체 건전성
    def test_every_ref_resolves(self):
        refs = re.findall(r'"\$ref":\s*"#/([^"]+)"',
                          SCHEMA_PATH.read_text(encoding="utf-8"))
        for ref in refs:
            with self.subTest(ref=ref):
                node = self.schema
                for part in ref.split("/"):
                    self.assertIn(part, node, f"미해결 $ref: #/{ref}")
                    node = node[part]

    def test_top_level_required_covers_every_property(self):
        """선택 키를 만들면 그 키가 빠진 잠금이 통과한다."""
        self.assertEqual(set(self.schema["required"]),
                         set(self.schema["properties"]))

    def test_relpath_pattern_rejects_escapes(self):
        pat = re.compile(self.schema["$defs"]["relPath"]["pattern"])
        for bad in ("C:/other/x.md", "/etc/passwd", "../../other/x.md",
                    "20_script/../../x.md", "\\\\server\\share\\x.md"):
            with self.subTest(bad=bad):
                self.assertIsNone(pat.match(bad), f"탈출 경로 통과: {bad}")
        for good in ("20_script/master_script.md", "10_analysis/a.json"):
            with self.subTest(good=good):
                self.assertIsNotNone(pat.match(good))

    def test_segment_kind_enum_is_closed(self):
        kinds = self.schema["$defs"]["segment"]["properties"]["kind"]["enum"]
        self.assertEqual(set(kinds), {"NARRATION", "SOURCE_VIDEO"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
