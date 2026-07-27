#!/usr/bin/env python3
"""대본 잠금 하드 게이트 v1.1.

잠금이 유효하지 않으면 exit 1 로 하류를 막는다.
산문 규칙은 지켜지지 않는다. 지난 에피소드에서 감사 게이트가 SKILL.md 안의
문장이었고, 그대로 무시된 채 TTS가 실행돼 미판정 지적 11건이 합성 음성에 박혔다.

v1.0 대비 보강 (리스크 리뷰 반영):
    필수 locked_inputs 집합 강제        대본만 맞고 클립이 틀린 제작 차단
    episode 상대경로 강제                에피소드 밖 파일 잠금 차단
    ordered segments 무결성              순서가 뒤집힌 제작 차단
    hook/label 세그먼트 범위 검사         다른 챕터 문구 차용 차단
    editorial_decisions 필수 키 강제      키 오타로 검사 누락되는 것 차단
    deferred blocks 검사                 중대 오류를 DEFER로 우회하는 것 차단
    gates_passed 제거                     잠금 불변성과 모순되던 구조 폐기

사용:
    py -3.14 gate_lock.py --episode <에피소드 디렉터리> --stage tts
    PL_EPISODE_DIR=<...> py -3.14 gate_lock.py --stage tts

표준 라이브러리만 사용한다.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = "politics-longform-script-lock.v1"
LOCK_RELPATH = Path("20_script") / "script_lock.json"

REQUIRED_INPUTS = ("script", "source_map", "clip_manifest", "intake_manifest",
                   "episode_lexicon", "machine_audit", "project_gpt_ruling")

REQUIRED_EDITORIAL = ("chapter_order_approved", "source_media_verified",
                      "clip_timecodes_verified", "hook_selection_approved",
                      "lexicon_review_approved", "quote_accuracy_approved")

STAGE_BLOCKER = {"tts": "TTS", "assembly": "ASSEMBLY"}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(text):
    """공백만 접어 비교한다. 문자는 바꾸지 않는다."""
    return " ".join(text.split())


class Gate:
    def __init__(self, episode, stage):
        self.episode = Path(episode).resolve()
        self.stage = stage
        self.fails = []
        self.checks = 0
        self.script_lines = []

    def fail(self, code, detail):
        self.fails.append((code, detail))

    def check(self, ok, code, detail):
        self.checks += 1
        if not ok:
            self.fail(code, detail)
        return ok

    # ------------------------------------------------------------------
    def run(self):
        lock_path = self.episode / LOCK_RELPATH
        if not lock_path.is_file():
            self.fail("LOCK_MISSING", str(lock_path))
            return
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.fail("LOCK_UNPARSEABLE", f"{lock_path}: {exc}")
            return

        self.check(lock.get("schema_version") == SCHEMA_VERSION,
                   "SCHEMA_VERSION_MISMATCH",
                   f"{lock.get('schema_version')!r} != {SCHEMA_VERSION!r}")
        self.check(lock.get("status") == "SCRIPT_LOCKED",
                   "STATUS_NOT_LOCKED", repr(lock.get("status")))

        self._check_inputs(lock)
        self._check_ruling(lock)
        self._check_deferred(lock)
        self._check_editorial(lock)
        self._check_segments(lock)
        self._load_script(lock)
        self._check_blueprint_scoped(lock)

    # ------------------------------------------------------------------
    def _safe_path(self, name, rel):
        """episode 상대경로만 허용한다. 절대경로·상위탐색은 탈출한다."""
        p = PurePosixPath(str(rel).replace("\\", "/"))
        if p.is_absolute() or re.match(r"^[A-Za-z]:", str(rel)):
            self.fail("LOCKED_INPUT_PATH_OUTSIDE_EPISODE", f"{name}: 절대경로 {rel!r}")
            return None
        if ".." in p.parts:
            self.fail("LOCKED_INPUT_PATH_OUTSIDE_EPISODE", f"{name}: 상위탐색 {rel!r}")
            return None
        full = (self.episode / str(p)).resolve()
        try:
            full.relative_to(self.episode)
        except ValueError:
            self.fail("LOCKED_INPUT_PATH_OUTSIDE_EPISODE",
                      f"{name}: episode 밖 {full}")
            return None
        return full

    def _check_inputs(self, lock):
        inputs = lock.get("locked_inputs") or {}
        for name in REQUIRED_INPUTS:
            self.check(name in inputs, "LOCKED_INPUT_REQUIRED_MISSING",
                       f"필수 입력 {name} 없음")
        for name, entry in inputs.items():
            rel = (entry or {}).get("path")
            want = (entry or {}).get("sha256")
            if not rel or not want:
                self.fail("LOCKED_INPUT_INCOMPLETE", f"{name}: path/sha256 누락")
                continue
            if not SHA_RE.match(str(want)):
                self.fail("LOCKED_INPUT_SHA_MALFORMED", f"{name}: {want!r}")
                continue
            path = self._safe_path(name, rel)
            if path is None:
                continue
            if not path.is_file():
                self.fail("LOCKED_INPUT_MISSING", f"{name}: {path}")
                continue
            got = sha256_of(path)
            self.check(got == want, "LOCKED_INPUT_SHA_MISMATCH",
                       f"{name}: {rel}\n        기대 {want}\n        실제 {got}")

    def _check_ruling(self, lock):
        r = lock.get("ruling_summary") or {}
        for key in ("unresolved", "unresolved_high", "unresolved_quote_mismatch"):
            self.check(r.get(key) == 0, "RULING_UNRESOLVED",
                       f"{key} = {r.get(key)!r} (0 이어야 한다)")
        total = r.get("total_findings")
        parts = [r.get(k) for k in
                 ("approved_fix", "rejected_no_change", "deferred", "unresolved")]
        if total is not None and all(isinstance(p, int) for p in parts):
            self.check(sum(parts) == total, "RULING_COUNT_INCONSISTENT",
                       f"합 {sum(parts)} != total_findings {total}")

    def _check_deferred(self, lock):
        """중대 오류를 DEFER 로 돌려 잠금을 통과하는 우회를 막는다."""
        r = lock.get("ruling_summary") or {}
        items = r.get("deferred_items")
        declared = r.get("deferred")
        if isinstance(declared, int) and declared > 0 and not items:
            self.fail("DEFERRED_ITEMS_MISSING",
                      f"deferred={declared} 인데 deferred_items 가 없다")
            return
        for it in (items or []):
            ident = (it or {}).get("id", "?")
            if "blocks" not in (it or {}):
                self.fail("DEFERRED_ITEM_BLOCKS_MISSING",
                          f"{ident}: blocks 필드 없음 (미기입 우회 방지)")
                continue
            blocks = it.get("blocks") or []
            self.check(STAGE_BLOCKER[self.stage] not in blocks,
                       "DEFERRED_ITEM_BLOCKS_STAGE",
                       f"{ident}: blocks={blocks} (stage={self.stage})")
            for field in ("reason", "approved_by"):
                self.check(bool(it.get(field)), "DEFERRED_ITEM_INCOMPLETE",
                           f"{ident}: {field} 누락")

    def _check_editorial(self, lock):
        ed = lock.get("editorial_decisions") or {}
        for key in REQUIRED_EDITORIAL:
            if key not in ed:
                self.fail("EDITORIAL_DECISION_REQUIRED_MISSING",
                          f"필수 키 {key} 없음 (오타 확인)")
                continue
            self.check(ed[key] is True, "EDITORIAL_NOT_APPROVED",
                       f"{key} = {ed[key]!r}")
        self.check(ed.get("lexicon_conflicts") == 0, "LEXICON_CONFLICT",
                   f"lexicon_conflicts = {ed.get('lexicon_conflicts')!r}")

    # ------------------------------------------------------------------
    def _check_segments(self, lock):
        st = lock.get("structure") or {}
        chapters = st.get("chapters") or []
        segs = st.get("segments")

        self.check(st.get("chapter_count") == len(chapters),
                   "CHAPTER_COUNT_MISMATCH",
                   f"chapter_count={st.get('chapter_count')} vs {len(chapters)}")

        if not segs:
            self.fail("SEGMENT_ORDER_INTEGRITY_FAIL",
                      "structure.segments 가 없다 (순서 계약 누락)")
            return

        idxs = [s.get("index") for s in segs]
        self.check(idxs == list(range(1, len(segs) + 1)),
                   "SEGMENT_ORDER_INTEGRITY_FAIL",
                   f"index 가 1..{len(segs)} 연속이 아니다: {idxs[:12]}")

        ids = [s.get("segment_id") for s in segs]
        dupes = {x for x in ids if ids.count(x) > 1}
        self.check(not dupes, "SEGMENT_ORDER_INTEGRITY_FAIL",
                   f"segment_id 중복 {sorted(dupes)}")

        self.check(st.get("logical_segment_count") == len(segs),
                   "SEGMENT_ORDER_INTEGRITY_FAIL",
                   f"logical_segment_count={st.get('logical_segment_count')} "
                   f"vs segments={len(segs)}")

        n_nar = sum(1 for s in segs if s.get("kind") == "NARRATION")
        n_src = sum(1 for s in segs if s.get("kind") == "SOURCE_VIDEO")
        self.check(st.get("narration_block_count") == n_nar,
                   "SEGMENT_KIND_COUNT_MISMATCH",
                   f"narration {st.get('narration_block_count')} vs {n_nar}")
        self.check(st.get("source_clip_count") == n_src,
                   "SEGMENT_KIND_COUNT_MISMATCH",
                   f"source_clip {st.get('source_clip_count')} vs {n_src}")

        for s in segs:
            sid = s.get("segment_id", "?")
            kind = s.get("kind")
            if kind == "SOURCE_VIDEO":
                self.check(bool(s.get("source_id")) and bool(s.get("source_timecode")),
                           "SEGMENT_SOURCE_FIELDS_MISSING",
                           f"{sid}: SOURCE_VIDEO 인데 source_id/timecode 누락")
            elif kind == "NARRATION":
                self.check(s.get("source_id") is None and
                           s.get("source_timecode") is None,
                           "SEGMENT_SOURCE_FIELDS_UNEXPECTED",
                           f"{sid}: NARRATION 인데 source 필드가 있다")
            else:
                self.fail("SEGMENT_KIND_UNKNOWN", f"{sid}: kind={kind!r}")

        mapped = set()
        for ch in chapters:
            mapped |= set(ch.get("segment_indices") or [])
        self.check(mapped == set(idxs), "CHAPTER_SEGMENT_MAPPING_MISMATCH",
                   f"챕터 매핑 {sorted(mapped)[:12]} != 세그먼트 {idxs[:12]}")

    # ------------------------------------------------------------------
    def _load_script(self, lock):
        entry = (lock.get("locked_inputs") or {}).get("script") or {}
        rel = entry.get("path")
        if not rel:
            return
        path = self._safe_path("script", rel)
        if path is None or not path.is_file():
            return
        self.script_lines = path.read_text(encoding="utf-8").splitlines()

    def _segment_text(self, lock, seg_key):
        """세그먼트의 script_line_range 안 본문만 돌려준다."""
        segs = (lock.get("structure") or {}).get("segments") or []
        for s in segs:
            if str(s.get("index")) == str(seg_key):
                rng = s.get("script_line_range") or []
                if len(rng) != 2:
                    return None
                a, b = int(rng[0]), int(rng[1])
                return norm("\n".join(self.script_lines[max(0, a - 1):b]))
        return None

    def _check_blueprint_scoped(self, lock):
        """hook/label 이 **그 세그먼트 범위 안에** 있는지 본다.

        대본 전체에 존재하는지만 보면, 챕터 4의 문구를 챕터 1 화면에 써도
        통과한다. 문구는 실재하지만 화면이 틀린다.
        """
        if not self.script_lines:
            return

        for seg, hook in (lock.get("hooks") or {}).items():
            body = self._segment_text(lock, seg)
            if body is None:
                self.fail("UNKNOWN_SEGMENT_KEY", f"hooks.{seg}: 없는 세그먼트")
                continue
            text = (hook or {}).get("text")
            under = (hook or {}).get("underline")
            if text:
                self.check(norm(text) in body, "SEGMENT_SCOPED_TEXT_MISMATCH",
                           f"hooks.{seg}: 세그먼트 범위 밖 문구 {text[:36]!r}")
            if text and under:
                self.check(under in text, "UNDERLINE_NOT_IN_HOOK",
                           f"hooks.{seg}: {under!r}")

        for seg, labels in (lock.get("labels") or {}).items():
            if seg.startswith("_") or not isinstance(labels, list):
                continue
            body = self._segment_text(lock, seg)
            if body is None:
                self.fail("UNKNOWN_SEGMENT_KEY", f"labels.{seg}: 없는 세그먼트")
                continue
            for label in labels:
                self.check(norm(label) in body, "SEGMENT_SCOPED_TEXT_MISMATCH",
                           f"labels.{seg}: 세그먼트 범위 밖 라벨 {label!r}")


def main():
    ap = argparse.ArgumentParser(description="대본 잠금 하드 게이트")
    ap.add_argument("--episode", default=os.environ.get("PL_EPISODE_DIR"),
                    help="에피소드 디렉터리 (또는 PL_EPISODE_DIR)")
    # required=True 로 두면 argparse 가 --stage 만 보고 먼저 죽어서
    # 에피소드 경로를 어디서 주는지(PL_EPISODE_DIR)를 알려주지 못한다.
    ap.add_argument("--stage", choices=sorted(STAGE_BLOCKER),
                    help="검사할 하류 단계")
    ap.add_argument("--json", action="store_true", help="기계 판독용 출력")
    args = ap.parse_args()

    if not args.stage or not args.episode:
        print("BLOCKED: 인자가 부족하다\n"
              f"  --stage    {' | '.join(sorted(STAGE_BLOCKER))}\n"
              "  --episode  에피소드 디렉터리 (환경변수 PL_EPISODE_DIR 도 가능)",
              file=sys.stderr)
        return 2

    gate = Gate(args.episode, args.stage)
    gate.run()

    if args.json:
        print(json.dumps(
            {"stage": args.stage, "episode": str(args.episode),
             "checks": gate.checks, "passed": not gate.fails,
             "failures": [{"code": c, "detail": d} for c, d in gate.fails]},
            ensure_ascii=False, indent=1))
    else:
        if gate.fails:
            print(f"BLOCKED  stage={args.stage}  실패 {len(gate.fails)}건")
            for code, detail in gate.fails:
                print(f"  {code}\n        {detail}")
        else:
            print(f"PASS  stage={args.stage}  검사 {gate.checks}항목 통과")

    return 1 if gate.fails else 0


if __name__ == "__main__":
    sys.exit(main())
