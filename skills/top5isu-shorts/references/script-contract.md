# top5isu Standalone Script Contract

The script stage is owned inside `top5isu-shorts`; no external script skill
handoff is allowed. The logged-in ChatGPT page is an internal
`chatgpt_browser` writer backend controlled by this skill.

## Required Blueprint

`20_script/design_blueprint.md` must contain:

- `# 설계도`
- `## 기본 정보`
- `## 제작 판단`
- `## 대본`
- `## 트랙별 타임라인`
- `## 오디오 계획`
- `## 이미지 계획`
- `## CapCut 프로젝트`
- `## 검증 및 보고`

It must lock `style_profile: top5|gunlimbo` and `standalone_factory: true`.

## Internal Writer Flow

```text
EVIDENCE_PACKET
-> CHATGPT_WRITER
-> SCRIPT_QA
```

1. Codex/Hermes structures verified facts into
   `10_analysis/evidence_packet.json` and `writer_packet.json`.
2. `run_top5isu_chatgpt_writer.py --submit` opens a fresh ChatGPT conversation
   in the managed `openclaw` browser profile.
3. It requests `높음` reasoning when visible and submits only bounded,
   non-sensitive text.
4. ChatGPT returns sentinel-delimited JSON.
5. `validate_top5isu_writer_response.py` verifies facts, numbers, rank order,
   fixed greeting, forbidden phrases, and visible text marks.
6. Only the PASS response becomes the visible/factual script authority:
   `final_script.json` and `tts_copy_text.txt`.
7. Before TTS generation, create a separate `tts_spoken_copy.txt` from that
   authority. `tts_spoken_copy.txt` is the exact API input and may expand
   numerals or English abbreviations into Korean pronunciation, but it must not
   change company names, ranks, amounts, dates, or claims.
8. Never send `final_script.json` or `tts_copy_text.txt` directly to a TTS
   provider when unstable numeric/English tokens remain. Never overwrite the
   visible/caption authority with pronunciation spellings.

```text
display_caption_authority=final_script.json,tts_copy_text.txt
speech_api_authority=tts_spoken_copy.txt
same_facts_required=true
separate_files_required=true
```

```text
clipboard_forbidden=true
browser_identifiers_in_manifest=forbidden
```

## TOP5 Script

Use fixed greeting -> topic explanation -> 5 -> 4 -> 3 -> 2 -> 1 -> close.
The fixed greeting is `안녕하세요. 오늘의 탑파이브 주제인데요.` Every rank
carries source-backed fact IDs, narration, TTS timing, image role, and verified
amount/statistic when applicable.

## Gunlimbo Script

Use setup -> complication -> emotional turn -> close. Separate explanation TTS
from verified speaker speech. Record every preserved speaker range before
production.

## Outputs

- `design_blueprint.md`
- `writer_prompt.md`
- `writer_response.txt`
- `writer_response.json`
- `script_qa.json`
- `model_run_manifest.json`
- `final_script.json` — validated facts and visible script authority
- `tts_copy_text.txt` — display/caption text with normal numerals and names
- `tts_spoken_copy.txt` — pronunciation-only TTS API input
- `top5isu_build_contract.json`

No script may be treated as production authority until writer QA, blueprint,
and build-contract validation pass. ChatGPT failure never silently falls back to
another skill or an unvalidated script.
