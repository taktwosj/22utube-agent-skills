# 03 1차 추천
원본 설계도에 사용자 리뷰와 원본으로 확인된 Gemini 분석만 반영한다. `references/shorts-structure-taxonomy.md`에 따라 원본 `source_structure_pattern` 하나와 대응 `remake_structure_pattern` 하나를 명시한다.

- `source_order_signature`와 `target_order_signature`를 먼저 쓴다. 훅만 붙이고 원본 본문을 그대로 두는 안은 추천하지 않는다.
- 훅은 실제 payoff/proof/reversal/result에서 고르고, 필요한 대화·인과 묶음도 같이 이동한다.
- `execution_strategy`는 원본 `delivery_mode`와 별개로 고른다. `화자발언`은 원본을 살릴지의 판단이며, `TTS`는 훅·브리지·회수 중 필요한 역할만 맡긴다.
- `SAFE_UNCHANGED_FALLBACK`과 `BLOCKED_REFERENCE`는 정직하게 표시하고 우라까이 추천으로 승격하지 않는다.
- 제안은 `와우포인트 → 미해결 질문 → 선별된 원인/증거 → 회수`의 몰입 곡선과 가단야(가·단·야) 표를 포함한다.
