# 소스 규칙·회차 준비·수집 — 상세

> 원문: `spine-script-119/SKILL.md` 에서 줄 단위로 옮김. 내용 수정 없음.

## 소스 규칙

`togun-politics-pre119-writer/references/approved-channel-allowlist.json` 의 채널만 쓴다.

```text
척추      허용 목록 전 채널. group·format 으로 가르지 않고 구간 성격으로 가른다
          진행자·고정 논객이 화면에 나와 이어서 정치평론을 하는 구간
          예) 1인 주장 채널 본편 · 매불쇼 뉴스 코너 · 뉴스공장·핫스팟 논객 대담 · 새날·이동형TV 평론
          아님) 기자 리포트 · 청문회·본회의 중계 · 현장 원음 · 당사자 회견 · 비정치 코너 → 살
살        척추와 같은 채널의 다른 영상, 또는 허용 목록 다른 채널 영상
          같은 라이브 안의 뉴스 원본 재생 구간도 살(`B`)이다
판정      제목이 아니라 yt-dlp --print "%(channel_id)s" 로 실측
지역계열사  본사와 channel_id가 다르다. 개별 등재된 것만
영구차단   `_common.BLOCKED_VIDEO_IDS` · `BLOCKED_CHANNEL_MARKS` 에 적는다.
           `load_cards_def` 가 SOURCES 를 보고 `BLOCKED_SOURCE` 로 멈춘다.
           hTcRBTJ2xAc (미디어 파손)
           fRkePkq39Lk · JTBC · 썰전 (Content ID 소유권 주장, 2026-09-13)
           저작권 클레임이 한 번 온 곳은 재업로드본까지 쓰지 않는다.
           채널 표기로도 막으므로 다른 계정의 재업로드도 걸린다.
출처 표기  `출처 : <채널명>` 만. 플랫폼명·영문병기·영상 제목 금지
```

소재를 먼저 정하고 척추를 찾지 않는다. **진행자들이 평론으로 다루는 것 중에서 소재를 고른다.** 통짜 길이를 믿지 말고 해당 사안의 평론 구간만 센다. 라이브는 코너가 섞이므로 `TOPIC_RANGE` 에 평론 구간만 적는다.

## 회차 준비

신규 회차는 현재 PC의 로컬 `LOCAL_PRODUCTION_ROOT/119jungchi` 아래에서 작업한다. 스킬·인계 패키지는 NAS로 공유하지만, 회차 미디어·JSON·자막·TTS·카드·임시 파일·렌더·CapCut draft/cache는 로컬에 둔다. 인계 묶음을 받으면 먼저 로컬로 복사·검증하며, 저장할 때마다 NAS로 복제하지 않는다. 기존 회차를 자동 이동하지 않는다.

```powershell
$ep = "PL_20260902_주제_부제"
$settings = Get-Content -LiteralPath (Join-Path $env:LOCALAPPDATA 'ZSkillSync/paths.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$root = Join-Path $settings.LOCAL_PRODUCTION_ROOT ("119jungchi/" + $ep)
mkdir $root\clips, $root\srt, $root\narration, $root\cards, $root\work
copy <skill>\templates\cards_def.template.py   $root\work\cards_def.py
copy <skill>\templates\corrections.template.json $root\work\corrections.json
copy <skill>\templates\final_cuts.template.py  $root\work\final_cuts.py
copy <skill>\templates\scenes.template.py      $root\work\scenes.py
$env:SPINE_EPISODE_ROOT = $root
```

회차마다 쓰는 파일은 셋이다. `cards_def.py`(회차 정의), `final_cuts.py`(컷표), `scenes.py`(하이퍼프레임 장면). 스크립트는 전부 여기서 읽는다. 모든 스크립트는 `--root` 또는 `SPINE_EPISODE_ROOT` 를 받는다.

**스킬 스크립트를 회차 폴더로 복사해 고쳐 쓰지 않는다.** 2026-09-08~14 세 회차는 `hf_lib.py` 같은 제작 코드를 직전 회차 폴더에서 복사해 이어 썼고, 그 결과 스킬만으로는 최신 회차를 다시 만들 수 없었다. 회차에서 고친 제작 코드는 그 회차 안에 스킬로 올린다.

Mac은 `~/Library/Application Support/ZSkillSync/paths.json`의 `LOCAL_PRODUCTION_ROOT`를 해석한다. Windows 드라이브 문자를 Mac에 복사하지 않는다.

## 수집

원본은 `<root>\clips\<video_id>.mp4`, 자막은 `<root>\srt\<video_id>.ko-orig.vtt` 다. `build_assets.py` 와 `asr_window.py` 가 이 이름으로 찾는다. `LOCAL_PRODUCTION_ROOT` 밖, OneDrive, NAS 에 미디어를 두지 않는다. 다운로드는 `idm` 스킬을 따른다(403·360p 다운그레이드 처리).
`--download-sections` 을 쓰지 않는다. 전체 받고 `build_assets.py` 가 프레임 정확하게 자른다(재인코딩. `-c copy` 는 키프레임에 붙어 수 초 어긋난다).
자막은 `--sub-langs ko-orig` 만 받는다. 영문 자막을 같이 받으면 429로 영상 다운로드가 끊긴다.
받은 직후 `ffprobe` 로 video·audio 길이를 둘 다 확인한다. 한쪽이 0에 가까우면 버린다.
세로 영상(쇼츠)은 16:9 인셋에 안 맞는다. 가로 원본을 찾는다.

