# Politics Review Round 1 Prompt (111-politics-longform / G20)

> 외부 1차 검수용 Prompt. 사용자가 수동으로 전달·회수한다.
> 외부 결과는 추천 등급으로만 응답한다.

## 검수 범위

```text
politics_narration_framework.md의 작성된 나레이션
챕터 구조 적절성
원문 인용 정확도
사실·발언자 해석·제작자 판단의 구분
논리 연결
이름·기관 오타
자동자막 오류 표시
법률·명예훼손 민감 주장
```

## 검수 제외 (이 packet에 포함되지 않음)

```text
전체 자동자막 전문
repo 규칙
CapCut JSON
final SRT (이후 gate 산출물)
```

## 출력 요청

```text
문장별로 문제가 있으면 REVISE_REQUIRED와 함께 해당 문장과 이유를 제시하시오.
근거가 부족한 주장은 EVIDENCE_REQUIRED로 표시하시오.
새로운 고위험 주장(명예훼손·법률 민감)이 발견되면 반드시 표시하시오.
PASS / FINAL / ADOPTED / SCRIPT_LOCK / DESIGN_LOCK / USER_APPROVED / PRODUCTION_PASS
등의 단어로 최종 권위를 주장하지 마시오.
```
