# -*- coding: utf-8 -*-
"""pre119_handoff.json + upload_package.md. 값은 전부 cards_def.PUBLICATION 에서 온다."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def, package_root, resolve_root, root_parser  # noqa: E402


def hhmmss(us: int) -> str:
    s = us // 1_000_000
    return f"{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}" if s >= 3600 else f"{s//60:02d}:{s%60:02d}"


def main():
    args = root_parser("handoff + 업로드 패키지").parse_args()
    root = resolve_root(args)
    cd = load_cards_def(root)
    pub = cd.PUBLICATION
    tl = json.loads((root / "work" / "timeline.json").read_text(encoding="utf-8"))
    rec = {r["card_id"]: r for r in tl["cards"]}
    sha = (root / "work" / "script_sha.txt").read_text(encoding="utf-8").strip()

    words = pub["thumb_words"]
    if len(words) != 3 or any(len(w) > 5 or " " in w for w in words):
        raise SystemExit("THUMB_WORDS: 정확히 3개, 각 5자 이하, 공백 없음")
    if len(pub["thumb_sentences"]) != 3:
        raise SystemExit("THUMB_SENTENCES: 정확히 3개")

    timeline = [{"at": hhmmss(rec[cid]["target_start_us"]), "label": label} for cid, label in pub["timeline_marks"]]
    used = []
    for c in cd.CARDS:
        if c[1] == "SRC" and cd.SOURCES[c[2]][0] not in used:
            used.append(cd.SOURCES[c[2]][0])
    sources = [{"label": f"출처 : {ch}", "url": None} for ch in used]
    nar = sum(r["target_duration_us"] for r in tl["cards"] if r["kind"] == "NAR") / 1e6
    src = sum(r["target_duration_us"] for r in tl["cards"] if r["kind"] == "SRC") / 1e6

    handoff = {
        "schema": "togun-pre119-handoff-v3", "route": "TOGUN_PRE119_TO_119_DIRECT",
        "editorial_owner": "TOGUN_PRE119", "source_state": "PRE119_SOURCE_CANDIDATE",
        "episode_id": cd.EPISODE_ID, "project_name": cd.PROJECT_NAME,
        "central_question": cd.CENTRAL_QUESTION, "selected_thesis": cd.SELECTED_THESIS,
        "chapter_order": [c[0] for c in cd.CARDS],
        "between_image": "YES", "between_narration": "YES", "lower_mode": "MIXED",
        "execution_mode": "ASSEMBLY_ONLY", "cta_like_subscribe": "OFF",
        "publication_report": {
            "title": pub["title"],
            "content": {"simple_summary": pub["summary"], "timeline": timeline, "sources": sources},
            "thumbnail": {"words": words, "sentences": pub["thumb_sentences"]},
        },
        "minimal_edit_plan": {
            "chapter_count": len({c[6] if c[1] == "SRC" else c[4] for c in cd.CARDS}),
            "cta_like_subscribe": "OFF", "target_runtime_sec_est": round(tl["total_seconds"]),
            "narration_sec_est": round(nar), "source_video_sec_est": round(src),
            "media_download_root": str(root),
        },
        "script_lock": {"current_final_script_sha256": sha},
    }
    pkg = package_root(cd.EPISODE_ID) / "20_script"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "pre119_handoff.json").write_text(json.dumps(handoff, ensure_ascii=False, indent=1), encoding="utf-8")
    up = [f"# 업로드 패키지 — {cd.PROJECT_NAME}", "", "## 제목", "", pub["title"], "", "## 설명", "", pub["summary"], "",
          "### 타임라인", ""] + [f"{t['at']} {t['label']}" for t in timeline] + ["", "### 출처", ""] + \
         [x["label"] for x in sources] + ["", "## 썸네일", "", "단어 3개: " + " / ".join(words), ""] + \
         [f"- {s}" for s in pub["thumb_sentences"]]
    (pkg / "upload_package.md").write_text("\n".join(up) + "\n", encoding="utf-8")
    print("handoff:", pkg / "pre119_handoff.json"); print("upload:", pkg / "upload_package.md")


if __name__ == "__main__":
    main()
