# Codex FAST 실행 규약 — TOP5·군림보 쇼츠

## 적용 범위

이 reference는 `top5isu-shorts` 제작 중 Codex에게 다음 작업을 위임할 때만 읽는다.

- FFmpeg·TTS·CDP·CapCut 빌더 코드 수정
- validator·manifest·상태기계 수정 또는 읽기 전용 검수
- 재현 가능한 버그 수정과 회귀 테스트
- 대량 파일 구조·경로·draft JSON 검수

Image2 생성 대기, CapCut GUI 클릭, 클라우드 업로드, 시각·음성 최종 판단에는 이 규약을 적용하지 않는다.

역할은 `Codex=실행·수정·자체 테스트`, `Hermes=범위 지정·실환경 재검증·최종 보고`로 고정한다. Claude 검수 단계를 추가하지 않는다.

## 반드시 먼저 전달할 원문

Codex 지시서보다 아래 JSON을 **원문 그대로 먼저** 전달한다. 의역하지 않는다.

```json
{
  "execution_style": "FAST_PROVE_FIX_TEST_CONTINUE",
  "rules": [
    "계획을 반복하지 않고 실제 파일부터 확인한다.",
    "추정으로 문제를 설명하지 않고 재현 테스트로 먼저 증명한다.",
    "한 번에 현재 최우선 위험 하나만 수정한다.",
    "수정 직후 관련 테스트를 실행한다.",
    "테스트가 통과하면 사용자에게 다시 묻지 않고 승인 범위의 다음 작업으로 진행한다.",
    "이미 완료된 단계와 전체 프로젝트를 다시 조사하지 않는다.",
    "진행 보고는 실제 단계 완료 또는 blocker 발생 시에만 한다.",
    "긴 내부 사고과정을 사용자에게 출력하지 않는다."
  ],
  "stop_conditions": [
    "같은 근본 원인 수정 2회 실패",
    "Source of Truth 충돌",
    "승인 범위 밖 구조 변경 필요",
    "삭제·push·merge·게시 같은 외부 영향 작업"
  ]
}
```

## 고정 dispatch 절차

1. 작업 cwd 루트에 UTF-8 `PROMPT.md`를 쓴다.
2. 내용 순서는 `위 JSON 원문 → 작업 지시 → 승인 파일 목록 → 금지 목록 → 테스트 → 보고 형식`이다.
3. 명령행에는 한글 지시를 직접 넣지 않고 ASCII 한 줄만 전달한다.
4. 각 잡은 반드시 의도한 cwd에서 별도 명령으로 실행한다. 여러 cwd 작업을 같은 셸 dispatch로 묶지 않는다.
5. dispatch 직후 `workspaceRoot`와 `write`를 확인한다.

Windows Codex Companion 예시:

```bash
cd <작업디렉터리> && node "<USER_HOME>/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs" task --background --write "Read PROMPT.md at the workspace root and execute it. Report exactly the items its report section asks for."
```

- 쓰기 작업: 승인 파일을 명시하고 `--write` 사용
- 읽기 전용 검수: `--write` 제거
- `cwd`가 곧 sandbox root다.
- 상태 확인: `node ...codex-companion.mjs status --all`
- 필요 시 job JSON의 `workspaceRoot`와 `write`를 직접 확인한다.

## 검수 PROMPT 추가 조항

```text
산출물 0건은 실패다. 어느 항목이 깨끗하면 'X NO_FINDINGS'라고 명시하라.
출력 형식: SEVERITY | file:line | 실제로 뚫는 입력 | 왜 문제인가
이미 알고 고칠 예정인 파일은 범위에서 빼고 그렇다고 명시하라.
```

## 결과 판정

- Codex 결과는 self-report다. Hermes가 실제 파일·diff·테스트를 다시 확인한다.
- Codex sandbox의 writable temp 부재로 테스트가 대량 ERROR일 수 있다. 코드 결함으로 단정하지 말고 Hermes 실환경 실행과 대조한다.
- `BLOCKED_CROSS_ROOT_SANDBOX`는 코드 실패가 아니라 cwd/workspaceRoot dispatch 실패다.
- stop condition 발생 시 Codex는 멈추고 증거만 보고하며, Hermes가 다음 조치를 결정한다.
