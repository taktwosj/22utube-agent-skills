# 카드 모드: 비트 구조·작업지시문·척추 단계 — 상세

> 원문: `hyperframes-politics-119/SKILL.md` 에서 줄 단위로 옮김. 내용 수정 없음.

## 비트 구조

```text
비트 1개 = 나레이션 1줄 = wav 1개
span     = ceil(voice_duration * 30) / 30   프레임 정수
오디오   <audio data-start data-duration data-track-index="10" data-volume="1">
전환     tl.set(opacity 1) at start → 요소별 fromTo → tl.set(opacity 0) at start+span
```

119 조립은 그룹 안 비트 오프셋을 누적해 카드를 자른다. span 이 프레임 정수가 아니면 어긋난다.

## 작업지시문

새 회차에서 이 스킬을 쓸 때 그대로 복사해 쓴다.

```text
회차: <episode_id>
루트: <LOCAL_PRODUCTION_ROOT>/119jungchi/<episode_id>

hyperframes-politics-119 문법으로 설명 카드를 만든다.

1. narration/<ver>/timing.json 의 그룹별로 프로젝트를 하나씩 만든다.
   비트 1개 = 나레이션 1줄 = wav 1개. span = ceil(voice_duration*30)/30.
2. 챕터마다 시각 문법을 다르게 고른다. 스킬의 10종 목록에서 고르거나 새로 만든다.
   같은 문법을 두 챕터에 쓰지 않는다. 어떤 문법을 왜 골랐는지 한 줄로 적는다.
3. 크롬 네 모서리(브랜드 / NN·챕터명 / 출처 : 채널명 / NN·총개수)를 모든 카드에 넣는다.
4. 확인 안 된 주장은 챕터 라벨과 아이브로우에 발화자를 박는다.
   마무리 카드는 정산 원장으로 만들고 행마다 상태 칩을 붙인다.
5. 민주 블루 인셋 카드 템플릿을 쓰지 않는다. 정지 이미지 카드로 대체하지 않는다.
6. check --strict --snapshots 와 render 를 돌려 exit 0 을 확인하고,
   스냅샷을 눈으로 본 뒤 logs/*.exit 를 증거로 남긴다.

산출물: hyperframes_<ver>/<project>/renders/final.mp4 + design_manifest.json
```

## 척추 단계에서 미리 잡는다

`spine-script-119` 의 `plan_hyperframes.py` 로 장면표를 뽑을 때 이 문법으로 잡는다.
나레이션 원고를 쓰기 전에 챕터별 시각 문법을 먼저 배정해 두면, 원고가 그 문법에 맞는
길이와 대비 구조로 나온다. 원고를 다 쓴 뒤에 문법을 고르면 카드가 원고를 따라가기만 한다.

장면표에 챕터마다 적을 것: 시각 문법 번호, 비트 수, 대비축(무엇 대 무엇), 주장 라벨 필요 여부.

