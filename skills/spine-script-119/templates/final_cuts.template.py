# -*- coding: utf-8 -*-
"""최종 컷표 — make_cards.py 가 이 파일과 narration_lines.json 으로 cards_def.CARDS 를 새로 쓴다.

복사 위치: <root>/work/final_cuts.py

행: (key, kind, video_id, in_sec, out_sec, 메모)
kind: H 몽타주 / S 척추(진행자 평론·증언) / B 사건 원본·살. 척추 비율은 S 로 센다.  순서가 곧 타임라인 순서다.

경계 잡는 법 (2026-09-14 노무현 회차)
  1. cues.json(vtt_clean) 으로 대략 구간을 찾는다.
  2. 자동자막 cue 경계는 문장 중간에 걸리는 일이 많다. 후보 구간만 whisper 로 받아써서
     말이 시작·끝나는 시각을 대조해 in/out 을 찍는다. 받아쓰기는 scratchpad 에 둔다.
  3. 찍은 뒤 cards_def.TOPIC_RANGE 에 소스별 사용 구간을 적는다. 밖으로 나가면 check_captions 가 막는다.
  4. python final_cuts.py 로 H/S/B 합계를 본다. 척추 15분은 S 합으로 센다 (몽타주 재사용 제외).
"""

# 오프닝 몽타주. 본편에서 쓸 6~10초 구간 5~9개, 세기 순. 아군 내부의 경고·자기비판을 앞에.
MONTAGE = [
    # ("H1", "H", "video_id", 102.7, 108.7, "훅 한 줄"),
]

# (나레이션 블록, 그 블록 뒤에 붙는 컷들). 블록 순서는 cards_def.NARRATION_ORDER 에서 N_CTA 를 뺀 것과 같다.
# 컷이 없는 블록도 적는다 — 나레이션만 이어진다.
BODY = [
    # ("N_OPEN", [("OPEN_S", "S", "video_id", 22.0, 96.6, "첫 증언")]),
    # ("N_Q1A",  [("Q1_B", "B", "video_id", 594.2, 608.3, "사건 원본")]),
    # ("N_CLOSE", []),
]

# 블록 → (챕터 짧은 이름, 챕터 제목). 화면 자막 칩과 타임라인 표지에 쓴다.
CHAPTERS = {
    # "N_OPEN": ("질문", "네 번 진 사람"),
}


def all_cuts():
    out = list(MONTAGE)
    for _, cuts in BODY:
        out += cuts
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    tot = {"H": 0.0, "S": 0.0, "B": 0.0}
    for k, kind, v, a, b, m in all_cuts():
        tot[kind] += b - a
    print({k: round(x, 1) for k, x in tot.items()}, "sum", round(sum(tot.values()), 1))
