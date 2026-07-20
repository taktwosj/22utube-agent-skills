# Politics Review Round 2 Prompt (111-politics-longform / G20)

> Round 2는 Round 1과 **같은 external review conversation**에서 이어진다.

## Round 2에만 전달되는 항목 (delta policy)

```text
Round 1 문제 목록
Codex 결정표 (ADOPTED / PARTIALLY_ADOPTED / REJECTED / PENDING_EVIDENCE)
변경된 문장
변하지 않은 영역의 SHA
남은 근거 문제
현재 완성 원고
```

## 포함하지 않는 항목

```text
전체 자동자막
repo 규칙
CapCut JSON
과거 packet 전체
```

## same-conversation 규칙

```text
Round 2는 Round 1과 같은 external review conversation에서 이어진다.
receipt metadata에 conversation 참조가 기록된다.
같은 대화가 아닌 경우 SAME_CONVERSATION_REQUIRED 로 거부한다.
```

## 출력 요청

```text
Round 1 결정이 적절히 반영되었는지 확인하시오.
남은 근거 문제가 해결되었는지 확인하시오.
최종 추천 등급(PASS_RECOMMENDED / REVISE_REQUIRED / EVIDENCE_REQUIRED)을 제시하시오.
PASS / FINAL / ADOPTED / DESIGN_LOCK / USER_APPROVED / PRODUCTION_PASS 로
최종 권위를 주장하지 마시오.
```
