---
name: spine-script-119
description: "Use when building a Korean political longform episode around a spine video — 척추대본, 척추영상, 정치롱폼 척추, 1인 주장 채널 대본, or when the user asks to turn an approved solo-argument YouTube video plus supporting clips into a 119-ready PRE-119 packet. Produces 119_final_script.md, pre119_handoff.json, asset_evidence.json, narration cards, and SRT so 119 can assemble immediately without re-planning."
---

# 척추대본 119

119 CapCut 조립 **바로 앞단**이다. 1인 주장 채널 영상 하나를 논지의 척추로 삼아, 살 클립과 나레이션을 붙이고, 119가 재기획 없이 조립할 수 있는 패킷까지 만든다.

```text
소재 스캔 → 척추 확정 → 살 확보 → 나레이션 → 카드 → SRT → PRE-119 패킷
                                                              ↓
                                        119 validate → compile → preflight → build
```

110은 건드리지 않는다. 110은 자체 파이프라인(source discovery → 대본 → 111 → 112)으로 그대로 둔다.

## 구조 계약 (사용자 확정, 2026-09-02)

```text
총 길이      30분 전후. 12분 미만이면 완성하지 않는다
척추 실사용   최소 15분, 권장 16~18분, 러닝타임의 50% 이상
             오프닝 몽타주에서 재사용한 구간은 50% 산정에서 제외
척추 배치     한 덩어리 금지. 초·중·후반에 4~5블록으로 분산
나레이션      20~30%. 척추를 분석해 잇는 말이지 요약이 아니다
```

구성은 **시간순이 아니라 질문순**이다. 척추에서 사건의 요지와 핵심 발언을 먼저 뽑아 제시하고, 그 과정을 확인하는 방식으로 이어간다. 살은 다른 채널에서 붙이고 나레이션이 잇는다. 영상 초반에 이 회차를 만든 취지를 세운다.

## 소스 규칙

`togun-politics-pre119-writer/references/approved-channel-allowlist.json` 의 채널만 쓴다.

```text
척추      group=개인주장 / format=SOLO_ARGUMENT
살        메인스트림·공식/공적·화이트리스트·코멘터리·시사믹스
판정      제목이 아니라 yt-dlp --print "%(channel_id)s" 로 실측
지역계열사  본사와 channel_id가 다르다. 개별 등재된 것만
영구차단   hTcRBTJ2xAc (미디어 파손)
출처 표기  `출처 : <채널명>` 만. 플랫폼명·영문병기·영상 제목 금지
```

소재를 먼저 정하고 척추를 찾지 않는다. **척추 채널이 다루는 것 중에서 소재를 고른다.** 통짜 길이를 믿지 말고 해당 사안 구간만 센다.

## 회차 준비

```powershell
$ep = "PL_20260902_주제_부제"
$root = "E:\22utube\$ep"
mkdir $root\clips, $root\srt, $root\narration, $root\cards, $root\work
copy <skill>\templates\cards_def.template.py   $root\work\cards_def.py
copy <skill>\templates\corrections.template.json $root\work\corrections.json
$env:SPINE_EPISODE_ROOT = $root
```

`cards_def.py` 하나만 회차마다 쓴다. 스크립트는 전부 여기서 읽는다. 모든 스크립트는 `--root` 또는 `SPINE_EPISODE_ROOT` 를 받는다.

## 실행 순서

```text
1  scan_spine.py           척추 후보 스캔 (RSS, 영상 안 받음)
2  (수집)                  전체 다운로드 → 자막 ko-orig 만
3  vtt_clean.py --all      롤링 겹침 제거 + 용어 교정 → cues.json
3b mark_shorts.py          쇼츠 구간 잠금 → work/shorts.json
4  (나레이션 원고)          → Typecast 붙여넣기 → tts_raw.mp3 + tts_raw.srt
5  split_tts_lines.py      줄 단위 wav (NL01..) — 카드 단위가 된다
6  make_card_css.py        도형 CSS 10종
6b gen_short_art.py        쇼츠 삽화 프롬프트 → work/short_art_prompts.md
7  render_cards.py         NAR 카드 PNG (119 렌더러 + --css)
8  build_assets.py         컷 실측 → timeline.json + SRT + 비율 검사
9  check_captions.py       자막 QA — 길이·타이밍·용어
10 gen_script.py           119_final_script.md + sha
11 gen_handoff.py          pre119_handoff.json + upload_package.md
12 gen_evidence.py         asset_evidence.json
```

이후는 119다. `validate_pre119_handoff` → `compile_pre119_episode_cards` → `run_politics_assembly_preflight` → `build_politics_v8_project` → `capture_politics_relink_readback`.

롱폼 조립이 끝나면 쇼츠를 만든다.

```text
13 cut_shorts.py           ffmpeg 컷 + SRT + 여덟 자 SRT
14 build_short.py          쇼츠 CapCut 프로젝트
15 verify_shorts.py        정본 4벌·id 충돌·유령 참조·깨진 경로
```

`PYTHONDONTWRITEBYTECODE=1` 을 준다. 런타임 릴리스에 .pyc 가 생기면 activate 가 막힌다.

## 수집

전부 `E:\22utube\<episode_id>\` 에 받는다. C 드라이브와 OneDrive에 미디어를 두지 않는다.
`--download-sections` 을 쓰지 않는다. 전체 받고 `build_assets.py` 가 프레임 정확하게 자른다(재인코딩. `-c copy` 는 키프레임에 붙어 수 초 어긋난다).
자막은 `--sub-langs ko-orig` 만 받는다. 영문 자막을 같이 받으면 429로 영상 다운로드가 끊긴다.
받은 직후 `ffprobe` 로 video·audio 길이를 둘 다 확인한다. 한쪽이 0에 가까우면 버린다.
세로 영상(쇼츠)은 16:9 인셋에 안 맞는다. 가로 원본을 찾는다.

## 자막

```text
표시 한도    공백 제외 15자 이하 한 줄
cue 시각     타임라인 절대값, 카드 구간 안으로 clamp (시작 올림, 끝 내림)
타이밍       병합해도 원본 cue 경계를 앵커로 재분할한다
             균등 분할만 하면 병합 창 안에서 최대 4초 밀린다 (2026-09-02 실측)
교정 범위    raw / display 양쪽에 똑같이. 한쪽만 고치면 SOURCE_TRANSCRIPT_TEXT_CHANGED
교정 순서    겹침 제거 → 교정. 바꾸면 교정된 단어가 겹침 판정을 깬다
번인 자막    방송 자막이 박힌 소스는 BURNED_CAPTION 에 넣어 하단 슬롯을 끈다
             ffmpeg 로 프레임을 뽑아 눈으로 확인한 것만 넣는다
```

119의 `validate_srt_text_fidelity` 는 raw/display 가 같으면 통과한다. 양쪽에 같은 오인식이 있으면 못 잡는다. `check_captions.py` 가 그 구멍을 메운다.

## 나레이션

원고에는 아라비아 숫자를 쓰지 않는다. 화면 문구와 자막에는 쓴다(`DISPLAY_NUMERALS` 가 되돌린다).
종결어미가 `~습니다` 로만 반복되지 않게 흔든다. 방어문·결론 전환어·기계적 병렬·번역투를 쓰지 않는다.
`humanize-korean` 의 `metrics_v2.py --genre news` 로 계측한다. `risk_band` 가 `low` 가 아니면 `humanize-korean` 을 실제로 실행하고 재계측한다. 윤문했으면 FACT·QUOTE·NUMBER·NAME 을 원문과 대조한다.

Typecast 는 집 사운드 고정값을 쓴다. `00_asset_tools/tools/make_typecast_tts.py` 를 그대로 호출한다. 템포 1.2로 잠겨 있어 원고가 예상보다 짧게 읽힌다(약 10.3자/초).
API 크레딧이 없으면 원고를 통째로 사용자에게 주고 Typecast 웹 에디터에서 합성받는다. MP3와 SRT를 둘 다 받아야 한다. **SRT cue 하나가 원고 한 줄**이므로 `split_tts_lines.py` 가 줄 단위로 자른다.

## CTA

`이 영상이 보다 많은 분들에게 알려지도록 구독과 좋아요 부탁드립니다.`
오프닝 몽타주 직후 본편 진입 전, 그리고 회차 마지막. 두 곳 모두 같은 문장이다.

## 훅

첫 45초는 몽타주다. 본편에서 쓸 6~10초 구간 5~7개를 세기 순으로 배치하고 마지막에 CTA 카드를 붙인다. 나레이션·해설·상단 요약을 얹지 않는다. **아군 내부의 이탈·경고·자기비판 발화가 적대 진영 비판보다 세다.** 그런 발화를 앞에 둔다.

## 카드

`DEMOCRATIC_BLUE_INSET_CARD_V2`, `info_blocks` 정확히 1개, 1920×1080.

```text
글자수 한도   top_label 32 / headline 각 28 / footer 52
             block label 16 / main 24 / sub 42
```

**긴 나레이션을 정지 텍스트 한 장으로 덮지 않는다.** 40~55초짜리 카드는 화면이 죽는다. TTS SRT cue = 원고 한 줄이므로 줄 단위로 카드를 쪼개 평균 10초마다 화면이 바뀌게 한다.

카드에는 도형 그래픽을 넣는다. 자극적이지 않게, **실사 사진은 쓰지 않는다.**

```text
scale  저울 — 비대칭·판정        ratio  비율 바 — 수치 대비
time   타임라인 — 시간 간격       num    숫자 블록 — 사람 수·건수
flow   흐름 — 인과·구조          quote  인용 — 원본 발화
warn   경고 — 사선 해칭          split  갈라짐 — 분열·역전
herd   한 방향 — 군집            grid   격자 — 기본
```

설치본 템플릿은 건드리지 않는다. `render_democratic_blue_card.py --css` 로만 갈아끼운다. 지오메트리 검증은 119 렌더러가 그대로 한다.

## 하이퍼프레임

MP4로는 못 넣는다. `compile_pre119_episode_cards.py:191` 은 `NARRATION_VIDEO` 를 받지만 `build_politics_v8_project.py:504` 는 `SOURCE_VIDEO / CHAPTER_CARD / NARRATION_IMAGE` 셋만 처리하고 나머지는 `V8_CARD_TYPE_UNSUPPORTED` 로 예외를 던진다. 컴파일은 통과하고 빌드에서 죽는다.
**1920×1080 PNG 스틸로 뽑으면** `NARRATION_IMAGE` 로 그대로 들어간다.

## 업로드 문구

제목은 결말을 다 말하지 않는다. 썸네일은 `~했다` 요약형을 쓰지 않는다.

```text
단어 3개    각 5자 이하, 공백 없음. 충격 소재 → 타이밍 → 결과 텐션
문장 3줄    연속 의문. 궁금증으로 클릭을 만든다
```

## 쇼츠

쇼츠는 롱폼을 다 만든 뒤에 잘라내는 물건이 아니다. 나레이션과 삽화가 이미 만들어진 뒤에
구간을 고르면 쇼츠에 쓸 문장이 없다. 붙어 있는 나레이션을 끌어다 쓰게 되고, 그러면
앞뒤 문맥 없이는 말이 되지 않는다. 그래서 척추 자막을 확보한 직후 `mark_shorts.py` 로
구간을 잠그고, 그 결과를 나레이션 원고가 받는다.

목적은 쇼츠 자체가 아니라 롱폼 유입이다.

### 구조

기승전결이 아니라 논쟁 카드다. 시청자가 그대로 들고 나가 쓸 문장을 쥐여 준다.

```text
앞 삽화 + 나레이션   상대가 던지는 문장을 먼저 세운다        claim
본편 발화            그 주장의 근거처럼 보이는 사실
본편 발화 + 멘트      뒤집는 사실 — 누가, 무엇을, 왜 문제인가
뒤 삽화 + 나레이션    반박 카드 + 롱폼으로 넘기는 질문        counter
```

`counter` 는 회차에서 가장 센 사실 한 줄이다. 상대가 받아치지 못하는 것으로 고른다.

```text
"공소 취소를 가장 먼저 주장한 사람이 조국이다"
"노무현은 미국이 지정한 키르쿠크를 거절했다"
"문자를 받은 식약처장과 공무원은 전원 무혐의다"
```

숫자 나열은 반박 카드가 아니다. 지지율이 얼마에서 얼마로 떨어졌다는 사실만으로는
무엇을 주장하는지 전달되지 않는다.

### 계약

```text
회차당        2~3편
길이          구간 20~90초. 나레이션을 붙이면 1~3분. 늘어져도 된다
나레이션      롱폼 wav 를 그대로 쓴다. 쇼츠용으로 새로 합성하지 않는다
              앞 1~3줄 / 뒤 1~3줄. 붙어 있는 줄이 아니라 역할로 고른다
              쇼츠에 쓸 줄은 앞뒤 문맥 없이 혼자 성립하게 쓴다. 지시어로 시작하지 않는다
자막          여덟 자 안팎으로 쪼갠다. 나레이션 자막도 같다
              나레이션이 끝난 뒤 일 초 남겨 문장을 마무리한다
멘트          1~3개, 각 14자 이하. mood=anger 면 배경이 빨강
T1 · T2       각 12자 이하
출처          `출처 : <채널명>` 만. SOURCES 표기를 그대로 가져온다
근본          P0_ROOT_shrt_119short_v1  1080×1920
```

### 삽화

롱폼 CSS 카드는 전부 같은 결이라 쇼츠에서 화면이 죽는다. 삽화를 따로 만들어 나레이션
구간에 깐다. 신문 삽화·목판화 톤이고, **실존 인물의 얼굴을 그리지 않는다.** 화면 안에
글자·숫자·로고·정당 상징도 넣지 않는다. 개념 그래픽만 쓴다.

`gen_short_art.py` 가 프롬프트를 뽑는다. 롱폼 카드를 렌더할 때 같이 돌려서 한 번에 요청한다.
720p 로 충분하다. 쇼츠에서 작게 들어간다. 받은 파일은 `E:\22utube\_images\woodcut\` 에
`art` 이름 그대로 넣는다.

### CapCut 정본

CapCut 은 타임라인을 네 곳에 나눠 들고 있다. 한 곳이라도 어긋나면 열었을 때 근본 상태로
되돌아가거나, 구간을 옮기는 순간 영상이 사라진다.

```text
draft_content.json
template-2.tmp
Timelines/<타임라인 id>/draft_content.json
Timelines/<타임라인 id>/template-2.tmp
```

가져온 미디어는 클라우드 신원을 지운다. `material_id=""`, `category_name="local"`,
`source_platform=0`, `is_copyright=False`. 안 지우면 세 재질이 같은 id 로 묶여 하나로 합쳐진다.
나레이션 오디오는 `type="extract_music"` 에 `effect_id=""` 를 준다. 효과음 신원을 물려받으면
소리가 나지 않는다.

`verify_shorts.py` 가 이 넷과 id 충돌·유령 참조·깨진 경로를 본다. 사용자가 CapCut 에서
컷을 더 나눴을 수 있으므로 슬롯은 세 컷 **이상**이면 통과다.

## 조립 경계

CapCut 앱을 열지 않는다. 빌드까지만 하고 멈춘다. 실행 중이면 종료는 한다.
MP4 렌더와 업로드는 하지 않는다. 미디어 릴링크는 사용자 작업이다.
`--media-dir` 이 이미 있으면 빌더가 `PROJECT_TARGET_OR_MEDIA_DIR_EXISTS` 로 멈춘다. 재빌드 시 미디어 폴더와 프로젝트 폴더를 먼저 지운다.
지운 프로젝트가 CapCut `root_meta_info.json` 에 남으면 `ROOT_META_REGISTRATION_INVALID` 가 난다. 백업 뜨고 **폴더가 실제로 없는 항목만** 지운다.

## 보고

`references/report-format.md` 를 따른다.

## 상태

```text
SPINE_LOCKED               척추 확정, 실사용 15분 이상 확인
WAIT_SPINE_SOURCE          15분을 못 채움. 조립하지 않고 소스 확보 실패로 보고
WAIT_USER_TTS              Typecast 합성 대기
PACKET_READY               gen_evidence 까지 완료, 119 입력 준비됨
WAIT_USER_CAPCUT_CHECK     빌드 완료, 릴링크 대기
```

## 하지 않는 것

- 110·111·112 파이프라인을 건드리지 않는다.
- 허용 목록 밖 채널을 쓰지 않는다. 사용자가 준 URL이 아니면 예외도 없다.
- 나레이션을 늘려 길이를 채우지 않는다. 12분을 못 채우면 소스를 더 찾는다.
- 실측하지 않은 길이·channel_id를 보고에 쓰지 않는다.
- 승인된 콘텐츠를 생산 단계에서 재작성하지 않는다.
