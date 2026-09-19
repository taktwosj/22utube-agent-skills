# -*- coding: utf-8 -*-
"""하이퍼프레임 장면 정의 — render_scenes.py 가 SPECS 를 읽어 hf_lib.build 로 만든다.

복사 위치: <root>/work/scenes.py
장면 하나 = 연속한 나레이션 줄 서넛 = 십 초 안팎. file 이름이 곧 hyperframes/<file>.mp4 다.
plan_hyperframes.py --missing 이 만들어야 할 이름을 찍어 준다.

비트 (hf_lib)
  T(nl, mega, eyebrow, sub)     큰 글씨. 기본값이다
  P(nl, who, rows)              패널. rows = [(키, 값, "cy"|"")]
  Q(nl, who, q, note, accent)   말풍선. 발화자를 who 에
  도식 — 네다섯 장면에 하나. nl 에 줄 목록을 주면 한 도식이 여러 줄 동안 이어진다
    {"nl": [...], "type": "timeline", "kicker", "title", "points": [(날짜, 칩, "cy"|"yl")]}
    {"nl": [...], "type": "flow", "kicker", "title", "nodes": [(icon, 라벨, 작은글, 색)], "bypass": (a, c)}
         색 ∈ cobalt pale teal slate amber · icon 은 hf119.icons.ICON 이름
    {"nl": [...], "type": "relation", "kicker", "title", "hub": (사진이름, 표시이름), "spokes": [(라벨, 작은글)]}
    {"nl": [...], "type": "move", "kicker", "title", "from": (곳, 작은글), "to": (곳, 작은글), "note": "..."}
    {"nl": [...], "type": "doc", "kicker": "매체 · 날짜", "title": "기사 제목", "lines": [(줄, "hl"|"cy"|"")],
         "note": "보도 요지 · 원문 이미지 아님", "reveal": "line"|"all"}   기사 요지를 md 문서처럼. 3~5줄. motion "document"
  장면 옵션  "photo": (사진이름, 이름표, "L"|"R")  인물 원본 사진 액자.  "source": "출처 : 채널명"

강조는 <span class='hl'>옐로</span> 와 <span class='cy'>시안</span> 두 개뿐이다. 한 화면에 옐로는 한 역할.
화면 문구에 아라비아 숫자를 쓴다. 나레이션 원고와 달리 화면은 읽기 쉬운 쪽이 우선이다.
"""
from hf_lib import P, Q, T  # noqa: F401  render_scenes.py 가 스킬 scripts 를 import 경로에 넣는다

C0 = "00 / 질문"
# C1 = "01 / 챕터 제목"

SPECS = [
    # {"file": "NL01", "chapter": "구독과 좋아요", "beats": [
    #     T("NL01", "구독과 <span class='hl'>좋아요</span>", "이 영상이 더 많은 분께 닿도록", "부탁드립니다")]},
    # {"file": "NL02-NL05", "chapter": C0, "beats": [
    #     {"nl": ["NL02", "NL03", "NL04", "NL05"], "type": "timeline", "kicker": "일곱 번의 선거",
    #      "title": "네 번 <span class='hl'>졌다</span>. 그런데",
    #      "points": [("1988", "당선", "cy"), ("1992", "낙선", "yl"), ("2002", "대통령", "cy")]}]},
]
