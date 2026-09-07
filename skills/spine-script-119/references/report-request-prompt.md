# 척추대본 회차 보고서 요청문

회차가 끝난 뒤 보고서를 받을 때 그대로 붙여 쓰는 프롬프트다. 앞부분(경로·회차 id)만 바꾼다.

---

## 붙여 쓰는 프롬프트

```text
아래 회차의 척추대본 보고서를 써줘.

회차 루트   E:\22utube\<EPISODE_ID>
패킷        C:\Users\arajun\OneDrive\22utube\22factory_20260628\0000jungchi\<EPISODE_ID>\00_pre119_package

읽을 것 — 전부 실측값이다. 여기 없는 숫자는 쓰지 마라.
  work\timeline.json                     카드별 시각·길이
  work\cards_def.py                      SPINE_VIDEO_ID, SOURCES, BURNED_CAPTION, PUBLICATION
  work\preflight.json                    caption_layout / srt_text_fidelity / overlay_contract / findings
  work\build_report.json                 project_path / media_path / title / thumbnail
  work\readback.json                     각 게이트 PASS·FAIL
  asset_evidence.json                    카드 수, lane 상태
  90_reports\pre119_handoff_validation.json   status, script_lock sha 일치
  20_script\pre119_handoff.json          publication_report (제목·설명·타임라인·출처·썸네일)

검사도 같이 돌려서 그 출력을 근거로 써라.
  python <skill>\scripts\check_captions.py --root E:\22utube\<EPISODE_ID>

보고 형식은 references\report-format.md 를 그대로 따른다. 산출물 먼저, 검증 뒤.

반드시 지킬 것
  - 산출물 다섯 항목(프로젝트명·미디어·제목·내용·썸네일)을 맨 앞에 둔다.
    값은 pre119_handoff.json 의 publication_report 에서 그대로 가져온다. 새로 쓰지 않는다.
  - 출처는 `출처 : <채널명>` 만. 플랫폼명·영문병기·영상 제목을 붙이지 않는다.
  - 척추 비율은 오프닝 몽타주 재사용분을 뺀 값이다. 계산식을 같이 적어라.
  - 척추가 한 덩어리가 아님을 보이는 배치 표를 넣어라. 시각·챕터 문구·길이.
  - 실행하지 않은 검증은 NOT RUN 이다. PASS 로 쓰지 마라.
  - MEDIA_RELINK FAIL 은 정상이다. 릴링크가 사용자 작업이라고 적어라.
  - 12분 미만이거나 척추가 50% 미만이면 PASS 로 보고하지 마라.
  - 이번 회차에 우회한 스킬 결함이 있으면 SKILL_FIX_NEEDED 로 모아라. 없으면 없음.
  - 긴 로그를 붙이지 마라. 결론·최초 실패·다음 행동만.
  - NEXT 는 사용자가 지금 할 한 가지 행동이다.
```

---

## 근거 없이 쓰기 쉬운 항목

보고서를 쓸 때 아래는 **파일에서 읽은 값만** 쓴다. 기억이나 추정으로 채우면 틀린다.

| 항목 | 근거 파일 | 흔한 오류 |
|---|---|---|
| 총 길이 | `timeline.json.total_seconds` | 목표치를 실제값처럼 씀 |
| 척추 비율 | `timeline.json` + `SPINE_VIDEO_ID`, 훅 제외 | 훅 재사용분을 포함해 부풀림 |
| 나레이션 비율 | `timeline.json` kind=NAR 합 | TTS 전 추정치를 그대로 둠 |
| 소스 편수·채널 | `cards_def.SOURCES` | 실측 안 한 channel_id를 씀 |
| 게이트 상태 | `readback.json`, `preflight.json` | 안 돌린 게이트를 PASS로 씀 |
| 제목·썸네일 | `pre119_handoff.json` | 보고서에서 새로 지어냄 |
| 프로젝트·미디어 경로 | `build_report.json` | 예상 경로를 씀 |

## 회차 중간 점검용 (짧은 버전)

```text
E:\22utube\<EPISODE_ID> 상태만 짧게 확인해줘.
timeline.json 기준으로 총 길이 / 척추 분·퍼센트(훅 제외) / 나레이션 퍼센트 / 카드 수,
그리고 check_captions.py 출력의 [1] [2] 요약 한 줄씩. 계약 미달이면 무엇이 모자란지.
파일에 없는 숫자는 쓰지 마라.
```
