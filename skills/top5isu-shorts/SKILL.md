---
name: top5isu-shorts
description: Standalone end-to-end factory for Korean TOP5, ranking, 군림보, and gunlimbo Shorts. Use for script design, TTS/audio, images, CapCut project creation, validation, and final reporting in the top5isu template lane. Do not mix this lane with generic Tikitaka or shrt white production.
---

# top5isu Standalone Shorts Factory

## Factory Identity

```text
standalone_factory=true
external_skill_handoff=forbidden
single_entrypoint=$top5isu-shorts
template_profile=top5isu_v2_top55
fallback_allowed=false
```

This skill owns the complete TOP5·군림보 lane. It does not route script design,
production, CapCut assembly, or validation to another skill. Keep implementation
files inside this skill and split them by responsibility instead of adding more
user-facing skills.

## Commands

```text
$top5isu-shorts TOP5 쇼츠 끝까지
$top5isu-shorts 군림보 쇼츠 끝까지
$top5isu-shorts TOP5 설계도만
$top5isu-shorts 군림보 CapCut 프로젝트까지
```

The operator needs to remember only `$top5isu-shorts`.

## Profile Router

```text
TOP5, 탑5, 탑파이브, 순위, 랭킹, 5위부터 1위 -> style_profile=top5
군림보, gunlimbo, 군림보형 이야기                    -> style_profile=gunlimbo
both or unclear                                      -> WAIT_USER_PROFILE
```

Read only the selected profile:

- `style_profile=top5`: `references/top5-profile.md`
- `style_profile=gunlimbo`: `references/gunlimbo-profile.md`

Do not apply Tikitaka stages, handoff files, shrt-white coordinates, or generic
Shorts caption lanes to either profile.

### 군림보 라우팅·Image2 선행 게이트

운영자가 `군림보`, `블랙 TOP5`, `블랙 템플릿`, `TOP55`, 또는 `정보있슈`를
제작 프로필 의미로 말하면 다른 스킬보다 먼저 이 standalone factory의
`style_profile=gunlimbo`를 고정한다. **주제가 5개 순위가 아닌 단일 인물·사건·근황
설명이어도 군림보가 명시되면 이 라우팅이 우선한다.** `블랙 TOP5 스킬`이라는
표현은 반드시 5위→1위 대본을 요구한다는 뜻이 아니라, 군림보 문맥에서는 이
스킬의 블랙 TOP55 시각 계약을 가리킬 수 있다. 음성만 군림보로 쓰고 일반
0shrt나 `shrt white`에서 제작하는 것은 금지한다. 시작 전에 episode state의
`skill`, `style_profile`, `template_profile`, `fallback_allowed`를 읽어 확인한다.

잘못된 generic lane에서 REVIEW나 CapCut 프로젝트를 이미 만들었다면 그것을
부분 수정하지 말고 `REJECTED_WRONG_PROFILE`로 잠근 뒤 새 군림보 버전을 만든다.
사실검증 대본과 승인 음성은 해시가 유지되면 이전할 수 있지만 시각 자산과
조립은 TOP55 계약으로 다시 만든다.

운영자가 GPT 이미지를 요구하면 실제 ChatGPT Image2/CDP PNG가 0장인 상태에서
원본 크롭·기사 카드·PIL 그래픽을 완료 이미지로 보고하지 않는다. 먼저 일반
새 ChatGPT 대화에서 한 장을 생성하고, 원본 PNG와 `966×794` TOP55 프레임핏
미리보기를 운영자에게 승인받은 뒤 배치 생성한다. 자세한 복구 절차와
프롬프트 함정은 `references/gunlimbo-wrong-lane-image2-recovery.md`를 읽는다.

## Internal Lifecycle

One skill owns all stages:

```text
INTAKE
-> EVIDENCE_PACKET
-> CHATGPT_WRITER
-> SCRIPT_QA
-> AUDIO_ASSETS
-> CAPCUT_PROJECT
-> FINAL_REPORT
```

`CHATGPT_WRITER` is an internal browser backend owned by this skill, not an
external skill handoff. Read `references/chatgpt-writer-contract.md`. Create an
independent fresh ChatGPT conversation for each episode through the managed
`openclaw` profile; never reuse an existing conversation.

Create an episode with `scripts/create_top5isu_episode.py`. Fixed directories:

```text
00_source
10_analysis
20_script
30_audio
40_assets
50_capcut_project
90_reports
```

### INTAKE

- Lock `style_profile=top5|gunlimbo`.
- Record topic, source URLs/files, requested stop point, upload target, and facts
  requiring verification.
- Do not invent rankings, prices, revenue, dates, quotes, or source facts.
- Resolve the active factory root before writing an episode.
- `TOP5 만들자`, `만들자`, `진행`, or `끝까지` authorizes the default lane through a verified editable CapCut project file. After the operator selects the title or angle, do not insert another routine script-approval pause. Ask again only for unresolved facts that change the ranking, a genuinely undecided creative branch, rights/payment risk, or publish/upload/delete actions. A Clarify timeout does not cancel an earlier explicit approval. See `references/production-index-sync.md`.

#### CLEAN_VIDEO_REWORK

When the operator supplies a clean video derived from an existing Short after
captions, subtitles, or other text overlays were removed, keep it in this skill
as `intake_mode=clean_video_rework`. Do not treat it as an unrelated new source.

1. Save `source_short_ref`, `derived_from_existing_short=true`, and the clean
   video path in `10_analysis/clean_video_rework_manifest.json`.
2. Require `captions_removed=true`, `text_overlays_removed=true`, actual visual
   review, OCR overlay check, and playable-media ffprobe.
3. Run `scripts/validate_top5isu_rework_intake.py`.
4. If visual/OCR cleanliness is not proven, stop at
   `WAIT_CLEAN_VIDEO_REVIEW`; do not silently reject or replace the supplied
   clean source.
5. After PASS, reuse the existing episode intent and rebuild script, audio,
   assets, and CapCut project from the supplied clean video.

### SCRIPT_DESIGN

Read `references/script-contract.md` and
`references/chatgpt-writer-contract.md`. First create the verified evidence and
writer inputs:

```text
10_analysis/evidence_packet.json
10_analysis/writer_packet.json
```

For political TOP5 topics involving alleged reversals, betrayal, party-line changes, bills, votes, or public statements, read `references/political-top5-evidence-safety.md`. Do not infer an individual's prior position from party affiliation or a party platform; require person-specific past and current evidence before describing a personal reversal.

For loan or financial-product explainers involving deposit loans, public-rental loans, rates, limits, approval paths, lender screening, or refinancing, read `references/loan-product-shorts-evidence-and-wording.md`. Treat operator articles and consultation drafts as source material, not automatic current lender-policy authority. Exact rates, maximum percentages, approved amounts, and eligibility outcomes require a current official lender/BANKLY/MCP source; otherwise omit the number, use conditional review wording, and state that approval, limit, and rate require individual official screening. For every 임대아파트·공공임대 loan episode, lock the exact final spoken and display CTA `임대아파트대출 상담이 필요하다면 고정댓글을 확인하세요`; reserve its duration before script lock and verify the final CapCut caption text exactly.

For forecast financial rankings such as global operating profit, net income, revenue, or market-cap TOP5, read `references/forecast-financial-ranking-fact-check.md`. Preserve operator prose as source material, but do not make it production authority until metric, period, source type, native amount, common FX conversion, and recalculated order all pass. Enforce one same-date forecast snapshot across all ranks: later high-case revisions belong in separate outlook context unless every row is refreshed and resorted. A sensational next-year leadership claim requires same-metric, same-period evidence or must be softened/removed.

When a political TOP5 uses official politician portraits, paired webtoon visuals, or a TOP55 CapCut build, also read `references/political-top5-portrait-capcut-lessons.md`. Use official source photos and reference-image generation; name-only likeness generation is review-only and must not be accepted when age, glasses, or facial structure drift.

Then run:

```text
scripts/build_top5isu_writer_packet.py
scripts/run_top5isu_chatgpt_writer.py --submit
scripts/validate_top5isu_writer_response.py
```

The browser writer opens a fresh ChatGPT conversation in the managed `openclaw`
profile, requests `높음` reasoning when visible, submits only the bounded
non-sensitive writer packet, and recovers the response without clipboard use.
`끝까지` authorizes this internal writer submission. Customer data, secrets,
account changes, upload, publishing, and deletion remain outside that approval.

Required outputs:

```text
20_script/design_blueprint.md
20_script/writer_prompt.md
20_script/writer_response.txt
20_script/writer_response.json
20_script/script_qa.json
20_script/model_run_manifest.json
20_script/final_script.json
20_script/tts_copy_text.txt
20_script/tts_spoken_copy.txt
20_script/top5isu_build_contract.json
```

`model_run_manifest.json` stores hashes and status only. Browser URLs, tab IDs,
target IDs, conversation IDs, cookies, tokens, sessions, account identifiers,
prompt text, and response text are forbidden. A writer response becomes
production authority only after deterministic fact, number, order, and visible
text validation passes.

When Claude is used for audience/persona review, Claude is advisory only. It may
identify unclear wording or likely drop-off points, but it must not alter the
operator-approved source scope, story/beat order, scene count, cue boundaries,
or second-level timing. Hermes owns the deterministic timing gate: generate the
fixed-speed narration first, measure it with `ffprobe`, then derive subtitle and
image boundaries from the measured sentence manifest. Reject or ignore any
Claude recommendation that invents timestamps, reorders beats, changes scene
count, or overrides the original composition timing.

Run `scripts/validate_top5isu_blueprint.py` and
`scripts/validate_top5isu_contract.py`. If the user explicitly says `끝까지`, the
approved scope covers the internal stages, but factual ambiguity, missing source
evidence, ChatGPT login/UI failure, invalid writer output, or an undecided
required audio route remains a WAIT blocker.

### AUDIO_ASSETS

Read `references/production-contract.md` and
`references/supertone-voice-identity-and-recovery.md`.

- Generate or accept the selected narration and preserve the full audio.
- The operator's accepted SuperTone voice is an identity lock, not a best-effort default. Never silently fall back to Edge, macOS `say`, Yuna, an English/female auto-selected voice, or a different SuperTone voice. On missing/invalid credentials or 401/403, stop at `WAIT_SUPERTONE_AUTH`; when routing or credentials changed, generate and verify one short Korean preview before synthesizing the full script.
- Default SuperTone profile:

```text
VOICE_ID=otFXhy6zBa2LQ8AYSWUeDB
MODEL=sona_speech_2t
PITCH_SHIFT=0
PITCH_VARIANCE=1
SPEED=1
```

- Never print or serialize API keys.
- Keep the display/caption authority (`tts_copy_text.txt` or the validated final script) separate from a pronunciation-only `tts_spoken_copy.txt`. In the spoken copy, expand Arabic numerals and unstable English tokens into intentional Korean readings (`2026` → `이천이십육년`, `TOP5` → `탑 파이브`, `AI` → `에이아이`) without changing the factual value shown on screen.
- When the operator supplies final audio plus a pronunciation-form SRT, preserve it unchanged as `subtitles_spoken_original.srt` for timing, and create `subtitles_display.srt` with identical cue indices/times but restored display notation (`이천이십육년` → `2026년`, `오 위` → `5위`, `에이아이` → `AI`, `케이비증권` → `KB증권`, spoken Korean amounts → Arabic-numeral amounts). CapCut must use the display SRT, never the pronunciation SRT. Require the same cue count, zero overlaps, at most two lines, no pronunciation-only token residue, and final SRT/audio duration delta ≤ 50 ms.
- Interpret `대본 줘` by the active production context. During TTS pronunciation repair, return only a copy-ready `tts_spoken_copy` with every year, rank, amount, acronym, and English token written exactly as it should be spoken in Korean; do not return Arabic numerals or Latin abbreviations, and do not add explanation unless requested. During caption/SRT work, return the display copy with normal numerals and abbreviations instead. `음성 대본` means spoken copy; `화면 대본`, `자막`, or `SRT` means display copy.
- Generate narration **one grammatical sentence per API clip**. Split by sentence punctuation, not source-file line breaks: a line containing `안녕하세요. 오늘의 탑파이브 주제인데요.` is two clips. Store one manifest item per sentence, preserve already-PASS clips, and regenerate only failed sentence clips before rebuilding the joined audio, timings, and hashes.
- Run Korean ASR on every sentence clip before assembly. Check company name, rank, amount, closing phrase, clipped words, inserted words, repeated syllables, and adjacent duplicates; a generic duplicate-token check alone is insufficient. Then run ASR and a direct listen-through on the final joined audio. The operator's audible-artifact report overrides an automated PASS.
- Read `references/supertone-sentence-assembly-qa.md` for sentence splitting, pronunciation-copy repairs, selective regeneration, and final concat QA.
- Normalize with `ffmpeg loudnorm` to `-14 LUFS` before import.
- For a mandatory closing CTA, budget its measured fixed-speed duration before drafting the body. Never shorten, paraphrase, or speed up the locked CTA to hit the runtime; compress or merge earlier explanatory sentences instead. If adding or merging text changes sentence count or shifts sentence indices, rebuild every sentence clip. Selective `REPAIR_LINES` regeneration is allowed only when sentence indices remain stable. After the final repair, rebuild loudnorm audio, subtitle timing, image boundaries, and preview files from the current manifest so no stale pre-repair artifact survives.
- Measure the first real narration duration. When it differs from
  `target_duration_sec` beyond tolerance, run
  `run_top5isu_chatgpt_writer.py --submit --measured-duration-sec <seconds>`;
  revalidate the repaired script and regenerate TTS. Preserve facts, amounts,
  fact IDs, rank/story order, and fixed greeting. Never trim the waveform to
  force duration. If validated duration repairs oscillate between too long and
  too short, stop further repair calls, recover the already-PASS candidate
  closest to target, rerun writer validation, and regenerate TTS from that
  candidate. Only abnormal leading/trailing silence cleanup is allowed.
- `final_export_remeasure_required=true`.
- Replace every sample image. The episode image count is dynamic, but every
  image must retain exactly one transition animation.
- For still-image or Image2-heavy episodes, do not stop at one entrance
  animation per image. Add emotion-matched CapCut video-effect accents often
  enough to keep the frame alive: a still lasting 6 seconds or more receives
  at least one mid-shot accent, and a still lasting 10 seconds or more may
  receive two restrained accents. Use impact effects (`폭발`, `화면 균열`,
  `불꽃 스와이프`, `불꽃 회오리`) only for shock, anger, decisive numbers,
  punishment, or reversal; use motion effects (`속도 대시`, `스피드 라인`,
  `스트레치 인`) for explanation, momentum, expansion, or scene progression;
  and use atmospheric effects (`비`, `얕은 번개`, dark flash/fade) for anxiety,
  fatigue, grief, or unresolved tension. Avoid repetitive random effects,
  keep the strongest effects to one or two emotional peaks, and reject any
  effect that obscures the title, TTS captions, key faces, or source text.
- Generated TOP55 visual routing is locked to **Google Flow DOM/CDP first** and
  **GPT Image2 second**. Unless the operator explicitly names GPT/Image2 or a
  different generator, use Flow one image at a time, preserve the real generated
  original, and record generator/model label, dimensions, and SHA-256. Keep the
  GPT Image2 route and references installed as the fallback; never replace either
  route with local/proxy artwork.
- For generated TOP55 visuals **or operator-supplied reference stills**, read
  `references/top55-image2-window-production.md`. If the operator wants the
  supplied images sent back to ChatGPT to create similar cartoon/webtoon images,
  also read `references/gunlimbo-operator-reference-image2-and-text-cards.md`.
  It defines scene mapping, actual composer attachment, exact-text separation,
  and the mandatory rejection of uploaded reference images mistakenly detected
  as newly generated CDP outputs. It also makes operator visual corrections a
 regeneration gate: explicit bans such as `피켓을 들게 하지 마` require a new
 reference-guided Image2 result with zero forbidden objects, not local erasure.
 The information logo is fixed at CapCut UI `50% / X 0 / Y 1500`
 (`scale=0.5`, `transform.y=0.78125`); older `로고 두 배` guidance is invalid.
 Record layout changes as root-safe overrides and verify a new 1080×1920 frame.
 The same reference defines stock-material cache cleanup, current-draft authority
 selection, and destination-safe CapCut cloud upload; the TOP55 caption gap is
 21px below the media window.
  When the operator supplies
  multiple ranked stills across messages, also read
  `references/operator-ranked-image-intake.md`: the latest explicit rank label
  overrides message-order inference, originals remain immutable, multiple
  multiple images per rank are valid, and an `각각 이미지 다시 올려봐` request must
  return every original as individually labeled media rather than only a contact
  sheet. A `HISTORICAL_OR_RETRO` QA label is descriptive, not a rejection: when
  the operator says the asset is an intentional `후킹`/retro contrast, record it
  as `APPROVED` with `role=intentional_retro_hook`, preserve its within-rank order,
  and pair it with a current-company identifier when useful. When a later same-rank
  image replaces an unverified or synthetic production asset, preserve both
  originals, record the replacement in `40_assets/asset_decisions.json`, remove
  only the superseded builder input, and regenerate/verify the expected assembly
  count. Also read
  `references/gunlimbo-top55-image2-production-lessons.md` for regular-vs-temporary
  ChatGPT image chats, editorial reaction labels vs verified quotes, abnormal TTS
  silence cleanup, subtitle `{"cues":[...]}` input, root prototype-count semantics,
  and installed-draft animation/text readback. Measure the active frame's
  transparent opening for generated assets; for supplied stills, preserve the
  originals under the source-video intake folder with ordered role labels,
  dimensions, SHA-256, visible logo/text notes, and operator-stated dialogue or
  story intent before using them in a script or CapCut plan. Generate real
  ChatGPT Image/CDP PNGs at the measured ratio when generation is requested, QA a
  single sample before batching, and deliver a contact sheet plus individual
  files before replacing project media. Stock photos or locally drawn
  infographic cards are not substitutes when the operator asked for generated
  images. After approval, preserve the prior editable project, create a fresh
  versioned `..._vN_Hermes` clone, and update project/version metadata; never
  silently overwrite the previous project.
- When a current-affairs or political clip must play first with the real speaker
  quote and the remaining visuals should explain the situation rather than
  depict the politician, read
  `references/gunlimbo-source-quote-first-situation-visuals.md`. Preserve the
  actual quote on `A_SOURCE`, start 군림보 explanation after it, remove narration
  duplication, and use situation-first Image2 scenes.
- For repeated flower/stock imagery, stale material identity, suffixed-folder path
  mismatch, post-open placeholder mirrors, or a Home row showing `0.0B`, follow
  `references/capcut-stock-cache-v2-rebuild-readback.md`. Rebuild a fresh version,
  preserve the full root-meta row shape, require real playback checkpoints, and
  select post-open authority by valid existing media paths—not newest mtime alone.
- For this operator, CapCut production is not complete at local-project PASS.
  Completion requires upload to `TAKKTWO/macmini`, direct cloud-row readback of
  name, size, duration, type, and edit time, and post-upload local draft readback.
  The final chat report must include upload title, concise content summary, and
  linked sources. Do not select another account space or folder; affirm an
  approved duplicate/re-upload prompt for the latest verified project.
- Mark one or two emotional peak images (`폭발`, `분노`, `반전`, `와우`) as
  high-impact slots and use `불꽃 회오리`, `불꽃 스와이프`, or `불꽃 마법`.
- TOP5 uses source-backed rank facts. 군림보 preserves approved speaker audio.
  With meaningful source speech, run:

  ```text
  scripts/prepare_top5isu_source_vocals.py <complete-source> <output-dir> \
    --python ~/.openclaw/venvs/demucs/bin/python --model htdemucs_ft
  ```

  Run whole-source Demucs/approved vocal isolation before cutting Q clips, cut
  Q clips only from `vocals_stem`, mute original mixed video audio, and require
  residual-music plus artifact review PASS. Failure is
  `WAIT_VOCAL_ISOLATION`, never a mixed-audio fallback.
  If source analysis proves there is no meaningful source speech, the only
  exception is `source_speaker_mode=no_meaningful_source_speech` with
  `speaker_segments=[]`, `source_dialogue_analysis_status=NO_DIALOGUE`, and
  `source_cta_reuse=false`.

### CAPCUT_PROJECT

The target is a real local editable CapCut project, not a JSON-only report.

#### Paired mirror layer contract

- 원본/클린 `VIDEO`를 하단에 두고, 동일한 source/target range의 `VIDEO_MIRROR`를 바로 위에 별도 레이어로 복제한다.
- 수평 미러링은 `VIDEO_MIRROR`에만 적용한다. 하단 `VIDEO`에는 `flip.horizontal=false`를 유지한다.
- `FRAME`, `LOGO`, `TTS_TEXT`, `SOURCE_TEXT`, `T2`, `T1`, 효과 등 다른 요소는 두 VIDEO 레이어보다 위에 둔다.
- 원본 영상의 baked-in 글자·자막·로고가 남아 있으면 해당 픽셀까지 뒤집히므로 단일 영상 클립 자체를 미러링하지 않는다. 먼저 clean/OCR gate를 통과하거나 미러링을 중단한다.
- builder가 `VIDEO`와 `VIDEO_MIRROR` 두 레이어를 생성·검증하지 못하면 `FAIL_PAIRED_MIRROR_LAYER_UNSUPPORTED`로 중단한다. `all_video_mirrored=true`만으로 PASS하지 않는다.
- 운영자가 `영상 그대로`라고 하면 crop·scale·unsharp·contrast·saturation 재인코딩을 금지한다. 명시 승인된 구간 trim과 오디오 분리만 허용한다.

#### MIX_MODE: video + Image2 sequencing

운영자가 `믹스모드`, `영상+이미지 조합`, 또는 동등한 표현을 쓰면 임의의 50:50 교차배치를 금지한다.

1. 이미지 위치보다 우라까이 구조 순서를 먼저 확정한다. 예를 들어 원본 `1-2-3-4-5`를 `5-3-4-5-1-2`처럼 재배치하거나 결과·마지막 장면을 분할해 1번 또는 2번 위치로 앞당길 수 있다.
2. 후킹 강도는 원본 순서가 아니라 확정된 target 타임라인에서 판단한다. 앞당긴 결과 장면과 중간 강훅 장면을 우선 후보로 삼는다.
3. 전체 영상에서 후킹이 강한 VIDEO 장면 2~4개만 선정한다. 첫 1~2장은 앞부분의 1번·2번 후킹을 강화하는 데 우선 사용하고, 필요한 경우 나머지를 중간 강훅에 사용한다.
4. 선정 장면의 끝부분 또는 후킹이 가장 강한 실제 프레임을 참고 이미지로 삼아 ChatGPT Image2 효과 이미지를 만든다.
5. 각 `DERIVED_IMAGE`는 참고한 후킹 VIDEO 바로 뒤에 배치한다. 모든 영상 뒤에 반복 삽입하거나 영상보다 먼저 보여주지 않는다.
6. 이미지 수는 회차당 2~4장이다. 후킹 강화에 필요한 장면만 사용하며 임의의 50:50 분량·기계적 영상/이미지 교차배치를 금지한다.
7. VIDEO는 하단 원본/클린 레이어와 바로 위 VIDEO_MIRROR 레이어를 사용하고, 제목·자막·로고·효과·전환·오디오 등 나머지 구조는 기존 승인 템플릿과 동일하게 유지한다.
8. 각 이미지는 정지 삽입물이 아니라 바로 앞 후킹 장면을 강조하는 효과 이미지로 설계하고 승인된 전환·강조 효과를 적용한다.
9. manifest에는 원본 구조, 최종 구조, 각 묶음의 `video_source_range`, `video_target_range`, `hook_strength_reason`, `derived_reference_frame`, `image_target_range`를 기록한다. 구조 재배치 전에 이미지를 정했거나 앞 VIDEO와 참조 연결이 없거나 이미지 수가 2~4장을 벗어나면 `FAIL_MIX_IMAGE_HOOK_CONTRACT`로 중단한다.

1. Validate the immutable root package with
   `scripts/validate_top5isu_package.py`.
2. Clone the verified root project `top5isu`; never edit the root.
3. Require fresh project and timeline IDs.
4. Replace all sample media and relink only current episode files.
5. Preserve exact track order:

```text
IMAGE_EFFECT_PRESETS,FRAME,LOGO,TTS_TEXT,SOURCE_TEXT,T2,T1
```

6. Preserve the TOP55 root layout: centered image transform, full-duration
   `FRAME` and `LOGO`, `TTS_TEXT` for narration captions, `SOURCE_TEXT` for
   source labels, and separate two-line title tracks `T1` and `T2`.
7. Require exactly one transition animation on every image. Require one or two
   high-impact image indices using `불꽃 회오리`, `불꽃 스와이프`, or
   `불꽃 마법`; ordinary images alternate the generic transition prototypes.
8. Resolve audio lanes as `A_TTS`, `A_SOURCE`, `A_SFX`, and `A_BGM`.
9. Before build, create ordered `asset_*.png` or `scene_*.png` inputs; other
   manifest filenames are not builder inputs. Use N images with N+1 boundaries
   and a real Markdown timeline table in the blueprint. Subtitle cues may use
   `start/end` or `start_sec/end_sec`; the builder normalizes both. If only the
   final cue exceeds measured audio by at most 1 ms from decimal rounding, clamp
   it to exact `duration_us`; larger overruns remain `FAIL subtitle cue range`.
10. Before invoking `build_top5isu_capcut.py`, read the current `build_project()` signature and call it with named keyword arguments; do not rely on a remembered positional order. Build in a short same-volume `._b-<UUID>` staging folder, pass the final draft path to the builder from the first build so generated media authority paths are already final, and promote only after staging PASS. Run `scripts/validate_top5isu_track_mapping.py` and `scripts/validate_top5isu_capcut_draft.py` against the promoted project.
11. Before first app launch, read `references/capcut-stale-subdraft-cloud-replacement.md` and verify the root `draft_content.json`, root `draft_info.json`, active Timeline `draft_content.json`, active Timeline `draft_info.json`, root/Timeline `template-2.tmp`, and every existing `subdraft/*/draft_content.json` are semantically identical where they are full-content mirrors. If correct physical images or hashes still render as one repeated template/stock image, also read `references/capcut-material-identity-cache-collision.md`; diagnose inherited material identity and stock cache metadata instead of repeatedly changing file paths. After staging promotion, replace the old staging prefix in every JSON, require all active media paths to exist, require zero stale staging prefixes, and keep distinct-schema `template.json` / `attachment/patch/mini_draft.json` as path-rewrite-only files. A stale `draft_info.json` or Timeline mirror can make CapCut show `미디어 연결 0/N` even when root materials point to files that exist. Cancel that dialog, quit CapCut, repair offline, and reopen; never manually reconnect one-by-one as the first response. After CapCut opens, it may rewrite mirror metadata; close the app, re-read the newest root draft, resynchronize full-content mirrors, and rerun validation before the final report. A stale subdraft can make CapCut show template sample media even when root materials point to the correct assets, so any subdraft mismatch is `FAIL_TOP5ISU_CONTENT_MIRROR`. If the operator visually reports placeholder media despite validator PASS, treat the visual report as a failed gate until actual media, segment references, app preview, and cloud replacement are verified. Verify `root_meta_info.json` contains exactly one matching project registration and that its `draft_json_file` points to the promoted root `draft_info.json`. If registration is absent, add it atomically while CapCut is closed; do not guess legacy counter semantics. Required `template-2.tmp` mirrors are allowlisted and must not be removed by a global `*.tmp` cleanup.
12. Default completion is an editable project folder plus current draft
    readback/hash, validators, and assembly report. Open/play the CapCut app only
    when the operator explicitly requests it.

#### Operator Manual Edit Policy

After the operator opens CapCut, manual edits, duration changes, track additions,
text corrections, and timing adjustments are normal production work:

```text
manual_edit_policy=MANUAL_EDIT_EXPECTED
manual_edit_difference_is_failure=false
current_draft_reread_required=true
```

Do not compare the edited project to an old snapshot and raise a problem merely
because values changed. Re-read the current `draft_content.json` and current
project metadata. Use `validate_top5isu_capcut_draft.py --manual-edit-expected`
to report the observed current state without failing on user-created structural
differences. Only unreadable/missing project data or an explicit new safety
blocker may stop re-entry.

Any attempt to use `shrt white` stops with
`FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN`.

### FINAL_REPORT

Read `references/report-contract.md`. `FINAL_LOCK` requires:

- blueprint PASS
- contract PASS
- template package PASS
- track mapping PASS
- CapCut draft PASS
- real local project path and fresh IDs
- app visual/playback review only when explicitly requested
- no sample media or `.bak` residue
- final export loudness measurement when an export exists
- `90_reports/assembly_report.md` with `# 조립도 보고서`
- exact `CapCut 프로젝트명`, project folder name, and local project path
- final `## 캣컵복사하기` block whose last non-empty line is the exact project name
- `scripts/validate_top5isu_assembly_report.py` PASS

The assembly report is written after CapCut assembly and must end with the exact
CapCut project file/folder name so the operator can copy it directly. Later
operator edits are `MANUAL_EDIT_EXPECTED` and do not invalidate the report solely
because duration, tracks, text, or timing changed; re-read the current draft and
issue a revised report only when requested.

After project-file completion, read `references/production-index-sync.md` and
automatically update the fixed production ID, latest CapCut pointer, version
history, upload information, and lightweight OneDrive episode. Keep raw CapCut
drafts and heavy media out of OneDrive. Missing Trend Hunter server source or
`video_id` does not undo project completion: write
`WAIT_TREND_HUNTER_VIDEO_ID`, complete the local/OneDrive metadata update, and
do not claim that the server card was updated.

YouTube/social upload, publish, schedule, and delete actions require explicit
operator approval. CapCut cloud project handoff is different from publishing:
the operator has standing approval for every verified completed project to be
uploaded to `TAKKTWO/macmini` and duplicate-safe re-uploaded there. Do not treat
OneDrive copying as satisfying that cloud-sync completion gate.

### CapCut Cloud Sync For Office Handoff

In a CapCut-project context, interpret the operator's `동기화`, `프로젝트 동기화`, or `캣컵 동기화` as CapCut cloud project upload/sync—not OneDrive copying. When the operator asks to synchronize a completed CapCut project so it can be opened at the office, read `references/capcut-cloud-sync-office-handoff.md`, run its generated-project cloud-upload preflight, and only then open CapCut.

For this operator the fixed cloud destination is:

```text
TAKKTWO / macmini
```

Do not inspect, select, recommend, or upload to another account space or folder.
Confirm the destination breadcrumb before the final upload click.
Before upload, open the promoted project once, verify the editor timeline duration and media, then return to Home so CapCut refreshes the project-row size and rounded duration; a cloned `root_meta_info.json` row may temporarily display the prototype duration until this open/close cycle. Require the Home duration to agree with the current draft before cloud upload.
To force the fixed destination, first enter `TAKKTWO / macmini`, then use
`업로드 → 프로젝트 업로드` and select the local project. Do not rely on Home
right-click upload: an existing cloud association may send it to `자동 업로드`
without a destination dialog. After a duplicate upload, re-read
`root_meta_info.json`; CapCut may rename both the cloud row and local project
folder with `(1)` and the validator/report must use the new actual path.
If CapCut warns that the same project already exists and asks whether to upload
again, replace, or continue, choose the affirmative continuation for the latest
verified project; the operator has explicitly approved this duplicate-safe
behavior. A closed dialog is not completion evidence—open the account-space
`MAC` folder and read back the cloud project name, size, duration, type, and
latest edit time before reporting success. Record CapCut cloud sync separately
from YouTube upload and resync only lightweight reports to OneDrive.

## Template Locks

Read `references/top5isu-template-contract.md`. For rebuilding the immutable
root from an operator-authored CapCut project, also read
`references/top55-root-rebuild.md`.

```text
required_tracks=IMAGE_EFFECT_PRESETS,FRAME,LOGO,TTS_TEXT,SOURCE_TEXT,T2,T1
protected_tracks=FRAME,LOGO,T1,T2,TTS_TEXT,SOURCE_TEXT
image_prototype_count_required=4
episode_image_count=dynamic
image_transition_animation_required=true
high_impact_effect_allowed=불꽃 회오리,불꽃 스와이프,불꽃 마법
high_impact_effect_required_count=1..2
sample_media_policy=replace_all
frame_full_duration=true
logo_full_duration=true
image_ui_y=0
image_json_transform_y=0.0
canvas=1080x1920
clone_required=true
root_template_mutation=false
fresh_project_id_required=true
fresh_timeline_id_required=true
```

## Profile Locks

### TOP5

- Fixed narration order: greeting -> topic explanation -> 5 -> 4 -> 3 -> 2 -> 1 -> close.
- Each rank is an independent `ranking_item`.
- Verify every amount, statistic, date, and ranking basis.
- TTS is primary; source audio is muted unless a verified quote is selected.

### 군림보

- Story order: setup -> complication -> emotional turn -> close.
- Before cutting any Q speaker clip, isolate vocals from each complete original
  source with Demucs/approved equivalent. Q clips must come from `vocals.wav`.
- Mute original mixed video audio; keep isolated Q speech on `A_SOURCE` and TTS
  on `A_TTS`.
- Missing/failed isolation stops at `WAIT_VOCAL_ISOLATION`; mixed Q audio is
  never an automatic fallback.
- Preserve approved speaker segments and keep them audible.
- TTS explains around source speech and must not replace the key speaker line.
- `speaker_segments_preserved=true` and `speaker_mute_forbidden=true`.

## 감시체계 변경 원칙

TOP5 감시·validator·상태계약을 수정할 때는 `references/executable-monitoring-hardening.md`를 먼저 읽는다. 기존 `production_contract.yaml`, `top5_harness.py`, 상태기계 및 validator를 감사한 뒤 실제 누락만 보강하며, 다른 스킬과 형식을 맞추기 위한 중복 프로토콜·Schema·하네스는 만들지 않는다. 실패 fixture의 RED→GREEN과 새 임시 폴더 격리 검증 없이 감시체계 변경을 완료로 보고하지 않는다.

## Codex 실행 워커 규약

TOP5·군림보 쇼츠의 FFmpeg, TTS, CDP, CapCut builder, validator, manifest 또는 상태기계 작업을 Codex에 위임할 때는 **REQUIRED REFERENCE:** `references/codex-fast-execution-for-shorts.md`를 먼저 읽는다. `FAST_PROVE_FIX_TEST_CONTINUE` JSON 원문을 작업 지시보다 먼저 넣고, UTF-8 `PROMPT.md`, 작업별 독립 cwd, 승인·금지 파일 목록, 테스트와 보고 형식을 고정한다. 읽기 전용 검수에는 `--write`를 사용하지 않는다. Codex는 실행·수정·자체 테스트만 맡고 Hermes가 실제 환경에서 다시 검증한다. Claude 검수 단계를 추가하지 않는다. Image2 생성 대기, CapCut GUI 클릭, 클라우드 업로드, 시각·음성 최종 판단에는 이 Codex 규약을 억지로 적용하지 않는다.

## Validation Order

```text
1. prepare_top5isu_source_vocals.py for each complete source when meaningful speaker speech exists
2. validate_top5isu_rework_intake.py when a clean-video rework manifest exists
3. build_top5isu_writer_packet.py
4. run_top5isu_chatgpt_writer.py --submit
5. validate_top5isu_writer_response.py
6. validate_top5isu_blueprint.py
7. validate_top5isu_contract.py
8. validate_top5isu_package.py
9. validate_top5isu_track_mapping.py
10. validate_top5isu_capcut_draft.py
11. validate_top5isu_assembly_report.py
12. optional CapCut app visual/playback review only when explicitly requested
13. final export loudness measurement when applicable
```

Project-file completion requires an editable local project, current draft
readback/hash, validators, and assembly report. App playback is not a default
gate. If any applicable gate fails, repair only inside this skill and rerun the
failed and downstream gates.

## Portable and Safety Rules

- Keep OneDrive manifests relative and the root archive immutable.
- Keep skill/runtime backups outside every configured skill-discovery directory;
  a backup containing `SKILL.md` creates an ambiguous duplicate skill.
- Reject foreign absolute user-profile paths and `.bak` files.
- Do not edit a local CapCut draft while CapCut is open.
- Never output secrets, cookies, tokens, or authentication files.
- Do not publish automatically without explicit approval.
