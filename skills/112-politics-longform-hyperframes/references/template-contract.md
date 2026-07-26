# HyperFrames 정치롱폼 템플릿 계약

## 1. 분리 경계

```text
OWNER=112-politics-longform-hyperframes
KEEP_111_CAPCUT=true
KEEP_000_CAPCUT=true
CapCut fallback=FORBIDDEN
REMOTE_URL_ALLOWED=false
```

기존 CapCut 스킬과 프로젝트를 수정하지 않는다. 기존 오세훈 HyperFrames
프로젝트는 읽기 전용 색상·비율 참고 자료이며 구조 원본이 아니다.

## 2. 필수 구조

```text
index.html
hyperframes.json
package.json
style_tokens.json
design.md
validation_report.json
test_template_contract.py
src/styles.css
src/template.js
compositions/narration-explainer.html
compositions/source-video.html
compositions/chapter-transition.html
compositions/timeline_manifest.json
assets/media/source-placeholder.mp4
assets/audio/source-placeholder.wav
```

`index.html`은 얇은 root composition이다. 디자인·content·composition logic을
분리하고 공용 frame component를 재사용한다.

## 3. Composition

| ID | 목적 |
|---|---|
| `narration-explainer` | 나레이션 설명 화면 |
| `source-video` | 원본 영상·별도 원음 화면 |
| `chapter-transition` | 챕터 전환 화면 |

ID, 표시 이름과 manifest 등록 이름을 일치시킨다. 1920x1080, 30fps를 사용하고
첫 프레임에서 주요 요소를 확인할 수 있어야 한다.

## 4. DOM

모든 composition은 공용 component를 통해 다음 역할을 독립 DOM element로 만든다.

```text
top-frame
bottom-frame
focus-lines
chapter-number
chapter-title
source-label
source-date
comment-label
subscribe-label
lower-caption-band
caption-text
```

각 요소에 composition prefix를 포함한 고유 `id`, 고유 `data-hf-id`,
`position:absolute`, `left`, `top`, `width`, `height`를 둔다. 중복 ID와 중복
`data-hf-id`는 0이어야 한다.

## 5. Style token

필수 group:

```text
canvas safeArea frame focusLines chapter source comment subscribe
captionBand captionText animation zIndex
```

필수 조절값: x, y, width, height, fontSize, letterSpacing, lineHeight,
textStroke, textGlow, backgroundOpacity, captionBandHeight, captionBandPadding,
focusLineIntensity, frameThickness, chapterTitlePosition, sourcePosition,
datePosition, commentPosition, subscribePosition.

공식 Studio editable control이 확인되지 않으면 `STUDIO_TOKEN_EDITING=TOKEN_FILE_ONLY`로
보고한다. 가짜 UI를 만들지 않는다.

## 6. 자막

```text
CAPTION_MAX_LINES=2
CAPTION_CONTAINER=lower-caption-band
CAPTION_DUMMY_TEXT_LINE_1=정치는 말보다
CAPTION_DUMMY_TEXT_LINE_2=결과로 평가받습니다
```

ellipsis, clipping, overflow 은폐를 사용하지 않는다. 자막은 남색 영역과 좌우 safe
margin 안에 완전히 표시한다. 같은 시점에는 narration 또는 source 자막 한 종류만
표시한다.

## 7. Video·audio

- `source-video` root의 직접 자식으로 muted video와 별도 audio를 둔다.
- video 기본값은 `object-fit:contain`이다.
- 세로·저해상도 영상은 crop하지 않고 letterbox 또는 로컬 배경을 사용한다.
- overlay는 video와 별도 layer로 둔다.
- narration 구간에는 narration WAV만, source 구간에는 source audio만 재생한다.

## 8. Frame·animation

top/bottom frame과 focus lines를 공용 요소로 둔다. subtle animation을 사용하되
첫 프레임을 숨기지 않는다. 과도한 zoom, shake, flash를 사용하지 않는다.

## 9. 검증

```text
contract test PASS
lint PASS
check --strict --snapshots PASS
composition 3개
required DOM 11개
duplicate id 0
duplicate data-hf-id 0
caption max 2 lines
safe area violation 0
remote media/font/CSS/JS/SVG 0
missing asset 0
preview RUNNING
preview URL verified
```

조건을 만족하면 `WAIT_USER_TEMPLATE_PREVIEW`에서 멈춘다. 사용자 승인 전 LOCK,
오세훈 전체 적용, final MP4 render, Git commit/push, runtime 배포를 하지 않는다.
