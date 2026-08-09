# 시각 자산

사용자가 이미지·그래픽을 명시적으로 요청했을 때만 이 문서를 읽고 C 작업자 한 명이
수행한다. 요청하지 않았으면 `NOT_REQUESTED` 또는 `NOT_APPLICABLE`이며 join은 기다리지
않는다. 입력은 승인 대본과 필요한 카드 목록이다. 출력은
이 회차 `Resources`의 지원되는 이미지·그래픽뿐이다. source, narration, root, target,
CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 제작 조건

먼저 [episode-card-contract.md](episode-card-contract.md)에서 현재 builder가 요청한 card type과
정적 자산을 실제 지원하는지 확인한다. 지원되는 카드가 실제로 필요한 경우에만 자산을 만든다.
이미지 배치는 0..N개로 고정하지 않는다. 챕터 안내와 챕터 사이의 강한 강조 지점 또는
나레이션 beat 중 편집상 필요한 위치만 고른다. 지원되는 배치가 없으면 C는
`NOT_APPLICABLE`로 끝내고 join owner는 source footage와 editable text overlay로 구성한다.

intro를 명시 요청한 경우에만 근본 layout contract의 `content_start_us` 길이로 두고 오늘 볼
쟁점을 소개하는 편집 가능한 2줄 텍스트를 쓴다. C는 intro를 만들거나 요구하지 않으며 임의로
5초를 확정하지 않는다. 챕터 카드는
16:9 이미지와 editable chapter label/hook을 쓰고, 하단 30%에는 핵심 피사체와 이미지 문구를
두지 않는다. 무음 챕터 카드는 3초다.

`CHAPTER_CARD`를 선택하면 이미지는 필수다. `NARRATION_IMAGE`는 나레이션과 이미지가 모두
명시 요청된 경우에만 선택한다. 이미지를 쓰지 않는다고 새 card type이나 schema field를
만들지 않는다.

명시 요청으로 활성화된 C의 필수 자산에서만 파일 존재·형식·해시 실패가 기술 중단 사유다.
실패가 난 자산만 다시 만든다. 실제
`Resources` 파일이 재개점이며 별도 receipt나 checkpoint를 만들지 않는다.
