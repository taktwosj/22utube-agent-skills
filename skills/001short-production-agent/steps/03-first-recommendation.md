# 03 1차 추천
원본 설계도에 사용자 리뷰와 원본으로 확인된 Gemini 분석만 반영한다. `references/shorts-structure-taxonomy.md`에 따라 원본 `source_structure_pattern` 하나와 대응 `remake_structure_pattern` 하나를 명시한다.

- `source_order_signature`와 `target_order_signature`를 먼저 쓴다. 훅만 붙이고 원본 본문을 그대로 두는 안은 추천하지 않는다.
- 훅은 실제 payoff/proof/reversal/result에서 고르고, 필요한 대화·인과 묶음도 같이 이동한다.
- `execution_strategy`는 원본 `delivery_mode`와 별개로 고른다. `화자발언`은 원본을 살릴지의 판단이며, `TTS`는 훅·브리지·회수 중 필요한 역할만 맡긴다.
- `SAFE_UNCHANGED_FALLBACK`과 `BLOCKED_REFERENCE`는 정직하게 표시하고 우라까이 추천으로 승격하지 않는다.
- 제안은 `와우포인트 → 미해결 질문 → 선별된 원인/증거 → 회수`의 몰입 곡선과 가단야(가·단·야) 표를 포함한다.
- `templates/urakkai-capcut-grid.md`를 복사해 `first-recommendation.md`에 `URAKKAI_CAPCUT_GRID_REQUIRED_ROWS` 우라까이표를 작성한다. 가로축은 실측 target `start–end`, 세로축은 레이어이며 모든 target 시간 칸을 근거 있는 값으로 채운다.
- 사용자 보고 메시지 본문에도 원본표 다음에 우라까이표 전체를 표시한다. 순서 서명, 파일 링크, 구조 요약만으로 대체하지 않는다. 이 규칙은 보고 형식이며 새로운 Stage 전이 validator를 추가하지 않는다.
