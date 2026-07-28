# 군림보 Wrong-Lane 및 Image2 복구 규칙

## 적용 신호

운영자가 `군림보`, `블랙 TOP5`, `블랙 템플릿`, `TOP55`, `정보있슈` 중 하나를 제작 프로필 의미로 말하면 일반 0shrt나 `shrt white`가 아니라 `top5isu-shorts`의 `style_profile=gunlimbo`로 고정한다.

## 시작 전 라우팅 체크

다음 값을 에피소드 상태에 먼저 기록한다.

```text
skill=top5isu-shorts
style_profile=gunlimbo
template_profile=top5isu_v2_top55
fallback_allowed=false
```

하나라도 다르거나 기존 프로젝트가 `shrt white`를 기반으로 하면 조립·렌더를 시작하지 않는다.

## 잘못된 lane을 발견했을 때

1. 기존 REVIEW·CapCut 프로젝트를 `REJECTED_WRONG_PROFILE`로 표시하고 FINAL·업로드 대상으로 사용하지 않는다.
2. 군림보 전용 새 버전 에피소드를 생성한다. 이전 프로젝트를 블랙처럼 보이게 덧칠하거나 구조만 부분 전환하지 않는다.
3. 사실검증 대본과 승인 음성은 내용·해시가 그대로라면 이전할 수 있지만, 시각 자산·템플릿·CapCut 조립은 TOP55 계약으로 다시 만든다.
4. 의미 있는 원본 화자가 없으면 `source_speaker_mode=no_meaningful_source_speech`, `source_dialogue_analysis_status=NO_DIALOGUE`, `speaker_segments=[]`를 명시한다.

## 실제 GPT Image2 게이트

운영자가 GPT 이미지를 요구한 경우 다음만 최종 이미지로 센다.

- 일반 ChatGPT 새 채팅에서 Image2/CDP로 생성·다운로드된 실제 PNG
- 원본 PNG의 크기·바이트·SHA-256이 확인된 파일
- TOP55 창에 맞춰 결정론적으로 crop/resize한 파생본과 manifest

원본 영상 크롭, 기사 스크린샷, PIL/HTML/SVG 정보카드, 로컬 도형 이미지는 진단·참고일 뿐 GPT 이미지 수에 포함하지 않는다. 이런 자산만 있는 상태에서 `GPT 이미지 완료`라고 보고하면 안 된다.

## 샘플 게이트

1. 새 **일반** ChatGPT 대화에서 한 장만 생성한다. 임시 채팅 URL은 이미지 도구가 비활성일 수 있으므로 사용하지 않는다.
2. 실제 PNG가 생겼는지 세고, TOP55 투명창 `966×794`에 넣은 프레임핏 미리보기를 만든다.
3. 레터박스, 검은 내부 여백, 사진풍/웹툰풍 불일치, 문자·로고, 인물·손 왜곡, 중앙 안전구도를 검사한다.
4. 운영자에게 원본 PNG와 블랙 프레임 미리보기를 각각 전달한다.
5. 운영자 승인 뒤에만 나머지 장면을 배치 생성한다.

프롬프트에 `black-frame`만 쓰면 모델이 이미지 내부에 검은 매트나 영화식 레터박스를 그릴 수 있다. 다음 요구를 명시한다.

```text
full-bleed to all four edges
no border, no black matte, no letterbox, no cinematic bars
clearly illustrated webtoon, not a photograph and not photorealistic
```
