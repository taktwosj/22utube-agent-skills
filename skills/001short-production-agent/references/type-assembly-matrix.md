# 유형 결정·조립 매트릭스

유형 선택부터 오디오 정책, 트랙 배치, 아티팩트 체인까지의 단일 조립설명서.
공식 시각 설명서(https://jsjtaktwo.mycafe24.com/skills/001short/)와 동기화.

## 두 축

음성 축: `A9` = 새 TTS 나레이션, `A10` = 원본 화자 목소리.
텍스트 축: `A9_TEXT` = TTS 자막(A9와 동일 문장, 1:1 강제), `A10_TEXT_WHITE/YELLOW` = 화자발언 자막(화자 1/2), `STATE_LASER` = 상황설명 자막.

**TTT** = 대응 음성이 없는, 새로 쓴 자막(대표: STATE_LASER 상황자막). 6번째 유형이 아니라 자막 방식이다. A9_TEXT는 음성이 있으므로 TTT가 아니다. TTT라는 단어가 오디오 축을 좁히지 않는다 — 유형 3~5는 A10을 유지한다.

## 조립 유형 5가지

| # | execution_strategy | 음성 | 자막 | production_mode × audio_policy |
|---|---|---|---|---|
| 1 화면+상황자막 (TTT형) | `caption_only` | 없음 (원본 무음) | STATE_LASER만; A9/A9_TEXT/A10/A10_TEXT/A11 empty | URAKKAI × `CAPTION_ONLY_MUTE_SOURCE` |
| 2 전체 TTS 설명형 | `full_tts` | A9 전체, 원본 무음 | A9_TEXT ↔ A9 verbatim | URAKKAI × `TTS_ONLY_MUTE_SOURCE` |
| 3 원본 화자발언형 | `original_audio_caption` | A10 원본 육성, A9 없음 | A10_TEXT_WHITE/YELLOW (+필요 시 STATE_LASER) | 하위 경로 4개 (아래) |
| 4 TTS 도입+화자 본문형 | `tts_intro_original_body` | A9 도입 2~4초 + A10 본문 | 각 자막을 해당 음성에 페어링 | URAKKAI × `A9_TTS_PLUS_A10_REASSEMBLED` |
| 5 나레이션+화자 혼합형 | `narration_plus_speaker` | A9 연결 + A10 증거·감정 | A9_TEXT + A10_TEXT | URAKKAI × `A9_TTS_PLUS_A10_REASSEMBLED`, overlap=`source_audio[].mode=duck` |

공통: T1/T2 항상, SCREEN_WHITE/SCREEN_EFFECT 전체 구간 템플릿 1개씩, STATE_GLITCH/STATE_FLICKER 예약, A12 항상 `비움`, VIDEO 항상 음소거(소리는 A9/A10 트랙 담당).

## 자격 규칙 (재료 → 가능한 유형)

- 검증된 화자발언 없음 → **1·2만**. 있음 → 1~5 전부 후보.
- 최종 V구간에서 화자발언을 전부 제외하면 3·4·5 선택 불가.
- 새 TTS 필수: 2·4·5. 화자발언 필수: 3·4·5. 음성 재료 없이 가능한 유형: 1뿐.
- 원본 나레이션은 어떤 유형에서도 반입 금지(기록용) — 해설은 TTS나레이션으로 새로 쓴다.

유형 후보는 원본표에서 기계적으로 나오고(화자발언 유무), 최종 유형·오디오 정책은 우라까이 승인에서 잠근다. 별도 게이트를 만들지 않는다.

## 결정 트리 (예/아니오)

1. **Q1 사람 목소리가 있는가?** (BGM·효과음·무음은 목소리 아님) — 아니오→화면 글자는 전부 상황설명, Q1-1로 / 예→Q2
2. **Q1-1 화면·행동만 봐도 이해되는가?** — 예→**유형 1** / 아니오→**유형 2**
3. **Q2 검증된 화자발언이 있는가?** (나레이션뿐이면 없음) — 아니오→Q1-1 (1·2만) / 예→화자 수 추정([A]/[B]) 후 Q3
4. **Q3 최종 V구간에 화자발언을 유지하는가?** — 아니오→Q1-1 / 예→Q4
5. **Q4 시작 0~4초 맥락이 화면+화자발언으로 충분한가?** — 아니오→**유형 4** / 예→Q5
6. **Q5 본문 연결에 새 나레이션이 필요한가?** — 아니오→**유형 3** / 예→**유형 5**

유형 3 확정 시: **Q6 V순서를 바꾸는가?** 예→③ / 아니오→**Q7 일부 B를 제외하는가?** 예→④ / 아니오→**Q8 BGM 제거 필요?** 예→② / 아니오→①

## 유형 3 오디오 하위 경로

| 경로 | 조건 | production_mode × audio_policy | A10 재료 | Demucs |
|---|---|---|---|---|
| ① 클린 원본순서 | 순서 변경 0, 컷 0 | `SOURCE_ORDER_UNCHANGED_CLEAN_ONLY` × `SOURCE_ORDER_CLEAN_AUDIO` | raw `SOURCE_CLIP` | 불필요 |
| ② 화자 유지 원본순서 | 순서 유지, BGM 제거 | `SOURCE_ORDER_UNCHANGED_A10_RETAINED` × `A10_RETAINED_SYNC` | 전체 stem | 필요 |
| ③ 화자 유지 우라까이 | V순서 재배열 | `URAKKAI` × `A10_REASSEMBLED_SYNC` | V순서 재조립 stem | 필요 |
| ④ 순서보존 트림 | 일부 B만 제외, 순서 유지 | `URAKKAI` × `SOURCE_ORDER_CLEAN_AUDIO` + `audio_source=SOURCE_CLIP`, `urakkai.production_type="TRIM_ONLY_NO_REORDER"` | 원본에서 V구간대로 직접 컷 | 불필요 |

④ 안전장치: 사용 구간은 검증된 원본 Bxx의 부분집합, `final_order`는 `original_order`의 순서 보존 부분열, 각 A10 세그먼트 구간 = 짝 VIDEO 구간 완전 일치. 위반 시 기존 가드가 그대로 차단한다.

## 유형별 15행 값 요약 (최종 표 기준)

| 행 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| A9_TEXT | 없음 | 값 | 없음 | 값(도입) | 값(연결) |
| A10_TEXT_WHITE/YELLOW | 없음 | 없음 | 값 | 값(본문) | 값 |
| STATE_LASER | 값(TTT) | 없음 | 필요 시 | 필요 시 | 필요 시 |
| A9 | 없음 | 값 | 없음 | 값(2~4초) | 값 |
| A10 | 없음 | 없음 | 값 | 값 | 값(duck) |

원본표는 유형 판정 전이므로 항상 15행 전부 기록한다.

## SOURCE_CLIP A10 아티팩트 체인 (유형 3-①·④)

각 단계 산출물의 SHA-256이 다음 단계에 들어간다. 상류 파일 수정 시 디스크에서 새로 읽어 모든 하류 SHA를 한 번에 재기록한다.

1. `00_input/source_identity.json` + `source_metadata.json` + `source_intake_receipt.json`
2. `20_script/approved_timeline.json` — Vxx별 VIDEO 세그먼트(`source_range_us`, `locked_source_beat_id`) + 같은 시작/길이의 A10 세그먼트(개수·순서는 `build_manifest.source_audio`와 일치) + A10_TEXT/STATE 세그먼트 + T1/T2/SCREEN 전구간 1개씩; `production_mode`/`audio_policy`/`primary_speaker_id` 설정
3. `30_audio_srt/audio_lock.json` — `audio_source=SOURCE_CLIP`이면 `audio_path`는 원본 `00_input/source.mp4` (클린 영상은 화면 전용)
4. `30_audio_srt/final.srt` + `caption_lock.json` — cue당 A10_TEXT/STATE 1개, `cue_id`=timeline 행. 경계는 밀리초로 미리 절사해 SRT 왕복 오차 방지
5. `50_capcut_project/build_manifest.json` — `urakkai.video_clips`(사용 Bxx만) + `source_audio`(Vxx당 1개, `mode="on"`, 원본 오디오면 `capcut_source_range_us`를 실제 원본 구간으로 명시) + `vmake.receipt_path`
6. `40_assets_used/clean_visual_manifest.json` + receipt — expected/measured duration은 VMake 출력 실측값
7. `20_script/design_handoff.json` + `design_lock_evidence.json`
8. `20_script/production_plan.json` + validation receipt — `original_order` 전체, `final_order` 실사용 순서, `cleared_anchors`에 빈 역할 전부
9. `30_audio_srt/caption_timing_evidence.json` — `mapping[]`과 `cues[]`(authority=`SPEECH_AUDIO`/`STATE`) 모두 필수
10. `90_workflow/state.json` — 절대경로+SHA, `status=AUDIO_CAPTION_VALIDATED`, `next_action=CAPCUT_BUILD`
11. `50_capcut_project/build_config.json` → `build_episode_capcut.py --config`
