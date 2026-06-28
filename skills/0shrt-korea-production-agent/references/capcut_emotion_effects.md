# CapCut Emotion Effects Reference

## Feasibility in the current 0shrt pipeline

Confirmed stable through local CapCut JSON:

- Zoom in/out: `KFTypeScaleX`, `KFTypeScaleY`
- Pan / screen shake: `KFTypePositionX`, `KFTypePositionY`
- 45-degree tilt / rotation: `clip.rotation` and `KFTypeRotation`
- Opacity flash / blink: `clip.alpha` or white overlay asset
- Text emphasis: text tracks, stroke, shadow, position, scale, rotation
- Bottom captions: `auto_captions` text track, max 2 lines
- Stickers/overlays: possible when copied from an existing free sample draft
- Transitions/effects/filters: use only sample-copy from an existing free CapCut sample draft

Recommended stable route:

```text
Motion/rotation/shake → native CapCut JSON keyframes
Flash/vignette/halftone/speed lines/aura/stamp/card → generated overlay PNG/MP4 track
Grayscale/color wash → preprocessed duplicate image/video asset, unless a verified CapCut filter sample exists
Page turn/transition → sample-copy from a free CapCut transition draft
```

Do not invent CapCut `materials.effects`, filter, transition, or adjustment structures from memory. CapCut versions differ; copy known free sample structures only.

## Local emotion asset pack

Default reusable overlay/SFX pack:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack
```

Regenerate with:

```powershell
py -3 "${env:UTUBE_ROOT}\0shrt\production\generate_emotion_pack.py"
```

If OneDrive online-only files stall or CapCut cannot read the overlay media, cache the pack locally and use that cache as the media source:

```powershell
$env:UTUBE_ROOT = "$env:UTUBE_ROOT"
py -3 "${env:UTUBE_ROOT}\0shrt\production\cache_emotion_pack.py"
```

Current files:

```text
emotion_symbol_presets_40.md
stamp_result_presets.md
text_effect_presets.md
text_effect_presets.json
visual/01_VIS_비오는오버레이.mp4
visual/02_VIS_번개플래시.mp4
visual/02B_VIS_노란버스트집중선.mp4
visual/03_VIS_바람휘리릭.mov
visual/03B_VIS_바람휘리릭_검은배경.mp4
visual/04_VIS_먹구름.mp4
visual/05_VIS_붉은도장_파직.png
visual/06_VIS_붉은도장_상속제외.png
visual/stamps/modern/*.png
visual/stamps/modern_top15/*.png
visual/stamps/joseon/*.png
visual/stamps/joseon_top5/*.png
sfx/01_SFX_빗소리.mp3
sfx/02_SFX_바람휘리릭.mp3
sfx/03_SFX_천둥쾅.mp3
sfx/04_SFX_충격음_boom.mp3
sfx/05_SFX_도장_stamp.mp3
sfx/06_SFX_사이다_chime.mp3
```

Use MP4 overlays with Screen/Lighten or 20-40% opacity. Use the wind MOV as an alpha overlay; if CapCut alpha import fails, use `03B_VIS_바람휘리릭_검은배경.mp4` with Screen/Lighten. For comic-style evidence reveal, prefer `02B_VIS_노란버스트집중선.mp4` over plain white lightning.

Reusable effect bank:

```text
${env:UTUBE_ROOT}\0shrt\assets\effect_bank
```

Use the effect bank as a CapCut toolbox, not as one-off episode art:

```text
background image/video changes every episode
effect layers are reused
only text, timing, and position change
```

Core exports:

```text
video/fire/BANK_FIRE_OVERLAY_BLACK.mp4 -> Screen/Lighten
video/fire/BANK_FIRE_TEXT_SAMPLE_MUSCLE_PAIN_BLACK.mp4 -> Screen/Lighten sample fixed text
video/laugh/BANK_LAUGH_RING_KKK_GREEN.mp4 -> Chroma Key #00FF00
video/laugh/BANK_LAUGH_POP_KKK_GREEN.mp4 -> Chroma Key #00FF00
video/text/BANK_TEXT_POP_TIRED_GREEN.mp4 -> Chroma Key #00FF00
```

Keep editable CapCut bank drafts separately as `_EFFECT_BANK_역사춘` or `_EFFECT_BANK_0쇼츠공용` when the text will be reused with different wording.

For human emotion/status symbols, read:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack\emotion_symbol_presets_40.md
```

These presets are not static stickers. Each one must be implemented with an entrance motion, impact motion, and exit motion.

For stamp/result overlays, read:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack\stamp_result_presets.md
```

Stamp text must be a result/verdict, not an emotion label. Animate stamps as `150% → 95% → 105% → 100%` over 0.15s and sync with `sfx/05_SFX_도장_stamp.mp3`.

For impact text presets such as fire text, pink neon, or repeated laugh text, read:

```text
${env:UTUBE_ROOT}\0shrt\assets\emotion_pack\text_effect_presets.md
```

Use these preset names when planning or building CapCut text impact overlays:

```text
TXT_FIRE_레전드
TXT_FIRE_분노폭발
TXT_NEON_샤갈
TXT_NEON_핑크대사
TXT_CUTE_반짝
TXT_POP_하하하증식
TXT_POP_조롱폭발
TXT_COMIC_말풍선웃음
```

0shrt/history override:

```text
TXT_FIRE_레전드: 왕의 분노, 사약, 파직, 공개 응징
TXT_FIRE_분노폭발: 강한 클라이맥스에 한 번만 사용
TXT_POP_하하하증식: 신하 조롱, 궁녀 수군거림, 공개 망신
TXT_NEON_샤갈/TXT_NEON_핑크대사: 기본 비추천. 사용자가 코믹 현대식 톤을 요구할 때만 사용
```

Text impact overlays do not replace body captions. Keep bottom captions bottom-only, max two lines, and do not add purple middle overlays to this 0shrt profile.

## 감정선 효과 규칙

조선시대 쇼츠와 현대 막장 사이다 쇼츠는 동일한 감정 구조를 사용한다.
차이는 소품과 시대 배경뿐이다.

기본 감정선:

```text
평온 → 불쾌감 → 모욕 → 억울함 → 분노 축적 → 반전 예고 → 증거/권한 공개 → 빌런 충격 → 응징 → 사이다 → 교훈 → 댓글 유도
```

각 감정에는 고정 효과를 배치한다.

평온:
부드러운 줌인, 일반 자막, 약한 필름그레인

불쾌감:
비네팅, 하프톤 도트, 빨간 키워드 강조

모욕:
뾰족 말풍선, 분노 마크, 글자 흔들림, 쾅 효과음

억울함:
파란 톤, 먹칠 배경, 느린 줌아웃, 짧은 정적

분노 축적:
눈 클로즈업, 검은 그림자 얼굴, 심장박동음, 붉은 오라

반전 예고:
검은 반전 카드, 음악 컷, 페이지 넘김

증거/권한 공개:
서류 클로즈업 3연타, 번개 플래시, 철컥 효과음, 집중선

빌런 충격:
파란 얼음 배경, 땀방울, 동공 흔들림, 말더듬 자막

응징:
붉은 도장, 검은 대사 카드, 슬래시 컷, 쾅 효과음

사이다:
금색 빛, 밝아지는 색감, 짧은 박수, 따뜻한 BGM 상승

교훈:
검은 배경, 흰 글자, 금색 포인트, 마지막 단어 확대

댓글 유도:
좌우 분할 투표 카드, 사이다다 vs 너무했다 구조

주의:

```text
효과는 감정 전환점에만 사용한다.
한 장면에 2개 이상의 강한 효과를 겹치지 않는다.
참교육은 폭력이 아니라 증거, 권한, 계약, 기록, 관계 단절, 공식 처분으로 처리한다.
```

## Production preset names

```text
EMO_01_평온시작
EMO_02_불쾌비네팅
EMO_03_빌런말풍선
EMO_04_모욕분노마크
EMO_05_억울파랑톤
EMO_06_침묵먹칠
EMO_07_검은반전카드
EMO_08_검은반전카드
EMO_09_서류클로즈업3연타
EMO_10_번개플래시
EMO_11_붉은도장
EMO_12_빌런얼음당황
EMO_13_금색사이다
EMO_14_검은교훈카드
EMO_15_댓글투표카드
```

## 1-minute placement

```text
0~3초: 충격 훅 - 집중선, 짧은 줌인, 쾅 효과음, 큰 상단 제목
3~10초: 빌런의 선 넘는 대사 - 말풍선, 분노 마크, 대사 흔들림, 빨간 키워드
10~22초: 피해자의 억울함 - 파란 톤, 먹칠 배경, 느린 줌아웃, 짧은 정적
22~32초: 반전 예고 - 음악 컷, 검은 배경 한 줄, 페이지 넘김
32~43초: 증거/권한 공개 - 서류 클로즈업 3연타, 번개 플래시, 철컥, 집중선
43~53초: 참교육 - 붉은 도장, 검은 대사 카드, 쾅, 빌런 얼음
53~60초: 사이다 교훈 - 금색 빛, 검은 엔딩 카드, 한 줄 교훈, 댓글 유도
```

## Era mapping

```text
조선시대 쇼츠:
노비/궁녀/충신이 모욕당함
→ 왕명/교지/상소문으로 반전
→ 파직/사약/폐위/역사의 심판

현대 사이다 쇼츠:
노인/알바/가족/약자가 모욕당함
→ CCTV/공증/녹음/계약서로 반전
→ 해고/상속 제외/공개 사과/관계 단절
```

결국 둘 다 같은 감정이다.

```text
억울하게 당한 사람이, 증거와 권한으로 판을 뒤집는 것.
그 감정선에 효과를 맞추면 조선이든 현대든 조회수 공식은 같다.
```

## Effect maximization addendum

Use effects as grouped emotional systems, not isolated decorations. A finished 0shrt/History-style CapCut draft should normally use several of these groups when the script contains the matching beat:

```text
평온/시작: slow zoom, light film grain, warm tone
불쾌/압박: vignette, dark cloud, low BGM feeling
모욕/충격: speed or burst lines, short shake, boom SFX
억울함: rain overlay, blue wash, slow zoom-out, short silence
분노 축적: eye close-up, red aura, heartbeat or low hit
반전 예고: scattered wind overlays, whoosh SFX, quick BGM cut
증거/권한 공개: document close-up, yellow burst/flash, thunder or lock SFX
응징/판결: red verdict stamp, stamp SFX, one shake
사이다/회복: gold wash, chime, brighter tone
교훈/마무리: black lesson card or bottom-only lesson caption
```

Wind scatter rule:

```text
Never use one centered wind sticker.
Use 8-12 wind overlay segments or tracks.
Use visual/03_VIS_바람휘리릭.mov when alpha works.
Use visual/03B_VIS_바람휘리릭_검은배경.mp4 as fallback with Screen/Lighten.
Stagger starts irregularly across 0.0-2.2s.
Vary position, scale, rotation, and alpha.
Suggested scale: 0.31-0.72
Suggested rotation: -28 to +27 degrees
Suggested alpha: 0.42-0.66
```

Verdict stamp rule:

```text
Stamp text is the result, not the emotion.
Joseon production: prefer visual/stamps/joseon_top5 first.
Modern production: prefer visual/stamps/modern_top15 first.
Animation: 150% -> 95% -> 105% -> 100% over 0.15s.
Sync with sfx/05_SFX_도장_stamp.mp3 or sfx/04_SFX_충격음_boom.mp3.
```

Effect test profiles:

```text
0SHRT_EFFECT_TEST_01_VISUAL_MOOD
0SHRT_EFFECT_TEST_02_SFX_ONLY
0SHRT_EFFECT_TEST_03_STAMP_MODERN_TOP15
0SHRT_EFFECT_TEST_04_STAMP_MODERN_ALL50
0SHRT_EFFECT_TEST_05_STAMP_JOSEON_ALL20
0SHRT_EFFECT_TEST_06_FULL_COMBO_EMOTION
0SHRT_EFFECT_TEST_07_WIND_SCATTER_RANDOM
```

Save the profile manifest at `EP\video\effect_test_profiles_manifest.json`. After injecting effects, inspect `draft_content.json` and verify material paths exist, `wind_scatter_*` tracks are present when wind is used, typewriter SFX is absent, and 0shrt has no purple middle overlay. `capcut_visual_snapshot.py` can fail to rasterize MOV overlays; do not treat that as a CapCut failure if the MOV path exists and the draft has valid video material.
