---
name: 001short-production-agent
description: Use for original-shorts production, or when a new-session 001 conversation handoff JSON must load env safely and resume the same lane.
---

# 001short Compact Production

## Executable Protocol (Mandatory)

Load `protocol.json` before mode routing, stage selection, production-plan compilation, CapCut assembly, completion reporting, or public-upload decisions. `protocol.json` is the machine-readable contract; `SKILL.md` explains semantic judgment; `workflow.json` declares state transitions.

- Run `python3 scripts/validate_executable_protocol.py --self-check` before a new episode or isolated deployment test.
- Validate every machine-readable Stage 05 production plan with `scripts/validate_executable_protocol.py --plan <path>` before advancing or building.
- Validate `90_reports/completion_report.json` with `scripts/validate_executable_protocol.py --completion-report <path>` before any `all_harness_pass`, `WAIT_UPLOAD_APPROVAL`, `upload_ready`, or `uploaded` claim.
- If `SKILL.md`, `protocol.json`, and `workflow.json` conflict, stop with `STOP_PROTOCOL_CONFLICT`. Do not choose the convenient interpretation.
- `URAKKAI` must fail with `URAKKAI_STRUCTURE_UNCHANGED` when the approved final order is unchanged.
- `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY` must use one full-length muted VIDEO, one full-length A10 original-audio segment, full-length T1/T2, and zero STATE/A10_TEXT/A9_TEXT/A9/A11/A12 segments.
- A completion report missing upload title, upload description, or source credit must fail with `UPLOAD_METADATA_MISSING`; conversational memory or a previous message is not substitute evidence.
- Public upload states require explicit approval evidence and otherwise fail with `PUBLIC_UPLOAD_NOT_APPROVED`.
- 최종 완료 전 실제 CapCut 편집기를 열어 프리뷰·타임라인·트랙을 확인해야 한다. `application_open_or_playback=REQUIRED_BEFORE_COMPLETION`이며 Home 카드, JSON 존재, 정적 validator만으로 완료 처리하지 않는다. 완료보고에는 실제 프로젝트명, 화면 증거 파일+SHA, 종료 후 draft readback+SHA, final project hash가 필요하다.
- Stage 06의 raw VMake 최종 다운로드본은 canonical clean/hybrid 결과와 별도 증거다. 실제 다운로드 경로·SHA-256·size_bytes·ffprobe duration·`is_actual_vmake_final_download=true`를 기록하며 원본 또는 로컬 대체 파일을 raw VMake 다운로드로 제출하지 않는다. hybrid 후처리는 허용하되 raw VMake 다운로드 증거를 보존하고 canonical clean manifest에 처리 범위를 따로 기록한다.
- `URAKKAI`는 유효 VIDEO 구조 2개 이상, 승인 final order, 가짜 연속 분할 금지, 사용한 모든 VIDEO source/target range와 A10의 1:1 동기를 강제한다. `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`는 이 다중 컷 gate의 명시적 예외로 VIDEO/A10 각 1개 전체 길이와 source 순서 불변만 허용한다.
- `RENDER_COMPLETE`, `UPLOAD_READY`, `PUBLIC_UPLOAD_COMPLETE`를 주장할 때는 실제 MP4 경로·SHA-256·size_bytes·ffprobe duration이 완료보고에 있어야 한다.
- Before deployment to another computer or agent, run the isolated-copy procedure and pressure scenarios in `references/executable-protocol-testing.md`.
- Never invent a simplified machine contract that differs from the files the production builders actually consume. Before enforcing or publishing a production-plan schema, read at least one recent real clean-only plan and one recent real urakkai plan. The canonical episode shape is `timeline[].placements` with `order_signature`, explicit anchors, source/target ranges, and `cleared_anchors`; adapters may normalize legacy forms, but the schema and fixtures must model the actual builder input.
- A skill update is not complete while the newest test is RED, errors before assertions, or has not been rerun after the latest edit. Report it as unfinished and do not promote, deploy, or replace the known-good version until the complete suite, protocol self-check, real-plan compatibility check, and positive/negative fixtures are GREEN.
- An isolated archive and its SHA-256 become stale immediately when the active skill changes. After any post-package edit, rebuild the isolated copy, regenerate the file manifest and archive hash, rerun tests from the extracted copy, and only then hand it to another computer or agent.

## New Session Handoff Bootstrap

운영자가 `/new` 뒤 001 핸드오프 대화 JSON을 제공하면 다른 제작 스킬을 추가로 로드하지 않고 이 스킬 안에서 바로 재개한다.

1. 터미널에서 `$HOME/.hermes/.env`가 있으면 **한 번만** 조용히 로드한다. 값·키 목록·파일 내용은 출력하거나 핸드오프에 저장하지 않는다.
   ```bash
   set -a; [ ! -f "$HOME/.hermes/.env" ] || . "$HOME/.hermes/.env"; set +a
   ```
2. JSON을 임시 파일로 받은 뒤 `python3 scripts/validate_conversation_handoff.py --handoff <path>`를 실행한다. `PASS` 전에는 제작을 시작하지 않는다.
3. `owner_skill=001short-production-agent`, `lane=general_shorts_production`을 유지하고 안전 요약의 `request_scope`와 `next_action`부터 진행한다.
4. `resume_requested=true`일 때만 `episode_id`와 실제 state/readback을 대조해 과거 회차를 연다. 둘 중 하나라도 없으면 `HANDOFF_EPISODE_ID_REQUIRED`로 중단한다.
5. `resume_requested=false`이면 새 회차로 취급하며 과거 프로젝트를 열거나 수정하지 않는다.

핸드오프 정본 모양은 `templates/conversation-handoff.json`, schema는 `schemas/conversation_handoff.schema.json`이다. 토큰·쿠키·API 키·비밀번호·OAuth 값·session/conversation ID가 들어 있는 JSON은 `HANDOFF_SECRET_MATERIAL_FORBIDDEN`으로 거부하며 원문을 다시 출력하지 않는다.

## Lane Isolation

## Urakkai Editorial Authority

- At Stage 04, the Mac mini creator machine calls Claude CLI with Claude Opus 5 at low effort first; only a failed CLI call falls back to Codex CLI `gpt-5.6-sol` at low effort.
- The reviewer improves a draft; it never promotes a final design. Report the revised `URAKKAI_BLUEPRINT.md` and review evidence to the user, then stop at `WAIT_USER_URAKKAI_APPROVAL`. Apply user corrections to the same draft and report again. Stage 05 begins only after explicit user approval.
- Situation captions describe the visible present action, relationship, or emotion with a hook. Do not use edit-outline copy such as “show the reaction first,” “reveal the reason later,” “connect to the second reaction,” or “warm ending.” Read `references/stage04-external-review-contract.md` for the full rubric and dynamic speaker-line rule.

이 스킬은 `owner_skill=001short-production-agent`, `lane=general_shorts_production`인 독립 제작 lane이다. 활성화한 뒤에는 `000short-production-agent`, `top5isu-shorts`, `00-tikitaka`, `111-politics-longform` 또는 다른 영상 제작 스킬의 단계, 템플릿, 상태명, validator, 산출물 계약을 읽거나 합치지 않는다.

- 요청을 시작할 때 하나의 lane만 확정한다.
- `001short-production-agent`가 활성 lane이면 종료·명시적 전환 전까지 다른 제작 스킬을 호출하지 않는다.
- 공용 도구가 필요해도 `tools.json`과 현재 단계 계약에 등록된 방식으로만 사용한다.
- Git 설치·업데이트는 이 스킬 폴더만 선택 설치하며 full install, prune, strict 동기화를 사용하지 않는다.
- 다른 lane의 기존 episode나 CapCut 정본을 입력으로 재사용하지 않는다. 필요한 입력은 이 workflow의 handoff와 evidence 계약으로 새로 잠근다.

`workflow.json`과 episode state를 기준으로 현재 `steps/` 지침 하나만 읽는다. 필요한 산출물, `tools.json`, `references/blueprint_matrix.md`, 현재 단계의 `references/checks/` 문서만 읽는다.

01부터 09까지가 유일한 진행 순서다. 단계 상태는 `workflow.json`의 의미 기반 상태명만 사용하고, 실제 파일·SHA-256·ffprobe·CapCut 구조·렌더 증거 없이 다음 단계로 이동하지 않는다. 업로드는 제작 완료와 별도이며 항상 `WAIT_UPLOAD_APPROVAL`로 멈춘다.

속도 향상을 위해 병렬 작업자를 쓸 때는 `references/parallel-execution.md`를 읽는다. 작업자는 고유 root에 증거와 후보만 만들며, 조정자만 state·권위 산출물·정식 evidence·활성 CapCut draft를 쓴다. GUI 소유자는 항상 1명이고, 모든 barrier가 통과한 뒤 조정자가 상태를 한 단계씩 순서대로 갱신한다.

Hermes가 작업자 `live_transcripts`를 제공하면 경로를 실행 관찰 증거로 보존하되 완료 권위로 사용하지 않는다. 조정자가 실제 산출물·SHA-256·validator를 다시 확인해야 하며, 부모 세션 종료 뒤 delegation 지속을 가정하지 않는다. VMake·CapCut의 `computer_use` 입력은 background 우선으로 실행하고 도구가 `px` 또는 `foreground` escalation을 권고할 때만 같은 동작을 다음 단계로 올린 뒤 재캡처한다.

## Source Acquisition

YouTube Shorts URL이 원본 권위이면 `references/youtube-source-acquisition.md`를 읽는다. 메타데이터·영상·자동자막·분석 WAV 취득을 분리하여 선택 자막 요청 하나가 원본 영상 확보를 막지 않게 한다. 원본 영상의 baked-in 제목·자막 유무를 접촉 시트로 확인하고, 새 자막을 겹쳐 넣지 않는다.

## VMake Browser Runbook

### Early VMake dispatch and user-only visual decision

Immediately after `SOURCE_OCR_VERIFIED`, submit the source to VMake. Continue Stages 02--04 while its remote job runs. This explicit VMake rule overrides any earlier general wording that waits for final design approval.

`validate_clean_candidate.py` is a technical identity check only: original/candidate SHA difference, source identity, playable video stream, duration, and resolution. It never scores visual cleanliness, OCR residue, watermark removal, or output quality. Its `PASS` means only `TECHNICAL_IDENTITY_ONLY`; the user alone decides visual quality and final clean acceptance.

After `FINAL_DESIGN_LOCKED`, use `validate_clean_visual.py` to bind the downloaded candidate to the locked design before `CLEAN_VISUAL_READY`. If VMake has more than 10 minutes remaining immediately before CapCut work, create the interim original-video project for quick user review: mute `VIDEO`, preserve original audio on A10, set `WAIT_USER_CAPCUT_CHECK`, and later replace only the existing VIDEO asset with the verified clean file. Do not rebuild the project structure and do not call the interim project final.

VMake 업로드·처리 polling·다운로드·clean asset 등록을 수행하기 전에 `references/vmake-dom-clean-video-automation.md`를 읽는다. 이 reference가 DOM selector, `DOM.setFileInputFiles`, 다운로드 확인, 타 컴퓨터 이식성의 상세 권위다.

VMake가 완료됐지만 짧게 남는 댓글·워터마크·제목 또는 인페인팅 손상이 의심되면 `references/vmake-residual-cleanup-qa.md`를 추가로 읽는다. 전체 1fps 접촉시트와 첫 1.5초 4fps 접촉시트를 모두 통과하기 전에는 canonical `clean_source.mp4`로 승격하지 않는다. 로컬 보정을 쓴 결과는 순수 VMake 결과로 부르지 않고 hybrid 범위와 원본 오디오 PCM 검증을 manifest에 기록한다.

### VMake Direct-Insert Contract

`CLEAN_VISUAL_READY`가 되면 검증된 VMake canonical 결과 `40_assets_used/clean_source.mp4`를 `clean_video` asset으로 등록하고 001 CapCut 프로젝트의 모든 `VIDEO` placement에 직접 사용한다. 원본 `source.mp4`, VMake preview, 별도 재편집 영상 또는 검증되지 않은 프록시를 VIDEO 자산으로 대체하지 않는다. builder는 이 파일을 프로젝트 `Resources/media/clean_video.mp4`로 복사하며 A10 원본 오디오는 별도 자산으로 유지한다. production-plan validator가 다른 VIDEO asset key를 발견하면 `VMAKE_DIRECT_INSERT_ASSET_INVALID`로 중단한다.

Stage 06에서는 전용 API 업로더가 있다고 주장하지 말고 로그인된 Chrome을 CDP/브라우저 릴레이로 조작한다. **화면 좌표 클릭을 기본으로 사용하지 않는다.** 페이지 DOM에서 요소를 찾아 기계적으로 실행한다.

### DOM-first selector contract

운영자가 확인한 Upload 버튼 예시:

```html
<button type="button" class="btn--KTGbF intl-primary--jKiKf">...<span>Upload</span></button>
```

CSS module 클래스(`btn--KTGbF`, `intl-primary--jKiKf`)는 변경될 수 있으므로 단독 권위로 쓰지 않는다. 기본 선택은 `button[type="button"]` 중 정규화된 `textContent`가 정확히 `Upload`인 표시·활성 요소 하나다.

```javascript
const matches = [...document.querySelectorAll('button[type="button"]')]
  .filter(b => b.textContent.trim() === 'Upload' && !b.disabled && b.offsetParent !== null);
if (matches.length !== 1) throw new Error(`VMAKE_UPLOAD_BUTTON_COUNT=${matches.length}`);
matches[0].click();
```

- Upload은 CDP `Runtime.evaluate` 또는 현재 DOM ref로 클릭한다. `x,y` 좌표는 DOM 접근 불가 시 캡처 검증을 거친 최후 fallback이다.
- 파일 선택은 Finder 좌표 조작보다 hidden `input[type=file]`을 찾아 CDP `DOM.setFileInputFiles`로 회차의 절대 `source.mp4` 경로를 직접 주입한다.
- file input 후보가 여러 개면 `accept`에 video가 포함되고 Upload 영역과 연결된 활성 input 하나만 선택한다. 후보 수가 1이 아니면 중단하고 DOM을 다시 관찰한다.
- 처리 상태는 화면 좌표가 아니라 DOM의 `Processing`, 진행률 텍스트 또는 progress/aria 값을 polling한다.
- 완료는 `button`/`a` 중 정규화된 텍스트가 `Download HD` 또는 `Download`인 표시·활성 요소 하나를 찾아 클릭한다.
- 다운로드는 지정 다운로드 폴더와 Chrome download 상태를 함께 확인하고, 실제 새 MP4가 생기기 전에는 완료로 처리하지 않는다.

운영자가 직접 알려준 실제 순서는 아래와 같다.

1. Chrome에서 `https://vmake.ai/workspace` 접속.
2. 기존 VMake 계정으로 로그인. 비밀번호·OTP·CAPTCHA는 운영자가 직접 처리.
3. 팝업이 뜨면 `I don't want to receive marketing emails from Vmake.` 체크 후 닫기.
4. `https://vmake.ai/video-watermark-remover/upload`로 이동.
5. DOM에서 표시·활성 `Upload` 버튼 하나를 찾아 클릭한다.
6. hidden `input[type=file]` 또는 OpenClaw의 armed upload를 통해 회차 `source.mp4`를 직접 주입한다. managed Chrome에서는 `/tmp/openclaw/uploads/`에 SHA-256이 같은 임시본을 두고 chooser를 arm한다.
7. OS 파일 선택창은 DOM/file-input 경로가 실제로 없을 때만 최후 fallback으로 사용하며, Upload 클릭만 성공하고 file arm이 실패한 상태를 업로드 완료로 오인하지 않는다.
8. `Processing...` 완료까지 대기. 진행 중 새로고침·중복 업로드 금지.
9. 완료 화면의 `Download` 또는 `Download HD`로 결과 MP4 다운로드. 결제·크레딧·약관 화면은 자동 승인하지 않는다.
10. Downloads 결과를 회차 내부 `clean_source.mp4`로 복사하고 SHA-256·ffprobe·길이·해상도·OCR/눈검수 후에만 `CLEAN_VISUAL_READY`.

과거 실작업은 `Processing... 94%`에서 운영자가 취소했으므로 당시 다운로드 이후는 완료 증거가 아니다. 새 회차마다 실제 다운로드 파일과 clean receipt가 필요하다.

### Explicit clean-only passthrough

운영자가 `클린 작업하고 그대로`, `순서 그대로 클린만`, 또는 동등한 표현을 명시하면 canonical 값 `production_mode=SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`로 기록한다. 이는 0쇼츠 콘텐츠 lane에서 001 제작 workflow를 사용하는 clean-only 분기다. source 순서와 전체 길이를 보존하고, 우라까이 요청이 아니므로 구조를 억지로 재배치하거나 `FINAL_DESIGN_LOCKED`를 꾸며내지 않는다. `references/vmake-dom-clean-video-automation.md`에 따라 전체 길이 clean 파일과 visual receipt를 먼저 완성하며, CapCut은 요청 범위에 포함된 경우에만 진행한다.

운영자가 이어서 `우리 쇼츠 스킬로 만들고 T1/T2만 넣어`, `그대로 캣컵 만들고 동기화해`라고 하면 같은 mode를 유지한다. 이 branch는 전체 길이 VIDEO 1클립(volume 0) + 원본 오디오 A10 1클립(volume 1) + 전체 길이 T1/T2만 배치하고 `STATE·A10_TEXT·A9_TEXT·A9·A11·A12`를 비운다. 우라까이 구조 변경 gate나 하단 자막/TTS/SFX 생성을 강제하지 않는다. 상세 조립과 post-cloud ID 정규화는 `references/interim-capcut-project-sync.md`의 **Source-order unchanged title-only project** 절을 따른다.

## Urakkai Structural Contract

우라까이 설계·production plan·다중 VIDEO/A10 조립·눈검수·post-open 검증을 수행할 때는 `references/urakkai-structural-reorder-capcut.md`를 읽는다.

### BGM + 화면 텍스트 전용 우라까이

운영자가 `나레이션 아니고 BGM에 텍스트만`, `음성 없이 글자만`, `TTS 말고 화면 글자`, 또는 동등한 표현으로 정정하면 이를 **음성 TTS가 없는 화면 텍스트 모드**로 해석한다. 운영자가 나레이션을 명시적으로 거부한 문맥에서 `텍스트 TTS`라고 표현해도 음성 합성을 뜻한다고 되묻거나 자동 생성하지 않는다.

```text
spoken_narration=false
tts_audio=false
original_audio_volume=0
bgm_required=true
screen_text_anchor=STATE
clear_anchors=A9,A9_TEXT
```

- 원본 A10은 source range와 함께 재배치하되 `volume=0`으로 유지해 기존 내레이션이 새 순서와 충돌하지 않게 한다.
- 승인된 BGM은 A12에 전체 길이로 배치한다. 제작 단계에서 BGM 자산이 아직 정해지지 않았으면 `WAIT_BGM_SELECTION`으로 남기되 대본·구조 설계 단계는 계속할 수 있다.
- 설명 문구는 `STATE` 화면 텍스트이며 `A9_TEXT` 또는 TTS-linked caption으로 부르지 않는다.
- `tts_spoken_copy.txt`, 음성용 문장 manifest, A9 TTS 계획을 만들지 않는다. 이전 초안에 있으면 제거하고 `screen_text_copy.txt`와 production plan의 `screen_text`를 정본으로 갱신한다.
- T1/T2는 고정 상단 제목, STATE는 시간별 설명 문구로 분리한다.
- 수정 후 사람눈 설계도, 추천안, production-plan draft, writer gate를 함께 갱신하고 공통 script contract와 executable protocol validator를 다시 실행한다.
- 사용자가 나레이션을 거부하지 않은 채 `텍스트 TTS`만 단독으로 말해 음성 여부가 실제로 불명확한 경우에만 최소 질문으로 확인한다.
- BGM 모드 쇼츠의 완료 보고에는 영상 주제·정서·편집 속도에 맞는 **노래 후보를 정확히 3개** 추천한다. 각 후보는 곡명 또는 실제 검색 가능한 트랙 키워드와 추천 이유를 한 줄로 쓰고, 저작권·플랫폼 제공 여부를 확인하지 못했으면 `사용 전 권리/제공 여부 확인`을 표시한다.
- BGM-only의 A12 배치, 음성 stem 검증, VMAKE transient overlay fallback, CDP 완료 이벤트 다운로드, CapCut cloud-safe mirror·Windows-path scrub 절차는 `references/bgm-a12-capcut-cloud.md`를 따른다.

우라까이는 원본 장면 순서 `1→2→3→4→5`를 유지한 채 제목·크롭·TTS·자막만 바꾸는 리패키징이 아니다. 최소 한 번 이상 의미 있는 장면 재배치로 훅·충돌·맥락·검증·결말의 서사 순서를 새로 만들어야 한다. 예: `1→2→3→4→5`를 `3→4→1→2→5` 또는 결과 훅을 분할한 `5A→2→1→3→4→5B→6`으로 변경한다.

- Stage 02 원본 설계도에는 모든 변화 구간에 원본 순번과 source range를 붙인다.
- 구조 개수·번호·분할 방식은 고정하지 않는다. 상황, 행동, 화자, 전달 방식(`화자 발언`, `TTS`, `나레이션`, `효과음`, `영상 재생`) 또는 서사 기능이 바뀌는 지점에서 회차별 구조를 나눈다.
- 우라까이의 핵심은 특정 구조를 A/B로 분할하는 것이 아니라, 이렇게 구분한 상황별 구조를 분석해 의미 있는 새 순서로 재설계하는 것이다.
- Stage 03 추천안과 Stage 05 최종 설계도에는 `원본 구조`, `최종 구조`, 각 segment의 source range→target range를 모두 표시한다.
- 원본 순서와 최종 순서가 같으면 `URAKKAI_STRUCTURE_UNCHANGED`로 중단하며 최종 설계로 승인하지 않는다.
- 결과 장면을 훅으로 앞당길 때 동일 구간을 무의미하게 반복하지 않는다. 한 원본 상황 안에서도 기능이 실제로 달라지는 경우에만 `5A/5B`처럼 source range를 분할한다. `5A/5B`는 이번 회차의 선택일 뿐 일반 규칙이나 핵심 요건이 아니다.
- TTS는 구조 전환을 잇는 브리지이며 원본 장면 재배치를 대신하지 않는다.
- builder는 승인된 source range 순서를 그대로 집행하고 자체적으로 원본 순서로 복원하거나 다시 창작하지 않는다.
- `URAKKAI`에서는 원본 전체 길이와 최종 프로젝트 전체 길이를 같게 강제하지 않는다. 이미지·나레이션·TTS·장면 삭제/추가에 따라 최종 `total_duration_us`는 원본보다 짧거나 길 수 있으며, 최종 렌더는 원본 길이가 아니라 승인된 `total_duration_us`와 일치해야 한다.
- VMake `clean_source.mp4`가 원본 길이와 맞아야 하는 것은 편집 전 clean 결과의 누락·잘림을 막는 자산 검증이다. 이것을 최종 영상 길이 동일 gate로 확대하지 않는다.
- 속도 변경을 금지한 원본 VIDEO clip은 선택한 source/target range 길이를 맞추되, target-only 이미지·나레이션 구간이 전체 최종 길이를 바꾸는 것은 허용한다. `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`만 명시적 예외로 원본 전체 길이를 유지한다.

## Evidence-Calibrated Original Blueprint

Stage 02 원본 설계도는 줄거리 요약이 아니라 **원본 멀티모달 재현 대본**이다. 원본을 보지 않은 제작자도 무엇이 보이고·읽히고·들리는지 재현할 수 있어야 한다.

- 임의의 5초·1초 등 동일 간격으로 나누지 않는다. 자막 등장·퇴장, 화자·대사 전환, 차량·인물 행동, 효과음, 화면 처리 변화 시점으로 구간을 나눈다.
- 각 구조마다 `화면`, `화면 텍스트`, `화자·대사`, `들리는 소리`, `상황 설명`을 별도로 쓴다. 상황 설명으로 앞 네 항목을 대체하지 않는다.
- 증거 권위를 `SOURCE_OBSERVATION`, `TRANSCRIPT`, `SCREEN_LABEL`, `SCREEN_CLAIM`, `UNVERIFIED`로 구분한다. 제작자가 화면에 쓴 화자명·상황 설명·감정 평가는 **그 글자가 보인다는 사실만 확정**하며 객관적 사건이나 신원으로 승격하지 않는다.
- 자동자막·OCR·화면 자막이 충돌하면 원본 프레임과 원본 음성을 재확인한다. 확인하지 못한 욕설, 화자 신원, 경적, 창문음, 삽입 SFX, BGM은 추측하지 말고 `UNVERIFIED`로 남긴다.
- clean 영상이 원본과 동기이고 baked-in 글자만 제거한 비교본이면, 원본/clean 동기 프레임 차분으로 텍스트 변화 후보 시점을 찾을 수 있다. 차분 결과는 후보이며 대표 프레임 OCR·눈검수로 문구와 경계를 확정한다.
- 텍스트는 1080×1920 기준 bbox·정렬·줄 수·대표색·plate/외곽선·등장 구간을 기록한다. T1/T2가 실제 한 개의 복합 baked-in 제목이면 분석 편의를 위한 T1/T2 매핑과 원본 객체 사실을 구분한다.
- 원본 AAC가 단일 혼합 트랙이면 A10·현장음·A11·A12가 stream 수준에서 분리되었다고 주장하지 않는다. 청취 증거가 없는 음향은 `UNVERIFIED`다.
- Stage 02 정본에는 시간 구간을 가로축, `VIDEO·T1·T2·A9·A10·STATE·A11·A12·SCREEN`을 세로축으로 한 원본 매트릭스를 포함한다. 긴 표는 같은 세로축을 유지한 채 여러 표로 나눈다.
- 자세한 보고 규칙은 `references/structure-blueprint-reporting.md`를 따른다.

## Human-Readable Approval Gate

### 자동모드로 우라까이 대본까지 진행 후 수정 대기

운영자가 `자동모드로 대본까지 우라까이한 다음 보고`, `우라까이 대본 먼저 만들어 내가 수정`, 또는 동등한 범위를 명시하면 이를 Stage 01~03의 조사·원본 설계·실제 구조 재배치·대본 초안 작성까지 승인한 것으로 본다. 같은 범위 안에서 카테고리·추천 방향을 다시 묻지 않는다.

- 원본 구조를 먼저 증거 기반으로 번호화하고, 최종 후보의 `order_signature`가 실제로 달라야 한다.
- `20_script/original-blueprint.md`, `20_script/first-recommendation.md`, `20_script/URAKKAI_BLUEPRINT.md`를 작성한다.
- 기계 검증이 필요하면 비정본 `20_script/production_plan.draft.json`을 만들고 executable protocol validator를 실행할 수 있다. PASS는 구조 계약 통과만 뜻하며 운영자 승인이나 최종 잠금을 뜻하지 않는다.
- canonical `20_script/production_plan.json`, `final-blueprint.md`, `FINAL_DESIGN_LOCKED`, TTS, VMAKE, CapCut은 운영자 수정·승인 전 만들거나 실행하지 않는다.
- episode state는 `current_stage=04`, `status=WAIT_EXTERNAL_REVIEW`, `final_design_locked=false`로 멈춘다.
- 보고 본문에는 `원본 순서 → 수정 순서`, T1/T2, 복사 가능한 대본, source→target 표, 사실 귀속 문구, 아직 측정하지 않은 TTS timing을 표시한다.
- 사용자가 문장이나 T1/T2만 수정하면 같은 `URAKKAI_BLUEPRINT.md`에 반영해 다시 전달하고, 승인 후에만 Stage 05 정본 산출물을 컴파일한다.

새 원본 URL로 회차를 시작할 때는 승인 순서를 바꾸지 않는다.

1. 먼저 원본을 상황·행동·화자·전달 방식·서사 기능 변화점으로 분석한다.
2. `원본 설계도`를 먼저 보고한다. 각 구조는 시간, 구조 번호, 전달 방식, 구조 유형과 함께 `화면`, `화면 텍스트`, `화자·대사`, `들리는 소리`, `상황 설명`을 분리해 작성한다. `화면`에는 실제 인물·차량·행동·카메라 구도를, `화면 텍스트`에는 상단 고정 제목·중앙/하단 대사 자막·상황 설명·강조 문구·워터마크를, `화자·대사`에는 실제 들리는 발언·TTS·나레이션을, `들리는 소리`에는 경적·엔진·현장음·효과음을 쓴다. 상황 설명은 이 정보를 생략한 줄거리 요약이 아니라, 무엇이 보이고·읽히고·들리는지를 종합한 장면 대본이어야 한다.
3. 그 아래에 구조 이동 방향을 한두 줄로만 간단히 추천한다. 이 단계에서는 변경된 수정 구조의 상세 target 시간표를 만들거나 먼저 보여주지 않는다.
4. 운영자가 추천 방향을 확정한 뒤에만 `변경된 수정 구조` 상세표, T1/T2, A9, target range, production plan을 만든다.
5. 이미 승인된 수정안의 비교 보고를 다시 요청한 경우에만 변경된 수정 구조를 원본보다 먼저 표시한다.

Stage 03~05에서는 JSON 이름이나 선택지만 먼저 말하지 않는다. 운영자가 `추천안이 안 보인다`, `사람눈 설계도 보여줘`라고 다시 요구하지 않도록 **승인 단계에 맞는 실제 문구와 표를 메시지 본문에 먼저 표시**한다.

- `templates/human-design-blueprint.md`를 복사해 회차별 `HUMAN_DESIGN_BLUEPRINT.md`를 만든다.
- 최소 표시 항목: 영상 한 줄, 핵심 메시지, 확정 T1/T2, A9 문구, 시간별 화면·소리·STATE 표, 마지막 문구, VIDEO/A9/A10/STATE/A11/A12 anchor 배치, baked-in 텍스트 처리 방식.
- 원본·수정 구조를 표나 MD로 넘길 때는 `references/structure-blueprint-reporting.md`를 읽는다. **새 원본의 Stage 02 보고는 원본 설계도→짧은 추천→운영자 확인 순서**다. 운영자가 방향을 승인해 Stage 03 수정안을 요청했거나 이미 승인된 안을 비교할 때만 변경된 수정 구조를 원본보다 먼저 배치한다. 각 구조에는 실제 변화 시간·구조 번호·전달 방식·구조 유형과 `화면·화면 텍스트·화자·대사·들리는 소리·상황 설명`을 표시한다.
- Stage 03 수정 구조를 전달할 때는 메시지 본문과 함께 회차별 **`20_script/URAKKAI_BLUEPRINT.md`**를 같은 응답에 첨부한다. `original-blueprint.md`, `first-recommendation.md`, 분석 원본을 우라까이 승인 파일 대신 보내지 않는다. 운영자가 T1/T2만 수정하면 새 제목을 같은 `URAKKAI_BLUEPRINT.md`에 반영한 뒤 그 파일을 다시 전달하고, 승인 이후의 final blueprint·production plan은 별도 단계 산출물로 유지한다.
- `production_plan.json`은 사람이 승인한 설계의 컴파일 결과다. JSON을 사람용 추천안 대신 보여주지 않는다.
- 승인 질문은 설계도 전체를 보여준 **뒤에만** 한다. 선택지에만 `추천안 그대로 진행`이라고 쓰고 추천안 내용을 생략하지 않는다.
- 운영자가 빠르게 진행하라고 했더라도 화면 과밀, clean 처리, 원본 음성/TTS 선택처럼 결과가 달라지는 항목은 설계도에서 눈에 보이게 표시한다.

## Urakkai Claude Review Loop Contract

001 `URAKKAI` Stage 04의 검토 개선 loop는 정확히 2회 실행한다. 이는 독립 검토 대화 두 개를 한 번에 모으는 방식이 아니라, **검토 → Hermes 개선**을 순서대로 두 번 반복하는 계약이다.

1. Loop 1은 현재 승인 후보를 first-party Claude OAuth의 Claude Opus `--effort low`로 검토하고 Hermes가 개선한다.
2. Loop 2는 Loop 1 개선본을 같은 항목으로 다시 검토하고 Hermes가 재개선한다.
3. Hermes는 baseline·Loop 1·Loop 2 후보를 비교해 source range·segment ID·승인 범위를 지키는 최상안을 직접 확정한다. Claude가 제안한 절대 초나 구조를 그대로 권위로 승격하지 않는다.

- 검토 범위는 훅 명확성, 장면 이해도, 이탈 지점, 대사 중복, 감정 연결이다.
- 실패한 Claude loop만 동일 입력의 Hermes 서브에이전트 검토 1회로 대체한다. 두 loop 증거가 채워지지 않으면 `WAIT_EXTERNAL_REVIEW`에서 중단한다.
- `20_script/external-review.md`와 `.json`에 loop별 입력·출력 hash, Hermes 개선, 채택·반려와 최종 선택 사유를 기록한다.
- 토큰, 쿠키, OAuth 값, URL, tab/conversation/session ID는 저장하지 않는다.
- `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY`에는 이 loop를 강제하지 않는다.

## CapCut Build Readiness

Stage 08에서 수분 동안 프로젝트가 생성되지 않으면 미디어 복잡도를 먼저 탓하거나 다른 제작 lane의 빌더를 빌리지 않는다. `references/capcut-build-readiness.md`의 순서로 최초 실패 경계를 찾는다.

macOS에서 근본 ZIP 복구, CapCut Home 검색, 창 영역 캡처, editor-open 판정 또는 cloud validator 경로 오탐을 다룰 때는 `references/capcut-macos-ui-verification-fallback.md`를 읽는다. Home에 프로젝트 카드·길이가 보이는 것은 등록 증거일 뿐 편집기 open 증거가 아니다. Home 배너가 사라지고 프리뷰·타임라인·트랙이 실제로 보인 뒤에만 `편집기 로드 완료`로 보고한다.

T1/T2와 A9 TTS/A9_TEXT를 함께 조립하거나 실제 CapCut 시작·중간·끝 화면, paired mirror, 종료 후 draft를 검증할 때는 `references/capcut-tts-visual-qa-post-open.md`를 읽는다. JSON에 텍스트·오디오 material이 있다는 사실만으로 화면 표시·실제 타임라인 연결을 PASS하지 않는다. T1/T2/A9/A9_TEXT readback, TTS 파형·무음 검사, 실제 프리뷰 fit, CapCut 종료 후 ID 기반 재검증까지 분리한다. 네 mirror 파일 전체를 하나의 hash로 강제하지 않고 manifest가 선언한 pair/group만 byte-identical로 검사한다.

Stage 05의 사람용 설계를 근본 CapCut anchor에 연결하거나 Stage 08을 결정론적으로 집행할 때는 `references/root-contract-production-plan.md`를 읽는다. 근본 프로젝트는 불변 정본으로 유지하고, root별 contract와 회차별 production plan을 분리한다. 실행 시 `tracks[n]`으로 추론하지 않으며 계약 anchor가 있는 root·timeline·관련 subdraft만 수정한다. 관련 없는 subdraft에는 root 트랙 수를 강제하지 않는다.

- builder 호출 전에 정본 ZIP·canonical state·lock/evidence·track mapping을 한 번에 preflight한다.
- `workflow.json`, builder state write, `validate_stage.py`가 동일한 state 경로와 전이 상태를 사용해야 한다.
- 최종 CapCut 경로에 직접 조립하지 않는다. 고유 staging에서 조립·검증한 뒤 PASS일 때만 원자적으로 승격하고, 실패 시 staging만 정리한다.
- 트랙은 숫자 index가 아니라 role/name과 구조로 찾는다.
- 병렬 계약 테스트만으로 제작 가능을 선언하지 않는다. 잠긴 입력에서 실제 editable project와 다음 canonical state까지 만드는 통합 테스트가 필요하다.
- production-plan schema에 선언한 모든 operation은 executor 구현과 실제 root-fixture readback 테스트가 있어야 한다. T1/T2만 구현했으면 전체 통합이 아니라 T1/T2 pilot로 보고한다.
- 다른 PC로 넘길 때는 정확한 GitHub·base commit·branch·target skill, complete patch(신규 untracked 파일 포함), pilot ZIP, file manifest와 SHA-256을 하나의 handoff ZIP으로 제공한다. commit·push·runtime 설치·Windows 시각 검증의 실제 수행 여부를 각각 명시한다.
- 30분 정체처럼 보일 때는 첫 오류·canonical state·잔존 target을 먼저 읽는다. confirmed defect와 Windows 실행 증거가 필요한 hypothesis를 구분해 보고한다.

## CapCut Export and Telegram Handoff

운영자가 `CapCut 내보내기`, `영상으로 저장`, `MP4로 줘`, `여기 올려`라고 하면 `references/capcut-export-telegram-handoff.md`를 읽는다.

- editable project, CapCut cloud upload, MP4 export, Telegram attachment를 각각 별도 완료 상태로 관리한다.
- 출력은 episode-local 외장 2pow `60_export/` 경로를 우선하고 기존 파일을 묵시적으로 덮어쓰지 않는다.
- 내보내기 클릭이 한 번 무시되면 좌표를 계속 추측하거나 같은 수동 클릭을 반복 요청하지 않는다. 전체 화면을 확인하고, 타임라인·timecode·프리뷰가 함께 바뀌는 **입력 응답 probe**로 편집기 응답을 먼저 판정한다. 창 단위 캡처에 보이지 않는 macOS native permission dialog가 입력을 막을 수 있다.
- 로컬 편집기만 무응답일 때는 정상 종료/정적 무결성 확인/앱 재시작 순서를 지킨다. 이미 업로드 후 reopen 검증을 통과한 동일 정본만 `User3160027826975의 공간/MAC`에서 대체 경로로 열 수 있으며, `자동 업로드`의 동명 행을 MAC 정본으로 오인하지 않는다.
- 타임라인 probe는 PASS하지만 내보내기만 무응답이면 반복 클릭·단축키 추측을 중단하고 실제 MP4 미생성을 정확히 보고한다.
- macOS 권한창·비밀번호·결제창은 대신 누르지 않는다. 사용자가 직접 처리한 뒤 내보내기를 재개한다.
- MP4는 ffprobe, duration·해상도·FPS·audio stream, 무음, 첫·구조 전환·중간·끝 프레임을 검증한 뒤에만 `MEDIA:`로 전달한다.
- 로컬 내보내기 요청을 YouTube 게시 승인으로 확대하지 않는다.

## Interim Editable Project and Sync

운영자가 `영상은 나중에 바꿔도 된다`, `일단 CapCut 프로젝트까지`, `동기화해줘`라고 하면 `references/interim-capcut-project-sync.md`를 읽는다. 완성 자산을 기다리며 프로젝트 생성을 멈추지 말고, 준비된 anchor만 배치한 **교체 가능한 편집 프로젝트**를 만든다.

- baked-in 제목·자막이 있는 임시 VIDEO를 쓰면 새 STATE/A9/A11/A12를 억지로 겹치지 않는다. 해당 template segment를 명시적으로 비우고 deferred 목록에 기록한다.
- 원본 음성을 별도 A10에 배치하면 VIDEO segment volume을 0으로 설정해 이중 재생을 막는다.
- VIDEO와 A10은 프로젝트 `Resources/media` 안에 복사해 프로젝트 ZIP이 자체 포함되게 한다.
- clone은 새 project/draft/timeline ID를 사용하고 근본의 cloud entry/space/user 연결을 물려받지 않는다.
- 최종 등록 전 `root_meta_info.json`을 백업하고, 같은 프로젝트명·draft ID 행을 제거한 뒤 정확히 1개만 등록한다.
- local CapCut 생성, OneDrive handoff 복사, CapCut cloud 업로드를 서로 다른 증거로 보고한다.
- 조정자가 바로 앞 메시지에서 `cloud upload + MAC row readback + cloud reopen`을 남은 범위로 명시했고 운영자가 `나머지는 진행해`, `계속 진행`, `동기화까지 마무리`라고 답하면 그 답을 해당 범위의 명시적 업로드 승인으로 취급한다. 이때 `WAIT_USER_CAPCUT_CHECK`나 로컬 ZIP 전달에서 멈추지 말고 cloud row 재열기·실제 전환 검수까지 끝낸다. 앞서 업로드 범위를 명시하지 않았다면 별도 승인을 받는다.
- CapCut 프로젝트를 가리키며 `동기화`, `프로젝트 동기화`, `캣컵 동기화`라고 하면 **CapCut cloud project upload/sync**로 해석한다. OneDrive handoff를 대신 수행하고 동기화 완료라고 보고하지 않는다. 고정 목적지는 `User3160027826975의 공간/MAC`이며 `TAKKTWO`는 제외한다.
- 사용자가 명시적으로 `OneDrive 동기화`, `handoff ZIP 복사`, `파일 동기화`라고 한 경우에만 local + OneDrive 흐름을 사용한다.
- CapCut cloud 업로드 전에는 `references/interim-capcut-project-sync.md`의 cloud-safe preflight와 `scripts/validate_capcut_cloud_media.py`를 실행한다. VIDEO/A9/A10만 보지 말고 모든 live `material_id`·`extra_material_refs`, parseable root/timeline/cache mirror, unreferenced Windows path, `.bak`, 빈/잔존 subdraft까지 검사한다. Windows path 탐지는 JSON 문자열의 실제 drive prefix만 대상으로 하며 정상 `https://` URL을 `s:/` drive로 오인해 삭제하지 않는다. rich-text `content` 안의 machine-local font cache를 정리할 때는 JSON을 파싱해 `font.path`만 비우고 text·resource ID·색상·range를 유지한다.
- `미디어 경로 손실` 경고가 나오면 업로드를 강행하지 않는다. `미디어 확인`이 파일 목록 대신 편집기를 열어도 성공으로 해석하지 말고 CapCut을 닫아 deterministic path probe로 원인을 찾는다. 프로젝트 내부 resource로 relink하거나 portable online effect ID를 보존한 채 machine-local cache path만 제거한 후 Home의 정확한 행에서 재업로드한다.
- 업로드 후 `MAC` 폴더 cloud row의 이름·크기·길이·유형·최근 시각을 읽고, 그 cloud row를 다시 열어 첫 구조 전환, T1/T2, TTS, offline media 부재를 검수해야 성공으로 보고한다.
- OneDrive는 프로젝트 ZIP·사람눈 설계도·production plan·root contract·asset manifest·build receipt·state를 함께 저장하고, source/destination SHA-256을 `sync_manifest.json`으로 재검증한다.
- 완료 보고 전 promoted project readback, ID mirror, root-meta 단일 등록, ZIP 무결성, 전체 skill 테스트를 새로 실행한다.

## Mandatory Completion Upload Copy

운영자가 001쇼츠 제작 완료를 보고받을 때는 공개 업로드를 실행하지 않았더라도 **항상 메시지 마지막에 업로드 제목·설명·출처를 붙인다.** CapCut 프로젝트명이나 validator 결과만 보고하고 끝내지 않는다.

필수 출력 순서는 다음과 같다.

1. `업로드 제목`: 복사 가능한 최종 제목 한 줄
2. `설명`: 영상에서 실제 확인되는 상황만 사용한 완성 문안과 해시태그
3. `출처`: 원본 채널, 원본 제목, 원본 URL, 원본 게시일(메타데이터에 있을 때)
4. `공개 업로드 상태`: `WAIT_UPLOAD_APPROVAL`, 예약/공개 완료 등 실제 상태

- 제목·설명·출처는 원본 `source_metadata`에서 readback한다. 채널·원본 제목·게시일을 추측하지 않는다.
- 화면 T1/T2와 업로드 제목은 별도 필드다. 가독성을 위한 띄어쓰기를 업로드 제목에서 조정할 수 있지만 CapCut에 승인된 T1/T2를 묵시적으로 바꾸지 않는다.
- 설명은 화면에서 관찰된 사실과 원게시물 정보를 분리하며, 확인되지 않은 사고·신원·장소·법적 판단을 만들지 않는다.
- 회차에 `60_upload/upload_info.json`과 `60_upload/UPLOAD_INFO.md`를 저장한다. Paperclip handoff를 쓰는 회차는 `reports/upload_info.json`, `reports/UPLOAD_INFO.md`, `handoff_manifest.json`의 제목·설명 경로·source credit에도 반영한다.
- OneDrive/CapCut 동기화 완료 보고에도 이 항목을 생략하지 않는다. 운영자가 다시 `제목 내용 출처 써줘야지`라고 요구하게 만들면 완료보고 계약 위반이다.
