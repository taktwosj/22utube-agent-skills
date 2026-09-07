# -*- coding: utf-8 -*-
"""cards_def + timeline.json -> 119_final_script.md (승인 대본 + ASSEMBLY_ONLY_SEED)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def, package_root, resolve_root, root_parser  # noqa: E402


def hms(us):
    s = us / 1_000_000
    return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{s%60:06.3f}"


def main():
    args = root_parser("승인 대본 생성").parse_args()
    root = resolve_root(args)
    cd = load_cards_def(root)
    tl = json.loads((root / "work" / "timeline.json").read_text(encoding="utf-8"))
    rec = {r["card_id"]: r for r in tl["cards"]}
    ids = [c[0] for c in cd.CARDS]
    narr = root / "narration"

    body, seed = [], ["[ASSEMBLY_ONLY_SEED]"]
    for k, v in [("execution_mode", "ASSEMBLY_ONLY"), ("time_policy", "USE_ACTUAL_DURATION"),
                 ("target_runtime_lock", "false"), ("replan_allowed", "false"),
                 ("source_research_allowed", "false"), ("approved_asset_recheck", "false"),
                 ("lower_slot_exclusive", "true"), ("cta_default", "OFF"), ("between_image", "YES"),
                 ("between_narration", "YES"), ("lower_mode", "MIXED"), ("cta_like_subscribe", "OFF")]:
        seed.append(f"{k}: {v}")
    seed.append("")

    for i, card in enumerate(cd.CARDS):
        cid, kind = card[0], card[1]
        nxt = ids[i + 1] if i + 1 < len(ids) else "END"
        r = rec[cid]
        t0, t1 = hms(r["target_start_us"]), hms(r["target_start_us"] + r["target_duration_us"])
        if kind == "SRC":
            vid, _, _, label, title, hook, why = card[2:]
            ch, date, disp = cd.SOURCES[vid]
            lower = "NONE" if vid in cd.BURNED_CAPTION else "SRT"
            body += [f"### {i+1:02d} `{label}` — `{t0}` ~ `{t1}`", f"- 화면: {ch} {date} 보도 화면",
                     "- 원음: 원본 발화 그대로", "- 나레이션: 없음", f"- 상단 챕터 제목: {label}",
                     f"- 하단: {'없음' if lower == 'NONE' else '원본 SRT'}", "- 논거·의견 1줄: 없음",
                     "- 순차 논거·의견 2문장: 없음", f"- 다음 카드: {nxt}", ""]
            seed += ["[CARD]", f"order: {i+1}", f"card_id: {cid}", "card_type: SOURCE_VIDEO",
                     f"chapter_label: {label}", f"chapter_title: {title}", f"chapter_hook: {hook}",
                     f"source_display_label: {disp}", f"source_id: {vid}", "source_range_policy: CANDIDATE_WAIT_A",
                     f"source_in_candidate: {hms(int(r['source_in']*1_000_000))}",
                     f"source_out_candidate: {hms(int(r['source_out']*1_000_000))}",
                     "visual_asset_ref: WAIT_A", "visual_role: PRIMARY_SOURCE", "style_profile: N/A",
                     "narration_asset_ref: N/A", "narration_text:", "source_audio: ON", "narration_audio: OFF",
                     f"lower_mode: {lower}", "lower_line1:", "lower_line2:", "cta_like_subscribe: OFF",
                     f"why_this_segment: {why}", f"next_card: {nxt}", "[/CARD]", ""]
        else:
            nm, label, title, hook, why, _ = card[2:]
            flat = " ".join((narr / f"{nm}.txt").read_text(encoding="utf-8").split())
            body += [f"### {i+1:02d} `{label}` — `{t0}` ~ `{t1}`", "- 화면: 민주블루 인셋 카드", "- 원음: 없음",
                     f"- 나레이션: {flat}", f"- 상단 챕터 제목: {label}", "- 하단: 나레이션 TTS",
                     "- 논거·의견 1줄: 없음", "- 순차 논거·의견 2문장: 없음", f"- 다음 카드: {nxt}", ""]
            seed += ["[CARD]", f"order: {i+1}", f"card_id: {cid}", "card_type: NARRATION_IMAGE",
                     f"chapter_label: {label}", f"chapter_title: {title}", f"chapter_hook: {hook}",
                     "source_id: N/A", "source_range_policy: N/A", "source_in_candidate:", "source_out_candidate:",
                     "visual_asset_ref: WAIT_C", "visual_role: CHAPTER_TRANSITION",
                     "style_profile: DEMOCRATIC_BLUE_INSET_CARD_V2", "narration_asset_ref: WAIT_B",
                     f"narration_text: {flat}", "source_audio: OFF", "narration_audio: ON", "lower_mode: SRT",
                     "lower_line1:", "lower_line2:", "cta_like_subscribe: OFF", f"why_this_segment: {why}",
                     f"next_card: {nxt}", "[/CARD]", ""]
    seed.append("[/ASSEMBLY_ONLY_SEED]")

    total = tl["total_seconds"]
    head = [f"# PRE-119 승인 완료 대본 — {cd.PROJECT_NAME}", "", "```text", f"episode_id       {cd.EPISODE_ID}",
            "editorial_owner  TOGUN_PRE119", "execution_mode   ASSEMBLY_ONLY", "production_mode  C_NARRATION_VIDEO_MIX",
            f"총 길이          {total:.2f}s ({total/60:.2f}분)", f"카드 수          {len(cd.CARDS)}", "```", "",
            "## HOOK_LOCK", "", "첫 마흔다섯 초는 본편 발화만 세기 순으로 붙인 몽타주다. 나레이션과 상단 요약을 얹지 않는다.", "",
            "## 논제", "", f"- CENTRAL_QUESTION: {cd.CENTRAL_QUESTION}", f"- SELECTED_THESIS: {cd.SELECTED_THESIS}", "",
            "## CHAPTER_LOCK_TABLE", "", "| order | card_id | type | chapter_label | 출처 |", "|---|---|---|---|---|"]
    for i, card in enumerate(cd.CARDS):
        if card[1] == "SRC":
            head.append(f"| {i+1} | `{card[0]}` | SOURCE_VIDEO | {card[5]} | {cd.SOURCES[card[2]][2]} |")
        else:
            head.append(f"| {i+1} | `{card[0]}` | NARRATION_IMAGE | {card[3]} | 나레이션 |")
    head += ["", "## 세로 시간순 승인 대본", ""]

    out = package_root(cd.EPISODE_ID) / "20_script" / "119_final_script.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(head + body + ["## ASSEMBLY_ONLY_SEED", ""] + seed) + "\n", encoding="utf-8")
    sha = hashlib.sha256(out.read_bytes()).hexdigest().upper()
    (root / "work" / "script_sha.txt").write_text(sha, encoding="utf-8")
    print("script:", out); print("sha256:", sha); print("cards:", len(cd.CARDS), "total:", f"{total:.2f}s")


if __name__ == "__main__":
    main()
