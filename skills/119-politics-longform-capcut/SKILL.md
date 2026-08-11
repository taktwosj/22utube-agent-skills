---
name: 119-politics-longform-capcut
description: Use only when a political-longform request explicitly contains CapCut, 캡컷, 119, or 119정치롱폼.
---

# 119 정치롱폼 CapCut 제작

119는 대본 작성부터 편집 가능한 로컬 CapCut 프로젝트까지 이어 간다.
사용자가 CapCut을 직접 말했을 때만 사용한다. 캡컷, 119, 119정치롱폼도 같은 명시적
호출로 취급한다. 명시 호출이 없으면 119로 자동 우회하지 않는다.
`FORBIDDEN`: 명시 호출 없는 자동 우회.

## 시작

1. `episode_id`, 현재 active writer, 요청 결과를 확인한다.
2. 강한 PRE-119 표식 하나 또는 보조 표식 두 개 이상이 있으면 승인 여부보다 먼저
   [pre119-handoff-contract.md](references/pre119-handoff-contract.md)를 읽고 이 경로를 고정한다.
3. PRE-119 표식 기준을 충족하지 않고 승인된 대본도 없을 때만
   [direct-script.md](references/direct-script.md)를 읽는다.
4. 승인된 대본이 있으면 아래 입력 경로 하나를 고른다.
5. 현재 단계의 reference만 읽고 작업한다. 다른 단계 문서를 미리 읽지 않는다.

승인 전 모호함, 재현 가능한 코드·도구 결함, 또는 계약 변경에만
[matt-auxiliary-routing.md](references/matt-auxiliary-routing.md)를 읽는다. 정상 제작과 승인 SHA 이후 기획은 119 경로만 따른다.

| 관찰 가능한 상태 | 읽을 문서 | 상태 |
|---|---|---|
| PRE-119 강한 표식 1개 또는 보조 표식 2개 이상 | `pre119-handoff-contract.md` | `PRE119_VALIDATION` |
| 대본 미승인 | `direct-script.md` | `CAN_DRAFT` 또는 `WAIT_SCRIPT_APPROVAL` |
| 직접 대본 승인·제공 | 이 문서의 직접 경로 | `DIRECT_SCRIPT_READY` |
| 기존 Stage 2 산출물 사용을 명시 | `legacy-stage2.md` | `LEGACY_STAGE2_PREFLIGHT` |
| 실패 단계가 불명확 | `resume-map.md` | 한 단계 선택 |

직접 경로의 최소 입력은 `episode_id`, 승인된 최종 대본, 출처 URL·원본 SRT·로컬 미디어
중 하나 이상이다. 없는 제작 미디어는 승인 뒤 수집·생성할 수 있다. 직접 경로는 110·111,
외부검토 영수증, lock, review packet, 업로드 패키지에 의존하지 않는다.

## PRE-119 인계 입력 계약

EDITORIAL_OWNER = TOGUN_PRE119
PRODUCTION_OWNER = 119-politics-longform-capcut
ENTRY_STATE = DIRECT_SCRIPT_READY

119는 투군 PRE-119가 승인 후보로 작성한 다음 파일을 입력으로 사용한다.

- `20_script/119_final_script.md`
- `20_script/pre119_handoff.json`
- `00_source/source_packet.md`
- `10_analysis/pre119_editorial_packet.md`
- `90_reports/source_gap_and_status.md`

패킷 내부 PASS를 승인 근거로 사용하지 않는다. 외부에서 전달된 승인 SHA와 승인 증거를
`validate_pre119_handoff.py`에 주고 실제 대본 raw bytes SHA, 패킷 current SHA, 외부 승인
SHA의 3자 일치를 확인한다. 검증 결과는 별도 보고서에 쓰며 입력 패킷을 덮어쓰지 않는다.
검증기는 `episode_cards.json`을 만들지 않는다.

제작 시작 전 다음을 확인한다.

- `episode_id` 존재
- `90_reports/pre119_handoff_validation.json`의 외부 승인 3자 SHA 결속 `status = PASS`
- `CENTRAL_QUESTION` 존재
- `SELECTED_THESIS` 존재
- `CHAPTER ORDER` 존재
- `SOURCE_ID`와 `VIDEO_URL` 존재
- 후보 source in/out 또는 transcript gap 표시
- `BETWEEN_IMAGE` 값 존재
- `BETWEEN_NARRATION` 값 존재
- `LOWER_MODE`가 `SRT | COMMENTARY_2LINE | NONE` 중 하나
- 미확정·119 재검증 항목 존재

119가 변경하면 안 되는 항목:

- `CENTRAL_QUESTION`
- `SELECTED_THESIS`
- 정치적 방향
- `CHAPTER ORDER`
- 원본 클립의 논리적 순서
- 승인 나레이션 문장
- 승인 하단 논평 문구
- 사용자 승인 편집 방식 A/B/C

119가 기술 검증 과정에서 조정할 수 있는 항목:

- 실제 원음에 맞춘 source cut 시작·종료점
- 음절 절단 방지를 위한 컷 경계
- SRT split 또는 clamp
- 실제 나레이션 오디오 기준 cue timing
- 미디어 경로·SHA·duration
- builder가 요구하는 기술 필드

기술 조정으로 승인된 의미·논지·클립 순서가 바뀌면 119가 임의 수정하지 않고 투군 PRE-119로 복귀한다.

외부 승인 SHA 또는 승인 증거가 없으면:

→ `WAIT_EXTERNAL_APPROVAL_REQUIRED`

실제 대본 raw bytes SHA, 패킷 current SHA, 외부 승인 SHA가 다르면:

→ `WAIT_APPROVAL_HASH_MISMATCH`

중심 질문 또는 선택 논제가 없으면:

→ `WAIT_CENTRAL_QUESTION` 또는 `WAIT_THESIS`

transcript가 부족하면:

→ `WAIT_TRANSCRIPT`

source identity가 변경되면:

→ 기존 타임코드·인용·하단 문구·컷 순서를 무효화
→ `WAIT_SOURCE_REVERIFY`

119는 승인된 대본을 다시 작성하거나 PRE-119 SRT 구상 프롬프트를 자체 실행하지 않는다.

## 승인 뒤 선택적 병렬 실행

대본 승인 뒤 A와 D는 항상 시작한다. 사용자가 나레이션·TTS·별도 오디오를 명시적으로
요청했을 때만 B를 시작하고, 이미지·그래픽을 명시적으로 요청했을 때만 C를 시작한다.
활성 작업은 병렬 실행하며 각 작업자는 자기 출력만 쓴다.

| 작업 | 읽을 문서 | 독점 출력 |
|---|---|---|
| A 출처·SRT·다운로드·로컬 컷 | `source-media.md` | source media와 source captions |
| B 나레이션·정렬·SRT | 명시 요청 시에만 `narration.md` | narration media와 narration SRT |
| C 지원되는 시각 자산 | 명시 요청 시에만 `visual-assets.md` | episode `Resources` 자산 |
| D 근본·target·CapCut 종료 준비 | `capcut-assembly.md`의 준비 절 | 읽기 결과와 공식 resolver 출력 |

A와 D, 그리고 요청되어 활성화된 B/C는 서로의 미완성 결과를 정본으로 쓰지 않는다.
요청되지 않은 B/C는 `NOT_REQUESTED` 또는 `NOT_APPLICABLE`이며 join이 기다리지 않는다.
join owner 한 명은 A/D와 활성 B/C의 실제 산출물만 `episode_cards.json`으로 합친다.
PRE-119 경로에서는 `compile_pre119_episode_cards.py`가 실제 A/B/C/D 증거의 경로, SHA-256,
양의 duration과 RAW/DISPLAY 자막 provenance를 검증한 뒤에만 이 파일을 만든다. 기본
빌드는 source video의 embedded audio와 사용 가능한 source footage·editable text overlay로
진행한다. 별도 요청이 없으면 챕터 1→2→3→4의 `SOURCE_VIDEO`를 t=0부터 연속 배치하며
intro·image·narration은 넣지 않는다. narration audio/SRT나 episode image가 없어도 멈추지 않는다. 이후
`capcut-assembly.md`에 따라 build → relink → readback → visual 순서로 계속한다.
목표 조합은 `SOURCE_VIDEO=VIDEO+SOURCE`, `NARRATION_VIDEO=VIDEO+NARRATION`,
`CHAPTER_CARD=IMAGE+SILENT`, `NARRATION_IMAGE=IMAGE+NARRATION`이다. `VIDEO+SILENT`와
`IMAGE+SOURCE`는 별도 구현 전에는 지원한다고 말하지 않는다. lower 선택은 `SRT`,
`COMMENTARY_2LINE`, `NONE`이며 audio에 맞춰 기존 builder mode에 매핑한다. C는 image,
B는 narration을 선택한 경우에만 활성화한다.

## 핵심 불변식

- 한 회차에는 active writer 한 명만 둔다.
- CapCut 또는 백그라운드 프로세스가 열려 있으면 draft를 만들거나 고치지 않는다.
- active pointer가 선택한 검증 완료 근본만 사용한다. 과거 회차·실패본·`.bak`를 근본으로
  쓰지 않는다.
- resolved root bundle에 `runtime_adapters/v5_legacy_profile_adapter_v1.json`이 있으면
  [v5-legacy-profile-root-adapter.md](references/v5-legacy-profile-root-adapter.md)만 추가로 읽고
  그 adapter builder를 사용한다. ZIP 자체 수정·재압축과 stock builder 직접 사용은 금지한다.
- 원본 MP4, Media 폴더, CapCut draft, cache, 계정 정보는 로컬에 둔다. OneDrive에는
  portable root, cards, 상대경로 보고서와 해시만 둔다.
- 사용자 프로필 절대경로, `%LOCALAPPDATA%`, cache 경로를 portable JSON에 직렬화하지 않는다.
- ASR cue는 편집 컷을 정하지 않는다. 실제 컷에서 자막만 split 또는 clamp한다.
- 요청되지 않은 narration audio/SRT와 episode image는 제작 필수 입력이 아니다.
- 업로드·썸네일은 사용자가 명시적으로 요청한 별도 단계다.

## 실패와 재개

활성 단계의 API·media·schema·continuity·alignment·builder·readback·relink·visual 검사에서
구체적 기술 실패가 발생했을 때만 멈춘다. `첫 실패 재현 → 원인 최소 수정 → 같은 검사 재실행`으로 처리한다. 성공한
단계는 다시 읽거나 실행하지 않고, 실제 산출물에서 실패한 단계 하나만 재개한다.
요청되지 않은 B/C의 누락·무효는 실패가 아니며 resume-map 재개 대상으로 삼지 않는다.
나중에 B/C가 명시 요청되면 성공한 A/D를 다시 하지 않고 해당 작업만 추가한다.
재개점이 불명확할 때만 [resume-map.md](references/resume-map.md)를 읽는다.

## 단계 문서

- 대본: [direct-script.md](references/direct-script.md)
- 출처 미디어: [source-media.md](references/source-media.md)
- 나레이션(명시 요청 시): [narration.md](references/narration.md)
- 시각 자산(명시 요청 시): [visual-assets.md](references/visual-assets.md)
- 조립·검증: [capcut-assembly.md](references/capcut-assembly.md)
- 재개 선택: [resume-map.md](references/resume-map.md)
- 기존 Stage 2 전용: [legacy-stage2.md](references/legacy-stage2.md)

세부 card schema가 필요할 때만
[episode-card-contract.md](references/episode-card-contract.md)를 추가로 읽는다. 근본 승격
작업을 명시적으로 요청받았을 때만 [root-bundle-contract.md](references/root-bundle-contract.md)를
읽는다. 어느 단계도 관련 없는 reference 전체를 읽지 않는다.

## 완료 판정

직접 경로는 `STAGE2_PREFLIGHT`를 요구하거나 보고하지 않는다. 실제 결과를
`DIRECT_SCRIPT_READY`, `ROOT_CONTRACT`, `PROJECT_BUILD`, `MEDIA_RELINK`,
`MEDIA_RESOLUTION`, `VISUAL_GATE`로 보고한다. 레거시 경로만 `STAGE2_PREFLIGHT`를 쓴다.

`MEDIA_RELINK=PASS`와 `VISUAL_GATE=PASS`가 모두 있어야 CapCut 제작 완료다. 정적 JSON
검사는 화면 승인이 아니다. `MP4`와 `UPLOAD`는 각각 요청받아 실행한 경우에만
`PASS`로 보고하며, 실행하지 않았으면 `NOT RUN`이다. B/C 결과는 해당 작업을 요청받았을
때만 완료 보고에 포함하며, 요청되지 않은 B/C의 부재는 `MEDIA_RELINK`나 `VISUAL_GATE`를
막지 않는다.
