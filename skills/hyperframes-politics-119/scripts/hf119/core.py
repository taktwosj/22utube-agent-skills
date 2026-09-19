"""Scene paths, strip geometry and narration state. Configured by the caller."""
import json
import pathlib
import sys

DEFAULT_BRAND = "민주 디코더"
DIAGRAM_KINDS = ("timeline", "flow", "relation", "move", "doc")
ROOT = HF = ASSETS = PHOTOS = CAPCUT_119 = None
BRAND = DEFAULT_BRAND
LINES = {}
NL = chr(10)
STRIP_TOP, STRIP_H = 189, 702
DIA_H = STRIP_H - 122


def configure(*, people_art, capcut_119, asset_source):
    """Receive paths explicitly; this package never imports spine."""
    global PHOTOS, CAPCUT_119, ASSETS, STRIP_TOP, STRIP_H, DIA_H
    PHOTOS = pathlib.Path(people_art) / "_src"
    CAPCUT_119 = pathlib.Path(capcut_119)
    ASSETS = pathlib.Path(asset_source)
    STRIP_TOP, STRIP_H = _strip()
    DIA_H = STRIP_H - 122


def _strip() -> tuple[int, int]:
    """119 조립이 남기는 띠 사이 영역 (top, height). 119 스킬을 못 읽으면 같은 값을 그대로 쓴다."""
    try:
        sys.path.insert(0, str(CAPCUT_119 / "scripts"))
        from inset_card_layout import NARRATION_VIDEO_STRIP  # noqa: E402
        return int(NARRATION_VIDEO_STRIP["y"]), int(NARRATION_VIDEO_STRIP["height"])
    except Exception:
        print("HF_STRIP_FALLBACK: 119 inset_card_layout 을 못 읽어 189/702 를 쓴다", flush=True)
        return 189, 702

def init(root, brand=None):
    """회차 루트를 잡는다. brand 를 안 주면 cards_def.HF_BRAND, 그것도 없으면 DEFAULT_BRAND."""
    global ROOT, HF, LINES, BRAND
    ROOT = pathlib.Path(root)
    HF = ROOT / "hyperframes"
    lines = ROOT / "work" / "narration_lines.json"
    if not lines.is_file():
        raise SystemExit(f"NARRATION_LINES_MISSING: {lines} — tts_lines.py 를 먼저 돌린다")
    LINES = {r["name"]: r for r in json.loads(lines.read_text(encoding="utf-8"))}
    BRAND = brand or DEFAULT_BRAND
    for f in ("gsap.min.js", "PretendardVariable.woff2"):
        if not (ASSETS / f).is_file():
            raise SystemExit(f"HF_ASSETS_MISSING: {ASSETS / f}")
    return HF

def _photo_src(person):
    for ext in ("jpg", "png", "jpeg"):
        p = PHOTOS / f"{person}.{ext}"
        if p.is_file():
            return p
    raise SystemExit(f"PEOPLE_PHOTO_MISSING: {person} — {PHOTOS} 에 원본 사진을 넣는다")
