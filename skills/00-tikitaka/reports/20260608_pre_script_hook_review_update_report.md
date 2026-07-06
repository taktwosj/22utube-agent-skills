# 00-tikitaka Pre-Script Hook Review Update Report

## 결론

`00-tikitaka`에 최종 대본 전 보조 검토 게이트를 추가했다.

이번 수정의 핵심은 하단 첫마디 후보가 단어 조각으로 나오지 않게 하고, 각 후킹 후보마다 `계속 봐야 하는 이유`를 강제로 쓰게 하는 것이다.

## 수정 범위

- source skill: `$HOME/agent-skills/skills/00-tikitaka/SKILL.md`
- reference: `$HOME/agent-skills/skills/00-tikitaka/references/pre_script_hook_review.md`
- runtime install: `$HOME/agent-skills/scripts/install.*`
- report: `$HOME/agent-skills/skills/00-tikitaka/reports/20260608_pre_script_hook_review_update_report.md`

## 추가된 규칙

`Pre-Script Hook Review Gate`를 추가했다.

최종 대본 또는 `하단 첫마디 후보 5개` 전에 반드시 아래 5개를 출력한다.

```text
1. 3초 킬러 포인트
2. 후킹 유형 4종 후보
3. 숨김 도발 검토
4. 댓글/반응 교차 확인
5. 오디오오프 이해 보강
```

## 후킹 후보 강화

후킹 유형 4종 후보는 아래를 모두 포함해야 한다.

```text
- 충격형:
  - 계속 봐야 하는 이유:
- 숫자/시간형:
  - 계속 봐야 하는 이유:
- 정체 숨김형:
  - 계속 봐야 하는 이유:
- 리액션형:
  - 계속 봐야 하는 이유:
```

`계속 봐야 하는 이유`가 구체적이지 않으면 후보를 다시 쓰도록 했다.

## 하단 첫마디 후보 규칙 강화

`Bottom First-Line Rule`에 다음을 추가했다.

- 후보 5개는 완성 문장이어야 한다.
- 이름, 물건, 상황 일부만 던지는 조각 문장은 금지한다.
- 각 후보 아래에 `계속 봐야 하는 이유`를 붙인다.
- 댓글형 쇼츠는 댓글을 사실로 쓰지 말고 `시청자 과몰입 반응`으로만 처리한다.

나쁜 예로 아래를 명시했다.

```text
비욘세 눈빛이
엘런이 다가오자
이 장면 댓글창이
```

좋은 예로 아래를 추가했다.

```text
이 장면이 웃긴 이유는 영상보다 댓글이 더 과몰입했기 때문입니다
비욘세는 한마디도 안 했는데, 댓글창은 이미 눈빛 해석을 끝냈습니다
```

## 댓글/루머 안전장치

댓글은 시청자 반응으로만 사용한다.

금지:

- 루머 댓글을 사실화
- 음모론/범죄/성적 조롱/명예훼손성 댓글을 대본 사실로 사용
- 영상에 없는 해석을 사건처럼 설명

허용:

- `댓글창이 과몰입했다`
- `시청자들이 눈빛을 해석했다`
- `영상보다 댓글 반응이 커졌다`

## 백업

수정 전 백업:

```text
Pre-Git OneDrive backup paths were retired during the agent-skills Git migration.
Use Git history and runtime target backups for rollback.
```

## 로컬 동기화 결과

현재 Windows 로컬 런타임에는 `skil-down`으로 `00-tikitaka`만 선택 동기화했다.

```text
SYNCED 00-tikitaka
DONE synced=00-tikitaka
```

로컬 런타임 백업 패턴:

```text
%USERPROFILE%/.codex/skills_backups/00-tikitaka_<timestamp>
```

## 검증 결과

확인한 항목:

```text
1. source `00-tikitaka/SKILL.md`에 `Pre-Script Hook Review Gate` 존재
2. local `00-tikitaka/SKILL.md`에 `Pre-Script Hook Review Gate` 존재
3. source/local `SKILL.md` SHA256 일치
4. source/local `references/pre_script_hook_review.md` SHA256 일치
5. runtime install guide 존재
6. report 존재
7. UTF-8 mojibake 검사 통과
```

SHA256:

```text
00-tikitaka/SKILL.md
D396ED3A87CCADE8DC4945A881E0DD71EC3872FCE96B5820E20A530F1A6D2C96

00-tikitaka/references/pre_script_hook_review.md
EE8477DE86478D40BCB15ADC471049D61FB3DA69E6615578313E50F2E1842877
```

## 주의

현재 채팅 컨텍스트는 이미 시작된 런타임이므로, 스킬 목록과 본문 적용은 새 채팅 또는 Codex 재시작 후 안정적으로 반영된다.
