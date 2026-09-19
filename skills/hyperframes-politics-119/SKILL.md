---
name: hyperframes-politics-119
description: "Use when building HyperFrames explainer cards for a Korean political longform or shorts episode — 119 정치롱폼 그래픽, 정치 하이퍼프레임, 설명 카드, 나레이션 카드 영상. Produces 1920x1080 cards in the approved 119 grammar: deep-navy ground, one cyan and one yellow accent, fixed chrome (brand / chapter / source / counter), one distinct visual grammar per chapter, per-beat narration wav embedded, and claim-attribution labels for unverified assertions."
---

## Shared catalog location

For this user's shared catalog, edit the NAS `skills` source configured by ZSkillSync. Local application skill folders are generated copies. Routine skill updates use automatic synchronization and verification; historical Git release instructions apply only to a separately requested Git maintenance task. Resolve machine paths from current environment and local ZSkillSync settings. Production approval, evidence, and application safety gates still apply.

# 119 정치롱폼 하이퍼프레임

`spine-script-119` 가 잠근 나레이션을 받아 설명 카드를 만든다. 119 조립은 이 렌더의 `final.mp4`
를 `NARRATION_VIDEO` 카드의 영상으로 쓴다.

이 문서는 **화면 문법**을 고정한다. 프로젝트 생성·렌더 절차 자체는 `hyperframes-cli` 를 따른다.

승인 근거: 2026-09-11 사용자 승인. 기준 회차 `PL_20260911_한동훈_척추후보`
(`hyperframes_v3` 5종 + `hyperframes_v4` 5종). 맥미니 초안은 기준이 아니다.

## 두 가지 모드

```text
장면 모드   척추대본 119 회차의 나레이션 화면. 현행 기본 (2026-09-13 이재명 · 09-14 노무현 회차)
            만드는 곳  scripts/hf119 (생성) + spine-script-119/scripts/render_scenes.py (실행)
            단위      연속한 나레이션 줄 서넛 = 십 초 안팎 한 장면 = mp4 하나
            오디오    넣지 않는다. 119 조립이 나레이션 wav 를 카드에 붙인다
            자리      1920x1080 렌더 중 y 189~891 만 화면에 나간다. 119 가 위·아래 띠를 잘라 좌우 끝까지
                      1920x702 로 놓는다. 글자·도식·크롬은 그 띠 사이에만 (2026-09-15)
            크롬      좌상단 브랜드 · 우상단 NN / 챕터명 · 하단 진행선 · (필요할 때) 좌하단 출처
            화면      큰 글씨 비트(제목·패널·말풍선)가 기본. 네다섯 장면에 하나꼴로 도식
                      (timeline · flow · relation · move). 도식은 선이 그려지고 아이콘이 이동한다
카드 모드   챕터마다 다른 시각 문법을 쓰는 설명 카드. 아래 10종 문법·비트 구조·작업지시문
            비트마다 wav 를 임베드하고 네 모서리 크롬을 고정한다 (2026-09-11 기준 회차)
```

spine-script-119 회차는 장면 모드로 만든다. 카드 모드는 사용자가 챕터별 설명 카드를 따로 요청할 때 쓴다. 두 모드는 색·폰트·배경·격자·강조 규칙과 `하지 않는 것` 을 같이 따른다. 장면 모드의 절차·비트는 [references/scene-mode.md](references/scene-mode.md)에 있다. 장면 모드의 CSS 를 회차 스크립트에서 다시 쓰지 않는다. 정본은 `scripts/hf119/`다.

## 상세 문서

| 주제 | 파일 | 언제 읽나 |
|:--|:--|:--|
| 카드 모드 비트 구조·작업지시문·척추 단계 | [references/card-mode.md](references/card-mode.md) | 카드 모드로 설명 카드를 만들 때 |
| 공용 모듈 politics119_style.py | [references/shared-module.md](references/shared-module.md) | 카드 CSS·헬퍼를 쓸 때 |
| 장면 유형별 모션 조합·상한 | [references/motion/index.md](references/motion/index.md) | 장면에 모션 프리셋을 고를 때 |

## 고정 값

```text
크기      1920x1080, 30fps
폰트      Pretendard Variable — assets/PretendardVariable.woff2 로컬 임베드
모션      GSAP — assets/gsap.min.js 로컬. CDN 의존 금지
아이콘    Phosphor. 라이선스 파일 같이 복사
배경      radial-gradient(ellipse at 60% 20%, #164577, #06172f 70%)
격자      80px, #5486af12 — data-layout-ignore
본문      #f1f7ff
강조 1    시안 #63e2ef · #72e3eb · #8ef0ee
강조 2    옐로 #ffe276  ← 한 화면에 한 역할로만
어두운 판  #0d2c4c / #0b2947 / #123a63
밝은 판    #eaf2f7 (글자 #112d46)
```

강조색은 두 개뿐이다. 세 번째 색을 들이지 않는다. 옐로는 "대비되는 한 쪽"에만 쓴다.
양쪽 다 옐로면 대비가 죽는다.

## 크롬 — 네 모서리 고정

```text
좌상단   브랜드 라벨. 회차 내내 같은 문구. 좌측 5px 시안 보더
우상단   NN / 챕터명   (01 / 오프닝, 07 / 수사 타깃 주장 …)
좌하단   출처 : <채널명>   플랫폼·영문 병기·제목 금지
우하단   NN / 총개수      (02 / 03)
```

출처 표기는 채널명만 쓴다. 보도 근거일 때는 매체명만 쓴다.

## 시각 문법 — 챕터마다 다르게 (카드 모드)

같은 문법을 두 챕터에 쓰지 않는다. 전부 같은 결이면 화면이 죽는다.
현재 승인된 10종이다. 새 챕터는 여기서 고르거나 새로 만든다.

```text
01 키네틱 타이포    대각 리본 + 초대형 단어 등장. 오프닝 전용
02 카드 스택        종이 더미 깊이 + 숫자 히어로 + 처분 스탬프. 문서를 보여줄 때
03 녹취 대조        편집 시트에 줄 번호 + 이동하는 형광 + 여백 주석. 발췌·누락
04 경로 연결        비대칭 노드 + 구간 연결선 + 패킷. 전달 경로
05 타임라인         큰 날짜 + 펼쳐지는 레일. 시간순
06 기울어지는 저울  주장 슬래브 대 기록 슬래브, 빔이 기운다. 대립
07 이중 레일        두 갈래가 한 표적으로 수렴. 투트랙 수사
08 단계 스테퍼      고발 → 배당 → 진행. 절차 진행
09 정산 원장        행이 쌓이며 상태 칩이 붙는다. 마무리
10 안내             중앙 정렬 2판. CTA 전용
```

## 주장 라벨링 — 빼면 안 된다

보도로 확인된 사실과 출연자·기자의 주장을 화면에서 갈라 놓는다.

```text
챕터 라벨   확인 안 된 주장이면 라벨 자체에 붙인다
            예) 수사 타깃 주장 · 검찰 확인 없음
아이브로우  발화자를 앞에 세운다
            예) 봉지욱 기자 주장 · 검찰 확인 없음
표현 대조   같은 사안에 표현이 갈리면 좌우로 나누고 고지를 단다
            예) 두 표현은 같지 않습니다 · 하나는 기자의 요약, 하나는 당사자의 전언
상태 칩     마무리 원장에서 행마다 등급을 붙인다
            보도로 확인(시안) / 수사 중(보라) / 기자 주장(옐로)
원문 아님   원문 이미지가 아닌 재구성 카드에는 `보도 요지 · 원문 이미지 아님`
```

## 검사

```text
index.motion.json 에 staysInFrame 어서션을 넣는다 — 문구가 잘리는 것을 잡는다
첫 비트에는 appearsBy 를 건다
hyperframes check --strict --snapshots 로 exit 0
render --quality high --fps 30 로 exit 0
logs/check.exit, logs/render.exit 를 증거로 남긴다
스냅샷을 눈으로 확인한다. check 가 통과해도 대비·겹침은 사람이 본다
```

## 하지 않는 것

```text
CDN 로드                로컬 assets 만 쓴다
실존 인물 얼굴 생성      쇼츠 삽화와 같은 규칙이다
화면 안 글자 생성 이미지  타이포는 HTML 로만
세 번째 강조색
같은 시각 문법 재탕
확인 안 된 주장을 라벨 없이 단정
플랫폼명·영문 병기 출처
민주 블루 인셋 카드 템플릿    `democratic_blue_inset_card_v2`, `democratic_blue_center_info_card_v1`,
                              `render_democratic_blue_card.py` 로 만드는 정지 이미지 카드는
                              이 회차 계열에서 쓰지 않는다. 설명 카드는 HyperFrames 로만 만든다.
                              정지 이미지 카드는 움직임이 없어 같은 화면이 길게 이어진다
```


## 유지보수 검사

`scripts/self-check.sh`로 패키지·연결 파일을 확인한다. 정치 체인 4개 스킬 크기는 `python scripts/check_skill_sizes.py`로 확인한다. UTF-8 바이트 기준 SKILL.md 8 KiB, references 6 KiB, Python 15 KiB 초과는 경고만 내고 종료 코드 0을 유지한다. 테스트·백업·캐시는 크기 점검에서 제외한다.
