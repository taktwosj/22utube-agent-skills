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
