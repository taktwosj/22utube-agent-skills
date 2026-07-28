---
name: 110-politics-longform-script
description: "Use when the user says 정치롱폼, 정치미드폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, 110대본, 정치롱폼 대본, 초벌 대본, 대본 초안, 최근 정치이슈 검색, 승인 채널 검색, or asks to discover approved political sources or turn collected political videos and subtitles into a narration script. Entry point of the politics longform pipeline: 110 source discovery and script, then 111 voice and SRT, then 112 HyperFrames."
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
내부 2차 집필 프롬프트: [Retention Story Editor](references/retention-story-editor.md)
시사·정치 초벌 구조와 문체: [Political News Writing Framework](references/political-news-writing-framework.md)

## 승인 채널 소스 탐색

자동 정치이슈·영상 탐색을 시작하기 전에 반드시
[Approved Channel Allowlist](references/approved-channel-allowlist.json)를 읽고
그 목록만 사용한다. 운영 원본은 JSON의 `authority.url`에 기록된 Trend Hunter
`midform` 화면이며, JSON은 재현 가능한 실행을 위한 검증 스냅샷이다.

```text
CHANNEL_MATCH_PRIORITY = channel_id > handle > url > canonical_name
BLOCK_PRECEDES_ALLOW = true
AUTHORITY_UNAVAILABLE = WAIT_CHANNEL_AUTHORITY_UNAVAILABLE
AUTHORITY_SNAPSHOT_MISMATCH = WAIT_CHANNEL_ALLOWLIST_DRIFT
TREND_HUNTER_COLLECTION = EXTERNAL_AUTO_UPDATE
TRIGGER_SITE_COLLECTION = FORBIDDEN
STALE_SITE_SYNC = WAIT_TREND_HUNTER_SYNC_STALE
OUTSIDE_ALLOWLIST = WAIT_CHANNEL_NOT_ALLOWLISTED
MISSING_TRANSCRIPT = WAIT_SOURCE_ASR
ALLOWLIST_IS_NOT_RIGHTS_PASS = true
```

- Trend Hunter가 자동 업데이트한 `midform` 저장 결과를 읽기 전용으로 사용하고,
  `allowed_channels` 24개로 제한한다. 110이나 Paperclip이 `기간 영상 수집 실행`을
  누르거나 YouTube API 수집을 중복 실행하지 않는다.
- 코드 조회는 아래 전용 클라이언트만 사용한다. 이 요청은 HMAC 인증된 `GET`만
  보내며 수집·저장 action을 전송하지 않는다. 자격 파일은 기본적으로
  `~/.trend_hunter/midform_read_api.json`에서 읽고 출력물에는 비밀값을 기록하지 않는다.

```bash
python scripts/trend_hunter_read.py \
  --query "김민석" \
  --require-sync-date YYYY-MM-DD \
  --output <episode>/10_analysis/trend_hunter_snapshot.json
```

  자격 파일이 없으면 자동 생성하거나 임의 토큰을 사용하지 말고
  `WAIT_TREND_HUNTER_READ_CONFIG`로 멈춘다. 서버와 작업자에 동일한 자격 파일을
  설치하는 1회 부트스트랩은 사용자의 명시적 승인 범위에서만 수행한다.
- 가장 최근 `미드롱폼` 동기화가 완료 상태이고 `24/24`, 실패 `0`인지 확인한다.
  아직 오늘 동기화가 끝나지 않았거나 이전 보고 이후 새 완료 기록이 없으면 오래된
  자료로 보고하지 말고 `WAIT_TREND_HUNTER_SYNC_STALE`로 둔다.
- 실행 전 운영 화면의 채널 목록과 JSON 스냅샷을 대조한다. 운영 화면에 접근할 수
  없으면 `WAIT_CHANNEL_AUTHORITY_UNAVAILABLE`, 수량·ID·핸들·URL이 달라졌으면
  자동 갱신하지 말고 `WAIT_CHANNEL_ALLOWLIST_DRIFT`로 멈춘다.
- `blocked_channels`와 일치하면 다른 허용 조건보다 먼저 제외한다.
- 승인 목록 밖 결과는 자료에 섞지 말고 `WAIT_CHANNEL_NOT_ALLOWLISTED`로 보고한다.
- 사용자가 특정 URL을 직접 지정한 경우에만 명시적 예외 검토를 진행한다.
- 채널 승인과 영상별 사실성·저작권·공정이용 판단을 분리한다.
- 자막이 없으면 문장을 추정하지 말고 `WAIT_SOURCE_ASR`로 보고한다.
- 자동 수집은 후보 보고서까지만 수행한다. 사용자 주제·영상 승인 전에는 S2 대본,
  음성, HyperFrames, 업로드로 진행하지 않는다.

## 단계

```text
S0  승인 채널 소스 탐색  최근 이슈·영상주소·자막 후보 보고
S1  소스 패킷 생성      수집 자막 -> GPT 입력 묶음
S2  GPT 초벌 대본       script_draft_v1.md
S2R Retention Story Rewrite
                         PROJECT_GPT/Hermes 내부 작가 패스. 전체 대본 재구성
S3  기계 검증           verify_draft.py
S4  Claude 최초 전체 검수
                         claude_review_v1.md. 읽기 전용 지적서
S5  GPT/CODEX 수정      script_revised_v2.md + 변경 내역
S6  Claude diff 검수    필수 조건에 해당할 때 변경분과 지적 반영을 확인
S7  사용자 승인         user_approval.json
S8  잠금                gate_script_lock.py -> master_script_locked.md
S9  111 인계            음성·시간축·SRT
```

### S2R Retention Story Rewrite

S2R은 PROJECT_GPT/Hermes 내부 작가 패스다. 새 운영 시스템이 아니며
새 승인 단계가 아니다. 별도 상태 파일이나 receipt를 만들지 않는다. 초벌을 부분 교정하는
단계가 아니라 후킹, 정보 공개 순서, 챕터별 보상, 원본·나레이션 배치와
지속시청 구조를 기준으로 전체 대본을 재구성하는 2차 집필이다.

다음 조건이 전부 참일 때만 실행한다.

- 초벌 대본이 존재한다.
- 현재 source packet이 존재한다.
- 초벌 frontmatter의 `source_packet_sha256`과 실제 packet SHA가 일치한다.
- 사용자 승인 전 대본이다.
- 요청이 맞춤법·띄어쓰기·줄바꿈만 고치는 작업이 아니다.

초벌 binding이 없거나 현재 packet SHA와 다르면 `WAIT_SOURCE_BINDING`으로
멈춘다. 핵심 논지를 바꾸거나 source packet에 없는 새 사실이 필요하면 직접
추가하지 말고 `WAIT_PROJECT_GPT_RULING`으로 복귀한다.

S2R은 [Retention Story Editor](references/retention-story-editor.md)의 명령과
현재 [draft-schema.md](references/draft-schema.md)를 그대로 사용한다. 새
대본 schema를 만들지 않는다. S2R의 전체 수정 대본만
`20_script/script_draft_v1.md`에 쓰고, 변경 내역과 blocker는 실행 보고에만
둔다. 대본 파일은 `---`로 시작하며 보고 섹션을 포함하지 않는다. S2R 뒤에는
이 파일을 대상으로 S3 기계 검증을 진행한다. S3가 실패하면 Claude 검수로
진행하지 않는다.

10~20분 시사·뉴스형 정치롱폼이나 정치인 인물 서사는 S2R 전에 반드시
[Political News Writing Framework](references/political-news-writing-framework.md)를
읽고 구조와 문체를 적용한다. 구조 이름과 제작·검수 언어는 완성 대본에
노출하지 않는다.

S3에서 걸리면 S4로 가지 않는다. 양식 위반이면 `FAIL_DRAFT_FORMAT`,
내용 위반이면 `WAIT_DRAFT_VERIFICATION`.

### S4 최초 전체 검수

S4 최초 Claude 전체 검수는 필수다. Claude는 읽기 전용 검수자이며 대본
전문과 인용된 cue 창을 읽는다. Claude는 지적서만 작성하고 대본을 수정하지 않는다.
논지, 문장, 인용, 챕터 순서의 수정은 PROJECT_GPT/Hermes 작가
권한으로 돌려보낸다.

### S6 재검수 비용 규칙

S6은 S4 이후의 diff 검수다. S4의 최초 전체 검수를 대신하지 않는다.

S6 필수 조건:

- S4 verdict가 `APPROVED`가 아닌 경우
- S4 이후 대본 파일 SHA가 변경된 경우
- Claude 중요 지적을 반영한 경우
- 논지·챕터·직접인용·source 구간이 변경된 경우
- 사용자가 재검수를 요청한 경우

S6 생략 가능 조건은 다음 두 조건을 모두 만족할 때뿐이다.

- S4 verdict가 `APPROVED`
- S4 이후 대본 바이트 변경이 0

S6에서는 변경 내역과 S4 지적 목록을 우선 읽고, 바뀐 문맥을 이해하는 데
필요한 범위까지 확인한다. 수정본에는 변경 내역이 필수다. 없으면 무엇이
바뀌었는지 알 수 없어 전문을 다시 읽어야 한다.

S4 승인 대본을 `master_script_final.md`로 승격할 때는 byte-identical copy를
사용한다. 복사 중 BOM, 개행, 공백, frontmatter 직렬화 등으로 SHA가 달라지면
의미 변경 의도가 없더라도 S3 기계 검증과 S6를 다시 실행한다. 승인 상태를
새로 만들지 않고 기존 `master_script_final.md`, `user_approval.json`,
`master_script_locked.md`, `script_lock.json` 계약을 유지한다.

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

두 종류의 SHA를 혼동하지 않는다.

- `user_approval.json`의 `claude_review_sha256`은 Claude 검수 문서 파일
  자체의 SHA다.
- Claude 검수 문서 내부 `script_sha256`은 Claude가 실제 검수한 대본의
  SHA다.

S6 검수 문서 내부 `script_sha256`은 최종 대본 SHA와 일치해야 한다.
`user_approval.json`은 별도로 최종 Claude 검수 문서 파일의 경로와 SHA를
고정한다.

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

`quote_fidelity`는 source packet에 기록된 텍스트만 비교한다. 실제 영상
발화와 SRT의 일치, 음성 검증 완료, source truth 검증 완료를 뜻하지 않는다.
ASR 손상이 의심되면 추정 교정하지 말고 Retention Story Editor의 ASR 경계를
따른다.

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
20_script/script_draft_v1.md             S2/S2R. GPT 산출. 보고 섹션 없는 초벌 정본
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
WAIT_TREND_HUNTER_SYNC_STALE
WAIT_CHANNEL_AUTHORITY_UNAVAILABLE
WAIT_CHANNEL_ALLOWLIST_DRIFT
WAIT_CHANNEL_NOT_ALLOWLISTED
WAIT_SOURCE_ASR
BLOCKED_TRANSCRIPT_MISSING
BLOCKED_TRANSCRIPT_MISMATCH
BLOCKED_SOURCE_PACKET_NOT_BUILT
FAIL_DRAFT_FORMAT
WAIT_DRAFT_VERIFICATION
WAIT_CLAUDE_REVIEW
WAIT_PROJECT_GPT_RULING
WAIT_SOURCE_BINDING
WAIT_SOURCE_ASR_REVIEW
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
