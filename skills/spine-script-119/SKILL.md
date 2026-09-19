---
name: spine-script-119
description: "Use when building a Korean political longform episode around a spine video — 척추대본, 척추영상, 정치롱폼 척추, 1인 주장 채널 대본, or when the user asks to turn an approved solo-argument YouTube video plus supporting clips into a 119-ready PRE-119 packet. Produces 119_final_script.md, pre119_handoff.json, asset_evidence.json, narration cards, and SRT so 119 can assemble immediately without re-planning."
---

## Shared catalog location

For this user's shared catalog, edit the NAS `skills` source configured by ZSkillSync. Local application skill folders are generated copies. Routine skill updates use automatic synchronization and verification; historical Git release instructions apply only to a separately requested Git maintenance task. Resolve machine paths from current environment and local ZSkillSync settings. Production approval, evidence, and application safety gates still apply.

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

**척추는 채널이 아니라 구간이다** (사용자 확정, 2026-09-17). 허용 목록 어느 채널이든 진행자·고정 논객이 화면에 나와 이어서 정치평론을 하는 구간이면 척추다. 1인 주장 채널 본편, 매불쇼 뉴스 코너, 뉴스공장·박정호 핫스팟의 논객 대담, 새날·이동형TV 평론이 모두 된다. 기자 리포트, 청문회·본회의 중계, 현장 원음, 당사자 회견, 비정치 코너(경제·문화·음악)는 척추가 아니라 살이다. 살은 척추와 같은 채널의 다른 영상이나 허용 목록 다른 채널의 영상에서 붙인다. 척추 비율은 컷표의 `S` 컷으로 센다. 세 시간짜리 라이브 한 편에서 평론 구간은 `S`, 같은 방송 안의 뉴스 원본 재생은 `B` 로 가른다.

**증언 척추.** 인물 생애처럼 한 사람의 주장 영상으로 논지가 서지 않는 소재는 곁에서 본 여러 사람의 증언 영상을 합쳐 척추로 쓴다 (2026-09-14 노무현 회차, 사용자 승인 B안). `cards_def.SPINE_VIDEO_IDS` 에 증언 영상을 전부 적는다. 15분·50% 계약은 그대로다. 척추 컷은 컷표에서 `S`, 당시 현장 원본은 `B` 다. `build_assets.py` 는 `S` 컷으로 비율을 세고, `S`/`B` 표시가 없는 옛 회차에만 `SPINE_VIDEO_IDS` 로 센다.

구성은 **시간순이 아니라 질문순**이다. 척추에서 사건의 요지와 핵심 발언을 먼저 뽑아 제시하고, 그 과정을 확인하는 방식으로 이어간다. 살은 같은 채널의 다른 영상이나 허용 목록 다른 채널에서 붙이고 나레이션이 잇는다. 영상 초반에 이 회차를 만든 취지를 세운다.

## 상세 문서

| 주제 | 파일 | 언제 읽나 |
|:--|:--|:--|
| 소스 규칙·회차 준비·수집 | [references/source-and-prep.md](references/source-and-prep.md) | 회차를 시작하거나 소스를 고를 때 |
| 컷표·나레이션 줄 끼워 넣기 | [references/cut-table.md](references/cut-table.md) | 컷표를 짜거나 나레이션 줄을 넣을 때 |
| 자막 | [references/captions.md](references/captions.md) | 자막을 만들거나 검사할 때 |
| 나레이션·CTA·훅 | [references/narration.md](references/narration.md) | 나레이션 원고·CTA·훅을 쓸 때 |
| 작가모드 순환·간격·인물 서사 | [references/writer-mode-structure.md](references/writer-mode-structure.md) | 챕터 구조를 잡을 때 |
| 작가모드 원본·보상·동행·금지 | [references/writer-mode-sentences.md](references/writer-mode-sentences.md) | 나레이션 문장을 쓸 때 |
| 카드·업로드 문구 | [references/cards-and-upload.md](references/cards-and-upload.md) | 카드와 업로드 문구를 만들 때 |
| 하이퍼프레임·장면 제작 | [references/hyperframes.md](references/hyperframes.md) | 나레이션 영상을 만들 때 |
| 쇼츠 | [references/shorts.md](references/shorts.md) | 쇼츠를 만들 때. 계약은 이 문서 `### 계약` |

## 실행 순서

```text
0  (선택) 투군 사전 패킷      togun-politics-pre119-writer/templates/run-prompt.md 로 투군에 요청
                           소스맵·구성안·보상 포인트·SRT 매니페스트 → <root>/00_pre119_package/togun_pack/
                           나레이션 문체는 받지 않는다. 원고는 4 에서 작가모드로 쓴다
1  scan_spine.py           척추 후보 스캔 (허용 목록 전 채널 videos·streams 탭, yt-dlp 목록만. 영상 안 받음)
2  (수집)                  idm 스킬. 전체 다운로드 → <root>/clips/<video_id>.mp4, 자막 ko-orig → <root>/srt/
3  vtt_clean.py --all      롤링 겹침 제거 + 용어 교정 → cues.json
3b mark_shorts.py          쇼츠 구간 잠금 → work/shorts.json
4  (나레이션 원고)          narration/<block>.txt — 한 줄 한 문장. 원고가 곧 대본이다
                           보상앵커 작가모드로 쓴다 (아래 `작가모드` 절)
4b check_narration.py     TTS 전 원고 검사 — 금지 표현·숫자·인명 근사 변형·길이 추정
                           챕터별 동행 문장 수를 찍는다. 0 인 챕터는 WRITER_COVIEW_MISSING 경고
4c (투군 오류 찾기)        직책·소속·날짜·숫자 오류만 → work/togun_error_check.md → 대조 후 반영 → 4b 재실행
4d tts_lines.py           통과한 원고를 줄 단위 Typecast API 합성 → NLxx.wav + work/narration_lines.json
   (API 크레딧 없을 때)    웹 에디터 붙여넣기 → tts_raw.mp3 + tts_raw.srt → 5 split_tts_lines.py
4e renumber_narration.py  합성 뒤 줄을 끼워 넣거나 뺐을 때만. 만든 wav·장면을 살리고 번호만 다시 매긴다
5  split_tts_lines.py      (웹 에디터 경로) 줄 단위 wav (NL01..) — 카드 단위가 된다
6  gen_short_art.py        쇼츠 삽화 프롬프트 → work/short_art_prompts.md
6a asr_window.py          컷 후보 구간 whisper 받아쓰기 → work/asr/*.json (말이 시작·끝나는 시각)
                           컷 목록을 work/asr_jobs.tsv 에 모아 `--batch work/asr_jobs.tsv --edges 8` 로 한 번에.
                           모델 1회 로드, 경계 앞뒤 8초만. 영상 ID 가 `-` 로 시작하면 `--video=-abc`
6b final_cuts.py          컷표 확정 (아래 `컷표` 절) → make_cards.py 로 cards_def.CARDS 새로 쓰기
7  build_assets.py         컷 실측 → timeline.json + SRT + 비율 검사
8  check_captions.py       자막 QA — 길이·타이밍·용어·컷 화제 이탈
9  plan_hyperframes.py     만들 장면표 → work/scenes.py 작성 → render_scenes.py (필수)
                           화면은 `hyperframes-politics-119` 의 장면 모드를 따른다. 민주 블루
                           인셋 카드 같은 정지 이미지 카드로 대체하지 않는다
                           먼저 `render_scenes.py --check-only` 를 전체 목록으로 돌려 생성·check 오류를
                           한 번에 잡고, 통과하면 `render_scenes.py --jobs 4` 로 렌더한다. 챕터당 모션 1회
                           규칙은 한 프로세스 안에서만 세므로 이름을 나눠 따로 돌리면 검사가 빠진다
10 gen_script.py           119_final_script.md + sha
11 gen_handoff.py          pre119_handoff.json + upload_package.md
12 gen_evidence.py         asset_evidence.json
```

이후는 119다. `validate_pre119_handoff` → `compile_pre119_episode_cards` → `run_politics_assembly_preflight` → `build_politics_v8_project` → `capture_politics_relink_readback`.

롱폼 조립이 끝나면 쇼츠를 만든다.

```text
13 cut_shorts.py           ffmpeg 컷 + SRT + 여덟 자 SRT + 쇼츠 자막 용어 검사
14 build_short.py          쇼츠 CapCut 프로젝트
15 verify_shorts.py        정본 4벌·id 충돌·유령 참조·깨진 경로
```

`cut_shorts.py` 는 잘라낸 자막을 용어집과 대조해 오인식 의심을 찍고 `WAIT_SHORT_CAPTION_TERMS`
로 멈춘다. 롱폼의 `check_captions.py` 는 `work/timeline.json` 과 `C*.display.srt` 만 보므로
쇼츠 자막을 검사하지 않는다. 그 구멍을 13이 메운다. 걸린 항목은 `work/corrections.json` 에
넣고 `vtt_clean.py` 부터 다시 돌린다. 전부 오탐임을 눈으로 확인한 경우에만 `--allow-suspect`
를 쓴다. 쇼츠 자막은 화면에 그대로 박히므로 통과시키고 넘어가지 않는다.

`PYTHONDONTWRITEBYTECODE=1` 을 준다. 런타임 릴리스에 .pyc 가 생기면 activate 가 막힌다.

## 컷표
→ 본문: [references/cut-table.md](references/cut-table.md)

## 작가모드 — 보상앵커
→ 본문: [references/writer-mode-structure.md](references/writer-mode-structure.md)
→ 본문: [references/writer-mode-sentences.md](references/writer-mode-sentences.md)

## 하이퍼프레임
→ 본문: [references/hyperframes.md](references/hyperframes.md)

### 장면 제작
→ 본문: [references/hyperframes.md](references/hyperframes.md)

## 쇼츠
→ 본문: [references/shorts.md](references/shorts.md)

### 계약

```text
회차당        2~3편
길이          구간 20~90초. 나레이션을 붙이면 1~3분. 늘어져도 된다
본편 속도      1.2배. `_common.py` 의 `SHORT_SPEED` 가 정한다. 나레이션은 건드리지 않는다
나레이션      롱폼 wav 를 그대로 쓴다. 앞 1~3줄 / 뒤 1~3줄, 역할로 고른다
              쇼츠에 쓸 줄은 앞뒤 문맥 없이 혼자 성립하게 쓴다. 지시어로 시작하지 않는다
              여기에 쇼츠 전용 줄 두 종류를 더 합성한다
              · 도입 한 줄 — 이 쇼츠가 무엇을 묻는지 세운다. 회차마다 다르게
              · 마무리 두 줄 — 본편으로 넘기는 안내 + 구독 요청. 세 편이 같이 쓴다
                "더 자세한 내용은 아래 영상에서 보실 수 있습니다"
                "구독과 좋아요 부탁드립니다"
              쇼츠 하단에 롱폼 링크를 건다. 유입이 목적이라 이 두 줄을 빼지 않는다
              이 줄들은 `narration/N_SHORTS.txt` 에 두고 `NARRATION_ORDER` 맨 끝에 `N_SHORTS` 를 넣는다.
              롱폼 줄과 한 번에 합성하되 롱폼에는 넣지 않는다 — `make_cards` 가 이 블록을 건너뛰고,
              컷표(`BODY`)에 들어 있으면 `SHORTS_BLOCK_IN_BODY` 로 막는다
자막          여덟 자 안팎으로 쪼갠다. 나레이션 자막도 같다
              나레이션이 끝난 뒤 일 초 남겨 문장을 마무리한다
멘트          1~3개, 각 14자 이하. mood=anger 면 배경이 빨강
T1 · T2       각 12자 이하
출처          `출처 : <채널명>` 만. SOURCES 표기를 그대로 가져온다
근본          P0_ROOT_shrt_119short_v1  1080×1920
              CapCut 은 이름이 겹치면 폴더명 뒤에 `(N)` 을 붙여 바꾼다. 감시가 도는
              동안에는 정확한 이름으로 복사해 둬도 되돌아간다. `resolve_capcut_root_dir`
              가 접미만 다른 사본 중 원본을 찾으므로 폴더명을 손으로 맞추지 않는다.
```

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
- 허용 목록 밖 채널을 쓰지 않는다. 사용자가 준 URL이 아니면 예외도 없다. 척추도 이 목록 안에서 고른다.
- 나레이션을 늘려 길이를 채우지 않는다. 12분을 못 채우면 소스를 더 찾는다.
- 실측하지 않은 길이·channel_id를 보고에 쓰지 않는다.
- 승인된 콘텐츠를 생산 단계에서 재작성하지 않는다.
