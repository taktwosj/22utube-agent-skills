# -*- coding: utf-8 -*-
"""회차 루트 해석과 cards_def 로더. 모든 스크립트가 이걸로 시작한다.

회차 루트는 `--root E:\\22utube\\<episode_id>` 이고, 회차 정의는 `<root>/work/cards_def.py` 다.
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

SKILL_ROOT = Path(__file__).resolve().parent.parent
CAPCUT_119 = Path(r"C:\Users\arajun\.claude\skills\119-politics-longform-capcut")
JUNGCHI_ROOT = Path(r"C:\Users\arajun\OneDrive\22utube\22factory_20260628\0000jungchi")
ALLOWLIST = Path(r"C:\Users\arajun\.claude\skills\togun-politics-pre119-writer"
                 r"\references\approved-channel-allowlist.json")


def root_parser(desc: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--root", type=Path,
                   default=Path(os.environ["SPINE_EPISODE_ROOT"]) if os.environ.get("SPINE_EPISODE_ROOT") else None,
                   help=r"회차 루트 (E:\22utube\<episode_id>). 환경변수 SPINE_EPISODE_ROOT 로 대체 가능")
    return p


def resolve_root(args) -> Path:
    if args.root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")
    root = Path(args.root)
    if not (root / "work" / "cards_def.py").is_file():
        raise SystemExit(f"CARDS_DEF_MISSING: {root / 'work' / 'cards_def.py'}")
    return root


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
    return mod


def package_root(episode_id: str) -> Path:
    return JUNGCHI_ROOT / episode_id / "00_pre119_package"


def load_allowlist() -> dict:
    return json.loads(ALLOWLIST.read_text(encoding="utf-8"))


SHORTS_ROOT = Path(r"E:\22utube\_shorts")
SHORTS_ART = Path(r"E:\22utube\_images\woodcut")
SHORTS_CAPCUT_ROOT = "P0_ROOT_shrt_119short_v1"
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


HYPERFRAME_SCENE = re.compile(r"^(NL\d+)-(NL\d+)$")


def hyperframe_files(root: Path) -> dict[str, Path]:
    """하이퍼프레임 영상을 나레이션 이름에 건다.

    두 가지 이름을 받는다.

        NL88.mp4        그 한 줄만 덮는 영상
        NL88-NL90.mp4   NL88 부터 NL90 까지 연속한 여러 줄을 한 장면으로 덮는 영상

    긴 장면 쪽이 본래 쓰임이다. 카드마다 따로 만들면 삼 초짜리가 줄줄이 이어져
    끊긴 화면이 되고, 나레이션이 이어지는 동안 그래픽도 이어져야 한다.
    반환은 나레이션 이름 하나당 파일 하나이며, 한 줄이 두 파일에 걸리면 멈춘다.
    """
    folder = root / "hyperframes"
    if not folder.is_dir():
        return {}
    claimed: dict[str, Path] = {}

    def claim(name: str, path: Path) -> None:
        if name in claimed and claimed[name] != path:
            raise SystemExit(f"HYPERFRAME_DUPLICATE_CLAIM: {name} <- {claimed[name].name}, {path.name}")
        claimed[name] = path

    for path in sorted(folder.glob("*.mp4")):
        stem = path.stem
        scene = HYPERFRAME_SCENE.match(stem)
        if scene:
            for name in scene_members(root, scene.group(1), scene.group(2)):
                claim(name, path)
        elif re.fullmatch(r"NL\d+", stem):
            claim(stem, path)
    return claimed


def scene_members(root: Path, first: str, last: str) -> list[str]:
    """장면이 덮는 나레이션 이름을 타임라인 순서대로 돌려준다."""
    order = narration_order(root)
    try:
        a, b = order.index(first), order.index(last)
    except ValueError as exc:
        raise SystemExit(f"HYPERFRAME_SCENE_UNKNOWN_LINE: {first}-{last}") from exc
    if b < a:
        raise SystemExit(f"HYPERFRAME_SCENE_REVERSED: {first}-{last}")
    return order[a:b + 1]


def narration_order(root: Path) -> list[str]:
    """타임라인에 놓인 나레이션 카드를 순서대로."""
    path = root / "work" / "timeline.json"
    if not path.is_file():
        raise SystemExit(f"TIMELINE_MISSING: {path}")
    timeline = json.loads(path.read_text(encoding="utf-8"))
    return [c["narration_name"] for c in timeline["cards"] if c["kind"] != "SRC"]
