---
name: 110-politics-longform-script
description: Use when the user says 정치롱폼, 정치미드폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, 110대본, 정치롱폼 대본, 초벌 대본, or 대본 초안, or asks to turn collected political video sources and subtitles into a narration script. Entry point of the politics longform pipeline: 110 script, then 111 voice and SRT, then 112 HyperFrames.
---

# 110 Politics Longform Script

수집된 원본 영상과 자막에서 **확정 대본**까지를 담당한다. 여기서 나온
확정 대본이 111의 입력이다.

## Lane 경계

```text
CapCut lane(119) = OUT_OF_SCOPE
KEEP_UNCHANGED = C:\Users\arajun\agent-skills\skills\119-politics-longform-capcut
KEEP_UNCHANGED = C:\Users\arajun\worktrees\agent-skills-000-politics-new\skills\000-politics-longform
MODIFY_119_OR_ITS_WORKTREE = FORBIDDEN
MODIFY_000_OR_ITS_WORKTREE = FORBIDDEN
NEXT_STAGE = 111-politics-longform-voice-srt
```

119도 소스를 모으고 초벌 문안을 만들지만 그 산출물은 CapCut 화면 설계도와
하단 2줄 평론이다. 나레이션 대본이 아니다. 110은 119를 읽지도 호출하지도
않는다.

## 권위 분담

이 스킬의 존재 이유는 **누가 무엇을 정하는지 못박는 것**이다.

```text
PROJECT_GPT   무엇을 말할 것인가        논지 · 구성 · 인용 선택 · 챕터 순서
CLAUDE        말한 것이 원문과 맞는가    대조 · 검증 · 조립
USER          최종 확정                 script_lock 승인
```

Claude는 문장의 **의미를 바꾸지 않는다.** 완성 단계에서 하는 일은 대조,
표기 통일, 기계 검증, 최종 파일 조립이다. 논지를 고치거나 문장을 새로
쓰거나 인용을 바꾸면 그 시점에 이 계약은 깨진 것이다. 지적은 GPT에
돌려보내고 GPT가 판정한다.

## 왜 출처 줄을 요구하는가

직전 회차 대본은 산문이었다. 감사에서 11건이 나왔고 그중 가장 위험한 것이
인용 정확성 위반이었다.

```text
대본     "그 선택이 실패로 끝날 것" 이라고 따옴표 직접인용
원문     "실패로 끝날 거라고 봐요"
결과     어미 변경분이 인용부호 안에 들어갔다. 사람이 읽어서 발견했다
```

산문에는 "이 문장이 어느 소스 몇 초에서 왔는지"가 없다. 대조할 대상이 없으니
검증이 사람 눈에 의존한다.

엄격한 JSON을 요구하는 것도 답이 아니다. cue 번호를 세다가 틀리고 그 오류가
대본 오류로 둔갑한다. 그래서 **산문은 그대로 두고 출처 줄 하나만** 형식을
고정한다.

```markdown
### [원본] S05 | 00:11:23~00:20:07 | cue 412-468 | 생략 414,417-419 | 간투사 | 직접
> 실패로 끝날 거라고 봐요
```

cue는 선택이다. 타임코드만 있으면 SRT에서 역산한다.

양식과 유의사항: [draft-schema.md](references/draft-schema.md)

## 단계

```text
S1  소스 패킷 생성      수집 자막 -> GPT 입력 묶음
S2  GPT 초벌 대본       script_draft_v1.md
S3  기계 검증           verify_draft.py
S4  Claude 검수         claude_review_v1.md.  지적서일 뿐 수정본이 아니다
S5  GPT/CODEX 수정      script_revised_v2.md + 변경 내역
S6  Claude 최종 확인    필요하면 S3~S5 반복. 재검수는 diff 만 읽는다
S7  사용자 승인         user_approval.json
S8  잠금                gate_script_lock.py -> master_script_locked.md
S9  111 인계            음성·시간축·SRT
```

S3에서 걸리면 S4로 가지 않는다. 양식 위반이면 `FAIL_DRAFT_FORMAT`,
내용 위반이면 `WAIT_DRAFT_VERIFICATION`.

### S6 재검수 비용 규칙

v2를 처음부터 다시 읽으면 검수 비용이 두 배다.

```text
v1   대본 전문 + 인용된 cue 창을 읽는다
v2   변경 내역 + v1 지적 목록만 읽는다. 안 건드린 문단은 읽지 않는다
```

그래서 수정본에는 **변경 내역이 필수다.** 없으면 무엇이 바뀌었는지 알 수
없어 전문을 다시 읽어야 한다.

### S8 잠금 3요건

세 증거가 전부 있고, 넷이 같은 대본을 가리킬 때만 잠금이 나온다.

```text
verification_report_v*.json   기계 검증 0건
claude_review_v*.md           verdict: APPROVED
user_approval.json            approved: true
master_script_final.md        승인 대상 대본
```

네 SHA-256이 하나가 아니면 `FAIL_STALE_REVIEW_SHA`다. 검수는 v1을 봤는데
잠금이 v2를 가리키면 아무도 읽지 않은 문장이 확정 대본이 된다.

승인서가 경로를 직접 지목한다. 파일명으로 최신본을 고르지 않는다 — 자동
선택이 있으면 승인받지 않은 `v99`를 나중에 떨어뜨려 잠금을 바꿔칠 수 있다.

**이름은 증거보다 앞서지 않는다.** 승인 대상은 `master_script_final.md`이고,
`master_script_locked.md`는 게이트만 만든다. 잠금 전부터 이름이 `locked`면
그 자체가 거짓 신호다.

작성자가 자기 작업을 잠그는 것도 여기서 막힌다. 누가 실행하든 세 증거 없이는
잠금이 나오지 않는다. 검수 사건과 승인 사건의 id를 따로 기록하고
`recorded_by == executor`면 `FAIL_SELF_APPROVAL`이다.

다만 이 출처 필드가 위조를 **불가능하게** 만들지는 못한다. 파일을 쓸 수 있는
쪽은 필드도 쓸 수 있다. 하는 일은 비용을 올리고 누가 썼는지 귀속시키는
것이고, 진짜 보증은 사용자가 실제 승인 메시지를 남기는 데서 온다.

### S1 소스 패킷

```bash
py -3.14 scripts/build_source_packet.py --episode <에피소드 경로>
```

`00_source/source_manifest.json`과 `10_analysis/transcripts/S*.srt`를 읽어
`20_script/source_packet_v1.json`을 만든다. GPT는 이것만 보고 쓴다.

자막이 없으면 `BLOCKED_TRANSCRIPT_MISSING`. 매니페스트의 cue 수와 실제 SRT
cue 수가 다르면 `BLOCKED_TRANSCRIPT_MISMATCH` — 다른 회차 자막이 섞였다는
뜻이다.

### S3 기계 검증

```bash
py -3.14 scripts/verify_draft.py --episode <에피소드 경로>
```

```text
직접인용이 SRT 원문과 일치하는가 (공백만 정규화)
참조한 source_id 가 실재하는가
참조한 cue 범위가 실제 자막 범위 안인가
나레이션에 따옴표를 쓰지 않았는가
생략마다 허용 분류를 붙였는가
의혹·주장을 확정 서술로 쓰지 않았는가
나레이션 블록 수 · 원본 클립 수가 선언과 맞는가
대본이 이 자막 묶음을 보고 쓰였는가 (패킷 지문)
```

전부 0건이어야 통과다. 하나라도 걸리면 `verification_report_v1.json`에
기록하고 종료 코드 1이다.

## 의혹 표현

정치 소재는 **주장과 사실의 구분이 곧 법적 위험**이다.

```text
수집보고서가 의혹으로 표시한 사안은 대본에서도 의혹이다
'~라는 의혹이 제기됐다' / '~라고 주장했다'   허용
'~했다' / '~로 드러났다' / '~가 밝혀졌다'    확정 서술. 근거 없으면 금지
```

`source_packet_v1.json`의 `allegation_terms`에 실린 표현은
`verify_draft.py`가 확정 서술과 같은 문장에 있는지 검사한다.

수집보고서 경고문은 대본 단계까지 그대로 이어간다. 원 보고서가 "이 보고서는
해당 주장을 사실로 확정하지 않는다"고 적었으면 대본도 확정하지 않는다.

## 산출물

```text
20_script/source_packet_v1.json          S1. GPT 입력
20_script/script_draft_v1.md             S2. GPT 산출. 초벌 정본
90_reports/verification_report_v1.json   S3. 기계 검증 결과
20_script/claude_review_v1.md            S4. 지적서. 수정본이 아니다
20_script/script_revised_v2.md           S5. 수정본 + 변경 내역
20_script/master_script_final.md         S7. 사용자 승인 대상
20_script/user_approval.json             S7. 승인. 경로와 SHA 를 직접 지목
20_script/master_script_locked.md        S8. 게이트가 만든다
20_script/script_lock.json               S8. 게이트가 만든다. 111 인계
```

## 실패 상태

```text
BLOCKED_TRANSCRIPT_MISSING
BLOCKED_TRANSCRIPT_MISMATCH
BLOCKED_SOURCE_PACKET_NOT_BUILT
FAIL_DRAFT_FORMAT
WAIT_DRAFT_VERIFICATION
WAIT_CLAUDE_REVIEW
WAIT_PROJECT_GPT_RULING
WAIT_USER_SCRIPT_APPROVAL
WAIT_SCRIPT_NOT_FINALIZED
WAIT_MACHINE_VERIFICATION
FAIL_QUOTE_FIDELITY
FAIL_SOURCE_REFERENCE_INVALID
FAIL_ALLEGATION_STATED_AS_FACT
FAIL_SKIP_NOT_CLASSIFIED
FAIL_STALE_REVIEW_SHA
FAIL_SELF_APPROVAL
FAIL_PREMATURE_LOCK_NAME
FAIL_APPROVAL_PATH_OUT_OF_SCOPE
FAIL_APPROVAL_PATH_MISSING
FAIL_EXECUTOR_EDITED_SCRIPT
```

`FAIL_EXECUTOR_EDITED_SCRIPT`는 Claude가 GPT 판정 없이 문장을 바꿨을 때다.
`script_draft_v1.md`와 `master_script_final.md`의 문장 diff가 GPT 판정
목록과 일치하지 않으면 여기 걸린다.

## 금지 산출물

CapCut draft / project / material / text track / timeline / ZIP.
하나라도 생성되면 `FAIL_CAPCUT_DEPENDENCY_DETECTED`.

음성 합성, 자막 SRT 생성, 화면 배치, 렌더는 110의 일이 아니다. 각각 111과
112가 한다. 여기서 하면 잠금 사슬이 끊긴다.

## 필수 테스트

```text
119 구현 관련 문자열·import 0건 (금지 선언문 제외)
경계 선언 3요건 실재
KEEP_UNCHANGED 절대경로 2개 실재
직접인용 불일치를 실제로 탐지하는가 (음성 픽스처)
확정 서술 위반을 실제로 탐지하는가 (음성 픽스처)
cue 범위 밖 참조를 탐지하는가 (음성 픽스처)
```
