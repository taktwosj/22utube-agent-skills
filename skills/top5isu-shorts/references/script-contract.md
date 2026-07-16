# top5isu Standalone Script Contract

The script stage is owned inside `top5isu-shorts`; no external script handoff is allowed.

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

## TOP5 Script

Use: fixed greeting -> topic explanation -> 5 -> 4 -> 3 -> 2 -> 1 -> close.
Every rank carries its source, date/basis, narration, TTS timing, image role, and amount/statistic when applicable.

## Gunlimbo Script

Use: setup -> complication -> emotional turn -> close. Separate explanation TTS from verified speaker speech. Record every preserved speaker range before production.

## Outputs

- `design_blueprint.md`
- `script.json`
- `tts_copy_text.txt`
- `top5isu_build_contract.json`

No script may be treated as production authority until blueprint and build-contract validation pass.
