# -*- coding: utf-8 -*-
"""회차 루트 해석과 cards_def 로더. 모든 스크립트가 이걸로 시작한다.

회차 루트는 `--root <episode_root>` 이고, 회차 정의는 `<root>/work/cards_def.py` 다.
스킬 스크립트는 회차 폴더 밖에 살고, 회차별 값은 전부 cards_def 에만 둔다.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from runtime_paths import configured_path, production_path, require_local_path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CAPCUT_119 = configured_path('CAPCUT_119_SKILL', SKILL_ROOT.parent / '119-politics-longform-capcut')
JUNGCHI_ROOT = production_path('JUNGCHI_ROOT', '119jungchi')
ALLOWLIST = configured_path('PRE119_ALLOWLIST', SKILL_ROOT.parent / 'togun-politics-pre119-writer' / 'references' / 'approved-channel-allowlist.json')


def root_parser(desc: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--root", type=lambda value: require_local_path(Path(value),'EPISODE_ROOT'),
                   default=require_local_path(Path(os.environ["SPINE_EPISODE_ROOT"]),'EPISODE_ROOT') if os.environ.get("SPINE_EPISODE_ROOT") else None,
                   help="회차 루트. 환경변수 SPINE_EPISODE_ROOT 로 대체 가능")
    return p


def resolve_root(args) -> Path:
    if args.root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")
    root = require_local_path(Path(args.root),'EPISODE_ROOT')
    if not (root / "work" / "cards_def.py").is_file():
        raise SystemExit(f"CARDS_DEF_MISSING: {root / 'work' / 'cards_def.py'}")
    return root


# 영구차단. 어떤 회차에서도 쓰지 않는다. load_cards_def 가 SOURCES 를 보고 막는다.
# 저작권 소유권 주장이 들어온 곳은 여기 넣는다. 한 번 클레임이 오면 다시 쓰지 않는다.
BLOCKED_VIDEO_IDS = {
    "hTcRBTJ2xAc": "미디어 파손",
    "fRkePkq39Lk": "JTBC 썰전 — Content ID 소유권 주장 (2026-09-13)",
}
# 채널 표기에 이 조각이 들어가면 막는다. 재업로드본까지 걸리게 이름으로도 본다.
BLOCKED_CHANNEL_MARKS = ("JTBC", "jtbc", "썰전", "썰戰")


def assert_sources_allowed(sources) -> None:
    """SOURCES 에 영구차단 소스가 있으면 멈춘다."""
    bad = []
    for vid, meta in sources.items():
        if vid in BLOCKED_VIDEO_IDS:
            bad.append(vid + " (" + BLOCKED_VIDEO_IDS[vid] + ")")
            continue
        text = " ".join(str(x) for x in meta)
        for mark in BLOCKED_CHANNEL_MARKS:
            if mark in text:
                bad.append(vid + " — 채널 표기에 '" + mark + "'")
                break
    if bad:
        raise SystemExit(
            "BLOCKED_SOURCE: 영구차단 소스다. 빼고 다시 짠다." + chr(10)
            + chr(10).join("  " + b for b in bad))


def load_cards_def(root: Path):
    # 회차 work 폴더를 import 경로에 넣는다. cards_def 가 형제 모듈을 쓸 수 있어야 한다.
    work = str((root / "work").resolve())
    if work not in sys.path:
        sys.path.insert(0, work)
    spec = importlib.util.spec_from_file_location("cards_def", root / "work" / "cards_def.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cards_def"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    for name in ("EPISODE_ID", "PROJECT_NAME", "SOURCES", "BURNED_CAPTION", "CARDS",
                 "NARRATION_ORDER", "CENTRAL_QUESTION", "SELECTED_THESIS", "PUBLICATION"):
        if not hasattr(mod, name):
            raise SystemExit(f"CARDS_DEF_FIELD_MISSING: {name}")
    assert_sources_allowed(mod.SOURCES)
    return mod


def people_index() -> dict:
    """인물 누끼 라이브러리 색인. 파일명 -> {person, era, role, size, mode}."""
    idx = PEOPLE_ART / 'index.json'
    if not idx.is_file():
        return {}
    return json.loads(idx.read_text(encoding='utf-8'))


def find_person(person: str, era: str = '') -> Path | None:
    """인물 이름으로 누끼를 찾는다. era 를 주면 그 시기 것만.

    era 는 '현재' 또는 연도 문자열이다. 없으면 '현재' 를 먼저 보고, 그것도
    없으면 아무 시기나 하나 준다.
    """
    idx = people_index()
    hits = [(k, v) for k, v in idx.items() if v.get('person') == person]
    if not hits:
        return None
    if era:
        hits = [(k, v) for k, v in hits if v.get('era') == era] or []
        return PEOPLE_ART / hits[0][0] if hits else None
    for k, v in hits:
        if v.get('era') == '현재':
            return PEOPLE_ART / k
    return PEOPLE_ART / hits[0][0]


def stage_people(root: Path, wanted) -> dict:
    """회차 hyperframes/assets_people/ 로 필요한 누끼만 복사한다.

    wanted 는 (인물, 시기) 또는 인물 문자열의 목록이다.
    돌려주는 값은 인물키 -> 회차 안 상대경로. 하이퍼프레임 HTML 이 그대로 쓴다.
    라이브러리에 없으면 PEOPLE_ART_MISSING 으로 멈춘다 — 조용히 빼지 않는다.
    """
    import shutil
    dest = root / 'hyperframes' / 'assets_people'
    dest.mkdir(parents=True, exist_ok=True)
    out, missing = {}, []
    for item in wanted:
        person, era = (item if isinstance(item, (tuple, list)) else (item, ''))
        src = find_person(person, era)
        if src is None or not src.is_file():
            missing.append(person + ('/' + era if era else ''))
            continue
        tgt = dest / src.name
        if not tgt.is_file():
            shutil.copy2(src, tgt)
        out[person + ('_' + era if era else '')] = src.name
    if missing:
        raise SystemExit(
            'PEOPLE_ART_MISSING: 라이브러리에 없다. 누끼를 따서 '
            + str(PEOPLE_ART) + ' 에 넣고 index.json 을 갱신한다.' + chr(10)
            + chr(10).join('  ' + m for m in missing))
    return out


def package_root(episode_id: str) -> Path:
    return JUNGCHI_ROOT / episode_id / "00_pre119_package"


def load_allowlist() -> dict:
    return json.loads(ALLOWLIST.read_text(encoding="utf-8"))


SHORTS_ROOT = production_path('SHORTS_ROOT', '001short')
SHORTS_ART = production_path('SHORTS_ART', '001short/_images/woodcut')
# 인물 누끼(투명배경 PNG) 공용 라이브러리. 하이퍼프레임에 얹는다.
# 회차마다 새로 따지 않고 여기서 가져다 쓴다. 새로 딴 것은 여기에 넣는다.
PEOPLE_ART = production_path('PEOPLE_ART', '_images/people')
SHORTS_CAPCUT_ROOT = "P0_ROOT_shrt_119short_v1"


def resolve_capcut_root_dir(capcut_root, name: str):
    """근본 폴더를 찾는다. CapCut 이 붙인 "(N)" 접미를 감안한다.

    CapCut 은 드래프트 폴더 이름이 겹치면 뒤에 "(N)" 을 붙여 바꿔 버린다.
    감시 프로세스가 도는 동안에는 정확한 이름으로 복사해 둬도 되돌아간다.
    정확한 이름이 없으면 접미만 다른 사본 중 이름이 가장 짧은 것(=원본)을 쓴다.
    """
    from pathlib import Path
    capcut_root = Path(capcut_root)
    exact = capcut_root / name
    if exact.is_dir():
        return exact
    if not capcut_root.is_dir():
        return exact
    cands = [d for d in capcut_root.iterdir()
             if d.is_dir() and d.name.startswith(name) and (d / "draft_content.json").is_file()]
    if not cands:
        return exact
    cands.sort(key=lambda d: (len(d.name), -d.stat().st_mtime))
    return cands[0]
# 쇼츠는 본편 클립을 조금 빨리 돌린다. 나레이션은 건드리지 않는다.
SHORT_SPEED = 1.2


def load_cards_def_raw(root: Path):
    """필드 검사 없이 cards_def 만 읽는다.

    쇼츠 구간은 나레이션·카드보다 먼저 잠근다. 그 시점의 cards_def 에는
    CARDS 나 NARRATION_ORDER 가 아직 없다.
    """
    work = str((root / "work").resolve())
    if work not in sys.path:
        sys.path.insert(0, work)
    path = root / "work" / "cards_def.py"
    if not path.is_file():
        raise SystemExit(f"CARDS_DEF_MISSING: {path}")
    spec = importlib.util.spec_from_file_location("cards_def", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cards_def"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


HYPERFRAME_SCENE = re.compile(r"^(.+?)-(.+)$")


def hyperframe_files(root: Path) -> dict[str, Path]:
    """하이퍼프레임 영상을 **카드 id** 에 건다.

    이름 세 가지를 받는다.

        NL88.mp4                 그 나레이션 줄이 놓인 카드 전부
        NL88-NL90.mp4            NL88 부터 NL90 까지 연속한 카드
        C105_NL88-C107_NL90.mp4  카드 id 로 못박은 구간

    나레이션 이름은 회차 안에서 유일하지 않다. CTA 한 줄은 오프닝과 마지막에 두 번
    놓인다. 그래서 매핑은 이름이 아니라 카드 id 로 한다. 이름으로 준 파일은 그 이름이
    놓인 카드 전부를 덮는다 — CTA 처럼 같은 문장이 두 번 나오는 경우에 그게 맞다.
    """
    folder = root / "hyperframes"
    if not folder.is_dir():
        return {}
    cards = _narration_cards(root)
    by_name: dict[str, list[str]] = {}
    for c in cards:
        by_name.setdefault(c["narration_name"], []).append(c["card_id"])
    ids = [c["card_id"] for c in cards]
    claimed: dict[str, Path] = {}

    def claim(card_id: str, path: Path) -> None:
        if card_id in claimed and claimed[card_id] != path:
            raise SystemExit(f"HYPERFRAME_DUPLICATE_CLAIM: {card_id} "
                             f"<- {claimed[card_id].name}, {path.name}")
        claimed[card_id] = path

    def resolve(token: str) -> list[str]:
        if token in ids:
            return [token]
        if token in by_name:
            return by_name[token]
        raise SystemExit(f"HYPERFRAME_SCENE_UNKNOWN_LINE: {token}")

    for path in sorted(folder.glob("*.mp4")):
        stem = path.stem
        if stem in ids or stem in by_name:
            for card_id in resolve(stem):
                claim(card_id, path)
            continue
        m = HYPERFRAME_SCENE.match(stem)
        if not m:
            raise SystemExit(f"HYPERFRAME_SCENE_UNKNOWN_LINE: {stem}")
        head, tail = resolve(m.group(1)), resolve(m.group(2))
        if len(head) != 1 or len(tail) != 1:
            raise SystemExit(f"HYPERFRAME_SCENE_AMBIGUOUS: {stem} "
                             f"— 카드 id 로 이름을 주십시오")
        a, b = ids.index(head[0]), ids.index(tail[0])
        if b < a:
            raise SystemExit(f"HYPERFRAME_SCENE_REVERSED: {stem}")
        for card_id in ids[a:b + 1]:
            claim(card_id, path)
    return claimed


def _narration_cards(root: Path) -> list[dict]:
    path = root / "work" / "timeline.json"
    if not path.is_file():
        raise SystemExit(f"TIMELINE_MISSING: {path}")
    timeline = json.loads(path.read_text(encoding="utf-8"))
    return [c for c in timeline["cards"] if c["kind"] != "SRC"]


def narration_order(root: Path) -> list[str]:
    """타임라인에 놓인 나레이션 카드의 card_id 를 순서대로."""
    return [c["card_id"] for c in _narration_cards(root)]

# ── 나레이션 카드는 하이퍼프레임 영상만 쓴다 (2026-09-10 사용자 확정)
# 정지 카드로 조용히 대체하면 회차 절반이 같은 결의 글자판으로 남는다.
# 회차에서 굳이 정지 카드를 쓰려면 cards_def 에 ALLOW_STATIC_NARRATION_CARDS = True 를 둔다.


def static_narration_allowed(cards_def) -> bool:
    return bool(getattr(cards_def, "ALLOW_STATIC_NARRATION_CARDS", False))


def between_image_flag(root: Path, cards_def, covered=None) -> str:
    """정지 이미지 카드가 하나라도 있으면 YES, 전부 움직이는 영상이면 NO.

    119 의 compile 은 between_image=YES 인데 이미지 카드가 없으면
    PRE119_PLAN_IMAGE_CARD_REQUIRED 로 막는다. 하이퍼프레임 회차는 나레이션이
    전부 NARRATION_VIDEO 라 이미지 카드가 0장이다. 고정값을 쓰지 않고 실제
    카드 구성에서 뽑는다.
    """
    covered = hyperframe_files(root) if covered is None else covered
    static = any(c[1] != "SRC" and c[0] not in covered for c in cards_def.CARDS)
    return "YES" if static else "NO"


def require_hyperframes(root: Path, cards_def, covered) -> None:
    """영상이 없는 나레이션 카드가 있으면 만들기 전에 멈춘다."""
    if static_narration_allowed(cards_def):
        return
    missing = [n for n in narration_order(root) if n not in covered]
    if not missing:
        return
    plan = scene_plan(root, only=set(missing))
    lines = [f"HYPERFRAME_MISSING: 나레이션 카드 {len(missing)}개에 영상이 없다.",
             f"필요한 장면 {len(plan)}개:"]
    for sc in plan:
        lines.append(f"  {sc['file']:22} {sc['need_seconds']:7.3f}s  {len(sc['cards'])}장")
    lines.append("plan_hyperframes.py 로 전체 표를 뽑는다.")
    raise SystemExit("\n".join(lines))


def scene_plan(root: Path, target_seconds: float = 10.0, only: set | None = None) -> list[dict]:
    """only 은 카드 id 집합이다."""
    """연속한 나레이션 카드를 열 초 안팎 장면으로 묶는다.

    한 장면을 나눠 쓰는 카드는 타임라인에서 붙어 있어야 한다. 사이에 인용 클립이
    끼면 거기서 장면이 끊긴다. 그 경계를 여기서 정한다.
    """
    timeline = json.loads((root / "work" / "timeline.json").read_text(encoding="utf-8"))
    cards = timeline["cards"]

    def nar(i: int) -> bool:
        return cards[i]["kind"] != "SRC"

    def joined(a: int, b: int) -> bool:
        return (nar(a) and nar(b) and cards[b]["target_start_us"]
                == cards[a]["target_start_us"] + cards[a]["target_duration_us"])

    seen: dict[str, int] = {}
    for c in cards:
        if c["kind"] != "SRC":
            seen[c["narration_name"]] = seen.get(c["narration_name"], 0) + 1
    ambiguous = {n for n, k in seen.items() if k > 1}

    picked = [i for i, c in enumerate(cards)
              if nar(i) and (only is None or c["card_id"] in only)]
    if not picked:
        return []
    runs: list[list[int]] = [[picked[0]]]
    for i in picked[1:]:
        if i == runs[-1][-1] + 1 and joined(runs[-1][-1], i):
            runs[-1].append(i)
        else:
            runs.append([i])

    target = int(target_seconds * 1_000_000)
    plan: list[dict] = []
    for run in runs:
        chunks: list[list[int]] = []
        chunk: list[int] = []
        held = 0
        for i in run:
            chunk.append(i)
            held += cards[i]["target_duration_us"]
            if held >= target:
                chunks.append(chunk)
                chunk, held = [], 0
        if chunk:
            # 꼬리가 너무 짧으면 앞 덩어리에 붙인다. 삼 초짜리 장면은 만들 값이 없다.
            if chunks and held < target / 2:
                chunks[-1] = chunks[-1] + chunk
            else:
                chunks.append(chunk)
        for c in chunks:
            plan.append(_scene_entry(cards, c, ambiguous))
    return plan


def _scene_entry(cards: list, idx: list[int], ambiguous: set | None = None) -> dict:
    """장면 파일명을 정한다.

    나레이션 이름이 회차에서 유일하지 않으면(CTA 한 줄은 두 번 놓인다) 그 이름으로는
    구간을 못 찍는다. 그때는 카드 id 로 이름을 준다.
    """
    ambiguous = ambiguous or set()
    first, last = cards[idx[0]], cards[idx[-1]]

    def token(card: dict) -> str:
        return (card["card_id"] if card["narration_name"] in ambiguous
                else card["narration_name"])

    name = token(first) if len(idx) == 1 else f"{token(first)}-{token(last)}"
    need = sum(cards[i]["target_duration_us"] for i in idx)
    return {"file": f"{name}.mp4", "need_us": need, "need_seconds": need / 1_000_000,
            "start_us": first["target_start_us"],
            "cards": [{"nl": cards[i]["narration_name"],
                       "dur_us": cards[i]["target_duration_us"],
                       "card_id": cards[i]["card_id"]} for i in idx]}
