# Shorts Review Round 1 Prompt (00-tikitaka / G20)

> 외부 1차 검수용 Prompt. 사용자가 수동으로 전달하고 회수한다.
> 외부 결과는 추천 등급(PASS_RECOMMENDED / REVISE_REQUIRED / EVIDENCE_REQUIRED)으로만 응답한다.

## 검수 범위

```text
최초 설계도(원본 분석본)와 우라까이 초안
hook 점검
나레이션 자연스러움
상황 설명이 영상과 일치하는지
화자 발언 변조 여부
사건 결과 변조 여부
중복 표현·AI식 결론
```

## 검수 제외 (이 packet에 포함되지 않음)

```text
전체 OCR 캐시
전체 repo 규칙
CapCut JSON
final SRT (이후 gate 산출물)
```

## 출력 요청

```text
문장별로 문제가 있으면 REVISE_REQUIRED와 함께 해당 문장과 이유를 제시하시오.
근거가 부족한 주장은 EVIDENCE_REQUIRED로 표시하시오.
PASS / FINAL / ADOPTED / SCRIPT_LOCK / DESIGN_LOCK / USER_APPROVED / PRODUCTION_PASS
등의 단어로 최종 권위를 주장하지 마시오.
```
