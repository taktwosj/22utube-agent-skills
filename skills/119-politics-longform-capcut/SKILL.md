---
name: 119-politics-longform-capcut
description: Use only when a political-longform request explicitly contains CapCut, 캡컷, 119, or 119정치롱폼.
---

# 119 정치롱폼 CapCut 제작

119는 투군 PRE-119가 승인까지 끝낸 정치롱폼 설계를 실제 source·narration·visual·root 자산과 결합해 편집 가능한 로컬 CapCut 프로젝트로 조립한다.

사용자가 CapCut, 캡컷, 119, 119정치롱폼을 명시했을 때 사용한다. 명시 호출이 없으면 119로 자동 우회하지 않는다.

## 시작

1. `episode_id`, active writer, 사용자 요청 결과를 확인한다.
2. PRE-119가 최초 승인 대본을 만들 때는 [pre119-approved-script.md](templates/pre119-approved-script.md)를 사용한다. 영상만, 영상+나레이션, 영상+나레이션+HTML 챕터 이미지와 하단 3종을 한 형식에서 선택한다.
3. `20_script/pre119_handoff.json`, `togun-pre119-handoff-v3`, `TOGUN_PRE119_TO_119_DIRECT`, `EDITORIAL_OWNER=TOGUN_PRE119`, `PRE119_SOURCE_CANDIDATE` 중 강한 표식 하나가 있거나 보조 표식 두 개 이상이면 승인 여부보다 먼저 [pre119-handoff-contract.md](references/pre119-handoff-contract.md)를 읽는다.
4. PRE-119 경로가 선택되면 `validate_pre119_handoff.py`가 PASS하기 전 direct-script로 fallback하지 않는다.
5. 승인 대본에 `[ASSEMBLY_ONLY_SEED]` 또는 `execution_mode=ASSEMBLY_ONLY`가 있으면 `ASSEMBLY_ONLY` 조립 경로를 최우선으로 적용한다.
6. PRE-119가 아니고 승인 대본도 없을 때만 [direct-script.md](references/direct-script.md)를 읽는다.
7. 현재 단계의 reference만 읽으며 관련 없는 문서를 미리 읽지 않는다.

## 에피소드 저장 루트

앞으로 시작하는 모든 119 정치롱폼 에피소드의 경량 산출물과 작업 루트는 `<factory-root>\0000jungchi\<episode_id>`다. 시작할 때 해당 에피소드 폴더를 만들며, 기존 에피소드 파일은 이동하지 않는다. 원본 CapCut draft·cache·원본 MP4·Media 폴더 등 무거운 로컬 미디어는 소유 계약이 달리 정하지 않는 한 계속 machine-local에 둔다.

## Installed copies are immutable

다음 설치 경로의 파일은 직접 create·edit·copy·delete·relink하지 않는다.

- `%USERPROFILE%\.codex\skills\119-politics-longform-capcut`
- `%USERPROFILE%\.claude\skills\119-politics-longform-capcut`
- `%USERPROFILE%\AppData\Local\hermes\skills\22utube\119-politics-longform-capcut`

119 스킬 변경은 Git 정본 저장소 `taktwosj/22utube-agent-skills`의 `skills/119-politics-longform-capcut`에서만 수행한다. 공유 정본은 원격 `main`이다.

로컬 작업 경로는 고정하지 않는다. 그 저장소의 깨끗한 worktree면 어디든 된다. 특정 PC나 특정 절대경로를 정본이라고 부르지 않는다. 어떤 경로가 정본인지 확인할 때는 `git remote -v`로 저장소를 확인하고 `git log`로 해당 커밋이 `main`에 있는지 본다.

변경은 commit하고 `main`에 반영한 뒤, 동일한 source commit에서 공식 release `publish → activate → verify`를 실행한다.

브랜치에만 있고 `main`에 없는 변경은 아직 공유 정본이 아니다. 설치본이나 `main`을 읽고 최신이라고 단정하지 마라. 둘 다 마지막 release 시점의 상태이며 그 사이의 브랜치 작업은 보이지 않는다.

## 생산 중 계약 충돌

생산 중 승인 계획이 스킬 계약과 충돌하면 스킬을 수정하거나 우회책을 만들지 않는다. 첫 불일치에서 중단하고 문제·증거·영향·안전 rollback point를 보고한 뒤, 사용자에게 다음 중 정확히 하나를 선택하게 한다.

1. `별도승인 이번작업만` — 이 에피소드에 한정한 최소 one-off workaround만 허용하며 스킬은 수정하지 않는다.
2. `일단정지 어떤문제인지보고만` — workaround와 스킬 변경 없이 문제만 보고한다.
3. `스킬수정하기(스킬수정폴더에서)` — Git 정본 스킬 폴더만 수정하고 test·review·commit한 뒤 공식 release flow로 배포한다.

어느 선택에서도 Codex·Claude·Hermes installed copy를 직접 편집하지 않는다.

| 관찰 가능한 상태 | 읽을 문서 | 상태 |
|---|---|---|
| PRE-119 강한 표식 1개 또는 보조 표식 2개 이상 | `pre119-handoff-contract.md` | `PRE119_VALIDATION` |
| 대본 미승인 | `direct-script.md` | `CAN_DRAFT` 또는 `WAIT_SCRIPT_APPROVAL` |
| PRE-119 PASS + 승인 대본 + ASSEMBLY_ONLY_SEED | 이 문서 + 현재 책임 reference | `ASSEMBLY_ONLY_READY` |
| 직접 대본 승인·제공 | 이 문서의 직접 경로 | `DIRECT_SCRIPT_READY` |
| 기존 Stage 2 산출물 사용을 명시 | `legacy-stage2.md` | `LEGACY_STAGE2_PREFLIGHT` |
| 실패 단계가 불명확 | `resume-map.md` | 한 단계 선택 |

직접 경로 최소 입력은 `episode_id`, 승인된 최종 대본, 출처 URL·원본 SRT·로컬 미디어 중 하나 이상이다. 직접 경로는 110·111, 외부 검토 영수증, review packet, locked-clips 패킷에 의존하지 않는다.

## PRE-119 승인 잠금

PRE-119 입력은 다음 validator를 통과해야 한다.

```powershell
python scripts/validate_pre119_handoff.py `
  --package-root <pre119-package> `
  --approved-script-sha256 <user-approved-final-script-sha256> `
  --approval-evidence <user_message:id-or-runtime_approval:id>
```

PASS 전에는 `episode_cards.json`을 만들지 않는다. 패킷 내부의 `PASS`나 승인 필드는 외부 사용자 승인 evidence를 대신하지 못한다.

## ASSEMBLY_ONLY 잠금

`ASSEMBLY_ONLY_SEED`는 투군 PRE-119가 다음을 확정했다는 뜻이다.

```text
카드 순서
CARD_TYPE
상단 `chapter_label` 챕터 제목
챕터 제목·훅
나레이션 대사
HTML/CSS 설명카드 문구
하단 SRT | 순차 논평 2문장 | NONE
논평 입력 2줄(화면에는 한 번에 한 줄)
CTA 정책
WHY_THIS_SEGMENT
```

119는 다음 런타임 값만 결합한다.

```text
실제 파일 경로
SHA-256
실제 duration
검증된 source range
source channel/date/speaker
narration audio/SRT
rendered image
target start/duration
```

동일 identity·SHA·duration의 실제 PASS 산출물이 있으면 다시 조사·검증·생성하지 않는다.

화면용 문구는 승인 콘텐츠 안에서 독립 편집값으로 다룬다.

- `chapter_title`은 챕터의 의미·논지를 기록하고, `chapter_label`은 실제 상단 오버레이 문구다. 둘은 모두 비어 있지 않아야 하지만 서로 달라도 된다.
- `source_display_label`은 짧은 화면 출처명이다. 비어 있으면 검증된 `source_channel`을 사용하며, 출처의 정체성을 바꾸는 별칭은 허용하지 않는다.
- 이 유연성은 화면용 축약·후킹·배치 문구에만 적용한다. 승인 대본, 직접인용, 나레이션, 카드 순서와 사실관계는 그대로 잠근다.

허용 흐름:

```text
PRE119_VALIDATION=PASS
→ 기존 또는 필요한 A/B/C/D 자산
→ episode_cards.json
→ ASSEMBLY_PREFLIGHT
   - CAPTION_LAYOUT
   - SRT_TEXT_FIDELITY
   - USER_FINAL_ASSEMBLY_GRID
→ clean build
→ relink
→ save/close
→ readback
→ media resolution
→ visual gate
```

ASSEMBLY_ONLY 회차에서 금지:

```text
정치 이슈 재조사
승인 대본 재작성·재검토
기존 PASS source metadata·exact quote 재검증
목표 초를 맞추기 위한 강제 retime
GRID 보완용 추가 조사
builder 기능개선·TDD·candidate code 수정
새 adapter·독립 code review
정상 PASS 단계 전체 재실행
build 후 active draft 직접 수술
```

현재 조립을 실제로 불가능하게 만드는 결함이면 자동 개발 작업으로 확장하지 않고 `ASSEMBLY_BLOCKED:<정확한 원인>`으로 중단한다.

## 승인 뒤 A–D

없는 필수 산출물만 만들고 기존 PASS 산출물은 재사용한다.

| 작업 | 읽을 문서 | 독점 출력 |
|---|---|---|
| A 출처·SRT·다운로드·로컬 컷 | `source-media.md` | source media와 source captions |
| B 나레이션·정렬·SRT | `narration.md` | narration media와 narration SRT |
| C 민주블루 HTML/CSS 설명카드 등 | `visual-assets.md` | episode `Resources` 자산 |
| D 근본·target·CapCut 종료 준비 | `capcut-assembly.md` 준비 절 | 공식 resolver 결과 |

A–D는 다른 작업의 state·산출물·CapCut draft·`episode_cards.json`을 수정하지 않는다. 모두 준비된 뒤 join owner 한 명만 실제 산출물을 `episode_cards.json`으로 합친다. 이 파일이 유일한 조립 Source of Truth다.

현재 조립 기준은 사용자 수동 `V8_MANUAL_OVERLAY_65` 근본이다. [clean-assembly-harness.md](references/clean-assembly-harness.md)를 먼저 읽고 `build_politics_v8_project.py`로 clean build한다. 기존 active v7 builder로 자동 후퇴하지 않는다. 파일명·테스트 미디어 이름이 아니라 12개 고정 트랙의 역할·geometry·문구 슬롯과 경로 경계를 계약으로 사용한다.

## 전체 하단 자막 화면 계약

적용 대상:

```text
SOURCE_TTS
NARRATION_TTS
VIDEO100_EXPLAINER
```

잠금값:

```text
TARGET_CHARS_PER_LINE = 15
MAX_LINES             = 1
TARGET_CHARS_PER_CUE  = 15
HARD_MAX_LINE_CHARS   = 15
```

- `TARGET_CHARS_PER_LINE`도 `15`다. 한 cue는 공백 제외 15자 이하 한 줄만 표시한다.
- 공백은 세지 않고 문장부호는 센다.
- 한 cue 전체와 한 줄 hard max가 모두 15자를 넘으면 FAIL이다.
- 긴 문장은 글자 크기로 축소하지 않고 시간상 연속 cue로 분할한다.
- 원본 SRT·직접인용·승인 나레이션 문장은 축약·의역하지 않는다.
- `COMMENTARY_2LINE` 입력은 승인 문장 2개를 뜻하며 builder가 같은 한 줄 트랙에 시간상 순차 배치한다. 두 문장을 동시에 2줄로 표시하지 않는다.
- 3줄, 빈 줄, 작업 메모형 문구는 FAIL이다.
- SRT와 `VIDEO100_EXPLAINER`를 같은 시간대에 함께 표시하지 않는다.

## 민주블루 HTML 카드

`DEMOCRATIC_BLUE_INSET_CARD_V2`가 새 카드의 기본값이다. 한 카드에는 주제와 `info_block`을 정확히 하나만 넣고, 주제가 둘 이상이면 같은 화면의 좌우 칸으로 묶지 말고 시간상 연속 카드로 분리한다. V2는 제목 60px, 항목명 30px, 핵심문구 68px, 보조문구 40px을 고정하며 글자가 길다는 이유로 축소하지 않는다. `DEMOCRATIC_BLUE_CENTER_INFO_CARD_V1`은 구형 전체화면 프로젝트가 명시적으로 요구할 때만 사용한다. V2는 근본 프로젝트의 배경·띠 위에 얹는 이미지 레이어이며, 출력 래스터는 `1920×1080`만 허용한다. builder는 수동 근본과 같은 `scale=0.65`, 화면 `x=336, y=189, 1248×702` 프레임으로 배치한다.

```text
templates/democratic_blue_center_info_card_v1.html
templates/democratic_blue_center_info_card_v1.css
templates/democratic_blue_inset_card_v2.html
templates/democratic_blue_inset_card_v2.css
scripts/render_democratic_blue_card.py
```

투군이 확정한 JSON 문구를 주입해 1920×1080 PNG를 만들고, manifest의 SHA·해상도·하단 30% 안전영역을 확인한다. 외부 이미지 검색·AI 이미지 생성·다중 시안을 기본 실행하지 않는다.

## CTA 정책

회차 CTA는 `ON|OFF` 중 하나다. 현재 builder는 회차 전체 CTA ON/OFF를 지원한다. 카드별 값이 섞이면 `CTA_POLICY_MIXED_UNSUPPORTED`로 중단한다. CTA OFF는 active draft 수술이 아니라 build 전에 템플릿 CTA segment를 제거한다.

## 핵심 불변식

- 한 회차에는 active writer 한 명만 둔다.
- CapCut 또는 백그라운드 프로세스가 열려 있으면 draft를 만들거나 고치지 않는다.
- active pointer가 선택한 검증 완료 근본만 사용한다.
- 원본 MP4, Media 폴더, CapCut draft, cache, 계정 정보는 소유 계약이 달리 정하지 않는 한 machine-local에 둔다.
- portable JSON에는 사용자 프로필 절대경로와 cache 경로를 넣지 않는다.
- ASR cue가 편집 컷을 정하지 않는다. 실제 컷에서 자막을 split 또는 clamp한다.
- 목표 길이·원본/나레이션 비율은 사용자 절대 LOCK이 아니면 `[EST]`다.
- 실제 source와 narration duration을 사용한다.
- 업로드·썸네일·렌더는 사용자 명시 요청이 있는 별도 단계다. 정상 조립은 항상 `WAIT_USER_CAPCUT_CHECK`에서 멈춘다. 사용자가 화면 확인 완료와 MP4 export를 각각 명시한 `2pow 22factory MCP` export job만 [capcut-assembly.md](references/capcut-assembly.md#승인-후-mcp-export)의 제한된 후속 절차를 사용할 수 있다.

## 실패와 재개

일반 직접 경로는 `첫 실패 재현 → 원인 최소 수정 → 같은 검사 재실행`으로 처리한다. ASSEMBLY_ONLY에서는 자동 코드수정·기능개선으로 확장하지 않는다. 상위 조립 입력 오류는 상위 입력 또는 cards를 수정한 뒤 preflight와 clean rebuild를 다시 실행한다. active draft의 CTA·텍스트·template·attachment·history metadata를 연쇄 수술하지 않는다.

성공한 단계는 실제 identity·SHA·duration이 유지되면 다시 실행하지 않는다. 재개점이 불명확할 때만 [resume-map.md](references/resume-map.md)를 읽는다.

## 단계 문서

- PRE-119: [pre119-handoff-contract.md](references/pre119-handoff-contract.md)
- 대본: [direct-script.md](references/direct-script.md)
- 출처 미디어: [source-media.md](references/source-media.md)
- 나레이션: [narration.md](references/narration.md)
- 시각 자산: [visual-assets.md](references/visual-assets.md)
- 조립·검증: [capcut-assembly.md](references/capcut-assembly.md)
- 카드 계약: [episode-card-contract.md](references/episode-card-contract.md)
- 재개 선택: [resume-map.md](references/resume-map.md)
- 기존 Stage 2 전용: [legacy-stage2.md](references/legacy-stage2.md)

근본 승격을 명시적으로 요청받았을 때만 [root-bundle-contract.md](references/root-bundle-contract.md)를 읽는다.

## 완료 판정

직접 경로는 `STAGE2_PREFLIGHT`를 요구하거나 보고하지 않는다.

```text
PRE119_VALIDATION 또는 DIRECT_SCRIPT_READY
ASSEMBLY_ONLY_READY
ROOT_CONTRACT
EPISODE_CARDS
ASSEMBLY_PREFLIGHT
CAPTION_LAYOUT
SRT_TEXT_FIDELITY
USER_FINAL_ASSEMBLY_GRID
PROJECT_BUILD
MEDIA_RELINK
MEDIA_RESOLUTION
VISUAL_GATE
```

`MEDIA_RELINK=PASS`, `MEDIA_RESOLUTION=PASS`, `VISUAL_GATE=PASS`가 모두 있어야 CapCut 제작 완료다. 정적 JSON 검사나 GRID는 실제 화면 승인 증거가 아니다. `MP4`와 `UPLOAD`는 실행하지 않았으면 `NOT RUN`이다.

정상 조립 자동화의 사용자 전달 경계는 `PROJECT_BUILD=PASS` 뒤다. 프로젝트를 자동으로 열지 않고 `프로젝트 파일명`, `프로젝트 전체 경로`, `미디어 폴더 전체 경로`를 보고한 뒤 `WAIT_USER_CAPCUT_CHECK`로 멈춘다. 이 시점의 `MEDIA_RELINK`, `MEDIA_RESOLUTION`, `VISUAL_GATE`는 `NOT RUN — USER MANUAL`이며 CapCut 제작 완료라고 부르지 않는다. 별도 승인 후 MCP export는 이 정지 경계를 지우지 않고, 사용자 확인 뒤 새 job으로만 시작한다.
