# CapCut T1/T2/TTS 조립·시각 QA·post-open 계약

## 적용 범위

근본 CapCut ZIP에서 쇼츠 프로젝트를 신규 조립하면서 T1, T2, A9 TTS, A9_TEXT, A10 원본 음성을 함께 배치하고 실제 CapCut 화면과 종료 후 draft를 검증할 때 적용한다.

## 조립 계약

- 근본 ZIP은 불변 authority이며 매 build마다 새 staging과 새 build/project/timeline ID를 만든다.
- source authority와 working staging은 반드시 다른 경로여야 한다. 같으면 `SOURCE_WORKING_CONFLICT`로 중단한다.
- raw track index 대신 root contract의 logical anchor를 사용한다.
- T1/T2 노출 시간은 승인된 `production_design`이 권위다. 3초 같은 builder 상수를 두지 않는다. 전체 영상 유지가 승인안이면 VIDEO 전체 길이를 사용한다.
- A9를 비우기만 하고 끝내지 않는다. 실제 TTS material과 segment를 생성하고 `Resources/media`의 self-contained WAV에 연결한다.
- A9_TEXT는 A9와 start/duration이 같아야 한다.
- A10은 승인된 mix plan에 따라 A9 종료 후 시작하거나 duck한다. A9와 A10의 의도하지 않은 중복재생은 FAIL이다.
- distinct production material/segment에는 신규 ID를 사용한다.
- 실패 프로젝트, 이전 에피소드 프로젝트, 로컬에 풀려 있는 근본 프로젝트를 다음 build 입력으로 사용하지 않는다.

## 오디오 검증

TTS와 원본 음성은 하나의 lock으로 뭉치지 않는다.

```text
tts_lock.json
source_audio_lock.json
audio_mix_plan.json
```

TTS는 다음을 검사한다.

- 실제 파일 존재 및 SHA-256
- decode 성공
- PCM_S16LE, 48kHz, mono 권장
- 실제 측정 길이와 A9/A9_TEXT duration 일치
- mean/peak 기준 무음 아님
- CapCut 타임라인에서 파형 확인

## 자막 fit

JSON에 텍스트가 존재하는 것만으로 PASS하지 않는다.

- A9_TEXT는 실제 프리뷰에서 좌우·아래 잘림을 확인한다.
- 긴 문장은 의미 단위 줄바꿈을 적용하고 기본 최대 2줄로 검수한다.
- T1/T2/A9_TEXT의 OCR 또는 사람이 읽을 수 있는 프리뷰 증거를 남긴다.
- 시작 화면에서 T1/T2/A9_TEXT, 중간·끝에서 T1/T2 유지와 A9_TEXT 종료를 확인한다.
- baked-in 원본 자막이 있으면 STATE/A10_TEXT를 겹쳐 과밀하게 만들지 않는다.

## mirror 규칙

네 파일 전체가 하나의 hash여야 한다고 강제하지 않는다. CapCut post-open은 `draft_content`를 갱신하고 `template-2.tmp`를 그대로 둘 수 있다.

```text
GROUP_A: root/draft_content.json == timeline/draft_content.json
GROUP_B: root/template-2.tmp == timeline/template-2.tmp
```

GROUP_A hash와 GROUP_B hash가 서로 달라도 정상일 수 있다. 정본 manifest가 별도 mirror group을 선언한 경우에만 그 그룹을 추가 검사한다.

## post-open 재검증

1. CapCut에서 프로젝트를 연다.
2. 시작·중간·끝과 TTS 파형을 확인한다.
3. CapCut을 완전히 종료한다.
4. 실제 draft를 다시 읽는다.
5. paired mirror, ID, duration, root_meta, media path, T1/T2/A9/A9_TEXT를 재검사한다.

프로젝트명은 추적 권위가 아니다. CapCut이 충돌 시 `(1)` 같은 suffix를 붙일 수 있으므로 `draft_id`, `project_id`, `timeline_id`, build receipt로 실제 폴더를 다시 찾는다.

## root qualification

다음은 episode builder에서 임시 삭제하지 말고 근본 ZIP 자체를 재자격화한다.

- stale Windows 절대경로 또는 missing media
- unresolved combination/subdraft reference
- cloud handoff에서 나타나는 media reconnect 경고
- 카드 opening의 검은 header·여백 같은 반복 시각 결함

재자격화 후 새 SHA-256 manifest를 발행한다. episode build 중 root 구조를 임의 정리하는 코드는 정식 수정이 아니다.

## 상태와 판정

```text
CAPCUT_BUILD_CREATED
CAPCUT_STATIC_VALIDATED
WAIT_USER_CAPCUT_CHECK
```

`AGENT_PRIMARY_CLEAN_SOURCE` and `USER_FALLBACK_CLEAN_SOURCE` VIDEO-only swap/reassembly remain Stage08 work. After `WAIT_USER_CAPCUT_CHECK`, CapCut visual refinement/approval, render, and upload are user-only; no Stage09 router may create render evidence or advance those states.

- 에이전트의 구조·프리뷰 검수는 사용자 최종 시각 승인을 대신하지 않는다.
- 클라우드 목록 노출은 콘텐츠 QA PASS가 아니다.
- 사용자 승인 전 render/upload 완료를 보고하지 않는다.
- 고정 10회 Round를 workflow에 넣지 않는다. 여러 번의 반복은 일회성 스트레스 테스트로만 사용하고, 정상 운영은 오류 유형별 복귀와 clean rebuild를 따른다.

## 회귀 테스트 최소 세트

- A9/A9_TEXT가 실제로 배치되고 같은 길이를 갖는다.
- T1/T2가 승인 구간 전체에서 유지된다.
- A10 start/duck이 mix plan과 일치한다.
- source authority와 working staging 동일 경로는 FAIL한다.
- paired mirror는 post-open 후 PASS한다.
- 프로젝트 이름 suffix 변경 후에도 ID로 draft를 찾는다.
- 모든 retained material ref와 media file이 존재한다.
- active draft에 `.bak`, `before_*`, backup/helper/temp 파일이 없다.
