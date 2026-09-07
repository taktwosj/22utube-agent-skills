# -*- coding: utf-8 -*-
"""회차 정의 — 이 파일 하나만 회차마다 새로 쓴다. 스킬 스크립트는 전부 여기서 읽는다.

복사 위치: E:\\22utube\\<EPISODE_ID>\\work\\cards_def.py
"""

EPISODE_ID = "PL_YYYYMMDD_주제_부제"
PROJECT_NAME = "CapCut 프로젝트명 (한글 짧게)"
SPINE_VIDEO_ID = "척추 영상 video_id"   # 척추 비율 계산에 쓴다

# video_id: (channel 정식명, 업로드일, 화면 출처 표기)  — 출처 표기는 채널명만
SOURCES = {
    # "SrNJjPTkRCg": ("저널리스트", "2026-08-27", "저널리스트"),
}
# 방송 자막이 화면에 박힌 소스. 하단 슬롯을 비운다. ffmpeg 로 프레임 뽑아 눈으로 확인한 것만 넣는다.
BURNED_CAPTION = set()

# 나레이션 블록 순서. Typecast 붙여넣기 순서와 같아야 한다. 앞뒤 CTA 포함.
NARRATION_ORDER = ["N_CTA", "N_WHY", "N01", "N02", "N03", "N_CTA"]

# 쇼츠. 나레이션 원고를 쓰기 전에 채운다 — mark_shorts.py 가 여기서 읽는다.
# claim   상대가 던지는 문장.   counter  상대가 못 받아치는 사실 한 줄 (회차에서 가장 센 것)
# 나레이션은 롱폼 wav 를 역할로 골라 쓴다. 붙어 있는 줄을 그냥 가져오지 않는다.
SHORTS = [
    # dict(slug="01_주제", project_name="쇼츠_회차_주제",
    #      source="video_id", start=0.0, end=0.0,
    #      claim="상대가 던지는 문장",
    #      counter="상대가 못 받아치는 사실 한 줄",
    #      t1="열두 자 이하", t2="열두 자 이하",
    #      mentions=[(0.5, 7.0, "열네 자 이하", "normal"),
    #                (14.0, 21.0, "뒤집는 사실", "anger")],
    #      head_narration=["NL01"], tail_narration=["NL02"],
    #      art="01_삽화이름.png"),
]

CENTRAL_QUESTION = "한 문장 질문"
SELECTED_THESIS = "판정 두세 문장"

# 화면 자막에서 한글 숫자를 아라비아 숫자로 되돌릴 쌍. 음성은 손대지 않는다.
DISPLAY_NUMERALS = [
    # ("천구백칠십오년", "1975년"),
]
# check_captions 가 볼 회차 고유 인명·용어 (정확 표기)
GLOSSARY = []

PUBLICATION = {
    "title": "제목 — 결말을 다 말하지 않는다",
    "summary": "설명란 요약. 아라비아 숫자 사용 가능.",
    "timeline_marks": [  # (card_id, 표시 문구) — 12개 내외
        ("C00_HOOK_01", "오프닝"),
    ],
    "thumb_words": ["단어1", "단어2", "단어3"],          # 각 5자 이하, 공백 없음. 충격 소재 → 타이밍 → 결과 텐션
    "thumb_sentences": ["의문 1", "의문 2", "의문 3"],   # 연속 의문. `~했다` 요약 금지
}

CTA = {"top_label": "구독과 좋아요", "headline1": "이 영상이 도움이 되셨다면", "headline2": "구독과 좋아요 부탁드립니다",
       "footer": "채널에 큰 힘이 됩니다", "block_label": "CTA", "block_main": "구독 · 좋아요", "block_sub": "알림 설정까지",
       "css": "grid", "hl": ["구독", "좋아요"]}


def N(narr, label, title, hook, why, top, h1, h2, foot, bl, bm, bs, css, hl=()):
    """NAR 카드. 글자수 한도: top 32 / h1,h2 28 / foot 52 / bl 16 / bm 24 / bs 42.
    css ∈ grid scale ratio time num flow quote warn split herd"""
    return (narr, label, title, hook, why,
            {"top_label": top, "headline1": h1, "headline2": h2, "footer": foot,
             "block_label": bl, "block_main": bm, "block_sub": bs, "css": css, "hl": list(hl)})


def cta(narr, label="오프닝"):
    return (narr, label, label, "구독과 좋아요", "CTA",
            {k: CTA[k] for k in ("top_label", "headline1", "headline2", "footer", "block_label",
                                 "block_main", "block_sub", "css", "hl")})


# SRC: (card_id, "SRC", video_id, in_sec, out_sec, chapter_label, chapter_title, hook, why)
# NAR: (card_id, "NAR") + N(...)   — NL01.. 은 split_tts_lines 가 만든 줄 단위 wav 이름
CARDS = [
    # ---- 오프닝 몽타주 6개 (본편 재사용, 6~10초, 세기 순, 아군 내부 경고 먼저) ----
    # ("C00_HOOK_01", "SRC", "vid", 9.92, 17.02, "오프닝", "오프닝", "훅 한 줄", "왜 이 순서인가"),
    # ("C00_CTA", "NAR") + cta("NL01"),
    # ---- 취지 나레이션 (줄 단위 카드) ----
    # ("C01_WHY_1", "NAR") + N("NL02", "왜 이 영상인가", "취지", "훅", "왜", "탑라벨", "헤드1", "헤드2", "푸터", "블록라벨", "블록메인", "블록서브", "quote"),
    # ---- 척추 ① ... ⑤ 를 초·중·후반에 분산. 사이사이 살 SRC + 다리 NAR ----
]
