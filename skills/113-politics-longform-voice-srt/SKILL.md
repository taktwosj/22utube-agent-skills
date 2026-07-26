---
name: 113-politics-longform-voice-srt
description: Use when the user requests 정치롱폼 나레이션 음성 생성, Supertone TTS, 오디오 시간축 정본, 강제정렬, 최종 SRT 초안, 자막 QC 패키지, or 대본 내용 감사 for a politics longform episode. Covers the P00~P04 stages between SCRIPT_LOCK and HyperFrames assembly.
---

# 113 Politics Longform Voice + SRT

HyperFrames lane의 음성·자막 구간을 소유한다. 권위 대본 확정 이후 ~ 조립 직전.
조립은 `112-politics-longform-hyperframes`가 이어받는다.

```text
IN  = 확정된 권위 대본 (.md) + 원본 mp4/srt
OUT = 나레이션 WAV + 오디오 시간축 정본 + 최종 SRT 초안 + 자막 QC 패키지
```

## Lane 경계

`111-politics-longform`의 제작 계약을 **상속**하되 CapCut 조립 계보는 잇지 않는다.

```text
KEEP_UNCHANGED = skills\111-politics-longform
KEEP_UNCHANGED = skills\000-politics-longform 및 그 CapCut worktree
NEXT_STAGE     = 112-politics-longform-hyperframes
CapCut fallback = FORBIDDEN
```

111을 인플레이스 전환하지 않는다. HyperFrames 실패를 CapCut 자동 실행으로
우회하지 않는다. 사용자가 CapCut·일반 정치롱폼을 요청하면 111 lane으로 돌려보낸다.

111에서는 **구현 중립적 의미 규칙만** 상속한다: 진행판 상태 어휘,
`POLITICS_WRITER_MACHINE` 단일 writer 소유권, 확정 교정본의 상위 권위,
source caption 정규화 연결 일치(승인 교정 반영), 가운데점·문장부호 보존,
locked clip 0.25초 허용오차.

CapCut 화면 구현은 하나도 상속하지 않는다. 상속·폐기 전체 목록은
[lane-contract.md](references/lane-contract.md)를 따른다.

## 권한 경계

```text
script_authority              = PROJECT_GPT
final_subtitle_qc_authority   = PROJECT_GPT
user_role                     = INTERMEDIARY_AND_VISUAL_QC
executor_editorial_authority  = NONE
```

최종 자막 오류 판정은 **프로젝트 GPT가 한다.** 사용자는 중개자다.
확정 교정본이 나오면 `PROJECT_GPT_CORRECTED_SRT_LOCK`이 최상위 권위이며
자동자막·생성 자막·초벌 SRT·정렬 결과보다 우선한다.
`PROJECT_GPT_CORRECTED_SRT_LOCK=PASS` 전에는 최종 자막을 만들지 않는다.
검증 후 본문·줄바꿈·문장부호·cue 순서를 다시 자동 교정하거나 축약하지 않는다.
위반 시 `FAIL_PROJECT_GPT_CORRECTED_SRT_FIDELITY`.
교정본이 없는 에피소드는 이 게이트를 `NOT_APPLICABLE`로 기록한다.

권위 순서 전체와 lock 요건은 [lane-contract.md](references/lane-contract.md).
`USER_CORRECTED_SRT_LOCK`은 111 레거시 명칭이며 alias로만 남는다.

에이전트(Claude·Codex 동일)는 대본 문장·논지·결론·챕터 순서·발언자 귀속을
**절대 수정하지 않는다.** 오류를 발견하면 고치지 말고 보고서로 올린다.

우선순위: 사용자 최신 확정 지시 > 실제 파일·실행 결과 > AGENTS.md/CLAUDE.md >
WORK_ORDER > 프로젝트 GPT 권위 대본 > 111 SKILL.md > workflow/config/schema >
GitHub PR > 과거 대화 > 추정.

## 상태 어휘 (강제)

증거 없이 쓰면 안 되는 말: `PASS` `FINAL` `SCRIPT_LOCK` `upload_ready`
`production PASS` `렌더 완료` `업로드 완료`.
미실행·차단은 `WAIT` / `NOT RUN` / `BLOCKED` / `FAIL`.

## 재개 규칙

컨텍스트 압축 직후나 작업 재개 직후에는 **계약 파일을 다시 읽는다** —
`production_authority_event_v1.json`, `voice_manifest.json`,
`review_audio_timeline_v1.json`. 요약은 손실이라 SHA·오프셋 같은 정확값이 날아간다.
요약 안의 값을 근거로 PASS를 주장하지 않는다.

## 경로 분리 (필수)

```text
로컬 미디어 정본 (WAV/MP3/MP4, Git 미추적):
  {onedrive}\22factory_*\02_politics_longform\episodes\{EPISODE_ID}\

Git 추적 산출물 (SRT/JSON/보고서):
  {clean_checkout}\docs\politics-longform\episodes\{EPISODE_ID}\
```

Git에 올릴 때 `LOCAL_SHA256 == REPO_SHA256` 확인. WAV/MP3/MP4는 커밋하지 않고
manifest에 로컬 경로·크기·SHA-256·길이·생성도구만 기록한다.

**비정본 worktree 재사용 금지.** 권위 커밋 SHA로 clean clone을 새로 만든다.
`reset` / `rebase` / `push --force` / PR 병합 / 업로드 없음.

## 환경변수

모든 스크립트가 요구한다. 미설정 시 즉시 종료된다.

```bash
PL_EPISODE_DIR=<OneDrive 에피소드 폴더>
PL_REPO_EPISODE=<clean checkout 내 docs/.../episodes/{EPISODE_ID}>
PL_VIDEO_DIR=<원본 S01.mp4~ 폴더>
PL_SCRIPT_SHA256=<권위 대본 SHA-256>
```

## 용어 계약

전체 규칙은 [lane-contract.md](references/lane-contract.md)에 있다. 요약:

| 개념 | 명칭 | 112 visual_role |
|---|---|---|
| Supertone 합성음성 | `narration_audio` | — |
| 합성음성 자막 | `narration_caption` | `caption-text` |
| 원본 영상 발화 자막 | `source_speech_caption` | `caption-text` |
| 챕터 제목 | `chapter_title` | `chapter-title` |
| 챕터 번호 | `chapter_number` | `chapter-number` |
| 출처 라벨 | `source_label` | `source-label` |
| 출처 날짜 | `source_date` | `source-date` |
| 우상단 평론 라벨 | `comment_label` | `comment-label` |

`TTS`를 단독 역할명으로 쓰지 않는다. `Supertone TTS API`로만 한정한다.
111의 `role: tts`는 합성음성이 아니라 원본 발화 자막을 뜻해 정면 충돌한다.

## 자막 계약

**113은 자막의 의미와 데이터만 만든다. 화면 배치는 112 템플릿이 정한다.**

112 repo 정본 `style_tokens.json` 실측: 자막 밴드 1개, `maxLines: 2`,
`fontSize: 60`, `width: 1540`.

```text
cue 길이 상한을 113이 숫자로 정하지 않는다.
초과 판정 = 112의 hyperframes check --strict --snapshots layout 검사.
overflow가 나면 문구를 줄이지 말고 speech boundary에서 cue를 더 쪼갠다.
```

`comment_label`은 우상단 450px 라벨이며 111의 하단 2줄 평론 트랙과 다른 것이다.

```text
SOURCE_SPEECH_CAPTION_FIDELITY (v2):
  기준선 = 선택 원본 source_text에 승인 교정을 적용한 값
  표시 cue 텍스트를 시간순 정규화 연결한 값 == 기준선
  불일치 = FAIL_SOURCE_SPEECH_CAPTION_FIDELITY

  승인 교정 = source_caption_exceptions_v1.json에 기록된 항목만
  실행자 임의 교정 = 여전히 금지
```

기준선이 원본 원문이 아니라 **원본 + 승인 교정**인 이유, 예외 카테고리
(`ASR_TYPO` `SPEAKER_MARKER` `NONVERBAL` `BOUNDARY_TRIM` `SEGMENTATION`),
승인 절차는 [source-caption-exceptions.md](references/source-caption-exceptions.md).

원본이 유튜브 자동자막이면 자동자막 자체의 오류가 화면에 그대로 나간다.
실행자는 그걸 **발견해서 올리고**, 프로젝트 GPT가 승인한 것만 적용한다.

축약·요약·의역 금지. 가운데점 `·`, 띄어쓰기, 고유명사, 문장부호를 그대로
보존한다 (`수사·기소`, `재건축·재개발`). 렌더에서 잘리는 것이 **실제로 확인된**
경우에만 사용자에게 알리고 비자막 템플릿 문구를 고친다. 교정 자막을 쉼표로
되돌리지 않는다.

## 파이프라인

### P00 권위 이벤트 기록 (음성 생성 전 필수)

권위 대본 안의 `WAIT_USER_FINAL_APPROVAL` 같은 내부 게이트 문구는
**수정하지 않는다.** 최신 지시는 별도 파일로 기록해 충돌을 해소한다.

`90_reports/production_authority_event_v1.json`:
```json
{
  "current_stage": "VOICE_AND_SRT_DRAFT",
  "script_authority": "PROJECT_GPT",
  "executor_editorial_authority": "NONE",
  "supersedes": "WAIT_USER_FINAL_APPROVAL",
  "authority_source": "LATEST_USER_INSTRUCTION"
}
```

### P00b 대본 내용 감사 (음성 생성 차단 게이트)

SHA·cue 수 검증은 **무결성**일 뿐 내용 검사가 아니다. 수천 자를 합성한 뒤
문구가 바뀌면 전량 재생성이므로 반드시 P02 앞에 둔다.

전문을 읽고 검사할 항목: `references/script-audit-checklist.md`

산출 `90_reports/script_content_audit_v1.json` — finding별
`id, severity, line, category, original_text, observation, advisory_fix,
exposed_as_subtitle, ruling_required`.

```text
P02_EXECUTION = BLOCKED_UNTIL_PROJECT_GPT_SCRIPT_RULING
ruling_options = NO_CHANGE | REVISE_AND_RECOMMIT
```

`REVISE_AND_RECOMMIT`이면 새 commit SHA·blob SHA·SHA-256을 받아 P01부터 재검증하고
영향 세그먼트만 재생성한다.

### P01 원본 무결성

대본 SHA-256 재확인. 증거범위 안의 원본 `Sxx.srt` / `Sxx.mp4` 존재·cue 수 확인.
**증거범위 밖 소스 사용 금지.** 대본 클립 타임코드가 해당 SRT cue 범위 안인지 대조.
산출 `90_reports/source_integrity_report.json`.

### P02 narration_audio 생성 (Supertone TTS API)

**함정 3개 — 전부 실측으로 확인된 것이다.**

1. **레지스트리가 프로세스 env를 덮는다.**
   `00_asset_tools/tools/make_supertone_tts.py`의 `get_env()`는
   `read_windows_user_env(name) or os.environ.get(name)` 순이다.
   후보별 환경변수 override가 **동작하지 않는다.** 설정을 바꾸려면 그 도구를 쓰지 말고
   SDK에 파라미터를 직접 넘겨라 (`scripts/gen_narration_full.py`가 그렇게 한다).
2. **`SUPERTONE_TTS_GUIDE.md`는 stale.** 가이드의 Chunsik / `sona_speech_1` /
   pitch 1.2 / speed 1.2 조합은 프로덕션에서 쓰이지 않는다.
   확정값 — 도구 기본값·프로덕션 매니페스트 일치:
   ```python
   VOICE_ID = "otFXhy6zBa2LQ8AYSWUeDB"
   MODEL = "sona_speech_2"
   VOICE_SETTINGS = {"pitch_shift": 0, "pitch_variance": 1, "speed": 1}
   ```
3. **Codex 샌드박스는 아웃바운드 HTTPS를 막는다** (`WINERROR_10013`).
   Supertone 호출은 Codex가 아니라 메인 런타임에서 실행한다.
   Codex는 세그먼트 분할·검증·정렬·조립 등 오프라인 작업을 맡는다.

SDK는 **WAV 바이트만** 반환한다. 타임스탬프 없음.
```python
client.text_to_speech.create_speech(
    voice_id=..., text=..., language="ko", model=..., output_format="wav",
    voice_settings={"pitch_shift": 0, "pitch_variance": 1, "speed": 1})
```

API 키는 `winreg` HKCU\Environment에서 읽고 **출력·로그·manifest에 절대 남기지 않는다.**
존재 확인은 `PRESENT(length=N)` 형태로만.

전량 생성 전 짧은 샘플로 음색을 확정하고 프로젝트 GPT 판정을 받는다
(`WAIT_PROJECT_GPT_VOICE_SELECTION`). 샘플 텍스트는 대본 원문 발췌 —
인명·법률용어가 함께 들어간 구간을 고른다.

실행: `scripts/gen_narration_full.py`
세그먼트별 WAV + SHA-256 + `ffprobe` 실측 + 누적 오프셋 → `voice_manifest.json`.
`MAX_RETRY=3`. **실패를 추정 길이로 대체하지 않는다.**
manifest에 `authoritative_script_sha256`을 박아 staleness를 탐지한다.

### P02b 발음 검사 + 정렬

실행: `scripts/align_narration.py` (faster-whisper `medium` int8 cpu,
`word_timestamps=True, vad_filter=False, beam_size=5`).
HF 캐시가 있으면 네트워크 불필요 — Codex가 오프라인 실행 가능.

대본 세그먼트에 있는 위험 어휘가 ASR 전사에도 나타나는지 대조한다
(인명·`보완수사권`·`공소청`·`중수청`·`형사소송법`·`고위공직자범죄수사처` 등).
불일치는 오발음 확정이 아니라 **청취 확인 대상**이다. 오발음 확인 시 대본을
임의 수정하지 말고 `PROJECT_GPT_SCRIPT_REVISION_REQUIRED`로 복귀.

산출 `alignment_raw_v1.json`, `90_reports/pronunciation_check_v1.json`.

### P02c 오디오 시간축 정본 (잠금)

`scripts/extract_clips.py`로 원본 클립 오디오를 실제 타임코드로 추출한다
(`ffmpeg -vn -acodec pcm_s16le -ar 44100 -ac 2`, 원본 mp4 무수정).

나레이션 + 클립을 **대본 문서 순서대로** 연결해 시간축 정본을 만든다.
**묵시적 무음 금지** — 무음이 필요하면 별도 세그먼트로 JSON에 명시한다.

```text
AUDIO_TIMELINE_AUTHORITY = review_audio_timeline_v1.json
P06_AUDIO_RETIMING = FORBIDDEN
```

production_design은 이 시간축 위에 **영상만** 배치한다. 세그먼트 순서·길이·간격
변경 금지. 이래야 P03 SRT가 조립 단계에서 다시 틀어지지 않는다.

클립 세그먼트 검증 (111 상속):
```text
audio_duration_sec >= video_duration_sec - 0.25
|추출 실측 길이 - 대본 타임코드 길이| <= 0.25
라우드니스 정규화를 실행했을 때만 AUDIO_LOUDNESS_NORMALIZATION=PASS.
볼륨을 1.0으로 두기만 한 것은 PASS가 아니다.
```

### P03 최종 SRT 초안

**정렬 방법 우선순위 — 문자 수 비례 배분은 금지다.**

```text
1순위: 공급자 단어 타임스탬프    → Supertone SDK는 제공 안 함
2순위: 실제 WAV forced alignment
3순위: ASR 타임스탬프 + 문구는 권위 대본으로 재매핑   ← 현재 채택
금지 : 문자 수 비례 배분 (짧은 쇼츠엔 통해도 롱폼에선 블록 내부가 드리프트)
```

기존 쇼츠의 `reconcile_actual_tts.py:retime_caption_beats()`가 바로 그 금지 패턴이다.
**참조만 하고 쓰지 않는다.** 단 같은 파일의 `wav_duration` / `srt_timestamp` /
`write_srt` 직렬화 패턴은 재사용 가치가 있다.

자막 문자열은 **ASR 출력이 아니라 권위 대본 원문**을 쓴다. ASR에서 얻는 것은
타이밍과 발음 확인뿐이다.

`source_speech_caption`은 원본 SRT의 cue를 추출해 클립 시작 기준 상대시간으로
바꾼 뒤 시간축 정본의 해당 오프셋을 더한다. 위 `SOURCE_SPEECH_CAPTION_FIDELITY`를
여기서 적용한다.

정렬 수단이 없으면 `SRT_ALIGNMENT = BLOCKED / REASON = ALIGNMENT_METHOD_UNDEFINED`.

**기계 검증 10항목 — 전부 0이어야 통과.** `references/srt-validation.md`

기술적 줄바꿈만 적용. 대본 문구 재작성 금지.

산출:

```text
30_audio_srt/narration_caption_v1.srt
30_audio_srt/source_speech_caption_v1.srt
30_audio_srt/final_srt_draft_v1.srt
30_audio_srt/subtitle_qc_package_v1.json
30_audio_srt/production_input_v1.json     <- 112로 넘기는 단일 입력
90_reports/srt_validation_report_v1.json
90_reports/113_validation_report_v1.json
```

`production_input_v1.json` 필드는 112 SKILL.md와 template schema를 **실제로 읽고**
확정한다. 최소 의미 필드 목록은 [lane-contract.md](references/lane-contract.md).

### P04 인계

텍스트 산출물만 커밋(`politics-longform: add voice manifest and SRT draft` 형식),
일반 push. PR 병합·업로드 없음.
최종 상태 `WAIT_PROJECT_GPT_SUBTITLE_QC`.
QC 결과 `subtitle_corrections_v1.json`을 받아 반영한 뒤 112로 넘긴다.

112 인계 계약:
```text
episode_project = {episode}\60_hyperframes\project
넘기는 것 = 오디오 시간축 정본 + 최종 SRT + 나레이션/클립 WAV 로컬 경로 manifest
112는 대본, source range, WAV, SRT, chapter 순서를 바꾸지 않고 HTML로 구현한다.
preview 승인 전 render 없음.
```

## 실행 주체 판단

| 작업 | 주체 | 이유 |
|---|---|---|
| 외부 API 호출 (Supertone) | 메인 런타임 | Codex 샌드박스가 HTTPS 차단 |
| 미리 확정된 결정적 스크립트 실행 | 아무나 | 결과 동일. Codex는 spawn 비용만 추가 |
| 실패·진단·재시도 루프 (조립·렌더) | Codex | 반복 디버깅에서 값어치 |
| 대본 내용 판단 | 아무도 안 함 | 프로젝트 GPT 전속 |

Codex에 넘길 때 스크립트를 **clean checkout 안**에 복사하고 절대경로로 지시한다.
스킬이 Codex 런타임에 보이려면 `.codex/skills`에도 동기화돼 있어야 한다.

## 완료 보고 항목

생성 파일 절대경로 + SHA-256 / 나레이션 총·세그먼트별 실측 길이 /
시간축 정본 총 길이와 세그먼트 매핑 수 / SRT cue 수(나레이션·원본 구분) +
검증 10항목 / 발음 검사 결과 / commit SHA + remote head SHA / 현재 상태.
