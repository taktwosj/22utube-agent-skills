# 시각 자산

대본 승인 뒤 C 작업자 한 명이 수행한다. 입력은 승인 대본과 필요한 카드 목록이다. 출력은
이 회차 `Resources`의 지원되는 이미지·그래픽뿐이다. source, narration, root, target,
CapCut draft, `episode_cards.json`을 수정하지 않는다.

## 제작 조건

먼저 [episode-card-contract.md](episode-card-contract.md)에서 현재 builder가 요청한 card type과
정적 자산을 실제 지원하는지 확인한다. 지원되는 카드가 실제로 필요한 경우에만 자산을 만든다.
지원하지 않으면 이미지를 생성하거나 다운로드하지 않고 영상·나레이션 카드로 구성하도록
join owner에게 알린다.

인트로는 5초이며 오늘 볼 쟁점을 소개하는 편집 가능한 2줄 텍스트만 둔다. 챕터 카드는
16:9 이미지와 editable chapter label/hook을 쓰고, 하단 30%에는 핵심 피사체와 이미지 문구를
두지 않는다. 무음 챕터 카드는 3초다.

필수 자산의 파일 존재·형식·해시 검사에서 구체적 실패가 난 자산만 다시 만든다. 실제
`Resources` 파일이 재개점이며 별도 receipt나 checkpoint를 만들지 않는다.
